"""
Rensic Ingestion — Orchestrator (Production)
==============================================

Reads pending ingestion requests, calls the Alchemy API for each,
and writes raw transfer data + audit log.

Uses external_systems to connect to the Alchemy RPC API source.
"""
import logging
import time
import uuid
from datetime import datetime, timezone

import polars as pl
import requests as http_requests
from transforms.api import transform, Input, Output
from transforms.external.systems import external_systems, Source

# Magritte source "Alchemy RPC API" already has exports + eth-mainnet egress.
# Keys still come from Chain Configuration, not the source secret.
ALCHEMY_SOURCE_RID = "ri.magritte..source.c55dc141-7169-45ca-8058-c1d727bcd013"

from myproject.lookback import clamp_lookback as _clamp_lookback, blocks_per_day as _blocks_per_day, from_block_hex as _from_block_hex, lookback_days_from_window as _lookback_days, chain_ids_csv as _chain_ids_csv
from myproject.config import (
    CHAINS,
    DEFAULT_LOOKBACK_DAYS,
    MAX_PAGES_PER_REQUEST,
    get_transfer_categories,
)

logger = logging.getLogger(__name__)


def _redact(msg: str) -> str:
    import re
    return re.sub(r"/v2/[A-Za-z0-9_-]+", "/v2/<redacted>", str(msg))


# ---------------------------------------------------------------------------
# 1. Snapshot ingestion_requests from Investigation Case materialization
# ---------------------------------------------------------------------------
@transform.using(
    ingestion_requests=Output(
        "/George Gorzhiyev-a8216a/Rensic/data-integration/raw/ingestion_requests"
    ),
    cases=Input("ri.foundry.main.dataset.8c30e27c-723a-4471-8b58-c47cd48bf388"),
)
def seed_ingestion_requests(ingestion_requests, cases):
    """
    Queue one Alchemy request per Investigation Case.

    Source is the OSv2 materialization (edits included). Functions cannot
    write this dataset; Create Investigation writes objects, this snapshot
    turns them into orchestrator rows.
    """
    now = datetime.now(timezone.utc)
    schema = {
        "request_id": pl.Utf8,
        "case_id": pl.Utf8,
        "seed_address": pl.Utf8,
        "chain_ids": pl.Utf8,
        "lookback_days": pl.Int64,
        "status": pl.Utf8,
        "created_at": pl.Utf8,
        "requested_by": pl.Utf8,
    }
    try:
        df = cases.polars()
    except Exception as e:
        logger.warning("Could not read InvestigationCase materialization: %s", e)
        ingestion_requests.write_table(pl.DataFrame(schema=schema))
        return

    if df.is_empty():
        ingestion_requests.write_table(pl.DataFrame(schema=schema))
        return

    if "__is_deleted" in df.columns:
        df = df.filter(~pl.col("__is_deleted").fill_null(False))

    rows = []
    for row in df.iter_rows(named=True):
        case_id = row.get("case_id")
        seed = row.get("seed_address")
        if not case_id or not seed:
            continue
        created = row.get("created_at")
        if created is None:
            created_at = now.isoformat()
        elif isinstance(created, datetime):
            created_at = created.isoformat()
        else:
            created_at = str(created)
        rows.append({
            "request_id": f"req-{case_id}",
            "case_id": str(case_id),
            "seed_address": str(seed).strip().lower(),
            "chain_ids": _chain_ids_csv(row.get("chain_ids")),
            "lookback_days": _lookback_days(row.get("time_window_start"), row.get("time_window_end")),
            "status": "pending",
            "created_at": created_at,
            "requested_by": str(row.get("investigator_user_id") or "osdk"),
        })

    if not rows:
        ingestion_requests.write_table(pl.DataFrame(schema=schema))
        logger.info("No cases with seed addresses to enqueue")
        return

    ingestion_requests.write_table(pl.DataFrame(rows, schema=schema))
    logger.info("Enqueued %d ingestion requests from InvestigationCase materialization", len(rows))


# ---------------------------------------------------------------------------
# 2. Main orchestrator — PRODUCTION with Alchemy API
# ---------------------------------------------------------------------------
def _write_empty_outputs(raw_transfers, ingestion_log):
    raw_transfers.write_table(pl.DataFrame(schema=_raw_transfer_schema()))
    ingestion_log.write_table(pl.DataFrame(schema=_log_schema()))


def _row_get(row, *names, default=None):
    for name in names:
        if name in row and row[name] is not None:
            return row[name]
    return default


