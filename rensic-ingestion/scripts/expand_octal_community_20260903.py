#!/usr/bin/env python3
"""Add octal-crypto/etherscan-labels as a second community-tier source.

Merge policy (first-wins for community):
  official > existing community > new octal
Do not remove existing rows. Document overlaps with brianleect mirror.
"""
from __future__ import annotations

import csv
import json
import re
import ssl
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path

CSV_PATH = Path(
    "/Users/george/Documents/WilderformTools/rensic/rensic-ingestion/transforms-python/src/myproject/data/known_entities.csv"
)
SOURCES_MD = CSV_PATH.with_name("SOURCES.md")
APP_TS = Path("/Users/george/Documents/WilderformTools/rensic/rensic-app/src/knownEntities.ts")
CACHE_DIR = Path("/Users/george/Documents/WilderformTools/rensic/rensic-ingestion/.cache/octal-etherscan-labels/labels")
OCTAL_REPO = "https://github.com/octal-crypto/etherscan-labels"
OCTAL_SITE = "https://octal.art/etherscan-labels/"
OCTAL_RAW = (
    "https://raw.githubusercontent.com/octal-crypto/etherscan-labels/main/labels"
)
PULL_DATE = date.today().isoformat()
SOURCE_BASE = "Etherscan label (octal mirror)"

ETH_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
NUM_RE = re.compile(r"^(.+?)\s+(\d+)$")
SKIP_NAME_RE = re.compile(
    r"("
    r"website\s*down|airdrop\s*hunter|take\s*action|"
    r"old\s*contract|deprecated|"
    r"token\s*contract|erc[- ]?20|erc[- ]?721|erc[- ]?1155|"
    r"phish|scam"
    r")",
    re.I,
)
POOLISH_RE = re.compile(r"[#/]|:\s*.*/|\bLP\b|\bpool\b|\d+\s*/\s*\d+", re.I)
MEGA_COLON_LABELS = {
    "sushiswap",
    "bancor",
    "synthetix",
    "balancer",
    "rocket-pool",
    "curve-fi",
    "uniswap",
}

CAT_RANK = {
    "sanctions": 0,
    "mixer": 1,
    "gambling": 2,
    "exchange": 3,
    "shop": 4,
    "protocol": 5,
    "person": 6,
}
TIER_RANK = {"official": 0, "community": 1}

# Labels we intentionally skip (phishing mega-noise / junk)
SKIP_LABELS = {
    "take-action",
    "website-down",
    "airdrop-hunter",
    "phishing",
    "blocked",
    "spam-token",
    "something-fishy",
    "high-risk",
    "deprecated",
    "old-contract",
}

