#!/usr/bin/env python3
"""Expand known_entities with high-leverage role labels (thorough, cited)."""
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
HELPERS = Path("/tmp/ke_ts_helpers.txt")
DOCS = Path("/tmp/rensic-roles/docs")

ETH_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
PULL_DATE = date.today().isoformat()

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


def to_ascii(s: str) -> str:
    if s is None:
        return ""
    s = unicodedata.normalize("NFKD", s)
    return s.encode("ascii", "ignore").decode("ascii").strip()


def norm_addr(a: str) -> str:
    return a.strip().lower()


def make_row(
    address: str,
    name: str,
    category: str,
    tier: str,
    source: str,
    source_url: str,
) -> dict:
    return {
        "chain": "ethereum",
        "address": norm_addr(address),
        "name": to_ascii(name),
        "category": category,
        "secondary_category": "",
        "source": to_ascii(source),
        "source_url": source_url,
        "tier": tier,
    }


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
    upgrades: list[dict] = []
    for r in incoming:
        if not ETH_RE.match(r["address"]):
            stats["bad_addr"] += 1
            continue
        if r["name"] in ("", "SKIP") or "SKIP" in r["name"]:
            stats["skipped_placeholder"] += 1
            continue
        key = (r["chain"], r["address"])
        if key not in by_key:
            by_key[key] = r
            stats["added"] += 1
            stats[f"added_{r['tier']}"] += 1
            stats[f"added_cat_{r['category']}"] += 1
            continue
        cur = by_key[key]
        cur_tier = TIER_RANK.get(cur.get("tier", "official"), 0)
        new_tier = TIER_RANK.get(r.get("tier", "community"), 1)
        if new_tier < cur_tier:
            # upgrade community -> official; prefer new official name/source
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
        # same tier: keep existing good label (don't blank better names)
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
    return merged, dict(stats), upgrades


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
    helpers = HELPERS.read_text(encoding="utf-8")
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


