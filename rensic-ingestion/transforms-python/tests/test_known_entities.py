"""known_entities.csv integrity checks."""
import csv
import re
from pathlib import Path

CSV = Path(__file__).resolve().parents[1] / "src" / "myproject" / "data" / "known_entities.csv"
REQUIRED = ["chain","address","name","category","source","source_url","tier"]
TIERS = {"official", "community"}
ADDR_RE = re.compile(r"^0x[0-9a-f]{40}$")

def _rows():
    with CSV.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def test_csv_exists_and_has_rows():
    assert CSV.is_file()
    rows = _rows()
    assert len(rows) > 1000

def test_required_columns():
    rows = _rows()
    for key in REQUIRED:
        assert key in rows[0]

def test_unique_chain_address():
    rows = _rows()
    keys = [(r["chain"].strip().lower(), r["address"].strip().lower()) for r in rows]
    assert len(keys) == len(set(keys))

def test_tiers_and_labels():
    rows = _rows()
    for r in rows:
        assert r["tier"].strip().lower() in TIERS
        assert r["name"].strip()
        assert r["address"].strip() == r["address"].strip().lower()
        assert ADDR_RE.match(r["address"].strip().lower())
