#!/usr/bin/env python3
"""Add dual-tier labels: official (existing) vs community (Etherscan-style CEX nametags)."""
from __future__ import annotations

import csv
import json
import re
import urllib.request
from collections import Counter
from datetime import date
from pathlib import Path

CSV_PATH = Path(
    "/Users/george/Documents/WilderformTools/rensic/rensic-ingestion/transforms-python/src/myproject/data/known_entities.csv"
)
SOURCES_MD = CSV_PATH.with_name("SOURCES.md")
APP_TS = Path("/Users/george/Documents/WilderformTools/rensic/rensic-app/src/knownEntities.ts")

ETH_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
NUM_RE = re.compile(r"^(.+?)\s+(\d+)$")
SKIP_RE = re.compile(
    r"(token|deployer|old|contract|fee|multisig|deposit funder|wrapped|"
    r"mining|pool|commerce|controller|unlock|blockfolio|hbtc|fil|dollar|stable)",
    re.I,
)

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

# George-listed Coinbase community nametags (Etherscan label page).
COINBASE_COMMUNITY = [
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

# Major CEX label pages (Etherscan). Addresses pulled from MIT dump that mirrors those tags.
VENUES = {
    "coinbase": ("Coinbase", COINBASE_LABEL_URL),
    "binance": ("Binance", "https://etherscan.io/accounts/label/binance"),
    "kraken": ("Kraken", "https://etherscan.io/accounts/label/kraken"),
    "okx": ("OKX", "https://etherscan.io/accounts/label/okx"),
    "huobi": ("Huobi", "https://etherscan.io/accounts/label/huobi"),
    "kucoin": ("KuCoin", "https://etherscan.io/accounts/label/kucoin"),
    "gemini": ("Gemini", "https://etherscan.io/accounts/label/gemini"),
    "bitfinex": ("Bitfinex", "https://etherscan.io/accounts/label/bitfinex"),
    "bitstamp": ("Bitstamp", "https://etherscan.io/accounts/label/bitstamp"),
    "gate-io": ("Gate.io", "https://etherscan.io/accounts/label/gate-io"),
    "crypto-com": ("Crypto.com", "https://etherscan.io/accounts/label/crypto-com"),
    "bitmex": ("BitMEX", "https://etherscan.io/accounts/label/bitmex"),
    "bittrex": ("Bittrex", "https://etherscan.io/accounts/label/bittrex"),
    "poloniex": ("Poloniex", "https://etherscan.io/accounts/label/poloniex"),
    "bybit": ("Bybit", "https://etherscan.io/accounts/label/bybit"),
}

ETHERSCAN_LABELS_JSON = (
    "https://raw.githubusercontent.com/brianleect/etherscan-labels/master/"
    "data/etherscan/combined/combinedAllLabels.json"
)
# Cap numbered tags per venue (sanity; not millions of rows).
PER_VENUE_CAP = 25


def row(
    address: str,
    name: str,
    category: str,
    source: str,
    source_url: str,
    tier: str,
    secondary: str = "",
) -> dict:
    assert ETH_RE.match(address), address
    assert tier in ("official", "community"), tier
    return {
        "chain": "ethereum",
        "address": address.lower(),
        "name": name,
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
                # Backfill: all prior curated rows are official.
                "tier": (r.get("tier") or "official").strip().lower() or "official",
            }
        )
    return out


def fetch_etherscan_label_dump() -> dict:
    local = Path("/tmp/combinedAllLabels.json")
    if local.is_file():
        with local.open(encoding="utf-8") as f:
            return json.load(f)
    # Fallback: urllib (may fail on some Python SSL installs).
    import ssl
    ctx = ssl.create_default_context()
    try:
        req = urllib.request.Request(
            ETHERSCAN_LABELS_JSON,
            headers={"User-Agent": "rensic-ingestion/community-tier"},
        )
        with urllib.request.urlopen(req, timeout=90, context=ctx) as resp:
            return json.load(resp)
    except Exception:
        ctx = ssl._create_unverified_context()
        req = urllib.request.Request(
            ETHERSCAN_LABELS_JSON,
            headers={"User-Agent": "rensic-ingestion/community-tier"},
        )
        with urllib.request.urlopen(req, timeout=90, context=ctx) as resp:
            return json.load(resp)