def build_incoming() -> tuple[list[dict], dict]:
    rows: list[dict] = []
    meta: dict = {"families": []}

    def add(addr, name, cat, tier, source, url, family):
        if not ETH_RE.match(addr):
            return
        if not name or name == "SKIP" or "PLACEHOLDER" in name:
            return
        rows.append(make_row(addr, name, cat, tier, source, url))
        meta.setdefault("by_family", {}).setdefault(family, 0)
        meta["by_family"][family] += 1

    # ---- 1. MEV / builders / CREATE2 ----
    BN = "https://buildernet.org/docs/public-identity"
    add(
        "0xdadB0d80178819F2319190D340ce9A924f783711",
        "BuilderNet fee recipient",
        "protocol",
        "official",
        "BuilderNet public identity",
        BN,
        "mev",
    )
    add(
        "0x62A29205f7Ff00F4233d9779c210150787638E7f",
        "BuilderNet",
        "protocol",
        "official",
        "BuilderNet public identity",
        BN,
        "mev",
    )
    # Additional BuilderNet BLS/identity related EOAs published on the same page
    bn_html = (DOCS / "buildernet-identity.html").read_text(errors="replace")
    bn_addrs = sorted(set(re.findall(r"0x[a-fA-F0-9]{40}", bn_html)))
    for a in bn_addrs:
        if a.lower() in {
            "0xdadb0d80178819f2319190d340ce9a924f783711",
            "0x62a29205f7ff00f4233d9779c210150787638e7f",
        }:
            continue
        # Only keep if context suggests identity key (already on public-identity page)
        add(
            a,
            "BuilderNet published identity",
            "protocol",
            "official",
            "BuilderNet public identity",
            BN,
            "mev",
        )

    ADD_CREATE2 = "https://github.com/Arachnid/deterministic-deployment-proxy"
    add(
        "0x4e59b44847b379578588920ca78fbf26c0b4956c",
        "Arachnid CREATE2 Deployer",
        "protocol",
        "official",
        "Arachnid deterministic-deployment-proxy",
        ADD_CREATE2,
        "create2",
    )
    add(
        "0x3fab184622dc19b6109349b94811493bf2a45362",
        "Arachnid CREATE2 Deployer Signer",
        "protocol",
        "official",
        "Arachnid deterministic-deployment-proxy",
        ADD_CREATE2,
        "create2",
    )
    SEAPORT_SRC = (
        "https://github.com/ProjectOpenSea/seaport/blob/main/docs/Deployment.md"
    )
    add(
        "0x0000000000ffe8b47b3e2130213b802212439497",
        "Immutable CREATE2 Factory",
        "protocol",
        "official",
        "OpenSea Seaport Deployment",
        SEAPORT_SRC,
        "create2",
    )

    # ---- 2. L2 bridges / system (Optimism from superchain registry) ----
    OP_SRC = "https://github.com/ethereum-optimism/superchain-registry"
    op = json.loads((DOCS / "op-addresses.json").read_text())
    op_labels = {
        "OptimismPortalProxy": "Optimism Portal",
        "L1StandardBridgeProxy": "Optimism L1 Standard Bridge",
        "L1CrossDomainMessengerProxy": "Optimism L1 Cross Domain Messenger",
        "L1ERC721BridgeProxy": "Optimism L1 ERC721 Bridge",
        "SystemConfigProxy": "Optimism System Config",
        "BatchSubmitter": "Optimism Batch Submitter",
        "Proposer": "Optimism Proposer",
        "ProxyAdmin": "Optimism Proxy Admin",
        "ProxyAdminOwner": "Optimism Proxy Admin Owner",
        "Guardian": "Optimism Guardian",
        "DisputeGameFactoryProxy": "Optimism Dispute Game Factory",
        "EthLockboxProxy": "Optimism ETH Lockbox",
        "AddressManager": "Optimism Address Manager",
        "Challenger": "Optimism Challenger",
        "UnsafeBlockSigner": "Optimism Unsafe Block Signer",
        "SuperchainConfig": "Optimism Superchain Config",
        "SystemConfigOwner": "Optimism System Config Owner",
        "AnchorStateRegistryProxy": "Optimism Anchor State Registry",
        "DelayedWETHProxy": "Optimism Delayed WETH",
    }
    for key, label in op_labels.items():
        addr = op.get("10", {}).get(key)
        if addr:
            add(addr, label, "protocol", "official", "Optimism superchain-registry", OP_SRC, "bridge_op")

    BASE_SRC = "https://docs.base.org/base-chain/network-information/base-contracts"
    for addr, name in [
        ("0x49048044D57e1C92A77f79988d21Fa8fAF74E97e", "Base OptimismPortal"),
        ("0x3154Cf16ccdb4C6d922629664174b904d80F2C35", "Base L1 Standard Bridge"),
        ("0x866E82a600A1414e583f7F13623F1aC5d58b0Afa", "Base L1 Cross Domain Messenger"),
        ("0x608d94945A64503E642E6370Ec598e519a2C1E53", "Base L1 ERC721 Bridge"),
        ("0x73a79Fab69143498Ed3712e519A88a918e1f4072", "Base System Config"),
        ("0x0475cBCAebd9CE8AfA5025828d5b98DFb67E059E", "Base Proxy Admin"),
        ("0x8EfB6B5c4767B09Dc9AA6Af4eAA89F749522BaE2", "Base Address Manager"),
        ("0x5050f69a9786f081509234f1a7f4684b5e5b76c9", "Base Batch Sender"),
        ("0xc1366Fabe614d42D367A1ecE61821238A1d31cF5", "Base Output Proposer"),
        ("0x20AcF55A3DCfe07fC4cecaCFa1628F788EC8A4Dd", "Base Security Council"),
        ("0x9855054731540A48b28990B63DcF4f33d8AE46A1", "Base CB Multisig"),
        ("0x7bB41C3008B3f03FE483B28b8DB90e19Cf07595c", "Base Proxy Admin Owner"),
        ("0x14536667Cd30e52C0b458BaACcB9faDA7046E056", "Base SystemConfig Owner"),
        ("0x819501cdA743a606A93dbEF254FE0D263Ce7d102", "Base Challenger"),
        ("0x43edB88C4B80fDD2AdFF2412A7BebF9dF42cB40e", "Base Dispute Game Factory"),
        ("0x909f6cf47ed12f010A796527f562bFc26C7F4E72", "Base Anchor State Registry"),
        ("0xd0D07924AdD740a87e41Ca8A0d4CBBf6b074EF71", "Base Delayed WETH"),
        ("0x05cc379EBD9B30BbA19C6fA282AB29218EC61D84", "Base OptimismMintableERC20Factory"),
    ]:
        add(addr, name, "protocol", "official", "Base docs contract addresses", BASE_SRC, "bridge_base")

    ARB_SRC = "https://docs.arbitrum.io/build-decentralized-apps/reference/contract-addresses"
    for addr, name in [
        ("0x4DCeB440657f21083db8aDd07665f8ddBe1DCfc0", "Arbitrum One Rollup"),
        ("0x1c479675ad559DC151F6Ec7ed3FbF8ceE79582B6", "Arbitrum One Sequencer Inbox"),
        ("0x4Dbd4fc535Ac27206064B68FfCf827b0A60BAB3f", "Arbitrum One Delayed Inbox"),
        ("0x8315177aB297bA92A06054cE80a67Ed4DBd7ed3a", "Arbitrum One Bridge"),
        ("0x0B9857ae2D4A3DBe74ffE1d7DF045bb7F96E4840", "Arbitrum One Outbox"),
        ("0x72Ce9c846789fdB6fC1f34aC4AD25Dd9ef7031ef", "Arbitrum One L1 Gateway Router"),
        ("0xa3A7B6F88361F48403514059F1F16C8E78d60EeC", "Arbitrum One L1 ERC20 Gateway"),
        ("0xcEe284F754E854890e311e3280b767F80797180d", "Arbitrum One L1 Custom Gateway"),
        ("0xd92023E9d9911199a6711321D1277285e6d4e2db", "Arbitrum One L1 WETH Gateway"),
        ("0x760723CD2e632826c38Fef8CD438A4CC7E7E1A40", "Arbitrum One Classic Outbox"),
    ]:
        add(addr, name, "protocol", "official", "Arbitrum docs contract addresses", ARB_SRC, "bridge_arb")

    POLY_SRC = "https://github.com/maticnetwork/static/blob/master/network/mainnet/v1/index.json"
    poly = json.loads((DOCS / "polygon-pos.json").read_text())
    poly_map = {
        "DepositManagerProxy": "Polygon PoS Deposit Manager",
        "WithdrawManagerProxy": "Polygon PoS Withdraw Manager",
        "RootChainProxy": "Polygon PoS Root Chain",
        "StateSender": "Polygon PoS State Sender",
        "StakeManagerProxy": "Polygon PoS Stake Manager",
        "ERC20Predicate": "Polygon PoS ERC20 Predicate",
        "ERC721Predicate": "Polygon PoS ERC721 Predicate",
        "EventsHubProxy": "Polygon PoS Events Hub",
        "StakingInfo": "Polygon PoS Staking Info",
        "Registry": "Polygon PoS Registry",
    }
    for key, label in poly_map.items():
        addr = poly["Main"]["Contracts"].get(key)
        if addr:
            add(addr, label, "protocol", "official", "Polygon PoS mainnet contracts", POLY_SRC, "bridge_polygon")
    # Well-known PoS Predicate used by many bridges
    add(
        "0x40ec5B33f54e0E8A33A975908C5BA1c14e5BbbDf",
        "Polygon PoS ERC20 Predicate Proxy",
        "protocol",
        "official",
        "Polygon PoS bridge contracts",
        "https://docs.polygon.technology/pos/reference/contracts/contracts-mainnet/",
        "bridge_polygon",
    )
    add(
        "0xA0c68C638235ee32657e8f720a23ceC1bFc77C77",
        "Polygon PoS Root Chain Manager Proxy",
        "protocol",
        "official",
        "Polygon PoS bridge contracts",
        "https://docs.polygon.technology/pos/reference/contracts/contracts-mainnet/",
        "bridge_polygon",
    )

    # ---- 3. DEX ----
    UNI_V2 = "https://docs.uniswap.org/contracts/v2/reference/smart-contracts/v2-deployments"
    UNI_V3 = "https://docs.uniswap.org/contracts/v3/reference/deployments/ethereum-deployments"
    UNI_V4 = "https://docs.uniswap.org/contracts/v4/deployments"
    for addr, name, src, url, fam in [
        ("0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f", "Uniswap V2 Factory", "Uniswap V2 deployments", UNI_V2, "dex"),
        ("0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D", "Uniswap V2 Router 02", "Uniswap V2 deployments", UNI_V2, "dex"),
        ("0x1F98431c8aD98523631AE4a59f267346ea31F984", "Uniswap V3 Factory", "Uniswap V3 Ethereum deployments", UNI_V3, "dex"),
        ("0xE592427A0AEce92De3Edee1F18E0157C05861564", "Uniswap V3 SwapRouter", "Uniswap V3 Ethereum deployments", UNI_V3, "dex"),
        ("0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45", "Uniswap V3 SwapRouter02", "Uniswap V3 Ethereum deployments", UNI_V3, "dex"),
        ("0xC36442b4a4522E871399CD717aBDD847Ab11FE88", "Uniswap V3 NonfungiblePositionManager", "Uniswap V3 Ethereum deployments", UNI_V3, "dex"),
        ("0x61fFE014bA17989E743c5F6cB21bF9697530B21e", "Uniswap V3 QuoterV2", "Uniswap V3 Ethereum deployments", UNI_V3, "dex"),
        ("0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6", "Uniswap V3 Quoter", "Uniswap V3 Ethereum deployments", UNI_V3, "dex"),
        ("0x000000000022D473030F116dDEE9F6B43aC78BA3", "Uniswap Permit2", "Uniswap Permit2", UNI_V3, "dex"),
        ("0x000000000004444c5dc75cB358380D2e3dE08A90", "Uniswap V4 PoolManager", "Uniswap V4 deployments", UNI_V4, "dex"),
        ("0xbd216513d74c8cf14cf4747e6aaa6420ff64ee9e", "Uniswap V4 PositionManager", "Uniswap V4 deployments", UNI_V4, "dex"),
        ("0x52f0e24d1c21c8a0cb1e5a5dd6198556bd9e1203", "Uniswap V4 Quoter", "Uniswap V4 deployments", UNI_V4, "dex"),
        ("0x7ffe42c4a5deea5b0fec41c94c136cf115597227", "Uniswap V4 StateView", "Uniswap V4 deployments", UNI_V4, "dex"),
        ("0xd1428ba554f4c8450b763a0b2040a4935c63f06c", "Uniswap V4 PositionDescriptor", "Uniswap V4 deployments", UNI_V4, "dex"),
        ("0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F", "SushiSwap V2 Router 02", "SushiSwap V2 deployments", "https://docs.sushi.com/contracts/v2/deployment-addresses", "dex"),
        ("0xC0AEe478e3658e2610c5F7A4A2E1777cE9e4f2Ac", "SushiSwap V2 Factory", "SushiSwap V2 deployments", "https://docs.sushi.com/contracts/v2/deployment-addresses", "dex"),
        ("0x1111111254EEB25477B68fb85Ed929f73A960582", "1inch Aggregation Router V5", "1inch Aggregation Router V5", "https://docs.1inch.io/", "dex"),
        ("0x111111125421cA6dc452d289314280a0f8842A65", "1inch Aggregation Router V6", "1inch Aggregation Router V6", "https://docs.1inch.io/", "dex"),
        ("0xDef1C0ded9bec7F1a1670819833240f027b25EfF", "0x Exchange Proxy", "0x Protocol deployed addresses", "https://0x.org/docs/developer-resources/deployed-addresses", "dex"),
        ("0x6A000F20005980200259B80c5102003040001068", "ParaSwap Augustus V6", "ParaSwap smart contracts", "https://developers.paraswap.network/smart-contracts", "dex"),
    ]:
        add(addr, name, "protocol", "official", src, url, fam)

    # Universal Router from official JSON
    ur = json.loads((DOCS / "uni-ur.md").read_text())
    UR_SRC = "https://github.com/Uniswap/universal-router/blob/main/deploy-addresses/mainnet.json"
    for k, a in ur.items():
        add(a, f"Uniswap {k}", "protocol", "official", "Uniswap Universal Router deployments", UR_SRC, "dex")

    # CowSwap from networks.json
    cow = json.loads((DOCS / "cow-deploy.json").read_text())
    COW_SRC = "https://github.com/cowprotocol/contracts/blob/main/networks.json"
    cow_names = {
        "GPv2Settlement": "CowSwap GPv2 Settlement",
        "GPv2VaultRelayer": "CowSwap GPv2 Vault Relayer",
        "GPv2AllowListAuthentication": "CowSwap GPv2 AllowList Authentication",
    }
    for key, label in cow_names.items():
        entry = cow.get(key, {}).get("1")
        if entry and entry.get("address"):
            add(entry["address"], label, "protocol", "official", "Cow Protocol networks.json", COW_SRC, "dex")

    # ---- 4. Staking / LST ----
    add(
        "0x00000000219ab540356cBB839Cbe05303d7705Fa",
        "Beacon Deposit Contract",
        "protocol",
        "official",
        "ethereum.org staking deposit contract",
        "https://ethereum.org/en/staking/deposit-contract/",
        "staking",
    )
    LIDO_SRC = "https://docs.lido.fi/deployed-contracts/"
    for addr, name in [
        ("0xC1d0b3DE6792Bf6b4b37EccdcC24e45978Cfd2Eb", "Lido Locator"),
        ("0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84", "Lido stETH"),
        ("0x7f39C581F595B53c5cb19bD0b3f8dA6c935E2Ca0", "Lido wstETH"),
        ("0xFdDf38947aFB03C621C71b06C9C70bce73f12999", "Lido Staking Router"),
        ("0x889edC2eDab5f40e902b864aD4d7AdE8E412F9B1", "Lido Withdrawal Queue ERC721"),
        ("0xb9d7934878b5fb9610b3fe8a5e441e8fad7e293f", "Lido Withdrawal Vault"),
        ("0x388C818CA8B9251b393131C08a736A67ccB19297", "Lido EL Rewards Vault"),
        ("0xF573E9E3de1f86B085417ab294f56E7920B4e9Be", "Lido Deposit Security Module"),
        ("0xf98AC162eAB766bDB9507c3584c00C535B8F6216", "Lido Beacon Chain Depositor"),
        ("0xE76c52750019b80B43E36DF30bf4060EB73F573a", "Lido Burner"),
        ("0xF95f069F9AD107938F6ba802a3da87892298610E", "Lido MEV Boost Relay Allowed List"),
        ("0xb8FFC3Cd6e7Cf5a098A1c92F48009765B24088Dc", "Lido DAO Kernel"),
        ("0x5A98FcBEA516Cf06857215779Fd812CA3beF1B32", "LDO Token"),
        ("0x2e59A20f205bB85a89C53f1936454680651E618e", "Lido Aragon Voting"),
        ("0x3e40D73EB977Dc6a537aF587D48316feE66E9C8c", "Lido Treasury"),
        ("0xB9E5CBB9CA5b0d659238807E84D0176930753d86", "Lido Aragon Finance"),
        ("0x12a43b049A7D330cB8aEAB5113032D18AE9a9030", "Lido LEGO Committee"),
        ("0xa02FC823cCE0D016bD7e17ac684c9abAb2d6D647", "Lido Treasury Management Committee"),
        ("0x98be4a407Bff0c125e25fBE9Eb1165504349c37d", "Lido Relay Maintenance Committee"),
        ("0x55032650b14df07b85bF18A3a3eC8E0Af2e028d5", "Lido Node Operators Registry"),
        ("0xaE7B191A31f627b4eB1d4DaC64eaB9976995b433", "Lido Simple DVT Registry"),
        ("0xF0211b7660680B49De1A7E9f25C65660F0a13Fea", "Lido EasyTrack"),
        ("0x87D93d9B2C672bf9c9642d853a8682546a5012B5", "Lido Liquidity Observation Lab"),
        ("0x9de443AdC5A411E83F1878Ef24C3F52C61571e72", "Lido Base L1 ERC20 Token Bridge"),
        ("0x76943C0D61395d8F2edF9060e1533529cAe05dE6", "Lido Optimism L1 Tokens Bridge"),
        ("0x0F25c1DC2a9922304f2eac71DCa9B07E310e8E5a", "Lido Arbitrum L1 ERC20 Token Gateway"),
        ("0xCE0425301C85c5Ea2A0873A2dEe44d78E02D2316", "Lido Emergency Protected Timelock"),
        ("0xC1db28B3301331277e307FDCfF8DE28242A4486E", "Lido Dual Governance"),
    ]:
        add(addr, name, "protocol", "official", "Lido deployed contracts", LIDO_SRC, "staking")

    add(
        "0xae78736Cd615f374D3085123A210448E74Fc6393",
        "Rocket Pool rETH",
        "protocol",
        "official",
        "Rocket Pool docs / Spark registry",
        "https://docs.rocketpool.net/developers/usage/contracts/contracts",
        "staking",
    )

    # ---- 5. DAO treasuries ----
    for addr, name, src, url in [
        ("0x1a9C8182C09F50C8318d769245beA52c32BE35BC", "Uniswap Timelock", "Uniswap governance", "https://docs.uniswap.org/contracts/v1/guides/governance"),
        ("0x5e4be8Bc9637f0EAA1A755019e06A68ce081D58F", "Uniswap Governor Bravo", "Uniswap governance", "https://docs.uniswap.org/contracts/v1/guides/governance"),
        ("0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984", "UNI Token", "Uniswap default token list", "https://tokens.uniswap.org"),
        ("0xFe89cc7aBB2C53880561CD573757AE4b3B5bCE3C", "ENS DAO Wallet", "ENS DAO", "https://docs.ens.domains/dao/"),
        ("0xC18360217D8F7Ab5e7c516566761Ea12Ce7F9D72", "ENS Token", "ENS docs", "https://docs.ens.domains/"),
        ("0xc0Da02939E1441F497fd74F78cE7Decb17B66529", "Compound Governor Bravo", "Compound governance", "https://docs.compound.finance/governance/"),
        ("0x3d9819210A31b4961b30EF54bE2aeD79B9c9Cd3B", "Compound Comptroller", "Compound docs", "https://docs.compound.finance/"),
        ("0xc00e94Cb662C3520282E6f5717214004A7f26888", "COMP Token", "Compound docs", "https://docs.compound.finance/"),
        ("0x464C71f6c2F760DdA6093dCB91C24c39e5d6e18c", "Aave Collector V2", "Aave deployments", "https://docs.aave.com/developers/deployed-contracts/v3-mainnet/ethereum"),
        ("0xEC568fffba86c094Cf06b22134B23074DFE2252c", "Aave Governance V2", "Aave governance", "https://docs.aave.com/developers/deployed-contracts/governance-contracts"),
        ("0xde21F729137C5Af1b01d73aF1dC21eFfa2B8a0d6", "Gitcoin Grants Matching Pool", "Gitcoin", "https://gitcoin.co/"),
    ]:
        add(addr, name, "protocol", "official", src, url, "dao")

    # ---- 6. Mixers / privacy: Tornado already present; skip inventing Railgun/Privacy Pools without fetched addrs ----

    # ---- 7. NFT ----
    add("0x0000000000000068F116a894984e2DB1123eB395", "OpenSea Seaport 1.6", "protocol", "official", "OpenSea Seaport Deployment", SEAPORT_SRC, "nft")
    add("0x00000000006c3852cbEf3e08E8dF289169EdE581", "OpenSea Seaport 1.1", "protocol", "official", "OpenSea Seaport Deployment", SEAPORT_SRC, "nft")
    add("0x00000000000000ADc04C56Bf30aC9d3c0aAF14dC", "OpenSea Seaport 1.5", "protocol", "official", "OpenSea Seaport Deployment", SEAPORT_SRC, "nft")
    add("0x00000000F9490004C11Cef243f5400493c00Ad63", "OpenSea ConduitController", "protocol", "official", "OpenSea Seaport Deployment", SEAPORT_SRC, "nft")
    add("0x000000000000Ad05Ccc4F10045630fb830B95127", "Blur Marketplace", "shop", "official", "Blur.io marketplace", "https://blur.io/", "nft")

    for addr, name, src, url in [
        ("0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D", "Bored Ape Yacht Club", "Yuga Labs BAYC", "https://boredapeyachtclub.com/"),
        ("0x60E4d786628Fea6478F785A6d7e704777c86a7c6", "Mutant Ape Yacht Club", "Yuga Labs MAYC", "https://boredapeyachtclub.com/"),
        ("0xb47e3cd837dDF8e4c57F05d70Ab865de6e193BBB", "CryptoPunks", "Larva Labs CryptoPunks", "https://www.larvalabs.com/cryptopunks"),
        ("0xBd3531dA5CF66d67bC5614C2DdA6bF5eF3eB4B80", "Pudgy Penguins", "Pudgy Penguins", "https://pudgypenguins.com/"),
        ("0xED5AF388653567Af2F388E6224dC7C4b3241C544", "Azuki", "Azuki", "https://www.azuki.com/"),
        ("0x59728544B08AB483533076417FbBB2fD0B17CE3a", "LooksRare Exchange", "LooksRare docs", "https://docs.looksrare.org/developers/deployed-contracts"),
    ]:
        tier = "official"
        cat = "shop"
        if "LooksRare" in name:
            tier = "community"
        add(addr, name, cat, tier, src, url, "nft")

    # ---- 8. Stablecoins ----
    for addr, name, src, url in [
        ("0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48", "USD Coin", "Circle USDC contract addresses", "https://developers.circle.com/stablecoins/usdc-contract-addresses"),
        ("0xdac17f958d2ee523a2206206994597c13d831ec7", "Tether USD", "Tether transparency", "https://tether.to/en/transparency/"),
        ("0x6B175474E89094C44Da98b954EedeAC495271d0F", "Dai Stablecoin", "MakerDAO docs", "https://docs.makerdao.com/"),
        ("0x853d955aCEf822Db058eb8505911ED77F175b99e", "FRAX", "Frax Finance docs", "https://docs.frax.finance/"),
        ("0xBd3fa81B58Ba92a82136038B25aDec7066af3155", "Circle TokenMessenger (CCTP)", "Circle CCTP contracts", "https://developers.circle.com/stablecoins/docs/cctp-protocol-contracts"),
        ("0x0a992d191DEeC73a461EfF9bf6869C1dE1A4D0C2", "Circle MessageTransmitter (CCTP)", "Circle CCTP contracts", "https://developers.circle.com/stablecoins/docs/cctp-protocol-contracts"),
    ]:
        add(addr, name, "protocol", "official", src, url, "stablecoin")

    # ---- 9. Exploits (tiny; official-adjacent with clear labeling) ----
    add(
        "0x629e7Da20197a5429d30da36E77d06CdF796b71A",
        "Wormhole Exploiter 2022",
        "protocol",
        "community",
        "Wormhole incident report 2022-02-02 (exploiter attribution)",
        "https://wormholecrypto.medium.com/wormhole-incident-report-02-02-22-ad9b8f21eec6",
        "exploit",
    )

    # ---- 10. Public figures ----
    add(
        "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
        "Vitalik Buterin",
        "person",
        "official",
        "vitalik.ca",
        "https://vitalik.ca",
        "person",
    )

    # Dedupe incoming preferring official
    by: dict[str, dict] = {}
    for r in rows:
        a = r["address"]
        if a not in by:
            by[a] = r
            continue
        if TIER_RANK[r["tier"]] < TIER_RANK[by[a]["tier"]]:
            by[a] = r
    out = list(by.values())
    meta["incoming_unique"] = len(out)
    meta["families"] = sorted(meta.get("by_family", {}).keys())
    return out, meta


