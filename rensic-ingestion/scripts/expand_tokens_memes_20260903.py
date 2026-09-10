#!/usr/bin/env python3
"""Expand known_entities with official ERC-20 token lists + curated ETH meme coins."""
from __future__ import annotations

import csv
import json
import re
import unicodedata
from collections import Counter
from datetime import date
from pathlib import Path

CSV_PATH = Path(
    "/Users/george/Documents/WilderformTools/rensic/rensic-ingestion/transforms-python/src/myproject/data/known_entities.csv"
)
SOURCES_MD = CSV_PATH.with_name("SOURCES.md")
APP_TS = Path("/Users/george/Documents/WilderformTools/rensic/rensic-app/src/knownEntities.ts")
TOKEN_DIR = Path("/tmp/rensic-tokens")
PULL_DATE = date.today().isoformat()

ETH_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
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

TOKEN_LISTS = [
    (
        "uniswap.json",
        "Uniswap Labs Default token list",
        "https://tokens.uniswap.org",
        "Uniswap Labs Default",
        "Uniswap Labs published default list (tokenlists.org standard); canonical URL https://tokens.uniswap.org",
    ),
    (
        "gemini.json",
        "Gemini Token List",
        "https://www.gemini.com/uniswap/manifest.json",
        "Gemini Token List",
        "Gemini published Uniswap-compatible token list manifest",
    ),
    (
        "compound.json",
        "Compound token list",
        "https://raw.githubusercontent.com/compound-finance/token-list/master/compound.tokenlist.json",
        "Compound",
        "Compound Finance GitHub token-list (compound.tokenlist.json)",
    ),
    (
        "wrapped.json",
        "Wrapped Tokens token list",
        "https://wrapped.tokensoft.eth.link",
        "Wrapped Tokens",
        "TokenSoft Wrapped Tokens list (wrapped.tokensoft.eth.link)",
    ),
]