EXCHANGE_VENUES: dict[str, tuple[str, str]] = {
    "binance": ("Binance", "https://etherscan.io/accounts/label/binance"),
    "coinbase": ("Coinbase", "https://etherscan.io/accounts/label/coinbase"),
    "kraken": ("Kraken", "https://etherscan.io/accounts/label/kraken"),
    "okx": ("OKX", "https://etherscan.io/accounts/label/okx"),
    "huobi": ("Huobi", "https://etherscan.io/accounts/label/huobi"),
    "kucoin": ("KuCoin", "https://etherscan.io/accounts/label/kucoin"),
    "gemini": ("Gemini", "https://etherscan.io/accounts/label/gemini"),
    "bitfinex": ("Bitfinex", "https://etherscan.io/accounts/label/bitfinex"),
    "bitstamp": ("Bitstamp", "https://etherscan.io/accounts/label/bitstamp"),
    "crypto-com": ("Crypto.com", "https://etherscan.io/accounts/label/crypto-com"),
    "gate-io": ("Gate.io", "https://etherscan.io/accounts/label/gate-io"),
    "bitmex": ("BitMEX", "https://etherscan.io/accounts/label/bitmex"),
    "bittrex": ("Bittrex", "https://etherscan.io/accounts/label/bittrex"),
    "poloniex": ("Poloniex", "https://etherscan.io/accounts/label/poloniex"),
    "ftx": ("FTX", "https://etherscan.io/accounts/label/ftx"),
    "ascendex": ("AscendEX", "https://etherscan.io/accounts/label/ascendex"),
    "nexo": ("Nexo", "https://etherscan.io/accounts/label/nexo"),
    "blockfi": ("BlockFi", "https://etherscan.io/accounts/label/blockfi"),
    "coinsquare": ("Coinsquare", "https://etherscan.io/accounts/label/coinsquare"),
    "bithumb": ("Bithumb", "https://etherscan.io/accounts/label/bithumb"),
    "deribit": ("Deribit", "https://etherscan.io/accounts/label/deribit"),
    "liquid": ("Liquid", "https://etherscan.io/accounts/label/liquid"),
    "bitmart": ("BitMart", "https://etherscan.io/accounts/label/bitmart"),
    "hitbtc": ("HitBTC", "https://etherscan.io/accounts/label/hitbtc"),
    "digifinex": ("DigiFinex", "https://etherscan.io/accounts/label/digifinex"),
    "hotbit": ("Hotbit", "https://etherscan.io/accounts/label/hotbit"),
    "coinone": ("Coinone", "https://etherscan.io/accounts/label/coinone"),
    "upbit": ("Upbit", "https://etherscan.io/accounts/label/upbit"),
    "coinlist": ("CoinList", "https://etherscan.io/accounts/label/coinlist"),
    "coinmetro": ("CoinMetro", "https://etherscan.io/accounts/label/coinmetro"),
    "bitcoin-suisse": (
        "Bitcoin Suisse",
        "https://etherscan.io/accounts/label/bitcoin-suisse",
    ),
    "coinhako": ("CoinHako", "https://etherscan.io/accounts/label/coinhako"),
    "remitano": ("Remitano", "https://etherscan.io/accounts/label/remitano"),
    "korbit": ("Korbit", "https://etherscan.io/accounts/label/korbit"),
    "allbit": ("Allbit", "https://etherscan.io/accounts/label/allbit"),
    "oobit": ("Oobit", "https://etherscan.io/accounts/label/oobit"),
    "tidex": ("Tidex", "https://etherscan.io/accounts/label/tidex"),
    "fiat-gateway": ("Fiat Gateway", "https://etherscan.io/accounts/label/fiat-gateway"),
}

CATEGORY_LABELS: dict[str, tuple[str, str, str]] = {
    "tornado-cash": (
        "mixer",
        "Tornado Cash",
        "https://etherscan.io/accounts/label/tornado-cash",
    ),
    "ethereum-mixer": (
        "mixer",
        "Ethereum Mixer",
        "https://etherscan.io/accounts/label/ethereum-mixer",
    ),
    "gambling": (
        "gambling",
        "Gambling",
        "https://etherscan.io/accounts/label/gambling",
    ),
    "bridge": ("protocol", "Bridge", "https://etherscan.io/accounts/label/bridge"),
    "dex": ("protocol", "DEX", "https://etherscan.io/accounts/label/dex"),
    "defi": ("protocol", "DeFi", "https://etherscan.io/accounts/label/defi"),
    "protocol": (
        "protocol",
        "Protocol",
        "https://etherscan.io/accounts/label/protocol",
    ),
    "stablecoin": (
        "protocol",
        "Stablecoin",
        "https://etherscan.io/accounts/label/stablecoin",
    ),
    "algorithmic-stablecoin": (
        "protocol",
        "Stablecoin",
        "https://etherscan.io/accounts/label/algorithmic-stablecoin",
    ),
    "marketplace": (
        "shop",
        "Marketplace",
        "https://etherscan.io/accounts/label/marketplace",
    ),
}

