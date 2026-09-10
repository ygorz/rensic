"""
Rensic Ingestion — Alchemy API Client Utilities
=================================================

Helper functions for calling the Alchemy `alchemy_getAssetTransfers` API.
These are used by the orchestrator.py transform when in production mode.

This file contains NO transforms — it's a utility module only.
The orchestrator.py is the single source of truth for raw_asset_transfers output.
"""
import time
from datetime import datetime, timezone

import polars as pl

from myproject.config import (
    MAX_RESULTS_PER_PAGE,
    MAX_PAGES_PER_REQUEST,
    TRANSFER_CATEGORIES,
)

# ---------------------------------------------------------------------------
# SCHEMA DEFINITION for the raw output
# ---------------------------------------------------------------------------
RAW_TRANSFER_SCHEMA = {
    "chain_id": pl.Utf8,
    "tx_hash": pl.Utf8,
    "block_number": pl.Int64,
    "block_timestamp": pl.Utf8,
    "from_address": pl.Utf8,
    "to_address": pl.Utf8,
    "value": pl.Float64,
    "asset": pl.Utf8,
    "category": pl.Utf8,
    "token_contract_address": pl.Utf8,
    "token_id": pl.Utf8,
    "raw_value_hex": pl.Utf8,
    "decimal": pl.Int32,
    "unique_id": pl.Utf8,
    "ingestion_timestamp": pl.Utf8,
    "case_id": pl.Utf8,
}


def hex_to_int(hex_str):
    """Convert hex string (0x...) to integer, returning None if invalid."""
    if not hex_str or hex_str == "0x":
        return None
    try:
        return int(hex_str, 16)
    except (ValueError, TypeError):
        return None


def parse_timestamp(ts_str):
    """Parse ISO timestamp string, returning None if invalid."""
    if not ts_str:
        return None
    try:
        return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def fetch_transfers_paginated(client, url, params, max_pages=MAX_PAGES_PER_REQUEST):
    """
    Fetch all pages of alchemy_getAssetTransfers results.

    Args:
        client: HTTP client from Data Connection source (.post() method)
        url: Full URL including API key (e.g., https://eth-mainnet.g.alchemy.com/v2/KEY)
        params: Base parameters for the API call
        max_pages: Safety limit on number of pages

    Returns:
        List of raw transfer dicts from Alchemy
    """
    all_transfers = []
    page_key = None
    page_count = 0

    while page_count < max_pages:
        rpc_params = {**params}
        if page_key:
            rpc_params["pageKey"] = page_key

        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "alchemy_getAssetTransfers",
            "params": [rpc_params],
        }

        response = client.post(url, json=payload, timeout=30)
        response.raise_for_status()

        result = response.json().get("result", {})
        transfers = result.get("transfers", [])
        all_transfers.extend(transfers)

        page_key = result.get("pageKey")
        page_count += 1

        if not page_key:
            break

        # Rate limiting
        time.sleep(0.2)

    return all_transfers


def build_transfer_rows(transfers, chain_id, case_id):
    """
    Convert raw Alchemy transfer objects into flat rows matching our schema.

    Args:
        transfers: List of transfer dicts from Alchemy API
        chain_id: The blockchain network identifier
        case_id: The investigation case ID

    Returns:
        List of row dicts ready for Polars DataFrame
    """
    now = datetime.now(timezone.utc).isoformat()
    rows = []

    for i, t in enumerate(transfers):
        block_num_hex = t.get("blockNum", "0x0")
        block_number = hex_to_int(block_num_hex)

        metadata = t.get("metadata", {})
        block_ts = metadata.get("blockTimestamp", "")

        raw_contract = t.get("rawContract", {})
        token_contract = raw_contract.get("address")
        raw_value_hex = raw_contract.get("value")
        decimal_hex = raw_contract.get("decimal")
        decimal = hex_to_int(decimal_hex) if decimal_hex else None

        value = t.get("value")
        if value is not None:
            try:
                value = float(value)
            except (ValueError, TypeError):
                value = None

        row = {
            "chain_id": chain_id,
            "tx_hash": t.get("hash"),
            "block_number": block_number,
            "block_timestamp": block_ts,
            "from_address": (t.get("from") or "").lower(),
            "to_address": (t.get("to") or "").lower(),
            "value": value,
            "asset": t.get("asset"),
            "category": t.get("category"),
            "token_contract_address": token_contract.lower() if token_contract else None,
            "token_id": t.get("erc721TokenId") or t.get("tokenId"),
            "raw_value_hex": raw_value_hex,
            "decimal": decimal,
            "unique_id": t.get("uniqueId", f"{chain_id}:{t.get('hash', '')}:{i}"),
            "ingestion_timestamp": now,
            "case_id": case_id,
        }
        rows.append(row)

    return rows
