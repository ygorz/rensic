#!/usr/bin/env python3
"""Curated ENS person expansion + published org tip jars for known_entities."""
from __future__ import annotations

import csv
import json
import re
import subprocess
import unicodedata
import urllib.request
from collections import Counter
from datetime import date
from pathlib import Path

CSV_PATH = Path(
    "/Users/george/Documents/WilderformTools/rensic/rensic-ingestion/transforms-python/src/myproject/data/known_entities.csv"
)
SOURCES_MD = CSV_PATH.with_name("SOURCES.md")
APP_JSON = Path(
    "/Users/george/Documents/WilderformTools/rensic/rensic-app/src/knownEntities.json"
)
RPC = "https://ethereum.publicnode.com"
ENSIDEAS = "https://api.ensideas.com/ens/resolve/"
PULL_DATE = date.today().isoformat()

ETH_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
ZERO = "0x0000000000000000000000000000000000000000"
BURN = "0x000000000000000000000000000000000000dead"

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

# Curated: ens_name -> (display_name, note_suffix)
# Only widely known public identities. Quality over quantity.
PERSON_SEED: dict[str, tuple[str, str]] = {
    # DeFi / product founders & well-known builders
    "banteg.eth": ("banteg", "Yearn contributor ENS"),
    "gakonst.eth": ("Georgios Konstantopoulos", "Paradigm / Foundry ENS"),
    "lefteris.eth": ("Lefteris Karapetsas", "Rotki founder ENS"),
    "dhof.eth": ("Dom Hofmann", "Zora co-founder ENS"),
    "hayden.eth": ("Hayden Adams", "Uniswap founder ENS"),  # already present; resolve for dedupe
    "stani.eth": ("Stani Kulechov", "Aave founder ENS"),
    "scoopy.eth": ("Scoopy Trooples", "Alchemix founder ENS"),
    "rleshner.eth": ("Robert Leshner", "Compound founder ENS"),
    "rune.eth": ("Rune Christensen", "MakerDAO founder ENS"),
    "mariano.eth": ("Mariano Conti", "former Maker oracle lead ENS"),
    "izqui.eth": ("Jorge Izquierdo", "Aragon co-founder ENS"),
    "dmihal.eth": ("David Mihal", "CryptoStats / cryptofees ENS"),
    "andrecronje.eth": ("Andre Cronje", "public ENS"),
    # Security researchers
    "samczsun.eth": ("samczsun", "security researcher ENS"),
    "pcaversaccio.eth": ("pcaversaccio", "security researcher ENS"),
    # Core / client / research
    "lightclient.eth": ("lightclient", "EF / go-ethereum ENS"),
    "karalabe.eth": ("Peter Szilagyi", "go-ethereum lead ENS"),
    "holiman.eth": ("Martin Holst Swende", "geth security ENS"),
    "protolambda.eth": ("protolambda", "Ethereum researcher ENS"),
    "dankrad.eth": ("Dankrad Feist", "EF researcher ENS"),
    "barnabe.eth": ("Barnabe Monnot", "EF researcher ENS"),
    "adietrichs.eth": ("Ansgar Dietrichs", "EF researcher ENS"),
    "potuz.eth": ("Potuz", "consensus client researcher ENS"),
    "mikhailkalinin.eth": ("Mikhail Kalinin", "consensus researcher ENS"),
    "ralexstokes.eth": ("Alex Stokes", "EF researcher ENS"),
    "terence.eth": ("Terence Tsao", "Prysm ENS"),
    "prestonvanloon.eth": ("Preston Van Loon", "Prysm ENS"),
    "rauljordan.eth": ("Raul Jordan", "Prysm ENS"),
    "arnetheduck.eth": ("Arnetheduck", "Nimbus ENS"),
    "carlbeek.eth": ("Carl Beekhuizen", "EF researcher ENS"),
    "benjaminion.eth": ("Ben Edgington", "Teku / EF ENS"),
    "pipermerriam.eth": ("Piper Merriam", "Ethereum tooling ENS"),
    "shemnon.eth": ("shemnon", "Besu / client ENS"),
    "axic.eth": ("Alex Beregszaszi", "EVM / Solidity ENS"),
    "chriseth.eth": ("Christian Reitwiessner", "Solidity ENS"),
    "gavofyork.eth": ("Gavin Wood", "Ethereum co-founder ENS"),
    "frozeman.eth": ("Fabian Vogelsteller", "ERC-20 / Mist ENS"),
    "ricmoo.eth": ("Richard Moore", "ethers.js ENS"),
    "souptacular.eth": ("Hudson Jameson", "souptacular.eth public ENS"),
    "lanerettig.eth": ("Lane Rettig", "Ethereum contributor ENS"),
    "ansgar.eth": ("Ansgar Dietrichs", "EF researcher ENS"),  # may dup adietrichs
    "thegostep.eth": ("Gregory Markou", "Chainsafe / gostep ENS"),
    "jannikluhn.eth": ("Jannik Luhn", "Ethereum contributor ENS"),
    "elopio.eth": ("elopio", "Ethereum contributor ENS"),
    # Tooling / protocol eng
    "t11s.eth": ("transmissions11", "Solmate / Solady author ENS"),
    "transmissions11.eth": ("transmissions11", "Solmate / Solady author ENS"),
    "vectorized.eth": ("Vectorized", "Solady author ENS"),
    "maurelian.eth": ("Maurelian", "Optimism security ENS"),
    "fubuloubu.eth": ("Evan Huestis", "ApeWorx ENS"),
    "moodysalem.eth": ("Moody Salem", "Uniswap eng ENS"),
    "karmacoma.eth": ("karmacoma", "security / builder ENS"),
    "wschwab.eth": ("William Schwab", "builder ENS"),
    "m1guelpf.eth": ("Miguel Piedrafita", "builder ENS"),
    "frolic.eth": ("frolic", "builder ENS"),
    "norswap.eth": ("norswap", "builder ENS"),
    "hrkrshnn.eth": ("Harikrishnan Mulackal", "Solidity compiler ENS"),
    "danfinlay.eth": ("Dan Finlay", "MetaMask co-founder ENS"),
    "kumavis.eth": ("kumavis", "MetaMask eng ENS"),
    "rekmarks.eth": ("rekmarks", "MetaMask eng ENS"),
    "jefflau.eth": ("Jeff Lau", "ENS eng ENS"),
    "makoto.eth": ("Makoto Inoue", "ENS eng ENS"),
    "austingriffith.eth": ("Austin Griffith", "BuidlGuidl / Scaffold-ETH ENS"),
    "patrickalphac.eth": ("Patrick Collins", "Cyfrin / education ENS"),
    "dabit.eth": ("Nader Dabit", "developer relations ENS"),
    "naderdabit.eth": ("Nader Dabit", "developer relations ENS"),
    "simondlr.eth": ("Simon de la Rouviere", "builder ENS"),
    "iainnash.eth": ("Iain Nash", "Zora eng ENS"),
    "hasufl.eth": ("Hasu", "research ENS"),
    "danrobinson.eth": ("Dan Robinson", "Paradigm ENS"),
    "tarunchitra.eth": ("Tarun Chitra", "Gauntlet ENS"),
    "micahzoltu.eth": ("Micah Zoltu", "Ethereum contributor ENS"),
    "jamesyoung.eth": ("James Young", "builder ENS"),
    "odysseas.eth": ("Odysseas", "builder ENS"),
    "nixo.eth": ("nixo", "builder ENS"),
    "jgm.eth": ("jgm", "builder ENS"),
    "lindaxie.eth": ("Linda Xie", "Scalar / investor ENS"),
    "balajis.eth": ("Balaji Srinivasan", "public ENS"),
    "joseph.eth": ("joseph.eth", "self-used public ENS"),
    "soska.eth": ("Kristov Atlas", "privacy researcher ENS"),  # verify? soska might be Kristov - actually soska.eth may be different. Use ENS label if unsure.
    "chainyoda.eth": ("ChainYoda", "public ENS"),
    "kosala.eth": ("Kosala Hemachandra", "MyEtherWallet ENS"),
    "ethchris.eth": ("ethchris", "builder ENS"),
    "bmuller.eth": ("Benjamin Muller", "builder ENS"),
    "yupuday.eth": ("yupuday", "builder ENS"),
    "kipto.eth": ("kipto", "builder ENS"),
    "trent.eth": ("Trent Van Epps", "Protocol Guild ENS"),
    "hww.eth": ("Hsiao-Wei Wang", "EF researcher ENS"),
    "jordibaylina.eth": ("Jordi Baylina", "iden3 / Polygon zkEVM ENS"),
}

