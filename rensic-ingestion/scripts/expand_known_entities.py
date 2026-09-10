#!/usr/bin/env python3
"""Expand Rensic known_entities.csv from official, citable public sources."""
from __future__ import annotations

import csv
import json
import re
import ssl
import sys
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import date
from pathlib import Path

import yaml

CSV_PATH = Path("/Users/george/Documents/WilderformTools/rensic/rensic-ingestion/transforms-python/src/myproject/data/known_entities.csv")
SOURCES_MD = CSV_PATH.with_name("SOURCES.md")
APP_TS = Path("/Users/george/Documents/WilderformTools/rensic/rensic-app/src/knownEntities.ts")
WORK = Path("/tmp/rensic-ke-expand")
STATS_PATH = WORK / "stats.json"

ETH_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
UA = "Rensic known-entity pack builder (non-commercial research)"
CTX = ssl.create_default_context()

CAT_RANK = {
    "sanctions": 0,
    "mixer": 1,
    "gambling": 2,
    "exchange": 3,
    "shop": 4,
    "protocol": 5,
    "person": 6,
}

SOURCE_RANK = {
    "OFAC SDN": -1,
    "OFAC": 0,
    "FBI / IC3": 1,
    "FBI": 1,
}

SDN_XML_URL = "https://www.treasury.gov/ofac/downloads/sdn.xml"
OFAC_CITE = "https://sanctionslist.ofac.treas.gov/Home/SdnList"
SDN_NS = {"s": "https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/XML"}

IC3_BYBIT_URL = "https://www.ic3.gov/psa/2025/psa250226"
FBI_STAKE_URL = (
    "https://www.fbi.gov/news/press-releases/"
    "fbi-identifies-lazarus-group-cyber-actors-as-responsible-for-theft-of-41-million-from-stakecom"
)
FBI_HARMONY_URL = (
    "https://www.fbi.gov/news/press-releases/"
    "fbi-confirms-lazarus-group-cyber-actors-responsible-for-harmonys-horizon-bridge-currency-theft"
)
FBI_DMM_URL = (
    "https://www.fbi.gov/news/press-releases/"
    "fbi-dc3-and-npa-identification-of-north-korean-cyber-actors-tracked-as-tradertraitor-"
    "responsible-for-theft-of-308-million-from-bitcoindmmcom"
)

# Stake.com ETH IDs from the FBI press release (Cloudflare often blocks fbi.gov fetches).
FBI_STAKE_ETH = (
    "0x94f1b9b64e2932f6a2db338f616844400cd58e8a",
    "0xba36735021a9ccd7582ebc7f70164794154ff30e",
    "0xbda83686c90314cfbaaeb18db46723d83fdf0c83",
    "0x7d84d78bb9b6044a45fa08b7fe109f2c8648ab4e",
)

# IC3 PSA 250226 Ethereum list. Used when the live page fetch is incomplete.
FBI_BYBIT_ETH = (
    "0x51E9d833Ecae4E8D9D8Be17300AEE6D3398C135D",
    "0x96244D83DC15d36847C35209bBDc5bdDE9bEc3D8",
    "0x83c7678492D623fb98834F0fbcb2E7b7f5Af8950",
    "0x83Ef5E80faD88288F770152875Ab0bb16641a09E",
    "0xAF620E6d32B1c67f3396EF5d2F7d7642Dc2e6CE9",
    "0x3A21F4E6Bbe527D347ca7c157F4233c935779847",
    "0xfa3FcCCB897079fD83bfBA690E7D47Eb402d6c49",
    "0xFc926659Dd8808f6e3e0a8d61B20B871F3Fa6465",
    "0xb172F7e99452446f18FF49A71bfEeCf0873003b4",
    "0x6d46bd3AfF100f23C194e5312f93507978a6DC91",
    "0xf0a16603289eAF35F64077Ba3681af41194a1c09",
    "0x23Db729908137cb60852f2936D2b5c6De0e1c887",
    "0x40e98FeEEbaD7Ddb0F0534Ccaa617427eA10187e",
    "0x140c9Ab92347734641b1A7c124ffDeE58c20C3E3",
    "0x684d4b58Dc32af786BF6D572A792fF7A883428B9",
    "0xBC3e5e8C10897a81b63933348f53f2e052F89a7E",
    "0x5Af75eAB6BEC227657fA3E749a8BFd55f02e4b1D",
    "0xBCA02B395747D62626a65016F2e64A20bd254A39",
    "0x4C198B3B5F3a4b1Aa706daC73D826c2B795ccd67",
    "0xCd7eC020121Ead6f99855cbB972dF502dB5bC63a",
    "0xbdE2Cc5375fa9E0383309A2cA31213f2D6cabcbd",
    "0xD3C611AeD139107DEC2294032da3913BC26507fb",
    "0xB72334cB9D0b614D30C4c60e2bd12fF5Ed03c305",
    "0x8c7235e1A6EeF91b980D0FcA083347FBb7EE1806",
    "0x1bb0970508316DC735329752a4581E0a4bAbc6B4",
    "0x1eB27f136BFe7947f80d6ceE3Cf0bfDf92b45e57",
    "0xCd1a4A457cA8b0931c3BF81Df3CFa227ADBdb6E9",
    "0x09278b36863bE4cCd3d0c22d643E8062D7a11377",
    "0x660BfcEa3A5FAF823e8f8bF57dd558db034dea1d",
    "0xE9bc552fdFa54b30296d95F147e3e0280FF7f7e6",
    "0x30a822CDD2782D2B2A12a08526452e885978FA1D",
    "0xB4a862A81aBB2f952FcA4C6f5510962e18c7f1A2",
    "0x0e8C1E2881F35Ef20343264862A242FB749d6b35",
    "0x9271EDdda0F0f2bB7b1A0c712bdF8dbD0A38d1Ab",
    "0xe69753Ddfbedbd249E703EB374452E78dae1ae49",
    "0x2290937A4498C96eFfb87b8371a33D108F8D433f",
    "0x959c4CA19c4532C97A657D82d97acCBAb70e6fb4",
    "0x52207Ec7B1b43AA5DB116931a904371ae2C1619e",
    "0x9eF42873Ae015AA3da0c4354AeF94a18D2B3407b",
    "0x1542368a03ad1f03d96D51B414f4738961Cf4443",
    "0x21032176B43d9f7E9410fB37290a78f4fEd6044C",
    "0xA4B2Fd68593B6F34E51cB9eDB66E71c1B4Ab449e",
    "0x55CCa2f5eB07907696afe4b9Db5102bcE5feB734",
    "0xA5A023E052243b7cce34Cbd4ba20180e8Dea6Ad6",
    "0xdD90071D52F20e85c89802e5Dc1eC0A7B6475f92",
    "0x1512fcb09463A61862B73ec09B9b354aF1790268",
    "0xF302572594a68aA8F951faE64ED3aE7DA41c72Be",
    "0x723a7084028421994d4a7829108D63aB44658315",
    "0xf03AfB1c6A11A7E370920ad42e6eE735dBedF0b1",
    "0xEB0bAA3A556586192590CAD296b1e48dF62a8549",
    "0xD5b58Cf7813c1eDC412367b97876bD400ea5c489",
)