def _load_chain_urls(rpc_config):
    """RPC URLs from ChainConfiguration materialization (edits included)."""
    from myproject.config import CHAINS

    config_df = rpc_config.polars()
    if "__is_deleted" in config_df.columns:
        config_df = config_df.filter(~pl.col("__is_deleted").fill_null(False))
    chain_urls = {}
    for row in config_df.iter_rows(named=True):
        chain_id = str(_row_get(row, "chain_id", "chainId", "primary-key", "config-chain-id", default="") or "")
        api_key = str(_row_get(row, "api_key", "apiKey", "config-api-key", default="") or "")
        enabled = _row_get(row, "enabled", "config_enabled", "config-enabled", default=True)
        rpc_url = str(_row_get(row, "rpc_base_url", "rpcBaseUrl", "rpc-base-url", default="") or "")
        if enabled is False or str(enabled).lower() in ("false", "0"):
            continue
        if not chain_id:
            continue
        if not api_key or api_key in ("auto", "PASTE_YOUR_ALCHEMY_KEY_HERE"):
            logger.warning("Chain '%s' has no API key — skipping", chain_id)
            continue
        if not rpc_url or rpc_url == "auto":
            chain_config = CHAINS.get(chain_id)
            if chain_config:
                rpc_url = f"https://{chain_config.alchemy_subdomain}.g.alchemy.com/v2/"
            else:
                rpc_url = "https://eth-mainnet.g.alchemy.com/v2/"
        chain_urls[chain_id] = f"{rpc_url.rstrip('/')}/{api_key}"
    logger.info("Loaded RPC config: %d chains with valid API keys", len(chain_urls))
    return chain_urls


def _process_queue_row(row, client, chain_urls, run_id):
    request_id = row["request_id"]
    case_id = row["case_id"]
    seed_address = row["seed_address"]
    chain_ids = row["chain_ids"].split(",")
    lookback_days = _clamp_lookback(row.get("lookback_days", DEFAULT_LOOKBACK_DAYS))
    logger.info(
        "[%s] Processing: address=%s chains=%s lookback=%d days",
        run_id, seed_address, chain_ids, lookback_days,
    )
    req_start = datetime.now(timezone.utc)
    try:
        transfers = _fetch_transfers_live(
            client=client,
            chain_urls=chain_urls,
            case_id=case_id,
            seed_address=seed_address,
            chain_ids=chain_ids,
            lookback_days=lookback_days,
        )
        elapsed_ms = int((datetime.now(timezone.utc) - req_start).total_seconds() * 1000)
        logger.info("[%s] Completed: %d transfers in %d ms", run_id, len(transfers), elapsed_ms)
        return transfers, _log_entry(
            run_id=run_id, request_id=request_id, case_id=case_id,
            seed_address=seed_address, chain_ids=",".join(chain_ids),
            status="completed", row_count=len(transfers),
            elapsed_ms=elapsed_ms, error_message=None,
        )
    except Exception as e:
        elapsed_ms = int((datetime.now(timezone.utc) - req_start).total_seconds() * 1000)
        error_msg = _redact(f"{type(e).__name__}: {e}")
        logger.error("[%s] FAILED: %s", run_id, error_msg)
        return [], _log_entry(
            run_id=run_id, request_id=request_id, case_id=case_id,
            seed_address=seed_address, chain_ids=",".join(chain_ids),
            status="failed", row_count=0,
            elapsed_ms=elapsed_ms, error_message=error_msg,
        )


@external_systems(
    alchemy=Source(ALCHEMY_SOURCE_RID),
)
@transform.using(
    raw_transfers=Output(
        "/George Gorzhiyev-a8216a/Rensic/data-integration/raw/raw_asset_transfers"
    ),
    ingestion_log=Output(
        "/George Gorzhiyev-a8216a/Rensic/data-integration/raw/ingestion_log"
    ),
    queue=Input(
        "/George Gorzhiyev-a8216a/Rensic/data-integration/raw/ingestion_requests"
    ),
    rpc_config=Input(
        "ri.foundry.main.dataset.d4ffaad2-41f6-4c07-945e-f8706f5d4f10"
    ),
)
def run_ingestion_orchestrator(
    alchemy, raw_transfers, ingestion_log, queue, rpc_config
):
    """
    Production orchestrator: reads pending requests, calls Alchemy API,
    writes raw transfers + audit log.
    """
    _ = alchemy  # binds Alchemy HTTPS egress + export controls from the source
    run_id = str(uuid.uuid4())[:8]
    run_start = datetime.now(timezone.utc)
    logger.info("=== Ingestion orchestrator run %s started ===", run_id)

    try:
        requests_df = queue.polars()
    except Exception as e:
        logger.warning("Could not read requests: %s. Writing empty outputs.", e)
        _write_empty_outputs(raw_transfers, ingestion_log)
        return

    if requests_df.is_empty():
        logger.info("No requests found. Writing empty outputs.")
        _write_empty_outputs(raw_transfers, ingestion_log)
        return

    pending = requests_df.filter(pl.col("status").is_in(["pending", "completed"]))
    logger.info("Found %d requests to process", len(pending))
    if pending.is_empty():
        _write_empty_outputs(raw_transfers, ingestion_log)
        return

    try:
        chain_urls = _load_chain_urls(rpc_config)
    except Exception as e:
        logger.error("Failed to load RPC config: %s", e)
        chain_urls = {}

    client = http_requests.Session()
    client.headers.update({"Content-Type": "application/json"})

    all_transfers = []
    log_entries = []
    for row in pending.iter_rows(named=True):
        transfers, log_row = _process_queue_row(row, client, chain_urls, run_id)
        all_transfers.extend(transfers)
        log_entries.append(log_row)

    if all_transfers:
        raw_transfers.write_table(
            pl.DataFrame(all_transfers, schema=_raw_transfer_schema(), infer_schema_length=None)
        )
    else:
        raw_transfers.write_table(pl.DataFrame(schema=_raw_transfer_schema()))

    if log_entries:
        ingestion_log.write_table(pl.DataFrame(log_entries))
    else:
        ingestion_log.write_table(pl.DataFrame(schema=_log_schema()))

    total_ms = int((datetime.now(timezone.utc) - run_start).total_seconds() * 1000)
    logger.info(
        "=== Run %s complete: %d requests, %d transfers, %d ms ===",
        run_id, len(log_entries), len(all_transfers), total_ms,
    )