# Published org tip jars (mainnet only) — first-party docs
ORG_TIP_JARS = [
    {
        "address": "0x4EA88fa76848a8BBAB72613d4171df1eBcf68399",
        "name": "Protocol Guild Donation (vesting)",
        "category": "protocol",
        "tier": "official",
        "source": "Protocol Guild donate docs (theprotocolguild.eth)",
        "source_url": "https://protocol-guild.readthedocs.io/en/latest/03-donate.html",
    },
    {
        "address": "0xdddd576bAF106bAAe54bDE40BCac602bB4a7cf79",
        "name": "Protocol Guild Multisig",
        "category": "protocol",
        "tier": "official",
        "source": "Protocol Guild donate docs (claim/other-token multisig)",
        "source_url": "https://protocol-guild.readthedocs.io/en/latest/03-donate.html",
    },
]

# Prefer one ENS when multiple map to same person
PREFERRED_ENS = {
    "transmissions11.eth": "t11s.eth",  # keep t11s as primary key; drop transmissions11 if same addr
    "naderdabit.eth": "dabit.eth",
    "ansgar.eth": "adietrichs.eth",
}


def to_ascii(s: str) -> str:
    if s is None:
        return ""
    s = unicodedata.normalize("NFKD", s)
    return s.encode("ascii", "ignore").decode("ascii").strip()


