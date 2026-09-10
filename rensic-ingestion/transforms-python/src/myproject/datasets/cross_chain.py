"""
Rensic — Cross-Chain Correlation
==================================

Identifies when the same hex wallet address appears on multiple chains
within an investigation, and produces a correlation dataset.

This enables:
  - "This address is also active on Base and Arbitrum"
  - Cross-chain fund flow visualization in Vertex
  - Unified wallet profiles aggregating activity across chains
"""
import polars as pl
from transforms.api import transform, Input, Output


@transform.using(
    cross_chain_addresses=Output(
        "/George Gorzhiyev-a8216a/Rensic/data-integration/enriched/cross_chain_addresses"
    ),
    addresses=Input(
        "/George Gorzhiyev-a8216a/Rensic/data-integration/clean/addresses"
    ),
)
def build_cross_chain_correlations(cross_chain_addresses, addresses):
    """
    For each unique hex wallet address, aggregates activity across all chains.

    Output schema:
      - hex_address: The raw hex address (without chain prefix)
      - chains_active: Comma-separated list of chains this address is on
      - chain_count: Number of chains
      - total_value_in_all_chains: Sum of ETH received across all chains
      - total_value_out_all_chains: Sum of ETH sent across all chains
      - total_tx_count_all_chains: Sum of transactions across all chains
      - address_ids: Comma-separated list of composite address IDs
      - is_multi_chain: Boolean — true if active on 2+ chains
    """
    df = addresses.polars(lazy=True)

    # Extract raw hex address from composite ID (chain:0xAddress → 0xAddress)
    result = (
        df
        .with_columns(
            pl.col("address_id")
            .str.split_exact(":", 1)
            .struct.field("field_1")
            .alias("hex_address")
        )
        .group_by("hex_address")
        .agg(
            pl.col("chain_id").unique().sort().str.concat(", ").alias("chains_active"),
            pl.col("chain_id").n_unique().alias("chain_count"),
            pl.col("total_value_in_eth").sum().alias("total_value_in_all_chains"),
            pl.col("total_value_out_eth").sum().alias("total_value_out_all_chains"),
            pl.col("transaction_count").sum().alias("total_tx_count_all_chains"),
            pl.col("address_id").sort().str.concat(", ").alias("address_ids"),
        )
        .with_columns(
            (pl.col("chain_count") > 1).alias("is_multi_chain"),
            (pl.col("total_value_in_all_chains") - pl.col("total_value_out_all_chains"))
            .alias("net_flow_all_chains"),
        )
        .sort("total_tx_count_all_chains", descending=True)
        .collect()
    )

    cross_chain_addresses.write_table(result)
