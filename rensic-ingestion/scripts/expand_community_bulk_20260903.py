#!/usr/bin/env python3
"""Bulk-expand community-tier known entities from brianleect/etherscan-labels.

Prior community import capped ~25 numbered tags per CEX venue (~145 rows).
This pull takes ALL useful exchange / mixer / bridge / dex / defi / gambling /
stablecoin / marketplace / OFAC-label accounts from the MIT mirror, plus a
forced current Etherscan Binance 15 address that the 2023 dump lacks.
"""
from __future__ import annotations

import csv
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path

CSV_PATH = Path(
    "/Users/george/Documents/WilderformTools/rensic/rensic-ingestion/transforms-python/src/myproject/data/known_entities.csv"
)
SOURCES_MD = CSV_PATH.with_name("SOURCES.md")
APP_TS = Path("/Users/george/Documents/WilderformTools/rensic/rensic-app/src/knownEntities.ts")
DUMP_PATH = Path("/tmp/etherscan-labels/combinedAllLabels.json")
DUMP_URL = (
    "https://raw.githubusercontent.com/brianleect/etherscan-labels/main/"
    "data/etherscan/combined/combinedAllLabels.json"
)
MIRROR_README = "https://github.com/brianleect/etherscan-labels"
PULL_DATE = date.today().isoformat()

