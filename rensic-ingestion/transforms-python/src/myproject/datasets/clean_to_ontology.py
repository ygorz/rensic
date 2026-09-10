"""
Rensic Ingestion — Clean & Map to Ontology Schema
===================================================

Transforms raw asset transfer data into ontology-backed datasets.
Fixes: proper timestamp parsing, null handling, type casting.
"""
import polars as pl
from transforms.api import transform, Input, Output

from myproject.config import remap_pipeline_case_id


# ===========================================================================
# TRANSFORM 1: Build Address objects
# ===========================================================================
@transform.using(
    addresses=Output("/George Gorzhiyev-a8216a/Rensic/data-integration/clean/addresses"),
    raw_transfers=Input("/George Gorzhiyev-a8216a/Rensic/data-integration/raw/raw_asset_transfers"),
    known_entities=Input("/George Gorzhiyev-a8216a/Rensic/data-integration/clean/known_entities"),
)
def build_addresses(addresses, raw_transfers, known_entities):
    df = raw_transfers.polars(lazy=True)

    # Parse timestamp strings to proper datetime
    df = df.with_columns(
        pl.col("block_timestamp").str.to_datetime(format="%+", strict=False).alias("block_ts")
    )

    senders = df.select(
        pl.col("chain_id"),
        pl.col("from_address").alias("wallet_address"),
        pl.col("block_ts"),
        pl.when(pl.col("category").is_in(["external", "internal"]))
        .then(pl.col("value")).otherwise(0.0).alias("value_out"),
        pl.lit(0.0).alias("value_in"),
    ).filter(pl.col("wallet_address") != "")

    receivers = df.select(
        pl.col("chain_id"),
        pl.col("to_address").alias("wallet_address"),
        pl.col("block_ts"),
        pl.lit(0.0).alias("value_out"),
        pl.when(pl.col("category").is_in(["external", "internal"]))
        .then(pl.col("value")).otherwise(0.0).alias("value_in"),
    ).filter(pl.col("wallet_address") != "")

    combined = pl.concat([senders, receivers])

    agg_df = (
        combined.group_by(["chain_id", "wallet_address"])
        .agg(
            pl.col("block_ts").min().alias("first_seen"),
            pl.col("block_ts").max().alias("last_seen"),
            pl.col("value_in").sum().alias("total_value_in_eth"),
            pl.col("value_out").sum().alias("total_value_out_eth"),
            pl.len().alias("transaction_count"),
        )
        .with_columns(
            (pl.col("chain_id") + pl.lit(":") + pl.col("wallet_address")).alias("address_id"),
            (pl.col("total_value_in_eth") - pl.col("total_value_out_eth")).alias("net_flow_eth"),
        )
        # Cast transaction_count to Int64 (Long) to match ontology property type
        .with_columns(pl.col("transaction_count").cast(pl.Int64))
        .collect()
    )

    # Left-join curated labels. Do not invent riskScore. Leave address_type unset
    # unless a later pass can prove contract vs EOA.
    pack = known_entities.polars()
    if isinstance(pack, pl.LazyFrame):
        pack = pack.collect()
    if pack.is_empty() or "address" not in pack.columns:
        agg_df = agg_df.with_columns(pl.lit(None).cast(pl.Utf8).alias("address_label"))
    else:
        # Official pack beats community on the same address; then category rank.
        tier_rank = (
            pl.when(
                pl.col("tier").cast(pl.Utf8).fill_null("official").str.to_lowercase()
                == "community"
            )
            .then(1)
            .otherwise(0)
        )
        cat_rank = (
            pl.when(pl.col("category").str.to_lowercase() == "sanctions")
            .then(0)
            .when(pl.col("category").str.to_lowercase() == "mixer")
            .then(1)
            .when(pl.col("category").str.to_lowercase() == "gambling")
            .then(2)
            .when(pl.col("category").str.to_lowercase() == "exchange")
            .then(3)
            .when(pl.col("category").str.to_lowercase() == "shop")
            .then(4)
            .when(pl.col("category").str.to_lowercase() == "protocol")
            .then(5)
            .when(pl.col("category").str.to_lowercase() == "person")
            .then(6)
            .otherwise(9)
        )
        labels = (
            pack.with_columns(
                pl.col("chain").cast(pl.Utf8).str.strip_chars().str.to_lowercase().alias("_jc"),
                pl.col("address").cast(pl.Utf8).str.strip_chars().str.to_lowercase().alias("_ja"),
                tier_rank.alias("_tier_rank"),
                cat_rank.alias("_rank"),
                pl.col("name").cast(pl.Utf8).str.strip_chars().alias("address_label"),
            )
            .filter((pl.col("_ja") != "") & pl.col("address_label").is_not_null())
            .sort(["_tier_rank", "_rank", "_jc", "_ja"])
            .group_by(["_jc", "_ja"], maintain_order=True)
            .agg(pl.col("address_label").first())
        )
        agg_df = (
            agg_df.with_columns(
                pl.col("chain_id").cast(pl.Utf8).str.strip_chars().str.to_lowercase().alias("_jc"),
                pl.col("wallet_address").cast(pl.Utf8).str.strip_chars().str.to_lowercase().alias("_ja"),
            )
            .join(labels, on=["_jc", "_ja"], how="left")
            .drop("_jc", "_ja")
        )

    addresses.write_table(agg_df)