# ---------------------------------------------------------------------------
# 3. Live Alchemy API fetch
# ---------------------------------------------------------------------------
def _eth_block_number(client, url) -> int:
    """POST eth_blockNumber on the chain RPC. Fail loud; never scrape unbounded."""
    payload = {"jsonrpc": "2.0", "id": 1, "method": "eth_blockNumber", "params": []}
    try:
        response = client.post(url, json=payload, timeout=30)
    except Exception as e:
        raise RuntimeError("eth_blockNumber request failed: %s" % _redact(e)) from e
    try:
        data = response.json()
    except Exception:
        data = {}
    if not response.ok:
        err = (data.get("error") or {}).get("message") if isinstance(data, dict) else None
        raise RuntimeError(
            "eth_blockNumber HTTP %s: %s"
            % (response.status_code, _redact(err or response.reason))
        )
    if isinstance(data, dict) and data.get("error"):
        raise RuntimeError(
            "eth_blockNumber RPC error: %s"
            % _redact((data.get("error") or {}).get("message") or data["error"])
        )
    result = data.get("result") if isinstance(data, dict) else None
    try:
        return int(result, 16)
    except (TypeError, ValueError) as e:
        raise RuntimeError("eth_blockNumber returned unusable result") from e


def _fetch_transfers_live(client, chain_urls, case_id, seed_address, chain_ids, lookback_days):
    """
    Fetch real transfers from Alchemy alchemy_getAssetTransfers API.

    Calls the API twice per chain:
      1. Outgoing transfers (fromAddress = seed)
      2. Incoming transfers (toAddress = seed)

    Reads RPC URLs from the chain_urls dict (loaded from config dataset).
    Handles pagination via pageKey.
    Bounds each request with fromBlock/toBlock from lookback_days.
    """
    all_transfers = []

    loaded = sorted(chain_urls)
    if not loaded:
        raise RuntimeError("No RPC chains loaded from ChainConfiguration materialization")
    missing = [c.strip() for c in chain_ids if c.strip() and c.strip() not in chain_urls]
    if missing:
        raise RuntimeError(
            "No RPC config for chains %s (loaded %s)" % (missing, loaded)
        )

    for chain_id in chain_ids:
        chain_id = chain_id.strip()
        if not chain_id:
            continue
        api_url = chain_urls[chain_id]

        categories = get_transfer_categories(chain_id)
        latest = _eth_block_number(client, api_url)
        from_block = _from_block_hex(chain_id, lookback_days, latest)
        to_block = "latest"
        logger.info(
            "[%s] lookback=%dd fromBlock=%s toBlock=%s latest=%d bpd=%d",
            chain_id, lookback_days, from_block, to_block, latest,
            _blocks_per_day(chain_id),
        )

        # --- Fetch OUTGOING transfers (from seed address) ---
        outgoing = _paginated_fetch(
            client=client,
            url=api_url,
            seed_address=seed_address,
            direction="from",
            categories=categories,
            chain_id=chain_id,
            case_id=case_id,
            from_block=from_block,
            to_block=to_block,
        )
        all_transfers.extend(outgoing)
        logger.info("[%s] Outgoing: %d transfers", chain_id, len(outgoing))

        # --- Fetch INCOMING transfers (to seed address) ---
        incoming = _paginated_fetch(
            client=client,
            url=api_url,
            seed_address=seed_address,
            direction="to",
            categories=categories,
            chain_id=chain_id,
            case_id=case_id,
            from_block=from_block,
            to_block=to_block,
        )
        all_transfers.extend(incoming)
        logger.info("[%s] Incoming: %d transfers", chain_id, len(incoming))

    return all_transfers


