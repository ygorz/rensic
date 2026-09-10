"""Offline unit tests for Rensic ingestion pure helpers."""
import sys
from pathlib import Path
from datetime import datetime, timezone

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from myproject.lookback import (
    clamp_lookback, blocks_per_day, from_block_hex,
    lookback_days_from_window, chain_ids_csv,
)
from myproject.config import (
    make_address_id, make_transaction_id, extract_hex_address,
    is_same_wallet, DEFAULT_LOOKBACK_DAYS,
)

def test_clamp_lookback_bounds():
    assert clamp_lookback(30) == 30
    assert clamp_lookback(0) == 1
    assert clamp_lookback(999) == 365
    assert clamp_lookback("nope") == DEFAULT_LOOKBACK_DAYS
    assert clamp_lookback(None) == DEFAULT_LOOKBACK_DAYS

def test_blocks_per_day():
    assert blocks_per_day("ethereum") == 7200
    assert blocks_per_day("base") == 43200
    assert blocks_per_day("unknown") == 7200

def test_from_block_hex():
    assert from_block_hex("ethereum", 1, 7200) == "0x0"
    assert from_block_hex("ethereum", 1, 14400) == hex(7200)
    assert from_block_hex("base", 1, 50000) == hex(50000 - 43200)

def test_lookback_from_window_ms():
    start = 0
    end = 30 * 86400000
    assert lookback_days_from_window(start, end) == 30

def test_chain_ids_csv():
    assert chain_ids_csv(None) == "ethereum"
    assert chain_ids_csv(["base", "ethereum"]) == "base,ethereum"
    assert chain_ids_csv("optimism") == "optimism"

def test_address_helpers():
    aid = make_address_id("ethereum", "0xABC")
    assert aid == "ethereum:0xabc"
    assert extract_hex_address(aid) == "0xabc"
    assert is_same_wallet("ethereum:0xAbC", "base:0xabc")
    assert make_transaction_id("ethereum", "0xDEAD") == "ethereum:0xdead"