def pick_community_from_dump(data: dict) -> list[dict]:
    by_venue: dict[str, list[dict]] = {k: [] for k in VENUES}
    for addr, meta in data.items():
        if not ETH_RE.match(addr or ""):
            continue
        name = (meta.get("name") or "").strip()
        if not name or SKIP_RE.search(name):
            continue
        labels = [str(x).lower() for x in (meta.get("labels") or [])]
        venue_key = None
        for k in VENUES:
            if k in labels:
                venue_key = k
                break
        if not venue_key:
            continue
        display, src_url = VENUES[venue_key]
        ok = False
        m = NUM_RE.match(name)
        if m:
            base = m.group(1).strip()
            base_n = base.lower().replace(".", "").replace(" ", "")
            disp_n = display.lower().replace(".", "").replace(" ", "")
            if base_n == disp_n or base_n.startswith(disp_n[:4]):
                ok = True
                # Normalize casing: "Kucoin 7" -> "KuCoin 7"
                name = f"{display} {m.group(2)}"
        elif name.lower().replace(".", "") in (
            display.lower().replace(".", ""),
            venue_key.replace("-", ""),
            venue_key.replace("-", "."),
        ):
            ok = True
            name = display
        if not ok:
            continue
        by_venue[venue_key].append(
            row(
                addr,
                name,
                "exchange",
                f"Etherscan label / {display}",
                src_url,
                "community",
            )
        )

    out: list[dict] = []
    for k, rows in by_venue.items():
        # Prefer numbered tags sorted by number, then bare venue name.
        def sort_key(r: dict):
            m = NUM_RE.match(r["name"])
            if m:
                return (0, int(m.group(2)), r["address"])
            return (1, 0, r["address"])

        rows = sorted(rows, key=sort_key)
        # Dedupe address within venue
        seen = set()
        uniq = []
        for r in rows:
            if r["address"] in seen:
                continue
            seen.add(r["address"])
            uniq.append(r)
        out.extend(uniq[:PER_VENUE_CAP])
    return out