UNISWAP_V2_DOCS = "https://developers.uniswap.org/docs/protocols/v2/deployments"
UNISWAP_UR_JSON = (
    "https://raw.githubusercontent.com/Uniswap/universal-router/main/deploy-addresses/mainnet.json"
)
UNISWAP_UR_LABELS = {
    "UniversalRouterV1": "Uniswap Universal Router V1",
    "UniversalRouterV1_2_V2Support": "Uniswap Universal Router V1.2",
    "UniversalRouterV2": "Uniswap Universal Router V2",
    "UniversalRouterV2_1_1": "Uniswap Universal Router V2.1.1",
}
UNISWAP_PERMIT2_DOCS = "https://docs.uniswap.org/contracts/permit2/overview"
LIDO_DOCS = "https://docs.lido.fi/deployed-contracts/"
SEAPORT_README = "https://github.com/ProjectOpenSea/seaport"

UNISWAP_V2_ROUTER = ("0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D", "Uniswap V2 Router02")
UNISWAP_V3_ROUTER02 = ("0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45", "Uniswap V3 SwapRouter02")
UNISWAP_PERMIT2 = ("0x000000000022D473030F116dDEE9F6B43aC78BA3", "Uniswap Permit2")
LIDO_STETH = ("0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84", "Lido stETH")
LIDO_WSTETH = ("0x7f39C581F595B53c5cb19bD0b3f8dA6c935E2Ca0", "Lido wstETH")
SEAPORT_VERSIONS = (
    ("0x00000000006c3852cbEf3e08E8dF289169EdE581", "OpenSea Seaport 1.1"),
    ("0x00000000000000ADc04C56Bf30aC9d3c0aAF14dC", "OpenSea Seaport 1.5"),
    ("0x0000000000000068F116a894984e2DB1123eB395", "OpenSea Seaport 1.6"),
)

SKIP_GS_PREFIX = (
    "etherscan",
    "exchange-wallets",
    "miners",
    "sextortion",
    "eosio-gambling",
    "walletexplorer",
    "defi-fraud",
    "ransomwhere",
    "ransomware",
    "demo",
    "alt-right",
    "ofac",
)

SKIP_GS_NAMES = {
    "defi-protocols-csh.yaml",
    "samourai.yaml",
    "miners_additional.yaml",
    "ronin_bridge.yaml",
}

TOKENLIST_URL = "https://tokens.uniswap.org"
UNISWAP_V3_DOCS = "https://docs.uniswap.org/contracts/v3/reference/deployments/ethereum"
AAVE_V3_DOCS = "https://docs.aave.com/developers/deployed-contracts/v3-mainnet"

WELL_KNOWN_TOKENS = {
    "USDC": "USD Coin",
    "USDT": "Tether USD",
    "AAVE": "Aave",
}

UNISWAP_V3_ROUTER = ("0xe592427a0aece92de3edee1f18e0157c05861564", "Uniswap V3 SwapRouter")
AAVE_V3_POOL = ("0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2", "Aave V3 Pool")


def fetch(url: str, dest: Path, timeout: int = 120) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, context=CTX, timeout=timeout) as resp:
            dest.write_bytes(resp.read())
        return dest
    except Exception:
        import subprocess

        subprocess.check_call(
            ["curl", "-sL", "--fail", "-A", UA, "-o", str(dest), url],
            timeout=timeout,
        )
        if not dest.is_file() or dest.stat().st_size == 0:
            raise RuntimeError(f"empty download: {url}")
        return dest


def fetch_json(url: str, timeout: int = 120):
    dest = WORK / "json-cache" / re.sub(r"[^a-zA-Z0-9]+", "_", url)[-80:]
    fetch(url, dest, timeout=timeout)
    return json.loads(dest.read_text(encoding="utf-8"))


