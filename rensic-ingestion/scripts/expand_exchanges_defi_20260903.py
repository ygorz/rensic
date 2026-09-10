#!/usr/bin/env python3
"""One-shot expansion: Bybit PoR + KuCoin blog + official DeFi/protocol packs."""
from __future__ import annotations

import csv
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path

CSV_PATH = Path("/Users/george/Documents/WilderformTools/rensic/rensic-ingestion/transforms-python/src/myproject/data/known_entities.csv")
SOURCES_MD = CSV_PATH.with_name("SOURCES.md")
APP_TS = Path("/Users/george/Documents/WilderformTools/rensic/rensic-app/src/knownEntities.ts")

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

# Bybit Hacken PoR Oct 22 2025 — Ethereum network audited wallets only
# Source: https://www.bybit.com/common-static/cht-static/por/Bybit_PoR_Audit_2025_Oct_22.pdf
BYBIT_POR_URL = "https://www.bybit.com/common-static/cht-static/por/Bybit_PoR_Audit_2025_Oct_22.pdf"
BYBIT_ETH = [
    "0x412dd3f282b1fa20d3232d86ae060dec644249f6",
    "0x6Bd869be16359f9E26f0608A50497f6Ef122eE3E",
    "0x922fa922da1b0b28d0af5aa274d7326eaa108c3d",
    "0x88a1493366d48225fc3cefbdae9ebb23e323ade3",
    "0xA7A93fd0a276fc1C0197a5B5623eD117786eeD06",
    "0xbaed383ede0e5d9d72430661f3285daa77e9439f",
    "0xee5B5B923fFcE93A870B3104b7CA09c3db80047A",
    "0xf89d7b9c864f589bbF53a82105107622B35EaA40",
    "0x6F4565c9D673DBDD379ABa0b13f8088d1AF3Bb0C",
    "0xc22166664e820cda6bf4cedbdbb4fa1e6a84c440",
    "0xdae4fdcb7fc93738ec6d5b1ea92b7c7f75e4f2f6",
    "0x6B9B774502E6aFAAfCac84f840AC8A0844A1aBe3",
    "0x72187DB55473B693Ded367983212FE2db3768829",
    "0x80a9B4aAb0AD3c73cCE1C9223236b722DB5d6628",
    "0x63beE4A7e4aa5d76Dc6AB9b9d1852AABB9a40936",
    "0x33ae83071432116ae892693b45466949a38ac74c",
    "0x801bfD99636EC8961F7E2d2dD0a296d726f5F1Ae",
    "0xB829e684Df8e31B402a4D4AEDF3bbC18A52e7589",
    "0x371c31f9221459e10565CFe78937CBdA5Db1791c",
    "0xCab3F132A11E5b723Fc20dDAB8bb1B858d00a8E8",
    "0x25c7d768a7D53E6EBE5590c621437126c766E1EA",
    "0x79Ae8c1b31B1E61C4B9d1040217a051F954d4433",
    "0xc273A2e3FC4c8f8610eBe51123dC32d233913da7",
    "0xa9cf4Aa55c675bADb68519e3CFa8F4Be942e6D11",
    "0x6206AE3781f9F1b6FBcf44C7240b1bE14f3169eF",
    "0x869bCEE3a0baD2211A65c63eC47DBD3D85A84D68",
    "0x30Ba21597F22aAfa4B0E86C250c8a6EEbAf0da54",
    "0x61B2Aa17C1c1114E7583bB31F777FF4bDc7AB717",
    "0x3Bd0e57e2917d3d9a93F479b3a23B28C3f31a789",
    "0xb24692D17baBEFd97eA2B4ca604A481a7cc2c8EA",
    "0xc93e48d89F2d6DBc1672908aA68Ce7c24d0413B4",
    "0xd860962a96Cd471BbE60A83c33e65011D40eB65f",
    "0x933646D78ede6F1EF5CF4a0a03e3a819c8057922",
    "0x3cEf1f90BE0F15f1573Bda7A3E045CCA9CfF1D15",
    "0x429B41e5Eb73E2266AFFBc2D7a41553BD8f1EDe1",
    "0xd7C4D4B3F076BF9fE391190c42676B4dC269EE02",
    "0x4E5e17e8eF17c9a7ef9798ddf78f3a2c38367d16",
    "0x495eB9345788ee6Be50c9c36Ed67Ffa2bEb3699f",
    "0x3Db4cB6d753D9e0BA7cC84e576D17dcD01B6B67D",
    "0x4e19698c366f7DCD1cfAd4D7f621B4D275Bb1a6C",
    "0x7C41C7d883DbbE1eDfcefca9D7a7592DD30C8B51",
    "0x01E2Fb8F565D5e3cB9e0E8F0b607A96169B94393",
    "0x8a2458f32E5Ec9935F20E7C2e06e8D4820F726e5",
    "0xc19bb2709321bd6ad6d8396a885b7c151b8d48c5",
    "0x59800fc68c7039566ed7a04b0f735255093cac1d",
    "0x75df67943d35129dd22da5d14fda4983571f553a",
    "0xa0acdf9fa38b293f0bbdd01ca6bf3e7ed8291dd4",
    "0x35696b0847ed8428a098cba726b6514582aa5fc7",
    "0x86dbaa55f0e65857b58109c3cb725deff4da3851",
    "0x8d6d3479c94bb95e737b72186192ff5e7fedf3a2",
    "0xf2f40c3bb444288f6f64d8336dcc14dbd929fd94",
    "0x70f58622158d7e609ae5839c4ad0d477f468863f",
    "0xbce9aecd3985d4cbb9d273453159a26301fa02ef",
    "0xcbf446565eddf074b2c99e8f1c15582a0bfe6eba",
    "0x036c43bebe5fa5dff3c299584b4a6c1923c7d932",
    "0x18e296053cbdf986196903e889b7dca7a73882f6",
    "0x260b364fe0d3d37e6fd3cda0fa50926a06c54cea",
    "0xa1abfa21f80ecf401bd41365adbb6fef6fefdf09",
    "0x70167b76543c4a12b49b2f2b70cbf04d99345786",
    "0x4865d4bcf4ab92e1c9ba5011560e7d4c36f54106",
    "0xc6c6a48ee8e9f593724161c72414d76e94cda93f",
    "0xefef30bd1cca520619306c95091ab18473febc5c",
    "0x180a1b935d28494f9ff4233985562b18b3dcfa74",
    "0xad85405cbb1476825b78a021fa9e543bf7937549",
    "0x8fa129f87b8a11ee1ca35abd46674f8b66984d4a",
    "0x651641299c7ec0aa44ad7ed9b7e12702fed2022f",
    "0x187c9fbf5bd0f266883c03f320260c407c7b4100",
    "0xa4b9569bf942c3aad23c0c2d322fe4aff8e1bf30",
    "0x6522b7f9d481eceb96557f44753a4b893f837e90",
    "0xa31231e727ca53ff95f0d00a06c645110c4ab647",
    "0xf42aac93ab142090db9fdc0bc86aab73cb36f173",
    "0x93228d328c9c74c2bfe9f97638bbb5ef322f2bd5",
    "0x9cdb59516b37f5c1bd166bc41c5b9f68a57225bd",
    "0x0ac92eb5716516a08e7760d314d42e1d5d3c03ae",
    "0x18673311fec54ac2244a602e6d91845553d24e62",
    "0x7a84c1f1aa344d466b0f161f57b0321b98faf6ee",
    "0xc63fe58d36bef77a9a98df32a547537f45aac71d",
    "0xf8f061cfc030928a4acb8c4980911b4f5afc4002",
    "0x1c3944173abee256456b1498299fc501ad5bbd6f",
]