PROTO_EXTRA_LABELS: dict[str, str] = {
    "aave": "Aave",
    "curve-fi": "Curve",
    "lido": "Lido",
    "yearn-finance": "Yearn",
    "1inch": "1inch",
    "uniswap": "Uniswap",
    "compound": "Compound",
    "maker": "Maker",
    "instadapp": "Instadapp",
    "dydx": "dYdX",
    "opensea": "OpenSea",
    "ens": "ENS",
    "convex-finance": "Convex",
    "across-protocol": "Across",
    "hop-protocol": "Hop",
    "synapse": "Synapse",
    "multichain": "Multichain",
    "wormhole": "Wormhole",
    "kyberswap": "KyberSwap",
    "0x-protocol": "0x",
    "airswap": "AirSwap",
    "idex": "IDEX",
    "cream-finance": "Cream",
    "idle-finance": "Idle",
    "set-protocol": "Set Protocol",
    "zapper-fi": "Zapper",
    "abracadabra-money": "Abracadabra",
    "alchemix-finance": "Alchemix",
}

# Prefer higher-signal label class when an address appears under multiple labels.
LABEL_PRIORITY = {
    **{k: 0 for k in EXCHANGE_VENUES},
    **{k: 1 for k in CATEGORY_LABELS},
    **{k: 2 for k in PROTO_EXTRA_LABELS},
}

WANTED_LABELS = sorted(
    set(EXCHANGE_VENUES) | set(CATEGORY_LABELS) | set(PROTO_EXTRA_LABELS)
)


def ascii_name(s: str) -> str:
    out = []
    for ch in s:
        o = ord(ch)
        if o < 128:
            out.append(ch)
        elif ch in "\u2013\u2014":
            out.append("-")
        elif ch in "\u2018\u2019":
            out.append("'")
        elif ch in "\u201c\u201d":
            out.append('"')
        else:
            out.append("?")
    return "".join(out).strip()


def row(
    address: str,
    name: str,
    category: str,
    source: str,
    source_url: str,
    tier: str = "community",
    secondary: str = "",
) -> dict:
    assert ETH_RE.match(address), address
    assert tier in ("official", "community"), tier
    assert category in CAT_RANK, category
    return {
        "chain": "ethereum",
        "address": address.lower(),
        "name": ascii_name(name),
        "category": category,
        "secondary_category": secondary,
        "source": source,
        "source_url": source_url,
        "tier": tier,
    }


def load_existing() -> list[dict]:
    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    out = []
    for r in rows:
        addr = (r.get("address") or "").strip().lower()
        if not addr:
            continue
        out.append(
            {
                "chain": (r.get("chain") or "ethereum").strip().lower(),
                "address": addr,
                "name": (r.get("name") or "").strip(),
                "category": (r.get("category") or "").strip().lower(),
                "secondary_category": (r.get("secondary_category") or "").strip(),
                "source": (r.get("source") or "").strip(),
                "source_url": (r.get("source_url") or "").strip(),
                "tier": (r.get("tier") or "official").strip().lower() or "official",
            }
        )
    return out


def _fetch(url: str, dest: Path) -> tuple[str, bool, str]:
    ctx = ssl.create_default_context()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "rensic-ingest/1.0"})
        with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:
            data = resp.read()
        dest.write_bytes(data)
        return dest.stem, True, f"{len(data)}b"
    except Exception as e:
        return dest.stem, False, str(e)


def download_labels() -> tuple[list[str], list[str]]:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    ok: list[str] = []
    miss: list[str] = []
    jobs = []
    with ThreadPoolExecutor(max_workers=12) as ex:
        for lab in WANTED_LABELS:
            if lab in SKIP_LABELS:
                miss.append(lab)
                continue
            dest = CACHE_DIR / f"{lab}.json"
            if dest.is_file() and dest.stat().st_size > 20:
                ok.append(lab)
                continue
            url = f"{OCTAL_RAW}/{lab}.json"
            jobs.append(ex.submit(_fetch, url, dest))
        for fut in as_completed(jobs):
            lab, success, msg = fut.result()
            if success:
                ok.append(lab)
            else:
                miss.append(lab)
                print(f"MISS {lab}: {msg}")
    return sorted(set(ok)), sorted(set(miss))