# Extra meme/culture tokens NOT reliably covered only by lists, or worth explicit cite.
# Addresses verified via DefiLlama coins API prices (2026-09-03) and/or Uniswap list.
# BONK: ETH bridged token (Solana-native originally) with llama price on this 0x.
MEME_EXTRA = [
    # Already on Uniswap -> will also arrive via list; listed for SOURCES documentation
    {
        "address": "0x6982508145454ce325ddbe47a25d4ec3d2311933",
        "name": "Pepe",
        "tier": "official",
        "source": "Uniswap Labs Default token list",
        "source_url": "https://tokens.uniswap.org",
    },
    {
        "address": "0x95ad61b0a150d79219dcf64e1e6cc01f0b64c4ce",
        "name": "SHIBA INU",
        "tier": "official",
        "source": "Uniswap Labs Default token list",
        "source_url": "https://tokens.uniswap.org",
    },
    {
        "address": "0xcf0c122c6b73ff809c693db761e7baebe62b6a2e",
        "name": "FLOKI",
        "tier": "official",
        "source": "Uniswap Labs Default token list",
        "source_url": "https://tokens.uniswap.org",
    },
    {
        "address": "0xb131f4a55907b10d1f0a50d8ab8fa09ec342cd74",
        "name": "Memecoin",
        "tier": "official",
        "source": "Uniswap Labs Default token list",
        "source_url": "https://tokens.uniswap.org",
    },
    {
        "address": "0xaaee1a9723aadb7afa2810263653a34ba2c21c7a",
        "name": "Mog Coin",
        "tier": "official",
        "source": "Uniswap Labs Default token list",
        "source_url": "https://tokens.uniswap.org",
    },
    {
        "address": "0x761d38e5ddf6ccf6cf7c55759d5210750b5d60f3",
        "name": "Dogelon Mars",
        "tier": "official",
        "source": "Uniswap Labs Default token list",
        "source_url": "https://tokens.uniswap.org",
    },
    {
        "address": "0x72e4f9f808c49a2a61de9c5896298920dc4eeea9",
        "name": "HarryPotterObamaSonic10Inu",
        "tier": "official",
        "source": "Uniswap Labs Default token list",
        "source_url": "https://tokens.uniswap.org",
    },
    {
        "address": "0x594daad7d77592a2b97b725a7ad59d7e188b5bfa",
        "name": "Apu Apustaja",
        "tier": "official",
        "source": "Uniswap Labs Default token list",
        "source_url": "https://tokens.uniswap.org",
    },
    {
        "address": "0x812ba41e071c7b7fa4ebcfb62df5f45f6fa853ee",
        "name": "Neiro",
        "tier": "official",
        "source": "Uniswap Labs Default token list",
        "source_url": "https://tokens.uniswap.org",
    },
    {
        "address": "0xa35923162c49cf95e6bf26623385eb431ad920d3",
        "name": "Turbo",
        "tier": "official",
        "source": "Uniswap Labs Default token list",
        "source_url": "https://tokens.uniswap.org",
    },
    {
        "address": "0xe0f63a424a4439cbe457d80e4f4b51ad25b2c56c",
        "name": "SPX6900",
        "tier": "official",
        "source": "Uniswap Labs Default token list",
        "source_url": "https://tokens.uniswap.org",
    },
    # Not on Uniswap default; DefiLlama-priced ETH contracts + Etherscan cite
    {
        "address": "0x12970e6868f88f6557b76120662c1b3e50a646bf",
        "name": "Milady",
        "tier": "community",
        "source": "Etherscan token / DefiLlama",
        "source_url": "https://etherscan.io/token/0x12970e6868f88f6557b76120662c1b3e50a646bf",
    },
    {
        "address": "0x1151cb3d861920e07a38e03eead12c32178567f6",
        "name": "Bonk",
        "tier": "community",
        "source": "Etherscan token / DefiLlama",
        "source_url": "https://etherscan.io/token/0x1151cb3d861920e07a38e03eead12c32178567f6",
    },
    {
        "address": "0x576e2bed8f7b46d34016198911cdf9886f78bea7",
        "name": "MAGA",
        "tier": "community",
        "source": "Etherscan token / DefiLlama",
        "source_url": "https://etherscan.io/token/0x576e2bed8f7b46d34016198911cdf9886f78bea7",
    },
    {
        "address": "0x8390a1da07e376ef7add4be859ba74fb83aa02d5",
        "name": "GROK",
        "tier": "community",
        "source": "Etherscan token / DefiLlama",
        "source_url": "https://etherscan.io/token/0x8390a1da07e376ef7add4be859ba74fb83aa02d5",
    },
    {
        "address": "0xac57de9c1a09fec648e93eb98875b212db0d460b",
        "name": "Baby Doge Coin",
        "tier": "community",
        "source": "Etherscan token / DefiLlama",
        "source_url": "https://etherscan.io/token/0xac57de9c1a09fec648e93eb98875b212db0d460b",
    },
    {
        "address": "0x7a58c0be72be218b41c608b7fe7c5bb630736c71",
        "name": "ConstitutionDAO",
        "tier": "community",
        "source": "Etherscan token / DefiLlama",
        "source_url": "https://etherscan.io/token/0x7a58c0be72be218b41c608b7fe7c5bb630736c71",
    },
    {
        "address": "0xf4d2888d29d722226fafa5d9b24f9164c092421e",
        "name": "LooksRare",
        "tier": "community",
        "source": "Etherscan token / DefiLlama",
        "source_url": "https://etherscan.io/token/0xf4d2888d29d722226fafa5d9b24f9164c092421e",
    },
    {
        "address": "0x43dfc4159d86f3a37a5a4b3d4580b888ad7d4ddd",
        "name": "DODO",
        "tier": "community",
        "source": "Etherscan token / DefiLlama",
        "source_url": "https://etherscan.io/token/0x43dfc4159d86f3a37a5a4b3d4580b888ad7d4ddd",
    },
    # Shiba ecosystem docs
    {
        "address": "0x9813037ee221f0bfda40f938b757d13076c0b411",
        "name": "Bone ShibaSwap",
        "tier": "official",
        "source": "Shiba Inu docs",
        "source_url": "https://docs.shibatoken.com/",
    },
    {
        "address": "0x27c70cd1946795b6c30dd2f43ed2df4862c1d021",
        "name": "DOGE Killer",
        "tier": "official",
        "source": "Shiba Inu docs",
        "source_url": "https://docs.shibatoken.com/",
    },
]


