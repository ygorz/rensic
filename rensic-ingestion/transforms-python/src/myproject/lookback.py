"""Pure lookback / block-window helpers (offline-testable)."""
from datetime import datetime
from myproject.config import CHAINS, DEFAULT_LOOKBACK_DAYS

def clamp_lookback(value) -> int:
    try:
        days = int(value)
    except (TypeError, ValueError):
        days = DEFAULT_LOOKBACK_DAYS
    return max(1, min(days, 365))

def blocks_per_day(chain_id: str) -> int:
    chain = CHAINS.get(chain_id)
    bpd = getattr(chain, "blocks_per_day", None) if chain else None
    try:
        return int(bpd) if bpd else 7200
    except (TypeError, ValueError):
        return 7200

def from_block_hex(chain_id: str, lookback_days: int, latest: int) -> str:
    start = max(0, int(latest) - int(lookback_days) * blocks_per_day(chain_id))
    return hex(start)

def lookback_days_from_window(start, end) -> int:
    try:
        if start is None or end is None:
            return DEFAULT_LOOKBACK_DAYS
        if isinstance(start, datetime):
            start_ms = int(start.timestamp() * 1000)
        else:
            start_ms = int(start)
        if isinstance(end, datetime):
            end_ms = int(end.timestamp() * 1000)
        else:
            end_ms = int(end)
        days = int(round((end_ms - start_ms) / 86400000))
        return max(1, min(days, 365))
    except (TypeError, ValueError):
        return DEFAULT_LOOKBACK_DAYS

def chain_ids_csv(value) -> str:
    if value is None:
        return "ethereum"
    if isinstance(value, (list, tuple)):
        parts = [str(x).strip() for x in value if str(x).strip()]
        return ",".join(parts) if parts else "ethereum"
    text = str(value).strip()
    if text.startswith("[") and text.endswith("]"):
        inner = text[1:-1].replace(chr(39), "").replace(chr(34), "")
        parts = [p.strip() for p in inner.split(",") if p.strip()]
        return ",".join(parts) if parts else "ethereum"
    return text or "ethereum"