def append_sources(before, after, stats, meta, upgrades):
    by_tier = Counter(r.get("tier", "official") for r in after)
    by_cat = Counter(r["category"] for r in after)
    lines = [
        "",
        "",
        f"## High-leverage role labels expansion: {PULL_DATE}",
        "",
        "Add MEV/builders, L2 bridge & system contracts, DEX routers/aggregators,",
        "staking/LST, DAO treasuries, NFT marketplaces/collections, stablecoin plumbing,",
        "CREATE2 factories, and a tiny documented-exploit set. Prefer official docs;",
        "community only when that is all that exists (clearly labeled).",
        "",
        "### Source families",
        "",
        "- BuilderNet public identity: https://buildernet.org/docs/public-identity",
        "- Arachnid CREATE2: https://github.com/Arachnid/deterministic-deployment-proxy",
        "- Optimism superchain-registry addresses.json (chain 10 L1 system)",
        "- Base docs: https://docs.base.org/base-chain/network-information/base-contracts",
        "- Arbitrum docs: https://docs.arbitrum.io/build-decentralized-apps/reference/contract-addresses",
        "- Polygon PoS: https://github.com/maticnetwork/static (mainnet/v1/index.json)",
        "- Uniswap V2/V3/V4 + Permit2 + Universal Router official deployments",
        "- Cow Protocol networks.json; SushiSwap V2; 1inch routers; 0x Exchange Proxy; ParaSwap Augustus V6",
        "- ethereum.org Beacon Deposit Contract",
        "- Lido deployed contracts: https://docs.lido.fi/deployed-contracts/",
        "- DAO treasuries: Uniswap / ENS / Compound / Aave / Gitcoin official docs",
        "- OpenSea Seaport Deployment.md; Blur marketplace; BAYC/MAYC/Punks/Pudgy/Azuki official sites",
        "- Circle USDC + CCTP; Tether; MakerDAO DAI; Frax",
        "- Wormhole incident report (exploiter labeled community)",
        "",
        "### Deliberate gaps",
        "",
        "- Flashbots/beaverbuild/rsync/Titan builder **fee-recipient** EOAs rotate and are not",
        "  published as stable addresses in Flashbots Protect docs (only builder *names*/RPCs in",
        "  builder-registrations.json). BuilderNet identities included from official page.",
        "- ScamSniffer blacklist skipped (GPL-3.0 license; not clearly OK to rebundle).",
        "- Railgun / Privacy Pools / zkSync L1 / Starknet portals: official address pages did not",
        "  return parseable address tables in this pass; left for a follow-up.",
        "- No public Coinbase PoR hot-wallet dump; Base admin EOAs from Base docs only.",
        "- Sandwich/searcher bots: no stable official registry with citable fee recipients.",
        "- Exploit set kept tiny; only Wormhole 2022 exploiter with community caveat.",
        "",
        "### Counts",
        "",
        f"- Before: total={before['total']} official={before['official']} community={before['community']}",
        f"- After: total={by_tier.total()} official={by_tier.get('official',0)} community={by_tier.get('community',0)}",
        f"- Merge stats: {json.dumps(stats)}",
        f"- Incoming by family: {json.dumps(meta.get('by_family', {}))}",
        f"- Category totals after: {json.dumps(dict(by_cat))}",
        f"- Community->official upgrades: {len(upgrades)}",
        "",
    ]
    if upgrades:
        lines.append("### Notable upgrades (community -> official)")
        lines.append("")
        for u in upgrades[:40]:
            lines.append(
                f"- `{u['address']}`: {u['from_name']!r} ({u['from_source']}) -> {u['to_name']!r} ({u['to_source']})"
            )
        lines.append("")
    SOURCES_MD.write_text(SOURCES_MD.read_text(encoding="utf-8") + "\n".join(lines), encoding="utf-8")