def is_eth(addr: str) -> bool:
    return bool(ETH_RE.match((addr or "").strip()))


def norm_addr(addr: str) -> str:
    return addr.strip().lower()


def looks_like_url(s: str) -> bool:
    s = (s or "").strip().lower()
    return s.startswith("http://") or s.startswith("https://")


def row(address: str, name: str, category: str, source: str, source_url: str, secondary: str = "") -> dict:
    return {
        "chain": "ethereum",
        "address": norm_addr(address),
        "name": (name or "").strip() or norm_addr(address),
        "category": category,
        "secondary_category": secondary,
        "source": source,
        "source_url": source_url,
    }


def load_existing() -> list[dict]:
    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def cat_rank(r: dict) -> tuple:
    src = r.get("source") or ""
    src_boost = SOURCE_RANK.get(src, 10)
    if src == "OFAC SDN":
        src_boost = -1
    return (CAT_RANK.get(r.get("category") or "", 99), src_boost, src)


def merge_rows(groups: list[list[dict]]) -> tuple[list[dict], dict]:
    by_key: dict[tuple[str, str], dict] = {}
    conflicts = 0
    for group in groups:
        for r in group:
            key = (r["chain"], r["address"])
            if key not in by_key:
                by_key[key] = r
                continue
            old = by_key[key]
            if cat_rank(r) < cat_rank(old):
                conflicts += 1
                by_key[key] = r
            elif cat_rank(r) != cat_rank(old):
                conflicts += 1
    out = sorted(by_key.values(), key=lambda r: (r["category"], r["name"].lower(), r["address"]))
    return out, {"conflicts_resolved": conflicts, "unique": len(out)}


def _sdn_display_name(first: str, last: str) -> str:
    raw = " ".join(p for p in (first.strip(), last.strip()) if p)
    if not raw:
        return "OFAC SDN"
    if raw.isupper():
        return raw.title()
    return raw


def pull_ofac_sdn() -> tuple[list[dict], dict]:
    dest = WORK / "sdn.xml"
    print(f"Downloading OFAC SDN XML ({SDN_XML_URL})...")
    fetch(SDN_XML_URL, dest, timeout=180)
    tree = ET.parse(dest)
    root = tree.getroot()
    publish = root.findtext("s:publshInformation/s:Publish_Date", default="", namespaces=SDN_NS)
    record_count = root.findtext("s:publshInformation/s:Record_Count", default="", namespaces=SDN_NS)
    by_asset: Counter[str] = Counter()
    uniq: dict[str, dict] = {}
    for entry in root.findall("s:sdnEntry", SDN_NS):
        last = entry.findtext("s:lastName", default="", namespaces=SDN_NS) or ""
        first = entry.findtext("s:firstName", default="", namespaces=SDN_NS) or ""
        name = _sdn_display_name(first, last)
        idlist = entry.find("s:idList", SDN_NS)
        if idlist is None:
            continue
        for ident in idlist.findall("s:id", SDN_NS):
            idtype = (ident.findtext("s:idType", default="", namespaces=SDN_NS) or "").strip()
            num = (ident.findtext("s:idNumber", default="", namespaces=SDN_NS) or "").strip()
            if not idtype.startswith("Digital Currency Address - "):
                continue
            asset = idtype.split(" - ", 1)[-1]
            if asset != "ETH" and not (asset in ("USDT", "USDC") and is_eth(num)):
                continue
            by_asset[asset] += 1
            addr = norm_addr(num)
            if addr not in uniq:
                uniq[addr] = row(addr, name, "sanctions", "OFAC SDN", OFAC_CITE)
    rows = list(uniq.values())
    info = {
        "url": SDN_XML_URL,
        "publish_date": publish.strip(),
        "record_count": record_count.strip(),
        "bytes": dest.stat().st_size,
        "by_asset": dict(by_asset),
        "unique_eth_format": len(rows),
    }
    print(f"  OFAC SDN publish {info['publish_date']}: {len(rows)} unique ETH-format IDs")
    return rows, info


def extract_eth_addresses(text: str) -> list[str]:
    found = []
    seen = set()
    for m in re.finditer(r"0x[0-9a-fA-F]{40}", text or ""):
        addr = norm_addr(m.group(0))
        if addr not in seen:
            seen.add(addr)
            found.append(addr)
    return found


def pull_fbi() -> tuple[list[dict], dict]:
    info: dict = {"releases": [], "skipped": []}
    rows: list[dict] = []

    dest = WORK / "ic3-bybit.html"
    print(f"Downloading FBI/IC3 Bybit PSA ({IC3_BYBIT_URL})...")
    addrs: list[str] = []
    try:
        fetch(IC3_BYBIT_URL, dest, timeout=120)
        addrs = extract_eth_addresses(dest.read_text(encoding="utf-8", errors="replace"))
    except Exception as e:
        info["skipped"].append(f"Bybit IC3 live fetch failed ({e}); using snapshot from the same URL")
    if len(addrs) < len(FBI_BYBIT_ETH):
        addrs = [norm_addr(a) for a in FBI_BYBIT_ETH]
        info["releases_note"] = "Bybit list taken from IC3 PSA snapshot (live page incomplete)"
    for addr in addrs:
        rows.append(
            row(
                addr,
                "TraderTraitor (Bybit)",
                "sanctions",
                "FBI / IC3",
                IC3_BYBIT_URL,
            )
        )
    info["releases"].append(
        {
            "name": "Bybit 2025 / TraderTraitor",
            "url": IC3_BYBIT_URL,
            "eth_rows": len(addrs),
        }
    )
    print(f"  Bybit IC3 ETH addresses: {len(addrs)}")

    for addr in FBI_STAKE_ETH:
        rows.append(
            row(
                addr,
                "Lazarus Group (Stake.com)",
                "sanctions",
                "FBI",
                FBI_STAKE_URL,
            )
        )
    info["releases"].append(
        {
            "name": "Stake.com 2023",
            "url": FBI_STAKE_URL,
            "eth_rows": len(FBI_STAKE_ETH),
        }
    )

    info["skipped"].append(
        f"Harmony Horizon ({FBI_HARMONY_URL}): FBI press lists Bitcoin addresses only; no ETH IDs"
    )
    info["skipped"].append(
        f"DMM Bitcoin ({FBI_DMM_URL}): FBI press is a BTC theft; no ETH IDs published"
    )
    return rows, info