# KuCoin official transparency blog 2022-11-11 (unique ETH-format 0x wallets)
KUCOIN_BLOG = "https://www.kucoin.com/blog/transparency-and-trust-a-detailed-list-of-kucoin-s-wallets-vi"
KUCOIN_ETH = [
    "0xd6216fc19db775df9774a6e33526131da7d19a2c",
    "0xcad621da75a66c7a8f4ff86d30a2bf981bfc8fdd",
    "0xd89350284c7732163765b23338f2ff27449e0bf5",
    "0xb8e6d31e7b212b2b7250ee9c26c56cebbfbe6b23",
    "0xec30d02f10353f8efc9601371f56e808751f396f",
    "0x88bd4d3e2997371bceefe8d9386c6b5b4de60346",
    "0x2a8c8b09bd77c13980495a959b26c1305166a57f",
    "0x14ea40648fc8c1781d19363f5b9cc9a877ac2469",
    "0x03e6fa590cadcf15a38e86158e9b3d06ff3399ba",
    "0xf3f094484ec6901ffc9681bcb808b96bafd0b8a8",
    "0xf16e9b0d03470827a95cdfd0cb8a8a3b46969b91",
    "0x738cf6903e6c4e699d1c2dd9ab8b67fcdb3121ea",
    "0x1692e170361cefd1eb7240ec13d048fd9af6d667",
    "0xa3f45e619ce3aae2fa5f8244439a66b203b78bcc",
    "0xebb8ea128bbdff9a1780a4902a9380022371d466",
]