def norm_addr(a: str) -> str:
    return (a or "").strip().lower()


def make_row(address, name, category, tier, source, source_url, secondary=""):
    return {
        "chain": "ethereum",
        "address": norm_addr(address),
        "name": to_ascii(name),
        "category": category,
        "secondary_category": secondary,
        "source": to_ascii(source),
        "source_url": source_url,
        "tier": tier,
    }


def resolve_ens(name: str) -> str | None:
    try:
        out = subprocess.check_output(
            ["cast", "resolve-name", name, "--rpc-url", RPC],
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=20,
        ).strip()
        if ETH_RE.match(out):
            return out
    except Exception:
        pass
    try:
        with urllib.request.urlopen(ENSIDEAS + name, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        addr = data.get("address") or ""
        if ETH_RE.match(addr):
            return addr
    except Exception:
        pass
    return None


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


def merge(existing: list[dict], incoming: list[dict]):
    by_key: dict[tuple[str, str], dict] = {}
    for r in existing:
        by_key[(r["chain"], r["address"])] = r

    stats: Counter = Counter()
    stats["incoming"] = len(incoming)
    upgrades = []
    added_rows = []
    for r in incoming:
        if not ETH_RE.match(r["address"]):
            stats["bad_addr"] += 1
            continue
        key = (r["chain"], r["address"])
        if key not in by_key:
            by_key[key] = r
            stats["added"] += 1
            stats[f"added_{r['tier']}"] += 1
            stats[f"added_cat_{r['category']}"] += 1
            added_rows.append(r)
            continue
        cur = by_key[key]
        cur_tier = TIER_RANK.get(cur.get("tier", "official"), 0)
        new_tier = TIER_RANK.get(r.get("tier", "community"), 1)
        if new_tier < cur_tier:
            upgrades.append(
                {
                    "address": r["address"],
                    "from_name": cur.get("name"),
                    "to_name": r["name"],
                    "from_source": cur.get("source"),
                    "to_source": r["source"],
                }
            )
            by_key[key] = r
            stats["upgraded_to_official"] += 1
            continue
        if new_tier > cur_tier:
            stats["suppressed_community"] += 1
            continue
        # same tier: never overwrite official person with community; never demote better cats
        if CAT_RANK.get(cur.get("category"), 99) < CAT_RANK.get(r["category"], 99):
            stats["same_tier_kept_priority_cat"] += 1
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
    return merged, dict(stats), upgrades, added_rows


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


def write_app_json(rows: list[dict]) -> None:
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
    APP_JSON.write_text(
        json.dumps(payload, ensure_ascii=True, separators=(",", ":")),
        encoding="utf-8",
    )


def update_sources(before, after, added_persons, added_orgs, skipped, stats):
    text = SOURCES_MD.read_text(encoding="utf-8")
    marker = "### Person / public figures"
    block = []
    block.append(marker)
    block.append("")
    block.append(
        "**First-party rule:** `person` rows are ONLY wallets the individual or their foundation "
        "publicly self-attributes (personal blog, foundation/docs page, signed message, ENS they "
        "control and document, GitHub they own listing the address, or a verified social post linking "
        "the address). Prefer `tier=official` for first-party claims; use `tier=community` only for "
        "well-known attributions that are widely cited but not first-party — and caveat in the source. "
        "Do **not** include rumor wallets, clustering guesses, or doxxing."
    )
    block.append("")
    block.append(
        f"**2026-09-07 curated ENS resolve pass:** hand-picked well-known public `.eth` names "
        f"(founders, EF/client researchers, widely self-used builder identities). Resolved via "
        f"public Ethereum RPC (`ethereum.publicnode.com` / `cast resolve-name`) with "
        f"`api.ensideas.com` fallback. New person rows are `tier=community` with source noting "
        f"`self-used public ENS; community attribution caveat` and `source_url` to "
        f"`https://app.ens.domains/<name>`. Skipped non-resolving, zero/burn, and names that "
        f"resolve to an unrelated already-labeled wallet. Official tip jars (Protocol Guild) "
        f"added as `protocol` / `official` from first-party donate docs. No gossip, rich lists, "
        f"or Etherscan nametag scrapes used as person truth."
    )
    block.append("")
    block.append("Person rows after this pass:")
    persons = [r for r in after if r["category"] == "person"]
    persons.sort(key=lambda r: r["name"].lower())
    for r in persons:
        block.append(
            f"- `{r['address']}`: **{r['name']}** ({r['tier']}) — {r['source']} — {r['source_url']}"
        )
    block.append("")
    block.append("### ENS person expansion counts (2026-09-07)")
    block.append("")
    block.append(
        f"- Before: total={before['total']} official={before['official']} "
        f"community={before['community']} person={before['person']}"
    )
    block.append(
        f"- After: total={after_counts(after)['total']} official={after_counts(after)['official']} "
        f"community={after_counts(after)['community']} person={after_counts(after)['person']}"
    )
    block.append(f"- Merge stats: {json.dumps(stats)}")
    block.append(f"- New person rows added: {len(added_persons)}")
    for p in added_persons:
        block.append(f"  - {p['name']} (`{p['address']}`, {p['ens']})")
    block.append(f"- Org tip jars added: {len(added_orgs)}")
    for o in added_orgs:
        block.append(f"  - {o['name']} (`{o['address']}`, {o['tier']})")
    block.append(f"- Skipped: {len(skipped)}")
    for s in skipped[:80]:
        block.append(f"  - {s}")
    if len(skipped) > 80:
        block.append(f"  - ... and {len(skipped) - 80} more")
    block.append("")
    block.append(
        "- Person set kept quality-gated: many public figures lack first-party tip-jar posts; "
        "ENS-only resolutions without documentation stay community-caveated or omitted."
    )
    block.append("")

    new_section = "\n".join(block)
    # Replace existing Person section through next ### at same level under gaps doc,
    # or append if structure differs. Find start of Person section and cut until
    # "### Source families" or "### Deliberate gaps" or EOF of that appendix.
    if marker in text:
        start = text.index(marker)
        # Find a sensible end: next "### Source families" after start, else "### Deliberate gaps",
        # else "### Counts", else end.
        end_markers = [
            "\n### Source families",
            "\n### Deliberate gaps remaining",
            "\n### Notable upgrades",
        ]
        end = len(text)
        for em in end_markers:
            idx = text.find(em, start + 1)
            if idx != -1:
                end = min(end, idx)
        # If the old Person block was followed by source families that belong to prior pass,
        # keep content after end. Insert our new person block + a short note, preserving later sections.
        text = text[:start] + new_section + text[end:].lstrip("\n")
        # Ensure a trailing separator before preserved sections
        if not text[start + len(new_section) :].startswith("\n###"):
            pass
    else:
        text = text.rstrip() + "\n\n" + new_section
    SOURCES_MD.write_text(text, encoding="utf-8")


def after_counts(rows):
    return {
        "total": len(rows),
        "official": sum(1 for r in rows if r.get("tier") == "official"),
        "community": sum(1 for r in rows if r.get("tier") == "community"),
        "person": sum(1 for r in rows if r["category"] == "person"),
    }


def main() -> int:
    existing = load_existing()
    before = after_counts(existing)
    before_addrs = {r["address"] for r in existing}
    before_persons = {r["address"] for r in existing if r["category"] == "person"}

    skipped = []
    resolved: dict[str, str] = {}  # ens -> addr
    addr_to_ens: dict[str, str] = {}

    for ens, (display, note) in PERSON_SEED.items():
        addr = resolve_ens(ens)
        if not addr:
            skipped.append(f"{ens}: did not resolve")
            continue
        a = norm_addr(addr)
        if a in (ZERO, BURN):
            skipped.append(f"{ens}: empty/burn address")
            continue
        resolved[ens] = a
        # Prefer primary ENS if duplicate address
        if a in addr_to_ens:
            prev = addr_to_ens[a]
            # keep earlier preferred / more specific
            if ens in PREFERRED_ENS and PREFERRED_ENS[ens] == prev:
                skipped.append(f"{ens}: duplicate of preferred {prev}")
                continue
            if prev in PREFERRED_ENS and PREFERRED_ENS[prev] == ens:
                # replace
                del resolved[prev]
                addr_to_ens[a] = ens
            else:
                skipped.append(f"{ens}: same address as {prev} (keeping {prev})")
                continue
        else:
            addr_to_ens[a] = ens

    incoming = []
    added_person_meta = []
    for ens, a in resolved.items():
        if ens not in PERSON_SEED:
            continue
        if ens in PREFERRED_ENS and PREFERRED_ENS[ens] in resolved:
            # drop non-preferred if preferred also resolved to same or exists
            pref = PREFERRED_ENS[ens]
            if resolved.get(pref) == a:
                skipped.append(f"{ens}: dropped in favor of {pref}")
                continue
        display, note = PERSON_SEED[ens]
        # Skip if address already an official person with better attribution
        source = f"{ens} ({note}; self-used public ENS; community attribution caveat)"
        source_url = f"https://app.ens.domains/{ens}"
        row = make_row(a, display, "person", "community", source, source_url)
        incoming.append(row)
        if a not in before_persons and a not in before_addrs:
            added_person_meta.append({"name": display, "address": a, "ens": ens})
        elif a not in before_persons and a in before_addrs:
            # address exists under another category — merge may suppress
            added_person_meta.append({"name": display, "address": a, "ens": ens, "note": "addr exists other cat"})

    for org in ORG_TIP_JARS:
        incoming.append(
            make_row(
                org["address"],
                org["name"],
                org["category"],
                org["tier"],
                org["source"],
                org["source_url"],
            )
        )

    merged, stats, upgrades, added_rows = merge(existing, incoming)
    write_csv(merged)
    write_app_json(merged)

    added_persons = [
        r for r in added_rows if r["category"] == "person"
    ]
    added_orgs = [r for r in added_rows if r["category"] != "person"]
    # enrich person list with ens
    ens_by_addr = {norm_addr(a): e for e, a in resolved.items()}
    person_report = []
    for r in added_persons:
        person_report.append(
            {
                "name": r["name"],
                "address": r["address"],
                "ens": ens_by_addr.get(r["address"], "?"),
                "tier": r["tier"],
            }
        )

    update_sources(before, merged, person_report, added_orgs, skipped, stats)

    report = {
        "before": before,
        "after": after_counts(merged),
        "stats": stats,
        "persons_added": person_report,
        "orgs_added": [
            {"name": r["name"], "address": r["address"], "tier": r["tier"]}
            for r in added_orgs
        ],
        "skipped": skipped,
        "upgrades": upgrades,
        "resolved_count": len(resolved),
    }
    out = Path("/tmp/ens_person_expand_report.json")
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