def coinbase_forced() -> list[dict]:
    return [
        row(
            a,
            n,
            "exchange",
            "Etherscan label / Coinbase",
            COINBASE_LABEL_URL,
            "community",
        )
        for a, n in COINBASE_COMMUNITY
    ]


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
        # Official always beats community on same address.
        if old_tier < new_tier:
            suppressed_community += 1
            continue
        if new_tier < old_tier:
            by_key[key] = r
            replaced += 1
            continue
        # Same tier: category precedence.
        if CAT_RANK.get(r["category"], 99) < CAT_RANK.get(old["category"], 99):
            by_key[key] = r
            replaced += 1
    merged = sorted(
        by_key.values(),
        key=lambda x: (
            TIER_RANK.get(x.get("tier", "official"), 9),
            x["category"],
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
    parts = [
        'export type EntityCategory = "sanctions" | "mixer" | "exchange" | "protocol" | "person";',
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
        body = ",\n".join(f"    {k}: {json.dumps(v, ensure_ascii=True)}" for k, v in obj.items())
        parts.append("  {")
        parts.append(body + ",")
        parts.append("  },")
    parts.append("];")
    parts.append(TS_HELPERS)
    APP_TS.write_text("\n".join(parts) + "\n", encoding="utf-8")


def append_sources(
    existing_n: int,
    merged: list[dict],
    info: dict,
    venue_counts: dict,
    coinbase_n: int,
) -> None:
    by_tier = Counter(r.get("tier", "official") for r in merged)
    by_cat = Counter(r["category"] for r in merged)
    exch_comm = Counter(
        r["name"].split()[0] if r["name"] else "?"
        for r in merged
        if r.get("tier") == "community" and r["category"] == "exchange"
    )
    # Better venue count for community
    venue_name = Counter()
    for r in merged:
        if r.get("tier") != "community":
            continue
        m = NUM_RE.match(r["name"])
        base = m.group(1) if m else r["name"]
        venue_name[base] += 1

    lines = [
        "",
        "",
        f"## Dual-tier labels: {date.today().isoformat()} (official vs community)",
        "",
        "### Two-lane policy",
        "",
        "1. **official** — PoR, company blogs, deployment docs, OFAC, FBI/IC3, OpenSanctions,",
        "   GraphSense government/project packs, etc. Drives ledger title + sort + category.",
        "   Investigator Flag MUST NOT overwrite official pack name/category in the UI.",
        "2. **community** — Etherscan nametags / community label dumps (unofficial).",
        "   Shown with caveat and a distinct desk chip style. Flag CAN override display for",
        "   the case/user (investigator wins over community for display only; community stays in pack).",
        "3. If both exist for the same address: **official wins** for title/sort/category.",
        "   Community row is suppressed on conflict (not mixed into official).",
        "4. Never call community labels \"Coinbase official\". Numbered names like \"Coinbase 1\"",
        "   with `tier=community` are fine.",
        "",
        "CSV column: `tier` = `official` | `community`. All pre-existing rows backfilled as `official`.",
        "",
        "### Community sources used",
        "",
        f"1. George-listed Coinbase 1-11 ETH nametags; primary cite `{COINBASE_LABEL_URL}` ({coinbase_n} rows).",
        "2. Additional major-CEX numbered Etherscan nametags via the MIT-licensed public mirror",
        f"   [`brianleect/etherscan-labels`]({ETHERSCAN_LABELS_JSON}) (combinedAllLabels.json).",
        "   Each community row cites the matching Etherscan label page as `source_url`, not the mirror.",
        "   Cap: well-known numbered exchange tags only (skip tokens/deployers/old/contracts);",
        f"   max {PER_VENUE_CAP} per venue.",
        "",
        "Community label pages cited:",
    ]
    for _k, (display, url) in VENUES.items():
        n = venue_name.get(display, 0)
        if n:
            lines.append(f"- {display}: `{url}` ({n} rows)")
    lines.extend(
        [
            "",
            "### Merge",
            "",
            f"- Existing before pull (all backfilled official): {existing_n}",
            f"- Incoming community unique: {info['incoming']}",
            f"- Newly added: {info['added']}",
            f"- Precedence replaces: {info['replaced']}",
            f"- Community suppressed by existing official: {info['suppressed_community']}",
            f"- Total rows now: {len(merged)}",
            "",
            "### Counts after this pull",
            "",
            f"- official: {by_tier.get('official', 0)}",
            f"- community: {by_tier.get('community', 0)}",
            f"- Coinbase community: {coinbase_n}",
            "",
        ]
    )
    for cat in ("sanctions", "mixer", "gambling", "exchange", "shop", "protocol", "person"):
        lines.append(f"- {cat}: {by_cat.get(cat, 0)}")
    lines.append("")
    lines.append(f"Community exchange venues (row counts): {dict(venue_name)}")
    lines.append(f"New community venue adds this pull: {venue_counts}")
    lines.append("")
    lines.append("### Still skipped")
    lines.append("")
    lines.append("- Arkham: no static public page with clear address attribution used.")
    lines.append("- Full Etherscan labelcloud dumps / millions of nametags: capped to numbered CEX tags.")
    lines.append("- Direct etherscan.io HTML scrape: Cloudflare-blocked; used MIT mirror + label page cites.")
    lines.append("")
    with SOURCES_MD.open("a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main() -> int:
    existing = load_existing()
    # Ensure every existing row has tier=official
    for r in existing:
        r["tier"] = "official"

    dump = fetch_etherscan_label_dump()
    from_dump = pick_community_from_dump(dump)
    forced_cb = coinbase_forced()

    # Merge forced Coinbase first so names match George's list, then dump.
    incoming_map: dict[str, dict] = {}
    for r in from_dump:
        incoming_map[r["address"]] = r
    for r in forced_cb:
        incoming_map[r["address"]] = r  # George list wins for Coinbase names
    incoming = list(incoming_map.values())

    existing_keys = {(r["chain"], r["address"]) for r in existing}
    venue_counts: Counter = Counter()
    for r in incoming:
        if (r["chain"], r["address"]) not in existing_keys:
            m = NUM_RE.match(r["name"])
            base = m.group(1) if m else r["name"]
            venue_counts[base] += 1

    merged, info = merge(existing, incoming)
    write_csv(merged)
    write_ts(merged)

    coinbase_n = sum(
        1
        for r in merged
        if r.get("tier") == "community" and r["name"].startswith("Coinbase")
    )
    append_sources(len(existing), merged, info, dict(venue_counts), coinbase_n)

    by_tier = Counter(r.get("tier", "official") for r in merged)
    print(
        json.dumps(
            {
                "existing": len(existing),
                "incoming": len(incoming),
                "added": info["added"],
                "replaced": info["replaced"],
                "suppressed_community": info["suppressed_community"],
                "total": len(merged),
                "official": by_tier.get("official", 0),
                "community": by_tier.get("community", 0),
                "coinbase_community": coinbase_n,
                "new_by_venue": dict(venue_counts),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