# ===========================================================================
# TRANSFORM 2: Build Transaction objects
# ===========================================================================
@transform.using(
    transactions=Output("/George Gorzhiyev-a8216a/Rensic/data-integration/clean/transactions"),
    raw_transfers=Input("/George Gorzhiyev-a8216a/Rensic/data-integration/raw/raw_asset_transfers"),
)
def build_transactions(transactions, raw_transfers):
    """One row per native ETH leg (external or internal).

    Do not collapse a hash to a single from/to. A swap can send ETH from a
    router to a contract and from that contract to the file wallet in the
    same hash. Fund flow needs each of those legs.
    """
    df = remap_pipeline_case_id(raw_transfers.polars(lazy=True))

    tx_df = (
        df.filter(pl.col("category").is_in(["external", "internal"]))
        .with_columns(
            pl.int_range(pl.len())
            .over(["chain_id", "tx_hash", "category", "from_address", "to_address", "value"])
            .alias("_n"),
        )
        .with_columns(
            pl.col("block_timestamp").str.to_datetime(format="%+", strict=False).alias("block_timestamp"),
            (
                pl.col("chain_id").cast(pl.Utf8)
                + pl.lit(":")
                + pl.col("tx_hash").cast(pl.Utf8)
                + pl.lit(":")
                + pl.col("category").cast(pl.Utf8)
                + pl.lit(":")
                + pl.col("from_address").cast(pl.Utf8)
                + pl.lit(":")
                + pl.col("to_address").cast(pl.Utf8)
                + pl.lit(":")
                + pl.col("value").cast(pl.Utf8)
                + pl.lit(":")
                + pl.col("_n").cast(pl.Utf8)
            ).alias("transaction_id"),
            (pl.col("chain_id") + pl.lit(":") + pl.col("from_address")).alias("from_address_id"),
            (pl.col("chain_id") + pl.lit(":") + pl.col("to_address")).alias("to_address_id"),
            pl.col("value").alias("value_eth"),
            pl.col("category").alias("transaction_category"),
        )
        .select(
            "chain_id",
            "tx_hash",
            "block_number",
            "block_timestamp",
            "from_address",
            "to_address",
            "value_eth",
            "transaction_category",
            "case_id",
            "transaction_id",
            "from_address_id",
            "to_address_id",
        )
        .collect()
    )

    transactions.write_table(tx_df)


# ===========================================================================
# TRANSFORM 3: Build Token Transfer objects
# ===========================================================================
@transform.using(
    token_transfers=Output("/George Gorzhiyev-a8216a/Rensic/data-integration/clean/token_transfers"),
    raw_transfers=Input("/George Gorzhiyev-a8216a/Rensic/data-integration/raw/raw_asset_transfers"),
)
def build_token_transfers(token_transfers, raw_transfers):
    df = raw_transfers.polars(lazy=True)

    token_df = (
        df.filter(pl.col("category").is_in(["erc20", "erc721", "erc1155"]))
        .with_row_index("row_idx")
        .with_columns(
            # Parse timestamp
            pl.col("block_timestamp").str.to_datetime(format="%+", strict=False).alias("block_ts"),
            # Composite keys
            (pl.col("chain_id") + pl.lit(":") + pl.col("tx_hash") + pl.lit(":") + pl.col("row_idx").cast(pl.Utf8)).alias("transfer_id"),
            (pl.col("chain_id") + pl.lit(":") + pl.col("tx_hash")).alias("transaction_id"),
            (pl.col("chain_id") + pl.lit(":") + pl.col("from_address")).alias("from_address_id"),
            (pl.col("chain_id") + pl.lit(":") + pl.col("to_address")).alias("to_address_id"),
            (pl.col("chain_id") + pl.lit(":") + pl.col("token_contract_address")).alias("token_contract_address_id"),
            pl.col("row_idx").cast(pl.Int32).alias("log_index"),
            pl.col("category").alias("token_standard"),
            pl.col("asset").alias("token_symbol"),
            pl.col("value").alias("amount"),
        )
        .select([
            "transfer_id", "transaction_id", "chain_id",
            "token_contract_address", "token_contract_address_id", "token_symbol", "token_standard",
            "amount", "token_id", "log_index", "from_address_id", "to_address_id",
            pl.col("block_ts").alias("block_timestamp"),
        ])
        .collect()
    )

    token_transfers.write_table(token_df)