def catalog_crypto_sources(catalog: dict) -> tuple[list[dict], list[str]]:
    picked = []
    skipped = []
    for ds in catalog.get("datasets") or []:
        name = ds.get("name") or ""
        title = ds.get("title") or ""
        tags = ds.get("tags") or []
        blob = " ".join([name, title, " ".join(tags)]).lower()
        cryptoish = any(k in blob for k in ("crypto", "wallet", "lazarus", "nbctf"))
        if not cryptoish:
            continue
        ds_type = ds.get("type")
        official = bool((ds.get("publisher") or {}).get("official"))
        if name in ("il_mod_crypto", "us_fbi_lazarus_crypto"):
            picked.append(ds)
            continue
        if ds_type != "source":
            skipped.append(f"{name}: collection/external, not a source dataset")
            continue
        if ds.get("deprecated") or ds.get("disabled"):
            skipped.append(f"{name}: deprecated/disabled")
            continue
        if name in ("us_ofac_sdn", "us_ofac_cons"):
            skipped.append(f"{name}: OFAC already ingested from official SDN XML")
            continue
        if name == "gb_fcdo_sanctions":
            skipped.append(f"{name}: UK FCDO free-text parse excluded by pack rules")
            continue
        if not official:
            skipped.append(f"{name}: publisher not official-origin")
            continue
        picked.append(ds)
    seen = set()
    uniq = []
    for ds in picked:
        if ds["name"] in seen:
            continue
        seen.add(ds["name"])
        uniq.append(ds)
    return uniq, skipped


def parse_ftm_wallets(path: Path, ds: dict) -> list[dict]:
    ds_name = ds.get("name") or ""
    title = ds.get("title") or ds_name
    pub = ds.get("publisher") or {}
    pub_name = pub.get("name") or pub.get("acronym") or "publisher"
    os_page = f"https://www.opensanctions.org/datasets/{ds_name}/"
    pub_url = pub.get("url") or ds.get("url") or os_page
    source_url = f"{os_page} ; {pub_url}"
    source = f"OpenSanctions / {pub.get('acronym') or pub_name}"
    force_sanctions = ds_name in ("il_mod_crypto", "us_fbi_lazarus_crypto") or "list.sanction" in (ds.get("tags") or [])
    rows = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                ent = json.loads(line)
            except json.JSONDecodeError:
                continue
            if ent.get("schema") != "CryptoWallet":
                continue
            props = ent.get("properties") or {}
            keys = props.get("publicKey") or props.get("address") or []
            if isinstance(keys, str):
                keys = [keys]
            topics = [str(t).lower() for t in (props.get("topics") or [])]
            currencies = props.get("currency") or []
            if isinstance(currencies, str):
                currencies = [currencies]
            currencies_u = {str(c).upper() for c in currencies}
            if currencies_u and not currencies_u.intersection({"ETH", "ETHER", "ETHEREUM"}):
                continue
            names = props.get("name") or props.get("holder") or []
            if isinstance(names, str):
                names = [names]
            label = next((n for n in names if n), "") or title
            for k in keys:
                if not is_eth(str(k)):
                    continue
                sanctionish = force_sanctions or any("sanction" in t for t in topics)
                category = "sanctions" if sanctionish else "sanctions"
                rows.append(row(str(k), str(label), category, source, source_url))
    return rows


def pull_opensanctions() -> tuple[list[dict], dict]:
    info: dict = {"datasets": [], "skipped": [], "rows_by_dataset": {}}
    cat_path = WORK / "os_index.json"
    print("Downloading OpenSanctions catalog...")
    fetch("https://data.opensanctions.org/datasets/latest/index.json", cat_path, timeout=180)
    catalog = json.loads(cat_path.read_text(encoding="utf-8"))
    sources, skipped = catalog_crypto_sources(catalog)
    info["skipped"] = skipped
    all_rows: list[dict] = []
    for ds in sources:
        name = ds["name"]
        resources = ds.get("resources") or []
        ftm = next((r for r in resources if r.get("name") == "entities.ftm.json"), None)
        url = ftm["url"] if ftm and ftm.get("url") else f"https://data.opensanctions.org/datasets/latest/{name}/entities.ftm.json"
        dest = WORK / "os" / f"{name}.ftm.json"
        print(f"  OpenSanctions {name}: {url}")
        try:
            fetch(url, dest, timeout=180)
        except Exception as e:
            info["skipped"].append(f"{name}: download failed ({e})")
            continue
        rows = parse_ftm_wallets(dest, ds)
        uniq = {}
        for r in rows:
            uniq[r["address"]] = r
        rows = list(uniq.values())
        info["datasets"].append(
            {
                "name": name,
                "title": ds.get("title"),
                "official": bool((ds.get("publisher") or {}).get("official")),
                "eth_rows": len(rows),
                "ftm_bytes": dest.stat().st_size,
            }
        )
        info["rows_by_dataset"][name] = len(rows)
        all_rows.extend(rows)
        print(f"    ETH 0x wallets: {len(rows)}")
    return all_rows, info