# Coinbase wrapped assets — company pages publish the ETH contract
CBETH_URL = "https://www.coinbase.com/cbeth"
CBBTC_URL = "https://www.coinbase.com/cbbtc/proof-of-reserves"
COINBASE_PROTOCOLS = [
    ("0xBe9895146f7AF43049ca1c1AE358B0541Ea49704", "Coinbase cbETH", "Coinbase cbETH docs", CBETH_URL),
    ("0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf", "Coinbase cbBTC", "Coinbase cbBTC PoR", CBBTC_URL),
]

# Morpho Blue Ethereum mainnet — docs.morpho.org
MORPHO_URL = "https://docs.morpho.org/developers/contracts/addresses/"
MORPHO = [
    ("0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb", "Morpho Blue"),
    ("0x870aC11D48B15DB9a138Cf899d20F13F79Ba00BC", "Morpho Adaptive Curve IRM"),
    ("0x3A7bB36Ee3f3eE32A60e9f2b33c1e5f2E83ad766", "Morpho ChainlinkOracleV2 Factory"),
    ("0x58D97B57BB95320F9a05dC918Aef65434969c2B2", "MORPHO"),
    ("0x1897A8997241C1cD4bD0698647e4EB7213535c24", "Morpho MetaMorpho Factory V1.1"),
    ("0x6566194141eefa99Af43Bb5Aa71460Ca2Dc90245", "Morpho Bundler3"),
]

# EigenLayer mainnet core — Layr-Labs github config
EIGEN_URL = "https://github.com/Layr-Labs/eigenlayer-contracts/blob/main/script/configs/mainnet.json"
EIGEN = [
    ("0x39053D51B77DC0d36036Fc1fCc8Cb819df8Ef37A", "EigenLayer DelegationManager"),
    ("0x858646372CC42E1A627fcE94aa7A7033e7CF075A", "EigenLayer StrategyManager"),
    ("0x91E677b07F7AF907ec9a428aafA9fc14a0d3A338", "EigenLayer EigenPodManager"),
    ("0x7750d328b314EfFa365A0402CcfD489B80B0adda", "EigenLayer RewardsCoordinator"),
    ("0x135dda560e946695d6f155dacafc6f1f25c1f5af", "EigenLayer AVSDirectory"),
    ("0xec53bf9167f50cdeb3ae105f56099aaab9061f83", "EIGEN"),
]

# SparkLend core — spark-address-registry (commit with SparkLend - Core section)
SPARK_URL = "https://github.com/sparkdotfi/spark-address-registry/blob/ad50b14f/src/Ethereum.sol"
SPARK = [
    ("0xC13e21B648A5Ee794902342038FF3aDAB66BE987", "SparkLend Pool"),
    ("0x02C3eA4e34C0cBd694D2adFa2c690EECbC1793eE", "SparkLend PoolAddressesProvider"),
    ("0x542DBa469bdE58FAeE189ffB60C6b49CE60E0738", "SparkLend PoolConfigurator"),
    ("0xdA135Cd78A086025BcdC87B038a1C462032b510C", "SparkLend ACL Manager"),
    ("0x8105f69D9C41644c6A0803fDA7D03Aa70996cFD9", "SparkLend Oracle"),
    ("0xBD7D6a9ad7865463DE44B05F04559f65e3B11704", "SparkLend WETH Gateway"),
    ("0xFc21d6d146E6086B8359705C8b28512a983db0cb", "SparkLend Protocol Data Provider"),
    ("0xb137E7d16564c81ae2b0C8ee6B55De81dd46ECe5", "SparkLend Treasury"),
]

# Ethena — cited via Ethena minting + tokens as listed in spark registry Ethena section
# Prefer Ethena docs URL when available; also listed in spark-address-registry
ETHENA_URL = "https://github.com/sparkdotfi/spark-address-registry/blob/ad50b14f/src/Ethereum.sol"
ETHENA = [
    ("0x4c9EDD5852cd905f086C759E8383e09bff1E68B3", "USDe"),
    ("0x9D39A5DE30e57443BfF2A8307A4256c8797A3497", "sUSDe"),
    ("0xe3490297a08d6fC8Da46Edb7B6142E4F461b62D3", "Ethena Minting"),
]