def normalize_exchange_name(raw: str, display: str) -> str:
    name = raw.strip()
    m = NUM_RE.match(name)
    if m:
        base = m.group(1).strip()
        base_n = re.sub(r"[.\s_-]+", "", base.lower())
        disp_n = re.sub(r"[.\s_-]+", "", display.lower())
        if (
            base_n == disp_n
            or base_n.startswith(disp_n[: min(4, len(disp_n))])
            or disp_n.startswith(base_n[: min(4, len(base_n))])
        ):
            return f"{display} {m.group(2)}"
        return name
    raw_n = re.sub(r"[.\s_-]+", "", name.lower())
    disp_n = re.sub(r"[.\s_-]+", "", display.lower())
    if raw_n == disp_n or raw_n in (disp_n, display.lower()):
        return display
    return name


def pick_from_octal(ok_labels: list[str]) -> tuple[list[dict], Counter, Counter, dict]:
    """Build community rows from octal label JSON files."""
    by_addr: dict[str, tuple[int, dict]] = {}
    by_cat: Counter = Counter()
    by_venue: Counter = Counter()
    skip_stats = Counter()
    incoming_raw = 0

    def consider(r: dict, lab: str, venue_key: str) -> None:
        nonlocal incoming_raw
        incoming_raw += 1
        addr = r["address"]
        prio = LABEL_PRIORITY.get(lab, 9)
        prev = by_addr.get(addr)
        if prev is None:
            by_addr[addr] = (prio, r)
            by_cat[r["category"]] += 1
            by_venue[venue_key] += 1
            return
        old_prio, old = prev
        # Prefer better label class; else better category; else keep first (first-wins).
        if prio < old_prio:
            by_cat[old["category"]] -= 1
            by_cat[r["category"]] += 1
            by_addr[addr] = (prio, r)
            return
        if prio == old_prio and CAT_RANK.get(r["category"], 99) < CAT_RANK.get(
            old["category"], 99
        ):
            by_cat[old["category"]] -= 1
            by_cat[r["category"]] += 1
            by_addr[addr] = (prio, r)

    for lab in ok_labels:
        path = CACHE_DIR / f"{lab}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        addresses = data.get("Addresses") or {}
        for addr, meta in addresses.items():
            if not ETH_RE.match(addr or ""):
                skip_stats["bad_address"] += 1
                continue
            name = (meta.get("Name Tag") or meta.get("Token Name") or "").strip()
            if not name:
                # unlabeled under a useful label — still skip without a nametag
                skip_stats["empty_name"] += 1
                continue
            if SKIP_NAME_RE.search(name):
                skip_stats["skip_name_re"] += 1
                continue

            if lab in EXCHANGE_VENUES:
                display, src_url = EXCHANGE_VENUES[lab]
                if lab == "fiat-gateway":
                    nice = name
                    source = f"{SOURCE_BASE} / Fiat Gateway"
                    venue_key = "Fiat Gateway"
                else:
                    nice = normalize_exchange_name(name, display)
                    source = f"{SOURCE_BASE} / {display}"
                    venue_key = display
                consider(
                    row(addr, nice, "exchange", source, src_url, "community"),
                    lab,
                    venue_key,
                )
                continue

            if lab in CATEGORY_LABELS:
                our_cat, suffix, src_url = CATEGORY_LABELS[lab]
                consider(
                    row(
                        addr,
                        name,
                        our_cat,
                        f"{SOURCE_BASE} / {suffix}",
                        src_url,
                        "community",
                    ),
                    lab,
                    suffix,
                )
                continue

            if lab in PROTO_EXTRA_LABELS:
                if POOLISH_RE.search(name):
                    skip_stats["poolish"] += 1
                    continue
                if ":" in name and lab in MEGA_COLON_LABELS:
                    skip_stats["mega_colon"] += 1
                    continue
                suffix = PROTO_EXTRA_LABELS[lab]
                consider(
                    row(
                        addr,
                        name,
                        "protocol",
                        f"{SOURCE_BASE} / {suffix}",
                        f"https://etherscan.io/accounts/label/{lab}",
                        "community",
                    ),
                    lab,
                    suffix,
                )

    rows = [r for _, r in by_addr.values()]
    return rows, by_cat, by_venue, {
        "incoming_raw": incoming_raw,
        "unique": len(rows),
        "skips": dict(skip_stats),
    }