def map_gs_category(raw: str, pack_cat: str, pack_title: str) -> str | None:
    blob = " ".join([raw or "", pack_cat or "", pack_title or ""]).lower()
    if any(k in blob for k in ("mixin", "mixing", "mixer", "tumbler", "coinjoin", "wasabi", "samourai", "tornado", "blender", "sinbad")):
        return "mixer"
    if any(k in blob for k in ("gambling", "casino", "dice", "betting")):
        return "gambling"
    if any(k in blob for k in ("exchange", "cex", "broker")):
        return "exchange"
    if any(k in blob for k in ("shop", "market", "marketplace", "darknet")):
        return "shop"
    if any(k in blob for k in ("defi", "protocol", "dex", "token", "router", "bridge")):
        return "protocol"
    if any(k in blob for k in ("sanction", "ofac", "sdn", "seizure", "forfeit", "lazarus", "terror")):
        return "sanctions"
    return None


def source_is_citable(url: str) -> bool:
    if not looks_like_url(url):
        return False
    u = url.lower()
    if any(b in u for b in ("etherscan.io", "arkham", "chainalysis", "eth-labels", "dawsbot")):
        return False
    return True


def parse_tagpack(path: Path) -> list[dict]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    if not isinstance(data, dict):
        return []
    pack_source = str(data.get("source") or "")
    pack_cat = str(data.get("category") or "")
    pack_title = str(data.get("title") or path.stem)
    pack_label = str(data.get("label") or pack_title)
    pack_currency = str(data.get("currency") or "").upper()
    tags = data.get("tags") or []
    if not isinstance(tags, list):
        return []
    rows = []
    for tag in tags:
        if not isinstance(tag, dict):
            continue
        addr = str(tag.get("address") or "").strip()
        currency = str(tag.get("currency") or pack_currency or "").upper()
        if currency and currency not in ("ETH", "ETHER", "ETHEREUM", ""):
            if not is_eth(addr):
                continue
        if not is_eth(addr):
            continue
        src = str(tag.get("source") or pack_source or "").strip()
        if not source_is_citable(src):
            continue
        label = str(tag.get("label") or pack_label or "").strip()
        if not label:
            continue
        cat = map_gs_category(str(tag.get("category") or ""), pack_cat, pack_title)
        if not cat:
            continue
        rows.append(row(addr, label, cat, f"GraphSense TagPack / {pack_title}", src))
    return rows


def pull_graphsense() -> tuple[list[dict], dict]:
    info: dict = {"packs_used": [], "packs_skipped": [], "rows_by_pack": {}}
    tree = fetch_json("https://api.github.com/repos/graphsense/graphsense-tagpacks/contents/packs?ref=master")
    all_rows: list[dict] = []
    for item in tree:
        if item.get("type") != "file":
            info["packs_skipped"].append(f"{item.get('name')}: not a file")
            continue
        name = item.get("name") or ""
        lname = name.lower()
        if not lname.endswith((".yaml", ".yml")):
            info["packs_skipped"].append(f"{name}: not yaml")
            continue
        if any(lname.startswith(p) for p in SKIP_GS_PREFIX) or name in SKIP_GS_NAMES:
            info["packs_skipped"].append(f"{name}: excluded by pack rules")
            continue
        size = int(item.get("size") or 0)
        if size > 400000:
            info["packs_skipped"].append(f"{name}: too large ({size} bytes) unlabeled-risk dump")
            continue
        url = item.get("download_url")
        dest = WORK / "gs" / name
        print(f"  GraphSense {name} ({size} bytes)")
        try:
            fetch(url, dest, timeout=60)
        except Exception as e:
            info["packs_skipped"].append(f"{name}: download failed ({e})")
            continue
        rows = parse_tagpack(dest)
        if not rows:
            info["packs_skipped"].append(f"{name}: no ETH tags with a citable source URL")
            continue
        uniq = {}
        for r in rows:
            uniq[r["address"]] = r
        rows = list(uniq.values())
        info["packs_used"].append({"name": name, "eth_rows": len(rows), "size": size})
        info["rows_by_pack"][name] = len(rows)
        all_rows.extend(rows)
        print(f"    kept {len(rows)}")
    return all_rows, info