# Pendle V2 core ethereum — official deployments JSON
PENDLE_URL = "https://github.com/pendle-finance/pendle-core-v2-public/blob/main/deployments/1-core.json"
PENDLE = [
    ("0x888888888889758F76e7103c6CbF23ABbF58F946", "Pendle Router"),
    ("0x808507121b80c02388fad14726482e061b8da827", "PENDLE"),
    ("0x1A6fCc85557BC4fB7B534ed835a03EF056552D52", "Pendle Market Factory V3"),
    ("0x5542be50420E88dd7D5B4a3D488FA6ED82F6DAc2", "Pendle PY YT LP Oracle"),
    ("0x8270400d528c34e1596EF367eeDEc99080A1b592", "Pendle Treasury"),
]

# Rocket Pool rETH — listed in spark-address-registry token section (official Spark registry)
# Also the canonical rETH token used across DeFi
RETH_URL = "https://github.com/sparkdotfi/spark-address-registry/blob/ad50b14f/src/Ethereum.sol"
ROCKET = [
    ("0xae78736Cd615f374D3085123A210448E74Fc6393", "Rocket Pool rETH"),
]

# Ether.fi weETH from same Spark registry token section
WEETH_URL = RETH_URL
ETHERFI = [
    ("0xCd5fE23C85820F7B72D0926FC9b05b43E359b7ee", "ether.fi weETH"),
]


def norm(addr: str) -> str:
    return addr.lower()


def row(address: str, name: str, category: str, source: str, source_url: str) -> dict:
    return {
        "chain": "ethereum",
        "address": norm(address),
        "name": name,
        "category": category,
        "secondary_category": "",
        "source": source,
        "source_url": source_url,
    }


def load_existing() -> list[dict]:
    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def build_incoming() -> list[dict]:
    out: list[dict] = []
    for a in BYBIT_ETH:
        assert ETH_RE.match(a), a
        out.append(row(a, "Bybit", "exchange", "Bybit Hacken PoR Oct 2025", BYBIT_POR_URL))
    for a in KUCOIN_ETH:
        out.append(row(a, "KuCoin", "exchange", "KuCoin transparency wallet list", KUCOIN_BLOG))
    for a, name, src, url in COINBASE_PROTOCOLS:
        out.append(row(a, name, "protocol", src, url))
    for a, name in MORPHO:
        out.append(row(a, name, "protocol", "Morpho address book", MORPHO_URL))
    for a, name in EIGEN:
        out.append(row(a, name, "protocol", "EigenLayer mainnet deployments", EIGEN_URL))
    for a, name in SPARK:
        out.append(row(a, name, "protocol", "Spark address registry", SPARK_URL))
    for a, name in ETHENA:
        out.append(row(a, name, "protocol", "Spark address registry (Ethena)", ETHENA_URL))
    for a, name in PENDLE:
        out.append(row(a, name, "protocol", "Pendle V2 deployments", PENDLE_URL))
    for a, name in ROCKET:
        out.append(row(a, name, "protocol", "Spark address registry (rETH)", RETH_URL))
    for a, name in ETHERFI:
        out.append(row(a, name, "protocol", "Spark address registry (weETH)", WEETH_URL))
    # dedupe incoming by address keeping first
    seen = set()
    uniq = []
    for r in out:
        if r["address"] in seen:
            continue
        seen.add(r["address"])
        uniq.append(r)
    return uniq


def merge(existing: list[dict], incoming: list[dict]) -> tuple[list[dict], dict]:
    by_key: dict[tuple[str, str], dict] = {}
    for r in existing:
        by_key[(r["chain"], r["address"])] = r
    added = 0
    replaced = 0
    for r in incoming:
        key = (r["chain"], r["address"])
        if key not in by_key:
            by_key[key] = r
            added += 1
            continue
        old = by_key[key]
        if CAT_RANK.get(r["category"], 99) < CAT_RANK.get(old["category"], 99):
            by_key[key] = r
            replaced += 1
        # else keep existing (sanctions/mixer beat exchange/protocol)
    merged = sorted(by_key.values(), key=lambda x: (x["category"], x["name"], x["address"]))
    return merged, {"added": added, "replaced": replaced, "incoming": len(incoming)}


def write_csv(rows: list[dict]) -> None:
    fields = ["chain", "address", "name", "category", "secondary_category", "source", "source_url"]
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
        "export type KnownEntity = {",
        "  chain: string;",
        "  address: string;",
        "  name: string;",
        "  category: EntityCategory;",
        "  secondaryCategory?: EntityCategory;",
        "  source: string;",
        "  sourceUrl: string;",
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