def merge(existing: list[dict], incoming: list[dict]) -> tuple[list[dict], dict]:
    by_key: dict[tuple[str, str], dict] = {}
    for r in existing:
        by_key[(r["chain"], r["address"])] = r

    existing_keys = set(by_key)
    existing_community = {
        k for k, v in by_key.items() if v.get("tier") == "community"
    }
    existing_official = {
        k for k, v in by_key.items() if v.get("tier") != "community"
    }

    added = 0
    overlap_official = 0
    overlap_community = 0
    # first-wins: never replace same-tier community with octal
    for r in incoming:
        key = (r["chain"], r["address"])
        if key not in by_key:
            by_key[key] = r
            added += 1
            continue
        old = by_key[key]
        if old.get("tier") != "community":
            overlap_official += 1
            continue
        # existing community wins (first-wins)
        overlap_community += 1

    merged = sorted(
        by_key.values(),
        key=lambda x: (
            TIER_RANK.get(x.get("tier", "official"), 9),
            CAT_RANK.get(x["category"], 99),
            x["name"],
            x["address"],
        ),
    )
    return merged, {
        "added": added,
        "overlap_official": overlap_official,
        "overlap_community": overlap_community,
        "overlap_total": overlap_official + overlap_community,
        "incoming": len(incoming),
        "existing_keys": len(existing_keys),
        "existing_community": len(existing_community),
        "existing_official": len(existing_official),
    }


def write_csv(rows: list[dict]) -> None:
    fields = [
        "chain",
        "address",
        "name",
        "category",
        "secondary_category",
        "source",
        "source_url",
        "tier",
    ]
    with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


TS_HELPERS = r'''
const BY_HEX: Record<string, KnownEntity> = {};
for (const row of KNOWN_ENTITIES) {
  BY_HEX[row.address.toLowerCase()] = row;
}

function hexOf(id: string | undefined): string | undefined {
  if (!id) {
    return undefined;
  }
  const raw = id.includes(":") ? id.split(":").pop()! : id;
  const h = raw.trim().toLowerCase();
  return /^0x[0-9a-f]{40}$/.test(h) ? h : undefined;
}

export function lookupKnownEntity(id: string | undefined): KnownEntity | undefined {
  const hex = hexOf(id);
  if (!hex) {
    return undefined;
  }
  return BY_HEX[hex];
}

export function entityCategories(row: KnownEntity | undefined): EntityCategory[] {
  if (!row) {
    return [];
  }
  const out: EntityCategory[] = [row.category];
  if (row.secondaryCategory && row.secondaryCategory !== row.category) {
    out.push(row.secondaryCategory);
  }
  return out;
}

export function isOfficialEntity(row: KnownEntity | undefined): boolean {
  return Boolean(row) && (row!.tier ?? "official") === "official";
}

export function isCommunityEntity(row: KnownEntity | undefined): boolean {
  return Boolean(row) && row!.tier === "community";
}

export function seedExposureLine(
  rows: { addressId?: string; membershipRole?: string; hopDistance?: number }[],
): string {
  const hop1 = rows.filter((r) => {
    const role = (r.membershipRole ?? "").toLowerCase();
    return role !== "seed" && r.hopDistance !== 0;
  });
  let mixer: KnownEntity | undefined;
  let sdn: KnownEntity | undefined;
  let other: KnownEntity | undefined;
  for (const r of hop1) {
    const ent = lookupKnownEntity(r.addressId);
    if (!ent) {
      continue;
    }
    const cats = entityCategories(ent);
    if (!mixer && cats.includes("mixer")) {
      mixer = ent;
    } else if (!sdn && cats.includes("sanctions")) {
      sdn = ent;
    } else if (!other) {
      other = ent;
    }
  }
  if (mixer) {
    const n = mixer.name;
    if (n.toLowerCase().includes("tornado")) {
      return "Direct to mixer (Tornado Cash)";
    }
    return `Direct to mixer (${n})`;
  }
  if (sdn) {
    return "Direct to OFAC SDN";
  }
  if (other) {
    return `Direct to ${other.category} (${other.name})`;
  }
  return "No labeled counterparties in this working set";
}
'''