def pull_tokenlist() -> tuple[list[dict], dict]:
    info: dict = {"picked": [], "skipped_reason": "list is large; only well-known tokens + official routers"}
    dest = WORK / "uniswap-default-token-list.json"
    print("Downloading Uniswap default token list...")
    fetch(TOKENLIST_URL, dest, timeout=60)
    data = json.loads(dest.read_text(encoding="utf-8"))
    tokens = data.get("tokens") or []
    picked = []
    seen_sym = set()
    for t in tokens:
        if int(t.get("chainId") or 0) != 1:
            continue
        sym = str(t.get("symbol") or "").upper()
        addr = str(t.get("address") or "")
        if sym not in WELL_KNOWN_TOKENS or not is_eth(addr):
            continue
        if sym in seen_sym:
            continue
        seen_sym.add(sym)
        name = WELL_KNOWN_TOKENS[sym]
        picked.append(row(addr, name, "protocol", "Uniswap default token list", TOKENLIST_URL))
        info["picked"].append({"symbol": sym, "address": norm_addr(addr)})
    picked.append(row(UNISWAP_V3_ROUTER[0], UNISWAP_V3_ROUTER[1], "protocol", "Uniswap V3 deployments", UNISWAP_V3_DOCS))
    info["picked"].append({"symbol": "UNI-V3-ROUTER", "address": UNISWAP_V3_ROUTER[0]})
    picked.append(row(UNISWAP_V3_ROUTER02[0], UNISWAP_V3_ROUTER02[1], "protocol", "Uniswap V3 deployments", UNISWAP_V3_DOCS))
    info["picked"].append({"symbol": "UNI-V3-ROUTER02", "address": UNISWAP_V3_ROUTER02[0]})
    picked.append(row(UNISWAP_V2_ROUTER[0], UNISWAP_V2_ROUTER[1], "protocol", "Uniswap V2 deployments", UNISWAP_V2_DOCS))
    info["picked"].append({"symbol": "UNI-V2-ROUTER02", "address": UNISWAP_V2_ROUTER[0]})
    picked.append(row(UNISWAP_PERMIT2[0], UNISWAP_PERMIT2[1], "protocol", "Uniswap Permit2", UNISWAP_PERMIT2_DOCS))
    info["picked"].append({"symbol": "PERMIT2", "address": UNISWAP_PERMIT2[0]})
    picked.append(row(AAVE_V3_POOL[0], AAVE_V3_POOL[1], "protocol", "Aave V3 deployments", AAVE_V3_DOCS))
    info["picked"].append({"symbol": "AAVE-V3-POOL", "address": AAVE_V3_POOL[0]})
    picked.append(row(LIDO_STETH[0], LIDO_STETH[1], "protocol", "Lido deployments", LIDO_DOCS))
    info["picked"].append({"symbol": "STETH", "address": LIDO_STETH[0]})
    picked.append(row(LIDO_WSTETH[0], LIDO_WSTETH[1], "protocol", "Lido deployments", LIDO_DOCS))
    info["picked"].append({"symbol": "WSTETH", "address": LIDO_WSTETH[0]})
    for addr, name in SEAPORT_VERSIONS:
        picked.append(row(addr, name, "protocol", "OpenSea Seaport", SEAPORT_README))
        info["picked"].append({"symbol": name, "address": addr})

    ur_dest = WORK / "uniswap-universal-router-mainnet.json"
    print("Downloading Uniswap Universal Router mainnet deployments...")
    try:
        fetch(UNISWAP_UR_JSON, ur_dest, timeout=60)
        ur = json.loads(ur_dest.read_text(encoding="utf-8"))
        for key, addr in ur.items():
            if not str(key).startswith("UniversalRouter"):
                continue
            if not is_eth(str(addr)):
                continue
            label = UNISWAP_UR_LABELS.get(str(key), "Uniswap " + str(key).replace("_", " "))
            picked.append(row(str(addr), label, "protocol", "Uniswap Universal Router deployments", UNISWAP_UR_JSON))
            info["picked"].append({"symbol": key, "address": str(addr)})
    except Exception as e:
        info["skipped_reason"] = f"{info.get('skipped_reason')}; Universal Router JSON failed ({e})"

    info["tokenlist_count"] = len(tokens)
    return picked, info