def append_sources(existing_n: int, merged: list[dict], info: dict, venue_counts: dict) -> None:
    by_cat = Counter(r["category"] for r in merged)
    exch = Counter(r["name"] for r in merged if r["category"] == "exchange")
    proto = Counter(r["name"].split()[0] for r in merged if r["category"] == "protocol")
    lines = [
        "",
        "",
        f"## Expansion pull: {date.today().isoformat()} (Bybit/KuCoin + DeFi protocols)",
        "",
        "Goal: more official exchange + protocol ETH labels. No Etherscan nametags, Arkham, Chainalysis, or unlabeled GraphSense exchange dumps.",
        "",
        "### Sources used (worked)",
        "",
        f"1. Bybit Hacken PoR PDF (`{BYBIT_POR_URL}`): {len(BYBIT_ETH)} Ethereum audited wallets.",
        f"2. KuCoin transparency blog (`{KUCOIN_BLOG}`): {len(KUCOIN_ETH)} unique ETH-format wallets from the published table.",
        f"3. Coinbase cbETH (`{CBETH_URL}`) + cbBTC PoR (`{CBBTC_URL}`): 2 protocol token contracts (not CEX hot wallets).",
        f"4. Morpho docs address book (`{MORPHO_URL}`): Morpho Blue + IRM + factory + token + Bundler3.",
        f"5. EigenLayer mainnet config (`{EIGEN_URL}`): DelegationManager, StrategyManager, EigenPodManager, RewardsCoordinator, AVSDirectory, EIGEN.",
        f"6. Spark address registry (`{SPARK_URL}`): SparkLend Pool + provider + configurator + ACL + oracle + gateway + data provider + treasury; also Ethena USDe/sUSDe/Minter, Rocket Pool rETH, ether.fi weETH.",
        f"7. Pendle V2 deployments (`{PENDLE_URL}`): Router, PENDLE, Market Factory V3, oracle, treasury.",
        "",
        "### Merge",
        "",
        f"- Incoming unique: {info['incoming']}",
        f"- Newly added: {info['added']}",
        f"- Precedence replaces: {info['replaced']}",
        f"- Total rows now: {len(merged)} (was {existing_n})",
        "",
        "### Counts after this pull",
        "",
    ]
    for cat in ("sanctions", "mixer", "gambling", "exchange", "shop", "protocol", "person"):
        lines.append(f"- {cat}: {by_cat.get(cat, 0)}")
    lines.append("")
    lines.append(f"Exchange names (row counts): {dict(exch)}")
    lines.append(f"New venue adds this pull: {venue_counts}")
    lines.append("")
    lines.append("### Still skipped / impossible with pack rules")
    lines.append("")
    lines.append("- Coinbase exchange hot/cold wallets: company publishes wrapped-asset contracts (cbETH/cbBTC) and BTC reserve addresses for cbBTC, not a public ETH CEX wallet CSV. Added protocol tokens only.")
    lines.append("- Kraken: Merkle PoR without a public on-chain address list.")
    lines.append("- Gemini: Trust Center / GUSD attestations do not publish a citable ETH exchange wallet list; GUSD contract not ingested without a non-explorer primary URL that prints the hex.")
    lines.append("- Bitstamp, Robinhood, Crypto.com, Gate.io, HTX/Huobi, MEXC, Bitget: PoR is Merkle/zk or dashboard-only; no public ETH address attestation file suitable as primary citation.")
    lines.append("- KuCoin current Hacken PoR PDFs: hosted behind bot-protection; used the 2022 company transparency blog list instead (official KuCoin URL).")
    lines.append("- GraphSense exchange-wallets-* packs: still excluded (unlabeled rotating hot wallets).")
    lines.append("- Etherscan nametag / labelcloud scrapes: pack rules.")
    lines.append("")
    with SOURCES_MD.open("a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main() -> int:
    existing = load_existing()
    incoming = build_incoming()
    existing_keys = {(r["chain"], r["address"]) for r in existing}
    venue_counts: dict[str, int] = Counter()
    for r in incoming:
        if (r["chain"], r["address"]) not in existing_keys:
            venue_counts[r["name"]] += 1
    merged, info = merge(existing, incoming)
    write_csv(merged)
    write_ts(merged)
    append_sources(len(existing), merged, info, dict(venue_counts))
    by_cat = Counter(r["category"] for r in merged)
    exch = Counter(r["name"] for r in merged if r["category"] == "exchange")
    print(json.dumps({
        "existing": len(existing),
        "incoming": len(incoming),
        "added": info["added"],
        "replaced": info["replaced"],
        "total": len(merged),
        "by_category": dict(by_cat),
        "exchanges": dict(exch),
        "new_by_venue": dict(venue_counts),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