def write_ts(rows: list[dict]) -> None:
    cats = sorted({r["category"] for r in rows} | set(CAT_RANK))
    cat_union = " | ".join(json.dumps(c) for c in cats)
    payload = []
    for r in rows:
        obj = {
            "chain": r["chain"],
            "address": r["address"],
            "name": r["name"],
            "category": r["category"],
            "source": r["source"],
            "sourceUrl": r["source_url"],
            "tier": r.get("tier") or "official",
        }
        if r.get("secondary_category"):
            obj["secondaryCategory"] = r["secondary_category"]
        payload.append(obj)

    json_path = APP_TS.with_name("knownEntities.json")
    json_path.write_text(
        json.dumps(payload, ensure_ascii=True, separators=(",", ":")),
        encoding="utf-8",
    )
    parts = [
        'import pack from "./knownEntities.json";',
        "",
        f"export type EntityCategory = {cat_union};",
        "",
        'export type EntityTier = "official" | "community";',
        "",
        "export type KnownEntity = {",
        "  chain: string;",
        "  address: string;",
        "  name: string;",
        "  category: EntityCategory;",
        "  secondaryCategory?: EntityCategory;",
        "  source: string;",
        "  sourceUrl: string;",
        "  tier: EntityTier;",
        "};",
        "",
        "export const KNOWN_ENTITIES: KnownEntity[] = pack as KnownEntity[];",
        TS_HELPERS,
    ]
    APP_TS.write_text("\n".join(parts) + "\n", encoding="utf-8")