ETH_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
NUM_RE = re.compile(r"^(.+?)\s+(\d+)$")
# Soft skip for junk names; never applied to forced rows.
SKIP_NAME_RE = re.compile(
    r"("
    r"website\s*down|airdrop\s*hunter|take\s*action|"
    r"old\s*contract|deprecated|"
    r"token\s*contract|erc[- ]?20|erc[- ]?721|erc[- ]?1155"
    r")",
    re.I,
)
# Pool / LP style names for bulk DEX protocol labels — keep category labels
# (dex/defi/bridge) even if poolish; only filter PROTO_EXTRA bulk.
POOLISH_RE = re.compile(r"[#/]|:\s*.*/|\bLP\b|\bpool\b|\d+\s*/\s*\d+", re.I)
# Mega ecosystem labels often use "Protocol: Pair" names — skip colon names there.
MEGA_COLON_LABELS = {
    "sushiswap", "bancor", "synthetix", "balancer", "rocket-pool", "curve-fi",
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

# Label slug -> (display name for venue rows, etherscan label page)
EXCHANGE_VENUES: dict[str, tuple[str, str]] = {
    "binance": ("Binance", "https://etherscan.io/accounts/label/binance"),
    "binance-deposit": ("Binance", "https://etherscan.io/accounts/label/binance"),
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
    "bitcoin-suisse": ("Bitcoin Suisse", "https://etherscan.io/accounts/label/bitcoin-suisse"),
    "coinhako": ("CoinHako", "https://etherscan.io/accounts/label/coinhako"),
    "remitano": ("Remitano", "https://etherscan.io/accounts/label/remitano"),
    "korbit": ("Korbit", "https://etherscan.io/accounts/label/korbit"),
    "allbit": ("Allbit", "https://etherscan.io/accounts/label/allbit"),
    "oobit": ("Oobit", "https://etherscan.io/accounts/label/oobit"),
    "tidex": ("Tidex", "https://etherscan.io/accounts/label/tidex"),
    "fiat-gateway": ("Fiat Gateway", "https://etherscan.io/accounts/label/fiat-gateway"),
}

# Non-exchange high-value category labels -> our category + cite page
CATEGORY_LABELS: dict[str, tuple[str, str, str]] = {
    # label: (our_category, source_name_suffix, etherscan_label_url)
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
    "bridge": (
        "protocol",
        "Bridge",
        "https://etherscan.io/accounts/label/bridge",
    ),
    "dex": (
        "protocol",
        "DEX",
        "https://etherscan.io/accounts/label/dex",
    ),
    "defi": (
        "protocol",
        "DeFi",
        "https://etherscan.io/accounts/label/defi",
    ),
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
    "ofac-sanctions-lists": (
        "sanctions",
        "OFAC label (Etherscan)",
        "https://etherscan.io/accounts/label/ofac-sanctions-lists",
    ),
}

# Named protocol ecosystems — include non-poolish names only (avoid 3k LP rows).
PROTO_EXTRA_LABELS: dict[str, str] = {
    "aave": "Aave",
    "curve-fi": "Curve",
    "lido": "Lido",
    "yearn-finance": "Yearn",
    "1inch": "1inch",
    "uniswap": "Uniswap",
    "compound": "Compound",
    "maker": "Maker",
    "makerdao": "MakerDAO",
    "instadapp": "Instadapp",
    "dydx": "dYdX",
    "opensea": "OpenSea",
    "blur": "Blur",
    "ens": "ENS",
    "convex-finance": "Convex",
    "frax": "Frax",
    "across-protocol": "Across",
    "hop-protocol": "Hop",
    "stargate": "Stargate",
    "synapse": "Synapse",
    "multichain": "Multichain",
    "anyswap": "AnySwap",
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
    "index-protocol": "Index Protocol",
}

# George-verified current Etherscan nametag (absent / reassigned in 2023 mirror).
FORCED_COMMUNITY = [
    (
        "0xc013426d7cef8be3ef3b366151ed85e4fe33688c",
        "Binance 15",
        "exchange",
        "Etherscan label / Binance",
        "https://etherscan.io/address/0xc013426d7cef8be3ef3b366151ed85e4fe33688c",
    ),
]

# George-listed Coinbase community nametags (keep explicit names).
COINBASE_FORCED = [
    ("0x71660c4005ba85c37ccec55d0c4493e66fe775d3", "Coinbase 1"),
    ("0x503828976d22510aad0201ac7ec88293211d23da", "Coinbase 2"),
    ("0xddfabcdc4d8ffc6d5beaf154f18b778f892a0740", "Coinbase 3"),
    ("0x3cd751e6b0078be393132286c442345e5dc49699", "Coinbase 4"),
    ("0xb5d85cbf7cb3ee0d56b3bb207d5fc4b82f43f511", "Coinbase 5"),
    ("0xeb2629a2734e272bcc07bda959863f316f4bd4cf", "Coinbase 6"),
    ("0xd688aea8f7d450909ade10c47faa95707b0682d9", "Coinbase 7"),
    ("0x02466e547bfdab679fc49e96bbfc62b9747d997c", "Coinbase 8"),
    ("0x6b76f8b1e9e59913bfe758821887311ba1805cab", "Coinbase 9"),
    ("0xa9d1e08c7793af67e9d92fe308d5697fb81d3e43", "Coinbase 10"),
    ("0x77696bb39917c91a0c3908d577d5e322095425ca", "Coinbase 11"),
]
COINBASE_LABEL_URL = "https://etherscan.io/accounts/label/coinbase"


def ascii_name(s: str) -> str:
    """Pack is ASCII-only; drop/replace non-ASCII nametag glyphs."""
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


def load_dump() -> dict:
    if not DUMP_PATH.is_file():
        raise FileNotFoundError(f"Missing dump at {DUMP_PATH}; download {DUMP_URL}")
    with DUMP_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def normalize_exchange_name(raw: str, display: str) -> str:
    name = raw.strip()
    m = NUM_RE.match(name)
    if m:
        base = m.group(1).strip()
        base_n = re.sub(r"[.\s_-]+", "", base.lower())
        disp_n = re.sub(r"[.\s_-]+", "", display.lower())
        # Accept near-matches: "Kucoin 7" -> "KuCoin 7", "Gate.io 1" etc.
        if (
            base_n == disp_n
            or base_n.startswith(disp_n[: min(4, len(disp_n))])
            or disp_n.startswith(base_n[: min(4, len(base_n))])
        ):
            return f"{display} {m.group(2)}"
        # Keep original numbered name if venue-labeled but differently named.
        return name
    # Bare venue name
    raw_n = re.sub(r"[.\s_-]+", "", name.lower())
    disp_n = re.sub(r"[.\s_-]+", "", display.lower())
    if raw_n == disp_n or raw_n in (disp_n, display.lower()):
        return display
    return name


def pick_from_dump(data: dict) -> tuple[list[dict], Counter, Counter]:
    """Return community rows, counts by our category, counts by venue/label."""
    by_addr: dict[str, dict] = {}
    by_cat: Counter = Counter()
    by_venue: Counter = Counter()

    def consider(r: dict, venue_key: str | None = None) -> None:
        addr = r["address"]
        prev = by_addr.get(addr)
        if prev is None:
            by_addr[addr] = r
            by_cat[r["category"]] += 1
            if venue_key:
                by_venue[venue_key] += 1
            else:
                by_venue[r["category"]] += 1
            return
        # Prefer higher-priority category; then prefer exchange-normalized names.
        if CAT_RANK.get(r["category"], 99) < CAT_RANK.get(prev["category"], 99):
            by_cat[prev["category"]] -= 1
            by_cat[r["category"]] += 1
            by_addr[addr] = r

    for addr, meta in data.items():
        if not ETH_RE.match(addr or ""):
            continue
        name = (meta.get("name") or "").strip()
        if not name:
            continue
        if SKIP_NAME_RE.search(name):
            continue
        labels = [str(x).lower() for x in (meta.get("labels") or [])]
        label_set = set(labels)

        # 1) Exchange venues (full, uncapped)
        venue_hit = None
        for lab in labels:
            if lab in EXCHANGE_VENUES:
                venue_hit = lab
                break
        if venue_hit:
            display, src_url = EXCHANGE_VENUES[venue_hit]
            # fiat-gateway only if name looks like a known venue or numbered tag
            if venue_hit == "fiat-gateway":
                # Keep all named fiat-gateway accounts; they are useful desk labels.
                pass
            nice = normalize_exchange_name(name, display)
            # Prefer venue-specific label page when not fiat-gateway generic
            if venue_hit != "fiat-gateway":
                source = f"Etherscan label / {display}"
            else:
                source = "Etherscan label / Fiat Gateway"
                # If name already names a venue, keep name as-is
                nice = name
            consider(
                row(addr, nice, "exchange", source, src_url, "community"),
                venue_key=display if venue_hit != "fiat-gateway" else "Fiat Gateway",
            )
            continue

        # 2) High-value category labels
        cat_hit = None
        for lab in labels:
            if lab in CATEGORY_LABELS:
                cat_hit = lab
                break
        if cat_hit:
            our_cat, suffix, src_url = CATEGORY_LABELS[cat_hit]
            consider(
                row(
                    addr,
                    name,
                    our_cat,
                    f"Etherscan label / {suffix}",
                    src_url,
                    "community",
                ),
                venue_key=suffix,
            )
            continue

        # 3) Named protocol extras (non-poolish only)
        proto_hit = None
        for lab in labels:
            if lab in PROTO_EXTRA_LABELS:
                proto_hit = lab
                break
        if proto_hit:
            if POOLISH_RE.search(name):
                continue
            if ":" in name and proto_hit in MEGA_COLON_LABELS:
                continue
            suffix = PROTO_EXTRA_LABELS[proto_hit]
            consider(
                row(
                    addr,
                    name,
                    "protocol",
                    f"Etherscan label / {suffix}",
                    f"https://etherscan.io/accounts/label/{proto_hit}",
                    "community",
                ),
                venue_key=suffix,
            )

    return list(by_addr.values()), by_cat, by_venue


def forced_rows() -> list[dict]:
    out = []
    for a, n, cat, src, url in FORCED_COMMUNITY:
        out.append(row(a, n, cat, src, url, "community"))
    for a, n in COINBASE_FORCED:
        out.append(
            row(
                a,
                n,
                "exchange",
                "Etherscan label / Coinbase",
                COINBASE_LABEL_URL,
                "community",
            )
        )
    return out


def merge(existing: list[dict], incoming: list[dict]) -> tuple[list[dict], dict]:
    by_key: dict[tuple[str, str], dict] = {}
    for r in existing:
        by_key[(r["chain"], r["address"])] = r
    added = 0
    replaced = 0
    suppressed_community = 0
    for r in incoming:
        key = (r["chain"], r["address"])
        if key not in by_key:
            by_key[key] = r
            added += 1
            continue
        old = by_key[key]
        old_tier = TIER_RANK.get(old.get("tier", "official"), 0)
        new_tier = TIER_RANK.get(r.get("tier", "community"), 1)
        if old_tier < new_tier:
            # official beats community — keep official
            suppressed_community += 1
            continue
        if new_tier < old_tier:
            by_key[key] = r
            replaced += 1
            continue
        # Same tier: allow name refresh for forced / better category
        if CAT_RANK.get(r["category"], 99) < CAT_RANK.get(old["category"], 99):
            by_key[key] = r
            replaced += 1
            continue
        # Same tier+cat: if incoming is forced Binance 15 or Coinbase forced, refresh name/url
        if r["address"] in {x[0].lower() for x in FORCED_COMMUNITY} or r[
            "address"
        ] in {a.lower() for a, _ in COINBASE_FORCED}:
            if r["name"] != old["name"] or r["source_url"] != old["source_url"]:
                by_key[key] = r
                replaced += 1
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
        "replaced": replaced,
        "suppressed_community": suppressed_community,
        "incoming": len(incoming),
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
    """Prefer full TS if modest; else JSON sidecar imported by thin TS wrapper."""
    n = len(rows)
    cats = sorted({r["category"] for r in rows} | set(CAT_RANK))
    cat_union = " | ".join(json.dumps(c) for c in cats)

    # Build JSON payload (compact) for either path
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

    use_json = n >= 2000
    if use_json:
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
        # ensure resolveJsonModule
        return

    parts = [
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
        "export const KNOWN_ENTITIES: KnownEntity[] = [",
    ]
    for obj in payload:
        body = ",\n".join(
            f"    {k}: {json.dumps(v, ensure_ascii=True)}" for k, v in obj.items()
        )
        parts.append("  {")
        parts.append(body + ",")
        parts.append("  },")
    parts.append("];")
    parts.append(TS_HELPERS)
    APP_TS.write_text("\n".join(parts) + "\n", encoding="utf-8")
    # Remove stale json if present from prior attempt
    stale = APP_TS.with_name("knownEntities.json")
    if stale.is_file():
        stale.unlink()


def append_sources(
    before_total: int,
    before_community: int,
    before_official: int,
    merged: list[dict],
    info: dict,
    dump_by_cat: Counter,
    dump_by_venue: Counter,
) -> None:
    by_tier = Counter(r.get("tier", "official") for r in merged)
    by_cat = Counter(r["category"] for r in merged)
    binance_c = sum(
        1
        for r in merged
        if r.get("tier") == "community"
        and r["category"] == "exchange"
        and r["name"].lower().startswith("binance")
    )
    venue_comm = Counter()
    for r in merged:
        if r.get("tier") != "community" or r["category"] != "exchange":
            continue
        m = NUM_RE.match(r["name"])
        base = m.group(1) if m else r["name"].split(":")[0].strip()
        venue_comm[base] += 1

    target = "0xc013426d7cef8be3ef3b366151ed85e4fe33688c"
    has_target = any(r["address"] == target for r in merged)
    target_row = next((r for r in merged if r["address"] == target), None)

    lines = [
        "",
        "",
        f"## Community bulk expand: {PULL_DATE}",
        "",
        "Prior community import was too thin (per-venue cap ~25 numbered CEX tags,",
        f"~{before_community} community rows). George found Vitalik-case counterparty",
        f"`{target}` labeled **Binance 15** on live Etherscan but missing from the pack",
        "(2023 mirror had a different address as Binance 15; labels reassigned).",
        "",
        "### Source",
        "",
        f"- MIT mirror [`brianleect/etherscan-labels`]({MIRROR_README})",
        f"  combined dump: `{DUMP_URL}`",
        f"- Pull date: {PULL_DATE} (mirror ETH scrape stamped 18/6/2023; ~29945 accounts)",
        "- Each community row cites the matching Etherscan label page (or address page)",
        "  as `source_url`; `source` names Etherscan label / venue.",
        "- Phishing labels skipped. Mega Sushi/Bancor/Synthetix/Rocket Pool/Balancer bulk",
        "  omitted from PROTO_EXTRA (LP noise); category labels `dex`/`defi`/`bridge` kept when named.",
        "",
        "### Forced / verified rows",
        "",
        f"- Binance 15: `{target}` -> name `Binance 15`, category `exchange`,",
        "  tier `community`, cite address page on Etherscan.",
        f"  Present after merge: **{has_target}**"
        + (f" ({target_row['name']}, {target_row['tier']})" if target_row else ""),
        "- Coinbase 1-11 forced name list retained.",
        "",
        "### Selection (uncapped venues)",
        "",
        "- ALL accounts under major CEX / fiat-gateway labels in the mirror",
        "  (Binance, Coinbase, Kraken, OKX, Huobi, KuCoin, Gemini, Bitfinex, Bitstamp,",
        "  Crypto.com, Gate.io, BitMEX, Bittrex, Poloniex, FTX, AscendEX, Nexo, BlockFi,",
        "  plus regional CEXes present in the dump).",
        "- High-value categories: tornado-cash / ethereum-mixer -> `mixer`;",
        "  gambling -> `gambling`; bridge / dex / defi / protocol / stablecoin -> `protocol`;",
        "  marketplace -> `shop`; ofac-sanctions-lists -> `sanctions` (community caveat).",
        "- Named protocol ecosystems (Aave, Curve, Lido, Uniswap, ...): non-poolish names only.",
        "",
        "### Dump pick counts (before official-wins merge)",
        "",
        f"- By mapped category: {dict(dump_by_cat)}",
        f"- By venue/label bucket (top): {dict(dump_by_venue.most_common(40))}",
        "",
        "### Merge",
        "",
        f"- Before: total {before_total} (official {before_official}, community {before_community})",
        f"- Incoming community unique: {info['incoming']}",
        f"- Newly added: {info['added']}",
        f"- Same-tier refreshes: {info['replaced']}",
        f"- Community suppressed by existing official: {info['suppressed_community']}",
        f"- After: total {len(merged)} (official {by_tier.get('official', 0)}, community {by_tier.get('community', 0)})",
        f"- Binance community rows (name startswith Binance): {binance_c}",
        "",
        "### Counts after this pull",
        "",
        f"- official: {by_tier.get('official', 0)}",
        f"- community: {by_tier.get('community', 0)}",
        "",
        *[f"- {k}: {by_cat.get(k, 0)}" for k in CAT_RANK],
        "",
        f"Community exchange venues (row counts): {dict(sorted(venue_comm.items()))}",
        "",
        "### Still skipped",
        "",
        "- Direct etherscan.io HTML scrape (Cloudflare).",
        "- Phishing / take-action / website-down / airdrop-hunter nametags.",
        "- Bulk LP pool contracts under Sushi/Balancer-style PROTO_EXTRA filters.",
        "- Bybit Etherscan label slug absent from 2023 mirror (official Bybit PoR already in pack).",
        "",
    ]
    with SOURCES_MD.open("a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main() -> int:
    existing = load_existing()
    before_total = len(existing)
    before_community = sum(1 for r in existing if r.get("tier") == "community")
    before_official = sum(1 for r in existing if r.get("tier") != "community")

    dump = load_dump()
    from_dump, dump_by_cat, dump_by_venue = pick_from_dump(dump)
    forced = forced_rows()

    # Forced wins on name/url for overlapping addresses.
    incoming_map: dict[str, dict] = {}
    for r in from_dump:
        incoming_map[r["address"]] = r
    for r in forced:
        incoming_map[r["address"]] = r
    incoming = list(incoming_map.values())

    merged, info = merge(existing, incoming)
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
    )

    by_tier = Counter(r.get("tier", "official") for r in merged)
    by_cat = Counter(r["category"] for r in merged)
    target = "0xc013426d7cef8be3ef3b366151ed85e4fe33688c"
    binance_c = sum(
        1
        for r in merged
        if r.get("tier") == "community"
        and r["category"] == "exchange"
        and r["name"].lower().startswith("binance")
    )
    print(
        json.dumps(
            {
                "before_total": before_total,
                "before_official": before_official,
                "before_community": before_community,
                "incoming": len(incoming),
                "dump_picked": len(from_dump),
                "added": info["added"],
                "replaced": info["replaced"],
                "suppressed_community": info["suppressed_community"],
                "after_total": len(merged),
                "after_official": by_tier.get("official", 0),
                "after_community": by_tier.get("community", 0),
                "binance_community": binance_c,
                "has_binance_15_target": any(r["address"] == target for r in merged),
                "target_row": next(
                    (
                        {
                            "name": r["name"],
                            "tier": r["tier"],
                            "category": r["category"],
                            "source_url": r["source_url"],
                        }
                        for r in merged
                        if r["address"] == target
                    ),
                    None,
                ),
                "by_category": dict(by_cat),
                "dump_by_cat": dict(dump_by_cat),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