def main() -> int:
    existing = load_existing()
    before_addrs = {r["address"] for r in existing}
    before = {
        "total": len(existing),
        "official": sum(1 for r in existing if r.get("tier") == "official"),
        "community": sum(1 for r in existing if r.get("tier") == "community"),
        "by_cat": dict(Counter(r["category"] for r in existing)),
    }
    incoming, meta = build_incoming()
    merged, stats, upgrades = merge(existing, incoming)
    write_csv(merged)
    write_app(merged)
    append_sources(before, merged, stats, meta, upgrades)

    after_tier = Counter(r.get("tier", "official") for r in merged)
    after_cat = Counter(r["category"] for r in merged)
    new_addrs = {r["address"] for r in merged} - before_addrs
    new_rows = [r for r in merged if r["address"] in new_addrs]

    # bucket new rows roughly
    buckets = Counter()
    for r in new_rows:
        n = r["name"].lower()
        if any(x in n for x in ("builder", "create2", "flashbot")):
            buckets["mev_create2"] += 1
        elif any(x in n for x in ("optimism", "base ", "arbitrum", "polygon", "bridge", "portal", "messenger", "inbox", "outbox", "rollup", "sequencer")):
            buckets["bridges_l2"] += 1
        elif any(x in n for x in ("uniswap", "sushi", "1inch", "0x ", "paraswap", "cowswap", "permit2", "router", "quoter", "poolmanager")):
            buckets["dex"] += 1
        elif any(x in n for x in ("lido", "rocket", "beacon", "steth", "wsteth", "reth", "eigen")):
            buckets["staking"] += 1
        elif any(x in n for x in ("treasury", "timelock", "governor", "dao", "ens ", "gitcoin", "compound", "aave collector", "uni token", "comp token")):
            buckets["dao"] += 1
        elif any(x in n for x in ("seaport", "blur", "bored", "mutant", "punk", "pudgy", "azuki", "looksrare", "opensea", "conduit")):
            buckets["nft"] += 1
        elif any(x in n for x in ("usd coin", "tether", "dai", "frax", "circle", "cctp")):
            buckets["stablecoin"] += 1
        elif "exploit" in n or "wormhole exploit" in n:
            buckets["exploit"] += 1
        else:
            buckets["other"] += 1

    report = {
        "before": before,
        "after": {
            "total": len(merged),
            "official": after_tier.get("official", 0),
            "community": after_tier.get("community", 0),
            "by_cat": dict(after_cat),
        },
        "stats": stats,
        "meta": meta,
        "new_count": len(new_rows),
        "new_by_bucket": dict(buckets),
        "upgrades_count": len(upgrades),
        "upgrades_sample": upgrades[:25],
        "new_sample": [{"name": r["name"], "tier": r["tier"], "source": r["source"]} for r in new_rows[:30]],
    }
    Path("/tmp/rensic-roles/expand_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