def _parse_alchemy_transfer(t, chain_id, case_id):
    block_num_hex = t.get("blockNum", "0x0")
    try:
        block_number = int(block_num_hex, 16)
    except (ValueError, TypeError):
        block_number = 0
    value = t.get("value")
    if value is not None:
        try:
            value = float(value)
        except (ValueError, TypeError):
            value = 0.0
    token_address = (t.get("rawContract") or {}).get("address")
    return {
        "chain_id": chain_id,
        "tx_hash": t.get("hash", ""),
        "from_address": (t.get("from") or "").lower(),
        "to_address": (t.get("to") or "").lower(),
        "value": value,
        "asset": t.get("asset", ""),
        "category": t.get("category", ""),
        "block_number": block_number,
        "block_timestamp": (t.get("metadata") or {}).get("blockTimestamp", ""),
        "token_contract_address": token_address.lower() if token_address else None,
        "token_id": str(t.get("erc721TokenId") or t.get("tokenId") or ""),
        "case_id": case_id,
    }


def _alchemy_payload(seed_address, direction, categories, page_key, from_block, to_block):
    params = {
        "category": categories,
        "withMetadata": True,
        "maxCount": "0x3E8",
        "order": "desc",
        "fromBlock": from_block,
        "toBlock": to_block,
    }
    if direction == "from":
        params["fromAddress"] = seed_address
    else:
        params["toAddress"] = seed_address
    if page_key:
        params["pageKey"] = page_key
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "alchemy_getAssetTransfers",
        "params": [params],
    }


def _paginated_fetch(
    client, url, seed_address, direction, categories, chain_id, case_id,
    from_block, to_block,
):
    """Fetch all pages of alchemy_getAssetTransfers for one direction."""
    transfers = []
    page_key = None
    page_count = 0
    while page_count < MAX_PAGES_PER_REQUEST:
        payload = _alchemy_payload(
            seed_address, direction, categories, page_key, from_block, to_block,
        )
        try:
            response = client.post(url, json=payload, timeout=30)
        except Exception as e:
            raise RuntimeError("Alchemy request failed: %s" % _redact(e)) from e
        try:
            data = response.json()
        except Exception:
            data = {}
        if not response.ok:
            err = (data.get("error") or {}).get("message") if isinstance(data, dict) else None
            raise RuntimeError(
                "Alchemy HTTP %s: %s" % (response.status_code, _redact(err or response.reason))
            )
        if isinstance(data, dict) and data.get("error"):
            raise RuntimeError(
                "Alchemy RPC error: %s" % _redact((data.get("error") or {}).get("message") or data["error"])
            )
        result = data.get("result") or {}
        raw_page = result.get("transfers") or []
        if not raw_page:
            break
        transfers.extend(_parse_alchemy_transfer(t, chain_id, case_id) for t in raw_page)
        page_key = result.get("pageKey")
        page_count += 1
        if not page_key:
            break
        time.sleep(0.2)
    logger.info(
        "Fetched %d transfers over %d pages (%s, %s)",
        len(transfers), page_count, chain_id, direction,
    )
    return transfers


# ---------------------------------------------------------------------------
# 4. Schema definitions & helpers
# ---------------------------------------------------------------------------
def _raw_transfer_schema():
    return {
        "chain_id": pl.Utf8,
        "tx_hash": pl.Utf8,
        "from_address": pl.Utf8,
        "to_address": pl.Utf8,
        "value": pl.Float64,
        "asset": pl.Utf8,
        "category": pl.Utf8,
        "block_number": pl.Int64,
        "block_timestamp": pl.Utf8,
        "token_contract_address": pl.Utf8,
        "token_id": pl.Utf8,
        "case_id": pl.Utf8,
    }


def _log_schema():
    return {
        "run_id": pl.Utf8,
        "request_id": pl.Utf8,
        "case_id": pl.Utf8,
        "seed_address": pl.Utf8,
        "chain_ids": pl.Utf8,
        "status": pl.Utf8,
        "row_count": pl.Int64,
        "elapsed_ms": pl.Int64,
        "error_message": pl.Utf8,
        "logged_at": pl.Utf8,
    }


def _log_entry(run_id, request_id, case_id, seed_address, chain_ids,
               status, row_count, elapsed_ms, error_message):
    return {
        "run_id": run_id,
        "request_id": request_id,
        "case_id": case_id,
        "seed_address": seed_address,
        "chain_ids": chain_ids,
        "status": status,
        "row_count": row_count,
        "elapsed_ms": elapsed_ms,
        "error_message": error_message,
        "logged_at": datetime.now(timezone.utc).isoformat(),
    }