def to_ascii(s: str) -> str:
    if s is None:
        return ""
    s = unicodedata.normalize("NFKD", s)
    return s.encode("ascii", "ignore").decode("ascii").strip()


def norm_addr(a: str) -> str:
    return a.strip().lower()


def load_existing() -> list[dict]:
    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["address"] = norm_addr(r["address"])
        r["chain"] = (r.get("chain") or "ethereum").lower()
        if not r.get("tier"):
            r["tier"] = "official"
        if r.get("secondary_category") is None:
            r["secondary_category"] = ""
    return rows


def make_row(address: str, name: str, source: str, source_url: str, tier: str) -> dict:
    return {
        "chain": "ethereum",
        "address": norm_addr(address),
        "name": to_ascii(name),
        "category": "protocol",
        "secondary_category": "",
        "source": to_ascii(source),
        "source_url": source_url,
        "tier": tier,
    }


def load_tokenlist(path: Path, source: str, source_url: str) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    out = []
    for t in data.get("tokens") or []:
        if int(t.get("chainId") or 0) != 1:
            continue
        addr = t.get("address") or ""
        if not ETH_RE.match(addr):
            continue
        name = to_ascii(t.get("name") or t.get("symbol") or "")
        if not name:
            continue
        out.append(make_row(addr, name, source, source_url, "official"))
    return out


def merge(existing: list[dict], incoming: list[dict]) -> tuple[list[dict], dict]:
    by_key: dict[tuple[str, str], dict] = {}
    for r in existing:
        by_key[(r["chain"], r["address"])] = r

    stats = Counter()
    stats["incoming"] = len(incoming)
    for r in incoming:
        if not ETH_RE.match(r["address"]):
            stats["bad_addr"] += 1
            continue
        key = (r["chain"], r["address"])
        if key not in by_key:
            by_key[key] = r
            stats["added"] += 1
            stats[f"added_{r['tier']}"] += 1
            continue
        cur = by_key[key]
        cur_tier = TIER_RANK.get(cur.get("tier", "official"), 0)
        new_tier = TIER_RANK.get(r.get("tier", "community"), 1)
        if new_tier < cur_tier:
            by_key[key] = r
            stats["upgraded_to_official"] += 1
            continue
        if new_tier > cur_tier:
            stats["suppressed_community"] += 1
            continue
        stats["same_tier_kept"] += 1

    merged = list(by_key.values())
    merged.sort(
        key=lambda x: (
            CAT_RANK.get(x["category"], 99),
            TIER_RANK.get(x.get("tier", "official"), 9),
            x["name"].lower(),
            x["address"],
        )
    )
    return merged, dict(stats)


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
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def write_app(rows: list[dict]) -> None:
    helpers = Path("/tmp/ke_ts_helpers.txt").read_text(encoding="utf-8")
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
        helpers.rstrip("\n"),
        "",
    ]
    APP_TS.write_text("\n".join(parts), encoding="utf-8")