# ===========================================================================
# TRANSFORM 4: Build Contract Interaction objects
# ===========================================================================
@transform.using(
    contract_interactions=Output("/George Gorzhiyev-a8216a/Rensic/data-integration/clean/contract_interactions"),
    raw_transfers=Input("/George Gorzhiyev-a8216a/Rensic/data-integration/raw/raw_asset_transfers"),
)
def build_contract_interactions(contract_interactions, raw_transfers):
    df = raw_transfers.polars(lazy=True)

    interactions_df = (
        df.filter(pl.col("token_contract_address").is_not_null())
        .group_by(["chain_id", "tx_hash", "token_contract_address"])
        .agg(
            pl.col("block_timestamp").first().alias("raw_ts"),
            pl.col("category").first().alias("interaction_category"),
        )
        .with_row_index("trace_idx")
        .select(
            (pl.col("chain_id") + pl.lit(":") + pl.col("tx_hash") + pl.lit(":") + pl.col("trace_idx").cast(pl.Utf8)).alias("interaction_id"),
            (pl.col("chain_id") + pl.lit(":") + pl.col("tx_hash")).alias("transaction_id"),
            pl.col("chain_id"),
            pl.col("token_contract_address").alias("contract_address"),
            (pl.col("chain_id") + pl.lit(":") + pl.col("token_contract_address")).alias("contract_address_id"),
            pl.col("raw_ts").str.to_datetime(format="%+", strict=False).alias("block_timestamp"),
            pl.col("interaction_category"),
        )
        .collect()
    )

    contract_interactions.write_table(interactions_df)