def append_sources(
    before_total: int,
    before_community: int,
    before_official: int,
    merged: list[dict],
    info: dict,
    dump_by_cat: Counter,
    dump_by_venue: Counter,
    pick_meta: dict,
    ok_labels: list[str],
    miss_labels: list[str],
) -> None:
    by_tier = Counter(r.get("tier", "official") for r in merged)
    by_cat = Counter(r["category"] for r in merged)
    target = "0xc013426d7cef8be3ef3b366151ed85e4fe33688c"
    target_row = next((r for r in merged if r["address"] == target), None)
    octal_rows = sum(
        1 for r in merged if SOURCE_BASE in (r.get("source") or "")
    )

    lines = [
        "",
        "",
        f"## Community octal mirror: {PULL_DATE}",
        "",
        "Second community-tier source (George agreed). Complements brianleect mirror.",
        "",
        "### Source",
        "",
        f"- [`octal-crypto/etherscan-labels`]({OCTAL_REPO}) (same data as `{OCTAL_SITE}`)",
        f"- Pull date: {PULL_DATE}",
        "- Machine-readable per-label JSON under `labels/<slug>.json` (not HTML scrape of octal.art).",
        f"- `source` column uses `{SOURCE_BASE} / <venue>` so mirrors are distinguishable.",
        "- Each row cites the matching Etherscan label page as `source_url` when possible.",
        f"- Labels fetched OK ({len(ok_labels)}): {', '.join(ok_labels)}",
        f"- Labels missing/404 ({len(miss_labels)}): {', '.join(miss_labels) if miss_labels else '(none)'}",
        "",
        "### Selection (same filters as brianleect bulk expand)",
        "",
        "- ETH `0x` only, tier=`community`.",
        "- Exchange venue labels (uncapped) + mixer/gambling/bridge/dex/defi/protocol/",
        "  stablecoin/marketplace category labels + named protocol extras (non-poolish).",
        "- Skip phishing mega-noise: take-action / website-down / airdrop-hunter labels",
        "  and name regex (phish/scam/website-down/take-action/airdrop-hunter/old-contract).",
        "- Mega colon / LP poolish names skipped for PROTO_EXTRA (incl. uniswap/curve).",
        "",
        "### Incoming pick counts (before merge)",
        "",
        f"- Raw considered address hits: {pick_meta.get('incoming_raw')}",
        f"- Unique addresses after intra-octal dedupe: {pick_meta.get('unique')}",
        f"- Skip stats: {pick_meta.get('skips')}",
        f"- By mapped category: {dict(dump_by_cat)}",
        f"- By venue/label bucket (top): {dict(dump_by_venue.most_common(40))}",
        "",
        "### Merge (first-wins community)",
        "",
        f"- Before: total {before_total} (official {before_official}, community {before_community})",
        f"- Incoming community unique: {info['incoming']}",
        f"- Newly added (unique vs existing): {info['added']}",
        f"- Overlap with existing official (suppressed): {info['overlap_official']}",
        f"- Overlap with existing community / brianleect (kept existing): {info['overlap_community']}",
        f"- Overlap total: {info['overlap_total']}",
        f"- After: total {len(merged)} (official {by_tier.get('official', 0)}, community {by_tier.get('community', 0)})",
        f"- Rows whose source cites octal mirror: {octal_rows}",
        "",
        "### Binance 15 check",
        "",
        f"- `{target}` present: **{bool(target_row)}**"
        + (
            f" (name=`{target_row['name']}`, tier=`{target_row['tier']}`, source=`{target_row['source']}`)"
            if target_row
            else ""
        ),
        "",
        "### Counts after this pull",
        "",
        f"- official: {by_tier.get('official', 0)}",
        f"- community: {by_tier.get('community', 0)}",
        "",
        *[f"- {k}: {by_cat.get(k, 0)}" for k in CAT_RANK],
        "",
        "### Still skipped",
        "",
        "- Direct etherscan.io HTML scrape (Cloudflare).",
        "- Phishing / take-action / website-down / airdrop-hunter / spam mega-noise.",
        "- Bulk LP / mega-colon protocol contracts under PROTO_EXTRA filters.",
        "- ofac-sanctions-lists / bybit label slugs absent from this octal snapshot.",
        "",
    ]
    with SOURCES_MD.open("a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main() -> int:
    existing = load_existing()
    before_total = len(existing)
    before_community = sum(1 for r in existing if r.get("tier") == "community")
    before_official = sum(1 for r in existing if r.get("tier") != "community")

    ok_labels, miss_labels = download_labels()
    from_octal, dump_by_cat, dump_by_venue, pick_meta = pick_from_octal(ok_labels)

    merged, info = merge(existing, from_octal)
    write_csv(merged)
    write_ts(merged)
    append_sources(
        before_total,
        before_community,
        before_official,
        merged,
        info,
        dump_by_cat,
        dump_by_venue,
        pick_meta,
        ok_labels,
        miss_labels,
    )

    by_tier = Counter(r.get("tier", "official") for r in merged)
    by_cat = Counter(r["category"] for r in merged)
    target = "0xc013426d7cef8be3ef3b366151ed85e4fe33688c"
    target_row = next((r for r in merged if r["address"] == target), None)
    print(
        json.dumps(
            {
                "before_total": before_total,
                "before_official": before_official,
                "before_community": before_community,
                "ok_labels": len(ok_labels),
                "miss_labels": miss_labels,
                "incoming": info["incoming"],
                "pick_meta": pick_meta,
                "added": info["added"],
                "overlap_official": info["overlap_official"],
                "overlap_community": info["overlap_community"],
                "overlap_total": info["overlap_total"],
                "after_total": len(merged),
                "after_official": by_tier.get("official", 0),
                "after_community": by_tier.get("community", 0),
                "by_category": dict(by_cat),
                "dump_by_cat": dict(dump_by_cat),
                "has_binance_15_target": bool(target_row),
                "target_row": (
                    {
                        "name": target_row["name"],
                        "tier": target_row["tier"],
                        "category": target_row["category"],
                        "source": target_row["source"],
                        "source_url": target_row["source_url"],
                    }
                    if target_row
                    else None
                ),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