def append_sources(
    before: dict,
    merged: list[dict],
    stats: dict,
    list_meta: list[dict],
    meme_meta: dict,
) -> None:
    by_tier = Counter(r.get("tier", "official") for r in merged)
    by_cat = Counter(r["category"] for r in merged)
    lines = [
        "",
        "",
        f"## Official ERC-20 token lists + ETH meme coins: {PULL_DATE}",
        "",
        "Expand known entities with Ethereum mainnet token contract addresses",
        "(ERC-20 etc). Official curated tokenlists for breadth; curated meme/culture",
        "set with citations. Skipped CoinGecko all-tokens dump (~5.8k ETH) to avoid scam noise.",
        "",
        "### Official tokenlists (tier=official, category=protocol)",
        "",
    ]
    for m in list_meta:
        lines.append(
            f"- **{m['list_name']}** — `{m['url']}` "
            f"(ETH tokens in file: {m['eth_count']}; newly added this pull: {m['added']}; "
            f"already present: {m['overlap']})"
        )
        lines.append(f"  - Provenance: {m['provenance']}")
    lines.extend(
        [
            "",
            "Name policy: use each list's `name` field (ASCII-normalized), matching prior",
            "rows such as `USD Coin` / `Aave` / `Wrapped Ether`.",
            "",
            "### Meme / culture tokens",
            "",
            "Well-known ETH meme/culture contracts with a source:",
            "- On Uniswap Labs Default (tier=official via list): PEPE, SHIB, FLOKI, MEME,",
            "  MOG, ELON (Dogelon), BITCOIN (HPOS10I), APU, Neiro, TURBO, SPX6900, etc.",
            "- Extra curated (DefiLlama price check 2026-09-03 + Etherscan token page,",
            "  tier=community unless project docs): LADYS (Milady), BONK (ETH), MAGA/TRUMP,",
            "  GROK (ETH meme, not xAI), BabyDoge, PEOPLE (ConstitutionDAO), LOOKS, DODO.",
            "- Shiba ecosystem via docs.shibatoken.com (tier=official): BONE, LEASH.",
            "- Skipped: native DOGE (not ETH); Solana-only BONK without ETH 0x; invented addrs;",
            "  CoinGecko full dump.",
            "",
            f"- Curated meme extras considered: {meme_meta['considered']}",
            f"- Newly added from meme extras: {meme_meta['added']} "
            f"(official {meme_meta['added_official']}, community {meme_meta['added_community']})",
            f"- Meme extras already present: {meme_meta['overlap']}",
            "",
            "### Merge rules",
            "",
            "- ETH `0x` lowercased, `chain=ethereum`, `category=protocol` for tokens.",
            "- Dedupe on chain+address; **official > community** (upgrade community on conflict).",
            "- Same-tier: keep existing row (preserve WETH/USDC etc. names/sources).",
            "",
            "### Counts",
            "",
            f"- Before: total {before['total']} (official {before['official']}, community {before['community']})",
            f"- Incoming unique candidates: {stats.get('incoming', 0)}",
            f"- Newly added: {stats.get('added', 0)} "
            f"(official {stats.get('added_official', 0)}, community {stats.get('added_community', 0)})",
            f"- Upgraded community -> official: {stats.get('upgraded_to_official', 0)}",
            f"- Community suppressed by existing official: {stats.get('suppressed_community', 0)}",
            f"- Same-tier kept existing: {stats.get('same_tier_kept', 0)}",
            f"- After: total {len(merged)} (official {by_tier.get('official', 0)}, "
            f"community {by_tier.get('community', 0)})",
            "",
            "### Category totals after pull",
            "",
        ]
    )
    for cat in ("sanctions", "mixer", "gambling", "exchange", "shop", "protocol", "person"):
        lines.append(f"- {cat}: {by_cat.get(cat, 0)}")
    lines.append("")
    with SOURCES_MD.open("a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main() -> int:
    existing = load_existing()
    before = {
        "total": len(existing),
        "official": sum(1 for r in existing if r.get("tier") != "community"),
        "community": sum(1 for r in existing if r.get("tier") == "community"),
    }
    before_addrs = {r["address"] for r in existing}

    list_rows: list[dict] = []
    list_meta = []
    for fname, source, url, list_name, provenance in TOKEN_LISTS:
        path = TOKEN_DIR / fname
        rows = load_tokenlist(path, source, url)
        uniq = {r["address"]: r for r in rows}
        rows = list(uniq.values())
        addrs = set(uniq)
        list_meta.append(
            {
                "list_name": list_name,
                "url": url,
                "eth_count": len(rows),
                "added": sum(1 for a in addrs if a not in before_addrs),
                "overlap": sum(1 for a in addrs if a in before_addrs),
                "provenance": provenance,
            }
        )
        list_rows.extend(rows)

    # Prefer earlier lists (Uniswap first) within official tokenlists
    list_map: dict[str, dict] = {}
    for r in list_rows:
        if r["address"] not in list_map:
            list_map[r["address"]] = r

    memes = []
    for m in MEME_EXTRA:
        if not ETH_RE.match(m["address"]):
            continue
        memes.append(
            make_row(m["address"], m["name"], m["source"], m["source_url"], m["tier"])
        )

    # Combine: lists first, then memes; official beats community
    incoming_map: dict[str, dict] = {}
    for r in list(list_map.values()) + memes:
        a = r["address"]
        if a not in incoming_map:
            incoming_map[a] = r
            continue
        cur = incoming_map[a]
        if TIER_RANK[r["tier"]] < TIER_RANK[cur["tier"]]:
            incoming_map[a] = r
    incoming = list(incoming_map.values())

    merged, stats = merge(existing, incoming)
    write_csv(merged)
    write_app(merged)

    meme_addrs = {r["address"] for r in memes}
    meme_new = [
        r for r in merged if r["address"] in meme_addrs and r["address"] not in before_addrs
    ]
    meme_meta = {
        "considered": len(memes),
        "added": len(meme_new),
        "added_official": sum(1 for r in meme_new if r["tier"] == "official"),
        "added_community": sum(1 for r in meme_new if r["tier"] == "community"),
        "overlap": sum(1 for a in meme_addrs if a in before_addrs),
        "new_names": [r["name"] for r in meme_new],
    }

    append_sources(before, merged, stats, list_meta, meme_meta)

    by_tier = Counter(r.get("tier", "official") for r in merged)
    new_addrs = {r["address"] for r in merged} - before_addrs
    new_official_tokens = [
        r
        for r in merged
        if r["address"] in new_addrs
        and r.get("tier") == "official"
        and r["category"] == "protocol"
    ]
    new_community_memes = [
        r
        for r in merged
        if r["address"] in new_addrs
        and r.get("tier") == "community"
        and r["address"] in meme_addrs
    ]

    checks = {
        "pepe": "0x6982508145454ce325ddbe47a25d4ec3d2311933",
        "shib": "0x95ad61b0a150d79219dcf64e1e6cc01f0b64c4ce",
        "floki": "0xcf0c122c6b73ff809c693db761e7baebe62b6a2e",
        "bonk": "0x1151cb3d861920e07a38e03eead12c32178567f6",
        "weth": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        "usdc": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
    }
    by_addr = {r["address"]: r for r in merged}
    check_out = {
        k: {
            "present": v in by_addr,
            "name": by_addr.get(v, {}).get("name"),
            "tier": by_addr.get(v, {}).get("tier"),
            "source": by_addr.get(v, {}).get("source"),
        }
        for k, v in checks.items()
    }

    report = {
        "before": before,
        "after": {
            "total": len(merged),
            "official": by_tier.get("official", 0),
            "community": by_tier.get("community", 0),
        },
        "stats": stats,
        "list_meta": list_meta,
        "meme_meta": meme_meta,
        "official_token_adds": len(new_official_tokens),
        "meme_community_adds": len(new_community_memes),
        "meme_community_names": [r["name"] for r in new_community_memes],
        "checks": check_out,
        "top_sources_after": Counter(r["source"] for r in merged).most_common(12),
    }
    print(json.dumps(report, indent=2))
    Path("/tmp/rensic-tokens/expand_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