def write_csv(rows: list[dict]) -> None:
    fields = ["chain", "address", "name", "category", "secondary_category", "source", "source_url"]
    with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def write_sources_md(
    existing_n: int,
    merged: list[dict],
    os_info: dict,
    gs_info: dict,
    tl_info: dict,
    ofac_info: dict,
    fbi_info: dict,
) -> None:
    by_cat = Counter(r["category"] for r in merged)
    by_src = Counter(r["source"] for r in merged)
    os_n = sum(os_info.get("rows_by_dataset", {}).values())
    gs_n = sum(gs_info.get("rows_by_pack", {}).values())
    tl_n = len(tl_info.get("picked") or [])
    fbi_n = sum(int(r.get("eth_rows") or 0) for r in (fbi_info.get("releases") or []))
    ofac_n = int(ofac_info.get("unique_eth_format") or 0)
    ofac_pub = ofac_info.get("publish_date") or "unknown"
    lines = [
        "# Rensic public known-entity pack",
        "",
        f"Pulled: {date.today().isoformat()}. OFAC SDN XML + FBI/IC3 + OpenSanctions / GraphSense / official protocol docs.",
        "",
        "## What we used",
        "",
        "1. OFAC Specially Designated Nationals (SDN) list, official XML export",
        "   (`sdn.xml` from treasury.gov OFAC downloads; same `Digital Currency Address - ETH`",
        "   identifiers as `sdn_advanced.xml` on sanctionslist.ofac.treas.gov).",
        f"   Publication date in the file: {ofac_pub}.",
        "   Extracted ETH, plus ETH-format 0x USDC/USDT identifiers that are not already",
        "   in the ETH set. Each sanctions row cites OFAC (`https://sanctionslist.ofac.treas.gov/Home/SdnList`), not an explorer.",
        "   A practical advanced-XML extractor is",
        "   https://github.com/0xB10C/ofac-sanctioned-digital-currency-addresses",
        "   (this pack parsed the official SDN XML directly so Spark does not download",
        "   the ~100MB advanced file at build time). The CSV in this folder is the",
        "   snapshot the Foundry transform reads.",
        "",
        "2. Tornado Cash mixer contracts from OFAC's own notices:",
        "   designation 2022-08-08 (https://ofac.treasury.gov/recent-actions/20220808), redesignation 2022-11-08,",
        "   and the 2025-03-21 deletion notice (complete ETH identifier list).",
        "   Treasury removed Tornado Cash from the SDN list on 2025-03-21, so those",
        "   contracts are category `mixer` here, not current sanctions. Roman Semenov",
        "   ETH identifiers remain on the current SDN extract as `sanctions`.",
        "",
        "3. Tiny public demo names (not Etherscan nametags, not exchange hot-wallet dumps):",
        "   - Vitalik Buterin `0xd8da6bf26964af9d7eed9e03e53415d37aa96045` (`person`) cited from https://vitalik.ca",
        "   - WETH `0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2` (`protocol`) cited from https://github.com/gnosis/canonical-weth",
        "",
        "4. FBI / IC3 official press and PSAs (ETH 0x only; category `sanctions` as FBI-attributed",
        "   actor wallets, same rule as the existing OpenSanctions FBI Lazarus pack).",
    ]
    for rel in fbi_info.get("releases") or []:
        lines.append(f"   - {rel['name']}: {rel.get('eth_rows', 0)} ETH (`{rel.get('url')}`)")
    lines.extend(
        [
            "",
            "5. OpenSanctions official-origin CryptoWallet datasets (bulk JSON, no API key).",
            "   Catalog: https://data.opensanctions.org/datasets/latest/index.json",
            "   Kept schema `CryptoWallet` with ETH-format `0x` + 40 hex only.",
            "   Category is `sanctions` when topics include sanction, and for IL MOD / FBI lists.",
            "   Each row cites the OpenSanctions dataset page AND the original publisher.",
            "   OpenSanctions bulk data is free for non-commercial use; commercial use needs a license",
            "   (https://www.opensanctions.org/docs/bulk/updates/).",
        ]
    )
    for ds in os_info.get("datasets") or []:
        lines.append(f"   - `{ds['name']}` ({ds.get('title')}): {ds.get('eth_rows', 0)} ETH-format wallets")
    lines.extend(
        [
            "",
            "6. GraphSense public TagPacks (MIT), https://github.com/graphsense/graphsense-tagpacks",
            "   ETH/ETH-format tags WITH a source URL. Prefer government, project docs, or",
            "   company announcements. Skip tags with no source. Map mixing_service -> mixer,",
            "   gambling -> gambling, exchange -> exchange, shop/marketplace -> shop,",
            "   defi/dex -> protocol; skip unlabeled junk.",
        ]
    )
    for p in gs_info.get("packs_used") or []:
        lines.append(f"   - {p['name']}: {p['eth_rows']} ETH tags")
    lines.extend(
        [
            "",
            "7. Small official protocol pack: Uniswap default token list (`https://tokens.uniswap.org`),",
            "   Uniswap V2/V3/Universal Router/Permit2 deployment docs, Aave V3, Lido stETH/wstETH,",
            "   and OpenSea Seaport canonical addresses. WETH already present. Not a DeFi internals dump.",
        ]
    )
    for p in tl_info.get("picked") or []:
        lines.append(f"   - {p['symbol']}: `{p['address']}`")
    lines.extend(
        [
            "",
            "## Merge rules",
            "",
            "Dedupe on chain+address. Conflict precedence: existing OFAC sanctions > new sanctions",
            "> mixer > gambling > exchange > shop > protocol > person. Keep source/source_url of the winning row.",
            "",
            "## Counts in this snapshot",
            "",
        ]
    )
    for cat in ("sanctions", "mixer", "gambling", "exchange", "shop", "protocol", "person"):
        lines.append(f"- {cat}: {by_cat.get(cat, 0)}")
    lines.append(f"- total rows: {len(merged)} (was {existing_n} before this expansion)")
    lines.extend(["", "### By source (winning rows after dedupe)", ""])
    for src, n in sorted(by_src.items(), key=lambda kv: (-kv[1], kv[0])):
        lines.append(f"- {src}: {n}")
    lines.extend(
        [
            "",
            "## New-row intake (before dedupe)",
            "",
            f"- OFAC SDN ETH-format IDs pulled: {ofac_n} (publish {ofac_pub})",
            f"- FBI / IC3 ETH wallets pulled: {fbi_n}",
            f"- OpenSanctions ETH wallets pulled: {os_n}",
            f"- GraphSense ETH tags pulled: {gs_n}",
            f"- Tokenlist / official protocol rows: {tl_n}",
            "",
            "## Sources skipped",
            "",
            "- Etherscan nametags, Arkham, Chainalysis, dawsbot/eth-labels: pack rules.",
            "- GraphSense etherscan-* and exchange-wallets-* packs: explorer nametags / rotating unlabeled hot wallets.",
            "- GraphSense defi-protocols-csh.yaml: arxiv research dump of hundreds of internal DeFi contracts; protocol coverage comes from the official tokenlist instead.",
            "- GraphSense miners / ransomware / sextortion / walletexplorer / eosio-gambling: unlabeled, BTC-heavy, or wrong chain.",
            "- GraphSense ronin_bridge.yaml: hack/exploiter wallets are not mixer/exchange/protocol taxonomy; skipped rather than mislabeled.",
            "- OpenSanctions us_ofac_sdn: already ingested from official SDN XML.",
            "- OpenSanctions gb_fcdo_sanctions: UK FCDO free-text parse excluded.",
            "- OpenSanctions ransomwhere: non-official publisher.",
            "- OpenSanctions FBI Lazarus BSC/Polygon 0x wallets skipped: this pack stores ETH chain only.",
            "- BTC/TRON addresses: this CSV does not store a non-ETH chain column for those networks.",
        ]
    )
    for s in fbi_info.get("skipped") or []:
        lines.append(f"- FBI: {s}")
    for s in os_info.get("skipped") or []:
        lines.append(f"- OpenSanctions catalog: {s}")
    for s in gs_info.get("packs_skipped") or []:
        lines.append(f"- GraphSense: {s}")
    lines.extend(
        [
            "",
            "## OFAC is not exhaustive",
            "",
            "This is a screening aid for the Rensic demo desk, not a complete sanctions",
            "or mixer universe. OFAC updates the SDN list; other regimes, private lists,",
            "and unpublished wallets are absent. Do not treat a missing label as a",
            "clearance. Re-pull from the official sources above to refresh.",
            "",
        ]
    )
    SOURCES_MD.write_text("\n".join(lines), encoding="utf-8")