# ===========================================================================
# TRANSFORM 5: Case Address membership (case-scoped observation)
# ===========================================================================
@transform.using(
    case_addresses=Output("/George Gorzhiyev-a8216a/Rensic/data-integration/clean/case_addresses"),
    raw_transfers=Input("/George Gorzhiyev-a8216a/Rensic/data-integration/raw/raw_asset_transfers"),
    addresses=Input("/George Gorzhiyev-a8216a/Rensic/data-integration/clean/addresses"),
    requests=Input("/George Gorzhiyev-a8216a/Rensic/data-integration/raw/ingestion_requests"),
)
def build_case_addresses(case_addresses, raw_transfers, addresses, requests):
    """
    One row per (case, address). Seed wallets from ingestion requests are hop 0;
    every other address seen in that case's transfers is discovered.

    address_id is chain:hex (hex lowercased). If seed_address already includes a
    chain prefix, only the last segment is treated as the hex so we do not emit
    ethereum:ethereum:0x... keys that miss the Address join.

    Metrics prefer case-scoped counts from this case's raw_asset_transfers
    (unique tx hash, native in/out). Address pipeline metrics fill remaining nulls.
    """
    raw = remap_pipeline_case_id(raw_transfers.polars(lazy=True))
    addr = addresses.polars(lazy=True)
    req = remap_pipeline_case_id(requests.polars(lazy=True))

    def address_id_expr(chain_col, hex_col):
        chain_part = (
            pl.col(chain_col).cast(pl.Utf8).fill_null("").str.strip_chars().str.to_lowercase()
        )
        hex_part = (
            pl.col(hex_col)
            .cast(pl.Utf8)
            .fill_null("")
            .str.strip_chars()
            .str.to_lowercase()
            .str.split(":")
            .list.get(-1)
        )
        return (chain_part + pl.lit(":") + hex_part).alias("address_id")

    raw = raw.with_columns(
        pl.col("block_timestamp").str.to_datetime(format="%+", strict=False).alias("block_ts")
    )

    senders = raw.select(
        pl.col("case_id"),
        address_id_expr("chain_id", "from_address"),
    )
    receivers = raw.select(
        pl.col("case_id"),
        address_id_expr("chain_id", "to_address"),
    )
    discovered = (
        pl.concat([senders, receivers])
        .filter(pl.col("address_id").str.split(":").list.get(-1) != "")
        .unique()
    )

    seeds = (
        req.select(
            pl.col("case_id"),
            pl.col("seed_address"),
            pl.col("chain_ids"),
        )
        .with_columns(pl.col("chain_ids").str.split(","))
        .explode("chain_ids")
        .with_columns(address_id_expr("chain_ids", "seed_address"))
        .filter(pl.col("address_id").str.split(":").list.get(-1) != "")
        .select("case_id", "address_id")
        .unique()
        .with_columns(
            pl.lit("seed").alias("membership_role"),
            pl.lit(0).cast(pl.Int32).alias("hop_distance"),
            pl.lit("Seed wallet from ingestion request").alias("inclusion_reason"),
        )
    )

    discovered_only = (
        discovered.join(seeds, on=["case_id", "address_id"], how="anti")
        .with_columns(
            pl.lit("discovered").alias("membership_role"),
            pl.lit(1).cast(pl.Int32).alias("hop_distance"),
            pl.lit("Seen in case transfers").alias("inclusion_reason"),
        )
    )

    membership = pl.concat([seeds, discovered_only], how="diagonal")

    native = pl.col("category").is_in(["external", "internal"])
    from_legs = raw.select(
        pl.col("case_id"),
        address_id_expr("chain_id", "from_address"),
        pl.col("tx_hash"),
        pl.col("block_ts"),
        pl.when(native).then(pl.col("value")).otherwise(0.0).alias("value_out"),
        pl.lit(0.0).alias("value_in"),
    )
    to_legs = raw.select(
        pl.col("case_id"),
        address_id_expr("chain_id", "to_address"),
        pl.col("tx_hash"),
        pl.col("block_ts"),
        pl.lit(0.0).alias("value_out"),
        pl.when(native).then(pl.col("value")).otherwise(0.0).alias("value_in"),
    )
    case_metrics = (
        pl.concat([from_legs, to_legs])
        .filter(pl.col("address_id").str.split(":").list.get(-1) != "")
        .group_by(["case_id", "address_id"])
        .agg(
            pl.col("block_ts").min().alias("first_seen_in_case"),
            pl.col("block_ts").max().alias("last_seen_in_case"),
            pl.col("tx_hash").n_unique().alias("transaction_count_in_case"),
            pl.col("value_in").sum().alias("total_value_in_eth"),
            pl.col("value_out").sum().alias("total_value_out_eth"),
        )
        .with_columns(
            (pl.col("total_value_in_eth") - pl.col("total_value_out_eth")).alias("net_flow_eth"),
            pl.col("transaction_count_in_case").cast(pl.Int32),
        )
    )

    addr_metrics = addr.select(
        pl.col("address_id").str.to_lowercase().alias("address_id"),
        pl.col("first_seen").alias("addr_first_seen"),
        pl.col("last_seen").alias("addr_last_seen"),
        pl.col("transaction_count").alias("addr_transaction_count"),
        pl.col("total_value_in_eth").alias("addr_total_value_in_eth"),
        pl.col("total_value_out_eth").alias("addr_total_value_out_eth"),
        pl.col("net_flow_eth").alias("addr_net_flow_eth"),
    )

    result = (
        membership.join(case_metrics, on=["case_id", "address_id"], how="left")
        .join(addr_metrics, on="address_id", how="left")
        .with_columns(
            (pl.col("case_id") + pl.lit(":") + pl.col("address_id")).alias("case_address_id"),
            pl.coalesce(pl.col("transaction_count_in_case"), pl.col("addr_transaction_count"))
            .cast(pl.Int32)
            .alias("transaction_count_in_case"),
            pl.coalesce(pl.col("first_seen_in_case"), pl.col("addr_first_seen")).alias(
                "first_seen_in_case"
            ),
            pl.coalesce(pl.col("last_seen_in_case"), pl.col("addr_last_seen")).alias(
                "last_seen_in_case"
            ),
            pl.coalesce(pl.col("total_value_in_eth"), pl.col("addr_total_value_in_eth")).alias(
                "total_value_in_eth"
            ),
            pl.coalesce(pl.col("total_value_out_eth"), pl.col("addr_total_value_out_eth")).alias(
                "total_value_out_eth"
            ),
            pl.coalesce(pl.col("net_flow_eth"), pl.col("addr_net_flow_eth")).alias("net_flow_eth"),
        )
        .select(
            "case_address_id",
            "case_id",
            "address_id",
            "membership_role",
            "hop_distance",
            "inclusion_reason",
            "first_seen_in_case",
            "last_seen_in_case",
            "transaction_count_in_case",
            "total_value_in_eth",
            "total_value_out_eth",
            "net_flow_eth",
        )
        .collect()
    )

    case_addresses.write_table(result)