TS_HELPERS = r"""
const BY_HEX: Record<string, KnownEntity> = {};
for (const row of KNOWN_ENTITIES) {
  BY_HEX[row.address.toLowerCase()] = row;
}

export function hexOf(id: string | undefined): string {
  if (!id) {
    return "";
  }
  const parts = id.trim().toLowerCase().split(":");
  return parts[parts.length - 1] ?? "";
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
"""


def write_ts(rows: list[dict]) -> None:
    cats_present = {r["category"] for r in rows}
    extra = [c for c in ("gambling", "shop") if c in cats_present]
    union = '"sanctions" | "mixer" | "exchange" | "protocol" | "person"'
    if extra:
        union = '"sanctions" | "mixer" | "exchange" | "protocol" | "person" | "gambling" | "shop"'
    parts = [
        f"export type EntityCategory = {union};",
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


def main() -> int:
    WORK.mkdir(parents=True, exist_ok=True)
    existing = load_existing()
    print(f"Existing rows: {len(existing)}")

    try:
        ofac_rows, ofac_info = pull_ofac_sdn()
        ofac_names = {
            r["address"]: r["name"]
            for r in existing
            if r.get("source") == "OFAC SDN" and r.get("name")
        }
        for r in ofac_rows:
            if r["address"] in ofac_names:
                r["name"] = ofac_names[r["address"]]
        existing_keep = [r for r in existing if r.get("source") != "OFAC SDN"]
    except Exception as e:
        print(f"OFAC SDN refresh failed, keeping existing OFAC rows: {e}")
        ofac_rows = [r for r in existing if r.get("source") == "OFAC SDN"]
        existing_keep = [r for r in existing if r.get("source") != "OFAC SDN"]
        ofac_info = {"unique_eth_format": len(ofac_rows), "publish_date": "unchanged", "error": str(e)}

    fbi_rows, fbi_info = pull_fbi()
    try:
        os_rows, os_info = pull_opensanctions()
    except Exception as e:
        print(f"OpenSanctions refresh failed, keeping existing rows: {e}")
        os_rows, os_info = [], {"datasets": [], "skipped": [str(e)], "rows_by_dataset": {}}
    try:
        gs_rows, gs_info = pull_graphsense()
    except Exception as e:
        print(f"GraphSense refresh failed, keeping existing rows: {e}")
        gs_rows, gs_info = [], {"packs_used": [], "packs_skipped": [str(e)], "rows_by_pack": {}}
    try:
        tl_rows, tl_info = pull_tokenlist()
    except Exception as e:
        print(f"Tokenlist/protocol refresh failed: {e}")
        raise

    merged, merge_info = merge_rows(
        [ofac_rows, fbi_rows, existing_keep, os_rows, gs_rows, tl_rows]
    )
    write_csv(merged)
    write_sources_md(len(existing), merged, os_info, gs_info, tl_info, ofac_info, fbi_info)
    write_ts(merged)

    by_cat = Counter(r["category"] for r in merged)
    by_src = Counter(r["source"] for r in merged)
    existing_keys = {(r["chain"], r["address"]) for r in existing}
    added = [r for r in merged if (r["chain"], r["address"]) not in existing_keys]
    added_by_src = Counter(r["source"] for r in added)
    added_by_cat = Counter(r["category"] for r in added)

    stats = {
        "existing": len(existing),
        "ofac_pulled": len(ofac_rows),
        "fbi_pulled": len(fbi_rows),
        "opensanctions_pulled": len(os_rows),
        "graphsense_pulled": len(gs_rows),
        "tokenlist_pulled": len(tl_rows),
        "merged_total": len(merged),
        "added": len(added),
        "by_category": dict(by_cat),
        "by_source": dict(by_src),
        "added_by_source": dict(added_by_src),
        "added_by_category": dict(added_by_cat),
        "ofac": ofac_info,
        "fbi": fbi_info,
        "opensanctions": os_info,
        "graphsense": gs_info,
        "tokenlist": tl_info,
        "merge": merge_info,
    }
    STATS_PATH.write_text(json.dumps(stats, indent=2), encoding="utf-8")
    summary = {
        k: stats[k]
        for k in (
            "existing",
            "ofac_pulled",
            "fbi_pulled",
            "opensanctions_pulled",
            "graphsense_pulled",
            "tokenlist_pulled",
            "merged_total",
            "added",
            "by_category",
            "added_by_source",
            "added_by_category",
        )
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
