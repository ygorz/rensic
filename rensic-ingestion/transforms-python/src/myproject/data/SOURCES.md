# Rensic public known-entity pack

## Dual-tier policy (summary)

- **official** — PoR, company blogs, deployment docs, OFAC, etc. Drives ledger title + sort.
- **community** — Etherscan nametags / similar community dumps. Shown with caveat; distinct desk style.
- Same address: official wins; community suppressed on conflict (not mixed into official).
- CSV column `tier` = `official` | `community`.

Pulled: 2026-09-01. OFAC SDN XML + FBI/IC3 + OpenSanctions / GraphSense / official protocol docs.

## What we used

1. OFAC Specially Designated Nationals (SDN) list, official XML export
   (`sdn.xml` from treasury.gov OFAC downloads; same `Digital Currency Address - ETH`
   identifiers as `sdn_advanced.xml` on sanctionslist.ofac.treas.gov).
   Publication date in the file: 08/28/2026.
   Extracted ETH, plus ETH-format 0x USDC/USDT identifiers that are not already
   in the ETH set. Each sanctions row cites OFAC (`https://sanctionslist.ofac.treas.gov/Home/SdnList`), not an explorer.
   A practical advanced-XML extractor is
   https://github.com/0xB10C/ofac-sanctioned-digital-currency-addresses
   (this pack parsed the official SDN XML directly so Spark does not download
   the ~100MB advanced file at build time). The CSV in this folder is the
   snapshot the Foundry transform reads.

2. Tornado Cash mixer contracts from OFAC's own notices:
   designation 2022-08-08 (https://ofac.treasury.gov/recent-actions/20220808), redesignation 2022-11-08,
   and the 2025-03-21 deletion notice (complete ETH identifier list).
   Treasury removed Tornado Cash from the SDN list on 2025-03-21, so those
   contracts are category `mixer` here, not current sanctions. Roman Semenov
   ETH identifiers remain on the current SDN extract as `sanctions`.

3. Tiny public demo names (not Etherscan nametags, not exchange hot-wallet dumps):
   - Vitalik Buterin `0xd8da6bf26964af9d7eed9e03e53415d37aa96045` (`person`) cited from https://vitalik.ca
   - WETH `0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2` (`protocol`) cited from https://github.com/gnosis/canonical-weth

4. FBI / IC3 official press and PSAs (ETH 0x only; category `sanctions` as FBI-attributed
   actor wallets, same rule as the existing OpenSanctions FBI Lazarus pack).
   - Bybit 2025 / TraderTraitor: 51 ETH (`https://www.ic3.gov/psa/2025/psa250226`)
   - Stake.com 2023: 4 ETH (`https://www.fbi.gov/news/press-releases/fbi-identifies-lazarus-group-cyber-actors-as-responsible-for-theft-of-41-million-from-stakecom`)

5. OpenSanctions official-origin CryptoWallet datasets (bulk JSON, no API key).
   Catalog: https://data.opensanctions.org/datasets/latest/index.json
   Kept schema `CryptoWallet` with ETH-format `0x` + 40 hex only.
   Category is `sanctions` when topics include sanction, and for IL MOD / FBI lists.
   Each row cites the OpenSanctions dataset page AND the original publisher.
   OpenSanctions bulk data is free for non-commercial use; commercial use needs a license
   (https://www.opensanctions.org/docs/bulk/updates/).
   - `us_fbi_lazarus_crypto` (US FBI Lazarus Group Crypto Wallets): 4 ETH-format wallets
   - `il_mod_crypto` (Israel Sanctioned Crypto Wallets List): 12 ETH-format wallets

6. GraphSense public TagPacks (MIT), https://github.com/graphsense/graphsense-tagpacks
   ETH/ETH-format tags WITH a source URL. Prefer government, project docs, or
   company announcements. Skip tags with no source. Map mixing_service -> mixer,
   gambling -> gambling, exchange -> exchange, shop/marketplace -> shop,
   defi/dex -> protocol; skip unlabeled junk.
   - interpol-real_services.yaml: 3 ETH tags
   - lazarus.yaml: 1 ETH tags
   - tornado_cash.yaml: 38 ETH tags

7. Small official protocol pack: Uniswap default token list (`https://tokens.uniswap.org`),
   Uniswap V2/V3/Universal Router/Permit2 deployment docs, Aave V3, Lido stETH/wstETH,
   and OpenSea Seaport canonical addresses. WETH already present. Not a DeFi internals dump.
   - AAVE: `0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9`
   - USDC: `0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48`
   - USDT: `0xdac17f958d2ee523a2206206994597c13d831ec7`
   - UNI-V3-ROUTER: `0xe592427a0aece92de3edee1f18e0157c05861564`
   - UNI-V3-ROUTER02: `0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45`
   - UNI-V2-ROUTER02: `0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D`
   - PERMIT2: `0x000000000022D473030F116dDEE9F6B43aC78BA3`
   - AAVE-V3-POOL: `0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2`
   - STETH: `0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84`
   - WSTETH: `0x7f39C581F595B53c5cb19bD0b3f8dA6c935E2Ca0`
   - OpenSea Seaport 1.1: `0x00000000006c3852cbEf3e08E8dF289169EdE581`
   - OpenSea Seaport 1.5: `0x00000000000000ADc04C56Bf30aC9d3c0aAF14dC`
   - OpenSea Seaport 1.6: `0x0000000000000068F116a894984e2DB1123eB395`
   - UniversalRouterV1: `0xEf1c6E67703c7BD7107eed8303Fbe6EC2554BF6B`
   - UniversalRouterV1_2_V2Support: `0x3fC91A3afd70395Cd496C647d5a6CC9D4B2b7FAD`
   - UniversalRouterV2: `0x66a9893cc07d91d95644aedd05d03f95e1dba8af`
   - UniversalRouterV2_1_1: `0x4C82D1fBFe28C977cBB58D8C7FF8FCF9F70a2cCA`

## Merge rules

Dedupe on chain+address. Conflict precedence: existing OFAC sanctions > new sanctions
> mixer > gambling > exchange > shop > protocol > person. Keep source/source_url of the winning row.

## Counts in this snapshot

- sanctions: 192
- mixer: 94
- gambling: 0
- exchange: 0
- shop: 0
- protocol: 18
- person: 1
- total rows: 305 (was 242 before this expansion)

### By source (winning rows after dedupe)

- OFAC SDN: 124
- OFAC: 91
- FBI / IC3: 51
- OpenSanctions / NBCTF: 13
- FBI: 4
- Uniswap Universal Router deployments: 4
- GraphSense TagPack / INTERPOL TagPack: 3
- OpenSea Seaport: 3
- Uniswap default token list: 3
- Lido deployments: 2
- Uniswap V3 deployments: 2
- public: 2
- Aave V3 deployments: 1
- Uniswap Permit2: 1
- Uniswap V2 deployments: 1

## New-row intake (before dedupe)

- OFAC SDN ETH-format IDs pulled: 124 (publish 08/28/2026)
- FBI / IC3 ETH wallets pulled: 55
- OpenSanctions ETH wallets pulled: 16
- GraphSense ETH tags pulled: 42
- Tokenlist / official protocol rows: 17

## Sources skipped

- Etherscan nametags (historical note): originally skipped from the official lane; community-lane Etherscan labels were added 2026-09-03 (see Dual-tier section). Arkham / Chainalysis / unlabeled dumps still skipped.
- GraphSense etherscan-* and exchange-wallets-* packs: explorer nametags / rotating unlabeled hot wallets.
- GraphSense defi-protocols-csh.yaml: arxiv research dump of hundreds of internal DeFi contracts; protocol coverage comes from the official tokenlist instead.
- GraphSense miners / ransomware / sextortion / walletexplorer / eosio-gambling: unlabeled, BTC-heavy, or wrong chain.
- GraphSense ronin_bridge.yaml: hack/exploiter wallets are not mixer/exchange/protocol taxonomy; skipped rather than mislabeled.
- OpenSanctions us_ofac_sdn: already ingested from official SDN XML.
- OpenSanctions gb_fcdo_sanctions: UK FCDO free-text parse excluded.
- OpenSanctions ransomwhere: non-official publisher.
- OpenSanctions FBI Lazarus BSC/Polygon 0x wallets skipped: this pack stores ETH chain only.
- BTC/TRON addresses: this CSV does not store a non-ETH chain column for those networks.
- FBI: Harmony Horizon (https://www.fbi.gov/news/press-releases/fbi-confirms-lazarus-group-cyber-actors-responsible-for-harmonys-horizon-bridge-currency-theft): FBI press lists Bitcoin addresses only; no ETH IDs
- FBI: DMM Bitcoin (https://www.fbi.gov/news/press-releases/fbi-dc3-and-npa-identification-of-north-korean-cyber-actors-tracked-as-tradertraitor-responsible-for-theft-of-308-million-from-bitcoindmmcom): FBI press is a BTC theft; no ETH IDs published
- GraphSense: Alt-Right.yaml: excluded by pack rules
- GraphSense: BITB_etf.yaml: no ETH tags with a citable source URL
- GraphSense: africrypt-hack.yaml: no ETH tags with a citable source URL
- GraphSense: aft-alqaeda-forfeit_vc.yaml: no ETH tags with a citable source URL
- GraphSense: binance.yaml: no ETH tags with a citable source URL
- GraphSense: binance_hack.yaml: no ETH tags with a citable source URL
- GraphSense: bitzillions_ltc.yaml: no ETH tags with a citable source URL
- GraphSense: blender_io.yaml: no ETH tags with a citable source URL
- GraphSense: chaininfo.yaml: no ETH tags with a citable source URL
- GraphSense: coinjoin_bounty.yaml: no ETH tags with a citable source URL
- GraphSense: defi-fraud-masterthesis.yaml: excluded by pack rules
- GraphSense: defi-protocols-csh.yaml: excluded by pack rules
- GraphSense: defi_updated: not a file
- GraphSense: demo.yaml: excluded by pack rules
- GraphSense: electrum_phishing.yaml: no ETH tags with a citable source URL
- GraphSense: eosio-gambling_part1.yaml: excluded by pack rules
- GraphSense: eosio-gambling_part2.yaml: excluded by pack rules
- GraphSense: eosio-gambling_part3.yaml: excluded by pack rules
- GraphSense: eosio-gambling_part4.yaml: excluded by pack rules
- GraphSense: eosio-gambling_part5.yaml: excluded by pack rules
- GraphSense: eosio-gambling_part6.yaml: excluded by pack rules
- GraphSense: eosio-gambling_part7.yaml: excluded by pack rules
- GraphSense: eosio-gambling_part8.yaml: excluded by pack rules
- GraphSense: eosio-gambling_part9.yaml: excluded by pack rules
- GraphSense: etherhiding.yaml: no ETH tags with a citable source URL
- GraphSense: etherscamdb_tagpack.yaml: too large (465249 bytes) unlabeled-risk dump
- GraphSense: etherscan-label-word-cloud.yaml: excluded by pack rules
- GraphSense: etherscan-wordcloud-exchange.yaml: excluded by pack rules
- GraphSense: etherscan-wordcloud-gambling.yaml: excluded by pack rules
- GraphSense: etherscan-wordcloud-market.yaml: excluded by pack rules
- GraphSense: etherscan-wordcloud-miner.yaml: excluded by pack rules
- GraphSense: etherscan-wordcloud-mixing_service.yaml: excluded by pack rules
- GraphSense: exchange-wallets-binance.yaml: excluded by pack rules
- GraphSense: exchange-wallets-bitfinexcom.yaml: excluded by pack rules
- GraphSense: exchange-wallets-bitmex_0.yaml: excluded by pack rules
- GraphSense: exchange-wallets-bitmex_1.yaml: excluded by pack rules
- GraphSense: exchange-wallets-bitmex_2.yaml: excluded by pack rules
- GraphSense: exchange-wallets-bitmex_3.yaml: excluded by pack rules
- GraphSense: exchange-wallets-bitmex_4.yaml: excluded by pack rules
- GraphSense: exchange-wallets-bitmex_5.yaml: excluded by pack rules
- GraphSense: exchange-wallets-bitmex_6.yaml: excluded by pack rules
- GraphSense: exchange-wallets-bybit.yaml: excluded by pack rules
- GraphSense: exchange-wallets-cryptocom.yaml: excluded by pack rules
- GraphSense: exchange-wallets-deribit.yaml: excluded by pack rules
- GraphSense: exchange-wallets-huobi.yaml: excluded by pack rules
- GraphSense: exchange-wallets-kucoin.yaml: excluded by pack rules
- GraphSense: exchange-wallets-okx.yaml: excluded by pack rules
- GraphSense: exchange-wallets-swissborg.yaml: excluded by pack rules
- GraphSense: forsage.yaml: no ETH tags with a citable source URL
- GraphSense: hacks.yaml: no ETH tags with a citable source URL
- GraphSense: hydra.yaml: no ETH tags with a citable source URL
- GraphSense: lazarus2.yaml: no ETH tags with a citable source URL
- GraphSense: lockbit_tattoos.yaml: no ETH tags with a citable source URL
- GraphSense: miners.yaml: excluded by pack rules
- GraphSense: miners_additional.yaml: excluded by pack rules
- GraphSense: mixing_fc2021.yaml: no ETH tags with a citable source URL
- GraphSense: ofac.yaml: excluded by pack rules
- GraphSense: plustoken.yaml: no ETH tags with a citable source URL
- GraphSense: ponzi_scheme.yaml: no ETH tags with a citable source URL
- GraphSense: protonmail.yaml: no ETH tags with a citable source URL
- GraphSense: ransomware.yaml: excluded by pack rules
- GraphSense: ransomwhere.yaml: excluded by pack rules
- GraphSense: richest_addresses.yaml: no ETH tags with a citable source URL
- GraphSense: ronin_bridge.yaml: excluded by pack rules
- GraphSense: samourai.yaml: excluded by pack rules
- GraphSense: satoshidice_bch.yaml: no ETH tags with a citable source URL
- GraphSense: service-wallets-checksig.yaml: no ETH tags with a citable source URL
- GraphSense: sextortion_excello.yaml: excluded by pack rules
- GraphSense: sextortion_talos.yaml: excluded by pack rules
- GraphSense: sinbad_io.yaml: no ETH tags with a citable source URL
- GraphSense: suidlanders.yaml: no ETH tags with a citable source URL
- GraphSense: twitter_hack_scam.yaml: no ETH tags with a citable source URL
- GraphSense: usdt_blacklist.yaml: no ETH tags with a citable source URL
- GraphSense: walletexplorer.yaml: excluded by pack rules
- GraphSense: wasabi_collector.yaml: no ETH tags with a citable source URL

## OFAC is not exhaustive

This is a screening aid for the Rensic demo desk, not a complete sanctions
or mixer universe. OFAC updates the SDN list; other regimes, private lists,
and unpublished wallets are absent. Do not treat a missing label as a
clearance. Re-pull from the official sources above to refresh.


## Expansion pull: 2026-09-03 (exchanges + protocols)

Goal: add meaningful exchange and protocol names for the desk using OFFICIAL citations only.

### Sources used

1. Bitfinex published wallets (`https://github.com/bitfinexcom/pub/blob/main/wallets.txt`): 4 ETH/ERC20 rows.
2. Binance transparency blog (`https://www.binance.com/en/blog/community/our-commitment-to-transparency-2895840147147652626`) cross-checked with Mazars PoR PDF (`https://public.bnbstatic.com/static/proof-of-reserve/Binance-POR-Report-7-December-2022-1.pdf`): 9 ETH rows (Small verified subset from Binance transparency blog + Mazars PoR PDF ETH list).
3. OKX Proof of Reserves download (`https://www.okx.com/proof-of-reserves/download`), ETH staking snapshot inside `https://static.okx.com/cdn/okx/por/chain/por_csv_2026070700_V3.zip`: 12 rows (5 deposit + unique withdrawals). OKX reserves zip coin totals lack per-address lists; used ETH staking snapshot addresses only.
4. Compound Comet mainnet deployments (`https://github.com/compound-finance/comet/tree/main/deployments/mainnet`).
5. Aave V3 Ethereum address book (`https://github.com/bgd-labs/aave-address-book`).
6. MakerDAO / Sky docs for DAI, MKR, SKY.
7. Curve Finance docs for 3pool / CRV / crvUSD.

### Merge

- Incoming added: 43
- Precedence replaces: 0
- Total rows now: 348

### Counts after this pull

- sanctions: 192
- mixer: 94
- exchange: 25
- protocol: 36
- person: 1

Exchange names (row counts): {'Binance': 8, 'Binance Cold': 1, 'Bitfinex': 4, 'OKX': 12}
Protocol names (sample): {'Aave': 1, 'Aave Collector': 1, 'Aave Protocol Data Provider': 1, 'Aave UI Pool Data Provider': 1, 'Aave V3 ACL Manager': 1, 'Aave V3 Oracle': 1, 'Aave V3 Pool': 1, 'Aave V3 Pool Addresses Provider': 1, 'CRV': 1, 'Compound V2 Comptroller': 1, 'Compound V3 Bulker': 1, 'Compound V3 Rewards': 1, 'Compound V3 USDC': 1, 'Compound V3 USDT': 1, 'Compound V3 WETH': 1, 'Curve 3pool': 1, 'DAI': 1, 'Lido stETH': 1, 'Lido wstETH': 1, 'MKR': 1, 'OpenSea Seaport 1.1': 1, 'OpenSea Seaport 1.5': 1, 'OpenSea Seaport 1.6': 1, 'SKY': 1, 'Tether USD': 1, 'USD Coin': 1, 'Uniswap Permit2': 1, 'Uniswap Universal Router V1': 1, 'Uniswap Universal Router V1.2': 1, 'Uniswap Universal Router V2': 1}

### Skipped targets

- Coinbase: No company-published public ETH address list found; PoR/transparency does not expose a citable address CSV. Etherscan/hildobby nametags excluded by pack rules.
- Kraken: Official PoR uses Merkle proofs without a public on-chain address list.
- Bybit: No official public ETH address list; GraphSense exchange-wallets-bybit excluded (unlabeled rotating hot wallets).
- KuCoin: No official public ETH address list; GraphSense exchange-wallets-kucoin excluded.
- Gemini: No current company-published ETH cold/hot address list suitable for citation.
- Bitstamp: No current company-published ETH address list found.
- Crypto.com: PoR page points wallet holdings to Nansen; not a primary company address attestation file.
- Robinhood: No published crypto deposit address list for ETH found.
- Gate.io: PoR is Merkle/zk oriented without a simple public ETH address CSV.
- OKX full reserve address dump: Latest reserves zip publishes coin totals + ETH staking validators; full signed wallet-address CSV URL not available without account UI. Took ETH staking deposit/withdrawal subset only.
- Binance rotating hot wallets beyond disclosed set: Took small verified subset from transparency blog + Mazars PoR ETH list; did not ingest unlabeled GraphSense dumps.


## Expansion pull: 2026-09-03 (Bybit/KuCoin + DeFi protocols)

Goal: more official exchange + protocol ETH labels. No Etherscan nametags, Arkham, Chainalysis, or unlabeled GraphSense exchange dumps.

### Sources used (worked)

1. Bybit Hacken PoR PDF (`https://www.bybit.com/common-static/cht-static/por/Bybit_PoR_Audit_2025_Oct_22.pdf`): 79 Ethereum audited wallets.
2. KuCoin transparency blog (`https://www.kucoin.com/blog/transparency-and-trust-a-detailed-list-of-kucoin-s-wallets-vi`): 15 unique ETH-format wallets from the published table.
3. Coinbase cbETH (`https://www.coinbase.com/cbeth`) + cbBTC PoR (`https://www.coinbase.com/cbbtc/proof-of-reserves`): 2 protocol token contracts (not CEX hot wallets).
4. Morpho docs address book (`https://docs.morpho.org/developers/contracts/addresses/`): Morpho Blue + IRM + factory + token + Bundler3.
5. EigenLayer mainnet config (`https://github.com/Layr-Labs/eigenlayer-contracts/blob/main/script/configs/mainnet.json`): DelegationManager, StrategyManager, EigenPodManager, RewardsCoordinator, AVSDirectory, EIGEN.
6. Spark address registry (`https://github.com/sparkdotfi/spark-address-registry/blob/ad50b14f/src/Ethereum.sol`): SparkLend Pool + provider + configurator + ACL + oracle + gateway + data provider + treasury; also Ethena USDe/sUSDe/Minter, Rocket Pool rETH, ether.fi weETH.
7. Pendle V2 deployments (`https://github.com/pendle-finance/pendle-core-v2-public/blob/main/deployments/1-core.json`): Router, PENDLE, Market Factory V3, oracle, treasury.

### Merge

- Incoming unique: 126
- Newly added: 126
- Precedence replaces: 0
- Total rows now: 474 (was 348)

### Counts after this pull

- sanctions: 192
- mixer: 94
- gambling: 0
- exchange: 119
- shop: 0
- protocol: 68
- person: 1

Exchange names (row counts): {'Binance': 8, 'Binance Cold': 1, 'Bitfinex (cold)': 2, 'Bitfinex (hot)': 2, 'Bybit': 79, 'KuCoin': 15, 'OKX (ETH staking deposit)': 5, 'OKX (ETH staking withdrawal)': 7}
New venue adds this pull: {'Bybit': 79, 'KuCoin': 15, 'Coinbase cbETH': 1, 'Coinbase cbBTC': 1, 'Morpho Blue': 1, 'Morpho Adaptive Curve IRM': 1, 'Morpho ChainlinkOracleV2 Factory': 1, 'MORPHO': 1, 'Morpho MetaMorpho Factory V1.1': 1, 'Morpho Bundler3': 1, 'EigenLayer DelegationManager': 1, 'EigenLayer StrategyManager': 1, 'EigenLayer EigenPodManager': 1, 'EigenLayer RewardsCoordinator': 1, 'EigenLayer AVSDirectory': 1, 'EIGEN': 1, 'SparkLend Pool': 1, 'SparkLend PoolAddressesProvider': 1, 'SparkLend PoolConfigurator': 1, 'SparkLend ACL Manager': 1, 'SparkLend Oracle': 1, 'SparkLend WETH Gateway': 1, 'SparkLend Protocol Data Provider': 1, 'SparkLend Treasury': 1, 'USDe': 1, 'sUSDe': 1, 'Ethena Minting': 1, 'Pendle Router': 1, 'PENDLE': 1, 'Pendle Market Factory V3': 1, 'Pendle PY YT LP Oracle': 1, 'Pendle Treasury': 1, 'Rocket Pool rETH': 1, 'ether.fi weETH': 1}

### Still skipped / impossible with pack rules

- Coinbase exchange hot/cold wallets: company publishes wrapped-asset contracts (cbETH/cbBTC) and BTC reserve addresses for cbBTC, not a public ETH CEX wallet CSV. Added protocol tokens only.
- Kraken: Merkle PoR without a public on-chain address list.
- Gemini: Trust Center / GUSD attestations do not publish a citable ETH exchange wallet list; GUSD contract not ingested without a non-explorer primary URL that prints the hex.
- Bitstamp, Robinhood, Crypto.com, Gate.io, HTX/Huobi, MEXC, Bitget: PoR is Merkle/zk or dashboard-only; no public ETH address attestation file suitable as primary citation.
- KuCoin current Hacken PoR PDFs: hosted behind bot-protection; used the 2022 company transparency blog list instead (official KuCoin URL).
- GraphSense exchange-wallets-* packs: still excluded (unlabeled rotating hot wallets).
- Etherscan nametag / labelcloud scrapes: pack rules.



## Dual-tier labels: 2026-09-03 (official vs community)

### Two-lane policy

1. **official** — PoR, company blogs, deployment docs, OFAC, FBI/IC3, OpenSanctions,
   GraphSense government/project packs, etc. Drives ledger title + sort + category.
   Investigator Flag MUST NOT overwrite official pack name/category in the UI.
2. **community** — Etherscan nametags / community label dumps (unofficial).
   Shown with caveat and a distinct desk chip style. Flag CAN override display for
   the case/user (investigator wins over community for display only; community stays in pack).
3. If both exist for the same address: **official wins** for title/sort/category.
   Community row is suppressed on conflict (not mixed into official).
4. Never call community labels "Coinbase official". Numbered names like "Coinbase 1"
   with `tier=community` are fine.

CSV column: `tier` = `official` | `community`. All pre-existing rows backfilled as `official`.

### Community sources used

1. George-listed Coinbase 1-11 ETH nametags; primary cite `https://etherscan.io/accounts/label/coinbase` (15 rows).
2. Additional major-CEX numbered Etherscan nametags via the MIT-licensed public mirror
   [`brianleect/etherscan-labels`](https://raw.githubusercontent.com/brianleect/etherscan-labels/master/data/etherscan/combined/combinedAllLabels.json) (combinedAllLabels.json).
   Each community row cites the matching Etherscan label page as `source_url`, not the mirror.
   Cap: well-known numbered exchange tags only (skip tokens/deployers/old/contracts);
   max 25 per venue.

Community label pages cited:
- Coinbase: `https://etherscan.io/accounts/label/coinbase` (15 rows)
- Binance: `https://etherscan.io/accounts/label/binance` (20 rows)
- Kraken: `https://etherscan.io/accounts/label/kraken` (14 rows)
- OKX: `https://etherscan.io/accounts/label/okx` (20 rows)
- Huobi: `https://etherscan.io/accounts/label/huobi` (25 rows)
- KuCoin: `https://etherscan.io/accounts/label/kucoin` (6 rows)
- Gemini: `https://etherscan.io/accounts/label/gemini` (7 rows)
- Bitfinex: `https://etherscan.io/accounts/label/bitfinex` (13 rows)
- Bitstamp: `https://etherscan.io/accounts/label/bitstamp` (6 rows)
- Gate.io: `https://etherscan.io/accounts/label/gate-io` (5 rows)
- Crypto.com: `https://etherscan.io/accounts/label/crypto-com` (5 rows)
- BitMEX: `https://etherscan.io/accounts/label/bitmex` (2 rows)
- Bittrex: `https://etherscan.io/accounts/label/bittrex` (3 rows)
- Poloniex: `https://etherscan.io/accounts/label/poloniex` (4 rows)

### Merge

- Existing before pull (all backfilled official): 474
- Incoming community unique: 161
- Newly added: 145
- Precedence replaces: 0
- Community suppressed by existing official: 16
- Total rows now: 619

### Counts after this pull

- official: 474
- community: 145
- Coinbase community: 15

- sanctions: 192
- mixer: 94
- gambling: 0
- exchange: 264
- shop: 0
- protocol: 68
- person: 1

Community exchange venues (row counts): {'Binance': 20, 'BitMEX': 2, 'Bitfinex': 13, 'Bitstamp': 6, 'Bittrex': 3, 'Coinbase': 15, 'Crypto.com': 5, 'Gate.io': 5, 'Gemini': 7, 'Huobi': 25, 'Kraken': 14, 'KuCoin': 6, 'OKX': 20, 'Poloniex': 4}
New community venue adds this pull: {'Coinbase': 15, 'Binance': 20, 'Kraken': 14, 'OKX': 20, 'Huobi': 25, 'KuCoin': 6, 'Gemini': 7, 'Bitfinex': 13, 'Bitstamp': 6, 'Gate.io': 5, 'Crypto.com': 5, 'BitMEX': 2, 'Bittrex': 3, 'Poloniex': 4}

### Still skipped

- Arkham: no static public page with clear address attribution used.
- Full Etherscan labelcloud dumps / millions of nametags: capped to numbered CEX tags.
- Direct etherscan.io HTML scrape: Cloudflare-blocked; used MIT mirror + label page cites.



## Community bulk expand: 2026-09-03

Prior community import was too thin (per-venue cap ~25 numbered CEX tags,
~145 community rows). George found Vitalik-case counterparty
`0xc013426d7cef8be3ef3b366151ed85e4fe33688c` labeled **Binance 15** on live Etherscan but missing from the pack
(2023 mirror had a different address as Binance 15; labels reassigned).

### Source

- MIT mirror [`brianleect/etherscan-labels`](https://github.com/brianleect/etherscan-labels)
  combined dump: `https://raw.githubusercontent.com/brianleect/etherscan-labels/main/data/etherscan/combined/combinedAllLabels.json`
- Pull date: 2026-09-03 (mirror ETH scrape stamped 18/6/2023; ~29945 accounts)
- Each community row cites the matching Etherscan label page (or address page)
  as `source_url`; `source` names Etherscan label / venue.
- Phishing labels skipped. Mega Sushi/Bancor/Synthetix/Rocket Pool/Balancer bulk
  omitted from PROTO_EXTRA (LP noise); category labels `dex`/`defi`/`bridge` kept when named.

### Forced / verified rows

- Binance 15: `0xc013426d7cef8be3ef3b366151ed85e4fe33688c` -> name `Binance 15`, category `exchange`,
  tier `community`, cite address page on Etherscan.
  Present after merge: **True** (Binance 15, community)
- Coinbase 1-11 forced name list retained.

### Selection (uncapped venues)

- ALL accounts under major CEX / fiat-gateway labels in the mirror
  (Binance, Coinbase, Kraken, OKX, Huobi, KuCoin, Gemini, Bitfinex, Bitstamp,
  Crypto.com, Gate.io, BitMEX, Bittrex, Poloniex, FTX, AscendEX, Nexo, BlockFi,
  plus regional CEXes present in the dump).
- High-value categories: tornado-cash / ethereum-mixer -> `mixer`;
  gambling -> `gambling`; bridge / dex / defi / protocol / stablecoin -> `protocol`;
  marketplace -> `shop`; ofac-sanctions-lists -> `sanctions` (community caveat).
- Named protocol ecosystems (Aave, Curve, Lido, Uniswap, ...): non-poolish names only.

### Dump pick counts (before official-wins merge)

- By mapped category: {'exchange': 524, 'protocol': 2163, 'mixer': 27, 'gambling': 147, 'sanctions': 42, 'shop': 144}
- By venue/label bucket (top): {'DEX': 233, 'Bridge': 188, 'Stablecoin': 169, 'Aave': 166, 'Gambling': 147, 'Protocol': 147, 'Marketplace': 144, 'Yearn': 141, 'KyberSwap': 122, 'DeFi': 121, 'Cream': 115, 'Huobi': 85, 'Set Protocol': 82, 'Lido': 82, 'Maker': 74, 'Idle': 67, 'Binance': 64, 'Zapper': 48, '0x': 45, 'Compound': 44, 'OFAC label (Etherscan)': 42, 'dYdX': 40, 'Index Protocol': 40, 'Bitfinex': 38, 'Alchemix': 38, 'ENS': 36, 'Tornado Cash': 26, 'Coinbase': 26, 'OKX': 26, 'Hop': 25, 'Coinsquare': 25, '1inch': 24, 'Fiat Gateway': 21, 'Crypto.com': 21, 'Convex': 21, 'KuCoin': 20, 'Poloniex': 20, 'Instadapp': 18, 'Bithumb': 18, 'Kraken': 18}

### Merge

- Before: total 619 (official 474, community 145)
- Incoming community unique: 3048
- Newly added: 2802
- Same-tier refreshes: 0
- Community suppressed by existing official: 101
- After: total 3421 (official 474, community 2947)
- Binance community rows (name startswith Binance): 54

### Counts after this pull

- official: 474
- community: 2947

- sanctions: 192
- mixer: 101
- gambling: 147
- exchange: 622
- shop: 144
- protocol: 2214
- person: 1

Community exchange venues (row counts): {'Allbit': 2, 'Anycoin Direct': 1, 'AscendEX': 4, 'AscendEX token': 1, 'BGBP (BGBP)': 1, 'BNB (BNB)': 1, 'Base, Introduced': 1, 'Binance': 43, 'Binance Beacon ETH': 1, 'Binance Charity': 1, 'Binance JEX': 1, 'Binance Pool': 1, 'Binance US': 1, 'Binance USD (BUSD)': 1, 'Binance Wrapped BCH': 1, 'Binance Wrapped BTC': 1, 'Binance Wrapped DOT': 1, 'Binance Wrapped FIL': 1, 'Binance Wrapped WRX': 1, 'BitMEX': 2, 'BitMart': 4, 'BitMartToken (BMC)': 1, 'BitMax': 1, 'BitMax token (BTMX)': 1, 'BitMax: Old Token': 2, 'Bitcoin Suisse': 6, 'Bitfinex': 25, 'Bitfinex LEO Token': 1, 'Bithumb': 18, 'Bitpanda Ecosystem Token': 1, 'Bitstamp': 9, 'Bittrex': 4, 'Bity.com': 1, 'BlockFi': 6, 'Blockfolio': 1, 'CoinHako': 2, 'CoinList': 3, 'CoinMetro': 6, 'CoinMetro Exchange': 1, 'Coinbase': 25, 'Coinhako': 3, 'Coinone': 4, 'Coinsquare': 25, 'Cronos Coin (CRO)': 1, 'Crypto.com': 17, 'Crypto.com NFT Marketplace': 2, 'CryptoCasher (CRR)': 1, 'DFT (DFT)': 1, 'DIGIFINEXTOKEN': 1, 'Deribit': 10, 'Dether (DTH)': 1, 'DigiFinex': 3, 'Eristica TOKEN': 1, 'Ethereum Wrapped Filecoin': 1, 'Euro Tether': 1, 'FTX': 4, 'FTX Exchange': 1, 'FTX US': 1, 'Folgory Coin (FLG)': 1, 'Gate.io': 7, 'Gemini': 10, 'Gemini dollar': 1, 'HitBTC': 6, 'Hotbit': 3, 'Hotbit Token (HTB)': 1, 'Huobi': 82, 'Huobi Mining Pool': 1, 'HuobiPoolToken': 1, 'HuobiToken (HT)': 1, 'Korbit': 8, 'Kraken': 18, 'KuCoin': 8, 'KuCoin Contract': 1, 'KuCoin Token (KCS)': 1, 'Kucoin Shares': 1, 'Liquid': 5, 'Luno': 2, 'MCO (MCO)': 1, 'Nexo': 7, 'Nexo (NEXO)': 1, 'OKB (OKB)': 1, 'OKX': 24, 'OKX DEX': 1, 'Oobit': 5, 'Oobit (OBT)': 1, 'Poloniex': 20, 'QASH (QASH)': 1, 'Remitano': 3, 'Tether': 2, 'Tether CNH (CNHT)': 1, 'Tether EUR (EURT)': 1, 'Tether Gold': 1, 'Tether Gold (XAUt)': 1, 'Tidex': 2, 'Upbit': 4, 'Uphold.com': 1, 'Wintermute': 1, 'Wrapped Binance Beacon ETH': 1, 'iBBT Utility Token': 1, 'swETH (swETH)': 1}

### Still skipped

- Direct etherscan.io HTML scrape (Cloudflare).
- Phishing / take-action / website-down / airdrop-hunter nametags.
- Bulk LP pool contracts under Sushi/Balancer-style PROTO_EXTRA filters.
- Bybit Etherscan label slug absent from 2023 mirror (official Bybit PoR already in pack).



## Community octal mirror: 2026-09-03

Second community-tier source (George agreed). Complements brianleect mirror.

### Source

- [`octal-crypto/etherscan-labels`](https://github.com/octal-crypto/etherscan-labels) (same data as `https://octal.art/etherscan-labels/`)
- Pull date: 2026-09-03
- Machine-readable per-label JSON under `labels/<slug>.json` (not HTML scrape of octal.art).
- `source` column uses `Etherscan label (octal mirror) / <venue>` so mirrors are distinguishable.
- Each row cites the matching Etherscan label page as `source_url` when possible.
- Labels fetched OK (76): 0x-protocol, 1inch, aave, abracadabra-money, across-protocol, airswap, alchemix-finance, algorithmic-stablecoin, allbit, ascendex, binance, bitcoin-suisse, bitfinex, bithumb, bitmart, bitmex, bitstamp, bittrex, blockfi, bridge, coinbase, coinhako, coinlist, coinmetro, coinone, coinsquare, compound, convex-finance, cream-finance, crypto-com, curve-fi, defi, deribit, dex, digifinex, dydx, ens, ethereum-mixer, fiat-gateway, ftx, gambling, gate-io, gemini, hitbtc, hop-protocol, hotbit, huobi, idex, idle-finance, instadapp, korbit, kraken, kucoin, kyberswap, lido, liquid, maker, marketplace, multichain, nexo, okx, oobit, opensea, poloniex, protocol, remitano, set-protocol, stablecoin, synapse, tidex, tornado-cash, uniswap, upbit, wormhole, yearn-finance, zapper-fi
- Labels missing/404 (0): (none)

### Selection (same filters as brianleect bulk expand)

- ETH `0x` only, tier=`community`.
- Exchange venue labels (uncapped) + mixer/gambling/bridge/dex/defi/protocol/
  stablecoin/marketplace category labels + named protocol extras (non-poolish).
- Skip phishing mega-noise: take-action / website-down / airdrop-hunter labels
  and name regex (phish/scam/website-down/take-action/airdrop-hunter/old-contract).
- Mega colon / LP poolish names skipped for PROTO_EXTRA (incl. uniswap/curve).

### Incoming pick counts (before merge)

- Raw considered address hits: 4728
- Unique addresses after intra-octal dedupe: 4272
- Skip stats: {'skip_name_re': 137, 'poolish': 497, 'bad_address': 11, 'mega_colon': 148456, 'empty_name': 66}
- By mapped category: {'protocol': 3387, 'exchange': 521, 'mixer': 62, 'gambling': 143, 'shop': 159}
- By venue/label bucket (top): {'DeFi': 1519, 'Stablecoin': 189, 'Bridge': 182, 'DEX': 174, 'Aave': 168, 'Marketplace': 155, 'Gambling': 143, 'Cream': 138, 'Protocol': 120, 'Set Protocol': 120, 'KyberSwap': 114, 'Huobi': 82, 'Maker': 73, 'Binance': 62, 'Tornado Cash': 61, 'Idle': 56, 'Lido': 52, '0x': 50, 'Zapper': 48, 'Compound': 47, 'Yearn': 44, 'dYdX': 40, 'Alchemix': 38, 'Bitfinex': 38, 'ENS': 38, '1inch': 29, 'Coinsquare': 25, 'OKX': 25, 'Hop': 23, 'FTX': 22, 'Crypto.com': 21, 'Fiat Gateway': 21, 'Convex': 20, 'KuCoin': 20, 'Poloniex': 20, 'Multichain': 19, 'Abracadabra': 18, 'Bithumb': 18, 'Instadapp': 18, 'Kraken': 18}

### Merge (first-wins community)

- Before: total 3421 (official 474, community 2947)
- Incoming community unique: 4272
- Newly added (unique vs existing): 1518
- Overlap with existing official (suppressed): 93
- Overlap with existing community / brianleect (kept existing): 2661
- Overlap total: 2754
- After: total 4939 (official 474, community 4465)
- Rows whose source cites octal mirror: 1518

### Binance 15 check

- `0xc013426d7cef8be3ef3b366151ed85e4fe33688c` present: **True** (name=`Binance 15`, tier=`community`, source=`Etherscan label / Binance`)

### Counts after this pull

- official: 474
- community: 4465

- sanctions: 192
- mixer: 101
- gambling: 153
- exchange: 638
- shop: 170
- protocol: 3684
- person: 1

### Still skipped

- Direct etherscan.io HTML scrape (Cloudflare).
- Phishing / take-action / website-down / airdrop-hunter / spam mega-noise.
- Bulk LP / mega-colon protocol contracts under PROTO_EXTRA filters.
- ofac-sanctions-lists / bybit label slugs absent from this octal snapshot.



## Official ERC-20 token lists + ETH meme coins: 2026-09-03

Expand known entities with Ethereum mainnet token contract addresses
(ERC-20 etc). Official curated tokenlists for breadth; curated meme/culture
set with citations. Skipped CoinGecko all-tokens dump (~5.8k ETH) to avoid scam noise.

### Official tokenlists (tier=official, category=protocol)

- **Uniswap Labs Default** — `https://tokens.uniswap.org` (ETH tokens in file: 403; newly added this pull: 312; already present: 91)
  - Provenance: Uniswap Labs published default list (tokenlists.org standard); canonical URL https://tokens.uniswap.org
- **Gemini Token List** — `https://www.gemini.com/uniswap/manifest.json` (ETH tokens in file: 85; newly added this pull: 56; already present: 29)
  - Provenance: Gemini published Uniswap-compatible token list manifest
- **Compound** — `https://raw.githubusercontent.com/compound-finance/token-list/master/compound.tokenlist.json` (ETH tokens in file: 27; newly added this pull: 4; already present: 23)
  - Provenance: Compound Finance GitHub token-list (compound.tokenlist.json)
- **Wrapped Tokens** — `https://wrapped.tokensoft.eth.link` (ETH tokens in file: 35; newly added this pull: 20; already present: 15)
  - Provenance: TokenSoft Wrapped Tokens list (wrapped.tokensoft.eth.link)

Name policy: use each list's `name` field (ASCII-normalized), matching prior
rows such as `USD Coin` / `Aave` / `Wrapped Ether`.

### Meme / culture tokens

Well-known ETH meme/culture contracts with a source:
- On Uniswap Labs Default (tier=official via list): PEPE, SHIB, FLOKI, MEME,
  MOG, ELON (Dogelon), BITCOIN (HPOS10I), APU, Neiro, TURBO, SPX6900, etc.
- Extra curated (DefiLlama price check 2026-09-03 + Etherscan token page,
  tier=community unless project docs): LADYS (Milady), BONK (ETH), MAGA/TRUMP,
  GROK (ETH meme, not xAI), BabyDoge, PEOPLE (ConstitutionDAO), LOOKS, DODO.
- Shiba ecosystem via docs.shibatoken.com (tier=official): BONE, LEASH.
- Skipped: native DOGE (not ETH); Solana-only BONK without ETH 0x; invented addrs;
  CoinGecko full dump.

- Curated meme extras considered: 21
- Newly added from meme extras: 21 (official 13, community 8)
- Meme extras already present: 0

### Merge rules

- ETH `0x` lowercased, `chain=ethereum`, `category=protocol` for tokens.
- Dedupe on chain+address; **official > community** (upgrade community on conflict).
- Same-tier: keep existing row (preserve WETH/USDC etc. names/sources).

### Counts

- Before: total 4939 (official 474, community 4465)
- Incoming unique candidates: 461
- Newly added: 342 (official 334, community 8)
- Upgraded community -> official: 106
- Community suppressed by existing official: 0
- Same-tier kept existing: 13
- After: total 5281 (official 914, community 4367)

### Category totals after pull

- sanctions: 192
- mixer: 101
- gambling: 153
- exchange: 628
- shop: 165
- protocol: 4041
- person: 1



## High-leverage role labels expansion: 2026-09-03

Add MEV/builders, L2 bridge & system contracts, DEX routers/aggregators,
staking/LST, DAO treasuries, NFT marketplaces/collections, stablecoin plumbing,
CREATE2 factories, and a tiny documented-exploit set. Prefer official docs;
community only when that is all that exists (clearly labeled).

### Source families

- BuilderNet public identity: https://buildernet.org/docs/public-identity
- Arachnid CREATE2: https://github.com/Arachnid/deterministic-deployment-proxy
- Optimism superchain-registry addresses.json (chain 10 L1 system)
- Base docs: https://docs.base.org/base-chain/network-information/base-contracts
- Arbitrum docs: https://docs.arbitrum.io/build-decentralized-apps/reference/contract-addresses
- Polygon PoS: https://github.com/maticnetwork/static (mainnet/v1/index.json)
- Uniswap V2/V3/V4 + Permit2 + Universal Router official deployments
- Cow Protocol networks.json; SushiSwap V2; 1inch routers; 0x Exchange Proxy; ParaSwap Augustus V6
- ethereum.org Beacon Deposit Contract
- Lido deployed contracts: https://docs.lido.fi/deployed-contracts/
- DAO treasuries: Uniswap / ENS / Compound / Aave / Gitcoin official docs
- OpenSea Seaport Deployment.md; Blur marketplace; BAYC/MAYC/Punks/Pudgy/Azuki official sites
- Circle USDC + CCTP; Tether; MakerDAO DAI; Frax
- Wormhole incident report (exploiter labeled community)

### Deliberate gaps

- Flashbots/beaverbuild/rsync/Titan builder **fee-recipient** EOAs rotate and are not
  published as stable addresses in Flashbots Protect docs (only builder *names*/RPCs in
  builder-registrations.json). BuilderNet identities included from official page.
- ScamSniffer blacklist skipped (GPL-3.0 license; not clearly OK to rebundle).
- Railgun / Privacy Pools / zkSync L1 / Starknet portals: official address pages did not
  return parseable address tables in this pass; left for a follow-up.
- No public Coinbase PoR hot-wallet dump; Base admin EOAs from Base docs only.
- Sandwich/searcher bots: no stable official registry with citable fee recipients.
- Exploit set kept tiny; only Wormhole 2022 exploiter with community caveat.

### Counts

- Before: total=5281 official=914 community=4367
- After: total=5389 official=1046 community=4343
- Merge stats: {"incoming": 159, "added": 108, "added_official": 107, "added_cat_protocol": 102, "upgraded_to_official": 25, "same_tier_kept": 26, "added_cat_shop": 6, "added_community": 1}
- Incoming by family: {"mev": 9, "create2": 3, "bridge_op": 19, "bridge_base": 18, "bridge_arb": 10, "bridge_polygon": 12, "dex": 28, "staking": 30, "dao": 11, "nft": 11, "stablecoin": 6, "exploit": 1, "person": 1}
- Category totals after: {"sanctions": 192, "mixer": 101, "gambling": 153, "exchange": 628, "shop": 171, "protocol": 4143, "person": 1}
- Community->official upgrades: 25

### Notable upgrades (community -> official)

- `0x99c9fc46f92e8a1c0dec1b1747d010903e884be1`: 'Optimism: Gateway' (Etherscan label / Bridge) -> 'Optimism L1 Standard Bridge' (Optimism superchain-registry)
- `0x1c479675ad559dc151f6ec7ed3fbf8cee79582b6`: 'Arbitrum: Sequencer Inbox' (Etherscan label / Bridge) -> 'Arbitrum One Sequencer Inbox' (Arbitrum docs contract addresses)
- `0x4dbd4fc535ac27206064b68ffcf827b0a60bab3f`: 'Arbitrum: Delayed Inbox' (Etherscan label / Bridge) -> 'Arbitrum One Delayed Inbox' (Arbitrum docs contract addresses)
- `0x8315177ab297ba92a06054ce80a67ed4dbd7ed3a`: 'Arbitrum: Bridge' (Etherscan label / Bridge) -> 'Arbitrum One Bridge' (Arbitrum docs contract addresses)
- `0x0b9857ae2d4a3dbe74ffe1d7df045bb7f96e4840`: 'Arbitrum: Outbox 4' (Etherscan label / Bridge) -> 'Arbitrum One Outbox' (Arbitrum docs contract addresses)
- `0x72ce9c846789fdb6fc1f34ac4ad25dd9ef7031ef`: 'Arbitrum One: L1 Gateway Router' (Etherscan label / Bridge) -> 'Arbitrum One L1 Gateway Router' (Arbitrum docs contract addresses)
- `0xcee284f754e854890e311e3280b767f80797180d`: 'Arbitrum One: L1 Arb - Custom Gateway' (Etherscan label / Bridge) -> 'Arbitrum One L1 Custom Gateway' (Arbitrum docs contract addresses)
- `0xd92023e9d9911199a6711321d1277285e6d4e2db`: 'Arbitrum One: Wrapped Ether Gateway' (Etherscan label / Bridge) -> 'Arbitrum One L1 WETH Gateway' (Arbitrum docs contract addresses)
- `0x401f6c983ea34274ec46f84d70b31c151321188b`: 'Polygon (Matic): Plasma Bridge' (Etherscan label / Bridge) -> 'Polygon PoS Deposit Manager' (Polygon PoS mainnet contracts)
- `0xa0c68c638235ee32657e8f720a23cec1bfc77c77`: 'Polygon (Matic): Bridge' (Etherscan label / Bridge) -> 'Polygon PoS Root Chain Manager Proxy' (Polygon PoS bridge contracts)
- `0x5c69bee701ef814a2b6a3edd4b1652cb9cc5aa6f`: 'Uniswap V2: Factory Contract' (Etherscan label / DeFi) -> 'Uniswap V2 Factory' (Uniswap V2 deployments)
- `0xc36442b4a4522e871399cd717abdd847ab11fe88`: 'Uniswap V3: Positions NFT' (Etherscan label / DEX) -> 'Uniswap V3 NonfungiblePositionManager' (Uniswap V3 Ethereum deployments)
- `0x1111111254eeb25477b68fb85ed929f73a960582`: '1inch v5: Aggregation Router' (Etherscan label / DEX) -> '1inch Aggregation Router V5' (1inch Aggregation Router V5)
- `0xdef1c0ded9bec7f1a1670819833240f027b25eff`: '0x: Exchange Proxy' (Etherscan label / DEX) -> '0x Exchange Proxy' (0x Protocol deployed addresses)
- `0x9008d19f58aabd9ed0d60971565aa8510560ab41`: 'CoW Protocol: GPv2Settlement' (Etherscan label / DEX) -> 'CowSwap GPv2 Settlement' (Cow Protocol networks.json)
- `0xb9d7934878b5fb9610b3fe8a5e441e8fad7e293f`: 'Lido: Withdrawals Manager Stub' (Etherscan label / Lido) -> 'Lido Withdrawal Vault' (Lido deployed contracts)
- `0x388c818ca8b9251b393131c08a736a67ccb19297`: 'Lido: Execution Layer Rewards Vault' (Etherscan label / Lido) -> 'Lido EL Rewards Vault' (Lido deployed contracts)
- `0xf95f069f9ad107938f6ba802a3da87892298610e`: 'Lido: MEV Boost Relay Allowed List' (Etherscan label / Lido) -> 'Lido MEV Boost Relay Allowed List' (Lido deployed contracts)
- `0xb8ffc3cd6e7cf5a098a1c92f48009765b24088dc`: 'Lido: Deployer 2' (Etherscan label / Lido) -> 'Lido DAO Kernel' (Lido deployed contracts)
- `0x2e59a20f205bb85a89c53f1936454680651e618e`: 'Lido: Aragon Voting' (Etherscan label / Lido) -> 'Lido Aragon Voting' (Lido deployed contracts)
- `0x3e40d73eb977dc6a537af587d48316fee66e9c8c`: 'Lido: Treasury' (Etherscan label / Lido) -> 'Lido Treasury' (Lido deployed contracts)
- `0xb9e5cbb9ca5b0d659238807e84d0176930753d86`: 'Lido: Aragon Finance' (Etherscan label / Lido) -> 'Lido Aragon Finance' (Lido deployed contracts)
- `0x55032650b14df07b85bf18a3a3ec8e0af2e028d5`: 'Lido: Node Operators Registry' (Etherscan label / Lido) -> 'Lido Node Operators Registry' (Lido deployed contracts)
- `0xf0211b7660680b49de1a7e9f25c65660f0a13fea`: 'Lido: Easy Track' (Etherscan label / Lido) -> 'Lido EasyTrack' (Lido deployed contracts)
- `0x87d93d9b2c672bf9c9642d853a8682546a5012b5`: 'Lido: Rewards Committee Multisig' (Etherscan label / Lido) -> 'Lido Liquidity Observation Lab' (Lido deployed contracts)

## Deliberate gaps + person expansion: 2026-09-03

Fill citeable Part A gaps left after 0.1.10 (privacy / L2 portals / stable plumbing / small exploit set) and expand `category=person` under a first-party attribution rule.

### Person / public figures

**First-party rule:** `person` rows are ONLY wallets the individual or their foundation publicly self-attributes (personal blog, foundation/docs page, signed message, ENS they control and document, GitHub they own listing the address, or a verified social post linking the address). Prefer `tier=official` for first-party claims; use `tier=community` only for well-known attributions that are widely cited but not first-party — and caveat in the source. Do **not** include rumor wallets, clustering guesses, or doxxing.

**2026-09-07 curated ENS resolve pass:** hand-picked well-known public `.eth` names (founders, EF/client researchers, widely self-used builder identities). Resolved via public Ethereum RPC (`ethereum.publicnode.com` + `cast resolve-name`) with `api.ensideas.com` fallback. New person rows are `tier=community` with source noting `self-used public ENS; community attribution caveat` and `source_url` to `https://app.ens.domains/<name>`. Skipped non-resolving, zero/burn, duplicate/non-preferred ENS, and `ansgar.eth` (different address than documented `adietrichs.eth`). Official Protocol Guild tip jars added as `protocol`/`official` from first-party donate docs. No gossip, rich lists, or Etherscan nametag scrapes used as person truth.

Person rows after this pass:
- `0xfd22004806a6846ea67ad883356be810f0428793`: **6529** (community) — punk6529.eth (self-used public ENS; community attribution caveat) — https://app.ens.domains/punk6529.eth
- `0x068484f7bd2b7d7c5a698d89e75ddcaf3a92b879`: **Alex Beregszaszi** (community) — axic.eth (EVM / Solidity ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/axic.eth
- `0x27fd13b48b27e9eca9804c1fd857ba44f755dc62`: **Alex Stokes** (community) — ralexstokes.eth (EF researcher ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/ralexstokes.eth
- `0xd3cdb511c245a01e820aae6bf4bdd5359b2ccc68`: **Andre Cronje** (community) — andrecronje.eth (public ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/andrecronje.eth
- `0xb506a2bae5352ba03040a323a73dbe3f9dc42bbf`: **Ansgar Dietrichs** (community) — adietrichs.eth (EF researcher ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/adietrichs.eth
- `0x648aa14e4424e0825a5ce739c8c68610e143fb79`: **Anthony Sassano** (community) — sassal.eth (self-used public ENS; community attribution caveat) — https://app.ens.domains/sassal.eth
- `0x198dbc9a9879d398bcacf139d8c130c466e272af`: **Arnetheduck** (community) — arnetheduck.eth (Nimbus ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/arnetheduck.eth
- `0x34aa3f359a9d614239015126635ce7732c18fdf3`: **Austin Griffith** (community) — austingriffith.eth (BuidlGuidl / Scaffold-ETH ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/austingriffith.eth
- `0x0916c04994849c676ab2667ce5bbdf7ccc94310a`: **Balaji Srinivasan** (community) — balajis.eth (public ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/balajis.eth
- `0x0035fc5208ef989c28d47e552e92b0c507d2b318`: **banteg** (community) — banteg.eth (Yearn contributor ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/banteg.eth
- `0x915aa445720020eb1a59151e831111369b08e118`: **Barnabe Monnot** (community) — barnabe.eth (EF researcher ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/barnabe.eth
- `0xd262d146e869915444d0f34ecdaabab5ab43007e`: **Ben Edgington** (community) — benjaminion.eth (Teku / EF ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/benjaminion.eth
- `0xfdbf9ee70baf09f77e5479673e63df529b9b0087`: **Benjamin Muller** (community) — bmuller.eth (builder ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/bmuller.eth
- `0x983110309620d911731ac0932219af06091b6744`: **Brantly Millegan** (community) — brantly.eth (widely self-used ENS; community attribution caveat) — https://app.ens.domains/brantly.eth
- `0xd334741d0766b257b18f2d058e844e17e346a0c1`: **Carl Beekhuizen** (community) — carlbeek.eth (EF researcher ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/carlbeek.eth
- `0x30dd44c838c57d6ea8c3401c1e32cea040c290e6`: **ChainYoda** (community) — chainyoda.eth (public ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/chainyoda.eth
- `0x9759e0ec15e75c71c503ad16cb99311c591b4b0f`: **Christian Reitwiessner** (community) — chriseth.eth (Solidity ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/chriseth.eth
- `0x02c15d12240e1dfe098f89e6ef9ef5bc4e477025`: **Dan Finlay** (community) — danfinlay.eth (MetaMask co-founder ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/danfinlay.eth
- `0x2f86a929be52dab975a82d852ee94c60adde177b`: **Dan Robinson** (community) — danrobinson.eth (Paradigm ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/danrobinson.eth
- `0x634c474a393e4498bc2f0c1dee16a50e9e0ebe2b`: **Dankrad Feist** (community) — dankrad.eth (EF researcher ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/dankrad.eth
- `0x6c73e9148ac9acd1a96d554b6b20905414f8696f`: **Danny Ryan** (community) — dannyryan.eth (EF researcher ENS; community attribution caveat) — https://app.ens.domains/dannyryan.eth
- `0x1c0aa8ccd568d90d61659f060d1bfb1e6f855a20`: **David Mihal** (community) — dmihal.eth (CryptoStats / cryptofees ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/dmihal.eth
- `0xb6b440e2d16c85bbf8a1780f18dbd3be2981628f`: **Dom Hofmann** (community) — dhof.eth (Zora co-founder ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/dhof.eth
- `0x59e6f460680f62fb957a2798edda82b258750640`: **elopio** (community) — elopio.eth (Ethereum contributor ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/elopio.eth
- `0x7903fbcb275f33e68b9435320e3788d0c1f06592`: **ethchris** (community) — ethchris.eth (builder ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/ethchris.eth
- `0x1c277bd41a276f87d3e92bccd50c7364aa2ffc69`: **Evan Huestis** (community) — fubuloubu.eth (ApeWorx ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/fubuloubu.eth
- `0xe1c1875d51159d09e94771eab644784ece29833d`: **Fabian Vogelsteller** (community) — frozeman.eth (ERC-20 / Mist ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/frozeman.eth
- `0xc9c022fcfebe730710ae93ca9247c5ec9d9236d0`: **frolic** (community) — frolic.eth (builder ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/frolic.eth
- `0x38f64793438429ae49a5c17ac793acf147225f66`: **Gavin Wood** (community) — gavofyork.eth (Ethereum co-founder ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/gavofyork.eth
- `0x2abc80332a8dfa064bd2f361e8b72d76ef8637c5`: **Georgios Konstantopoulos** (community) — gakonst.eth (Paradigm / Foundry ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/gakonst.eth
- `0x0c32f6f38f119c50d53686a1dbaac6f6166dfe6e`: **Gregory Markou** (community) — thegostep.eth (Chainsafe / gostep ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/thegostep.eth
- `0x839395e20bbb182fa440d08f850e6c7a8f6f0780`: **Griff Green** (community) — griff.eth (Giveth co-founder ENS; community attribution caveat) — https://app.ens.domains/griff.eth
- `0x598a11f39abfd20793fdd5c02f179976761f7481`: **Harikrishnan Mulackal** (community) — hrkrshnn.eth (Solidity compiler ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/hrkrshnn.eth
- `0xcec63f9b8a81011026ea1c9d49fbc5c54cc82d6f`: **Hasu** (community) — hasufl.eth (research ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/hasufl.eth
- `0x50ec05ade8280758e2077fcbc08d878d4aef79c3`: **Hayden Adams** (community) — hayden.eth (Uniswap founder ENS; community attribution caveat) — https://app.ens.domains/hayden.eth
- `0xb12d314ef27f7e7b928c9d6c715acfe7613d18ac`: **Hsiao-Wei Wang** (community) — hww.eth (EF researcher ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/hww.eth
- `0x80d63799b1e08a80f73fb7a83264b5c31600bf3a`: **Hudson Jameson** (community) — souptacular.eth (souptacular.eth public ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/souptacular.eth
- `0x18c8df1fb7fb44549f90d1c2bb1dc8b690cd0559`: **Iain Nash** (community) — iainnash.eth (Zora eng ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/iainnash.eth
- `0x5bb3e1774923b75ecb804e2559149bbd2a39a414`: **James Young** (community) — jamesyoung.eth (builder ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/jamesyoung.eth
- `0x8957e95950bcf7e40ba2bd8007b47ac67dcffa2d`: **Jannik Luhn** (community) — jannikluhn.eth (Ethereum contributor ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/jannikluhn.eth
- `0x866b3c4994e1416b7c738b9818b31dc246b95eee`: **Jeff Lau** (community) — jefflau.eth (ENS eng ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/jefflau.eth
- `0xcf8036070c46d39b9d8318aa3954579ddcba92ec`: **jgm** (community) — jgm.eth (builder ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/jgm.eth
- `0x4c64c7929895e76fbda25764d6ac44b75419b80e`: **Jordi Baylina** (community) — jordibaylina.eth (iden3 / Polygon zkEVM ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/jordibaylina.eth
- `0x6b2b69c6e5490be701abfbfa440174f808c1a33b`: **Jorge Izquierdo** (community) — izqui.eth (Aragon co-founder ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/izqui.eth
- `0x5f43cd8b5eead549de4444a644b4cb425a4ea5b2`: **joseph.eth** (community) — joseph.eth (self-used public ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/joseph.eth
- `0xd41bdbd4101e02057b7f621f681540ef3ac81e55`: **karmacoma** (community) — karmacoma.eth (security / builder ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/karmacoma.eth
- `0x8bf0083ecea9bbe0b6ca47bdb3cd1c39f10bdf02`: **kipto** (community) — kipto.eth (builder ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/kipto.eth
- `0x4566af7d0a1ab367a269ac4e6c89cae7e0224531`: **Kosala Hemachandra** (community) — kosala.eth (MyEtherWallet ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/kosala.eth
- `0xf67eeb6e0461b63c13114785401e739af8c131a3`: **kumavis** (community) — kumavis.eth (MetaMask eng ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/kumavis.eth
- `0xa016804e2112ed15073cd7d23b5233a8b3cac478`: **Lane Rettig** (community) — lanerettig.eth (Ethereum contributor ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/lanerettig.eth
- `0x2b888954421b424c5d3d9ce9bb67c9bd47537d12`: **Lefteris Karapetsas** (community) — lefteris.eth (Rotki founder ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/lefteris.eth
- `0x0000006916a87b82333f4245046623b23794c65c`: **lightclient** (community) — lightclient.eth (EF / go-ethereum ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/lightclient.eth
- `0x5e349eca2dc61abcd9dd99ce94d04136151a09ee`: **Linda Xie** (community) — lindaxie.eth (Scalar / investor ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/lindaxie.eth
- `0xffd1ac3e8818adcbe5c597ea076e8d3210b45df5`: **Makoto Inoue** (community) — makoto.eth (ENS eng ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/makoto.eth
- `0x6f2a8ee9452ba7d336b3fba03cac27f7818aead6`: **Mariano Conti** (community) — mariano.eth (former Maker oracle lead ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/mariano.eth
- `0xe158dcc1779fce4c48c8d3155ec35fae7c52d093`: **Martin Holst Swende** (community) — holiman.eth (geth security ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/holiman.eth
- `0x13489a7f09ea0dfe9fdc41390cfbb57f4b6ff0b3`: **Maurelian** (community) — maurelian.eth (Optimism security ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/maurelian.eth
- `0x0294dde5d521eed2c1ecf6b1464ac1fade9313c9`: **Micah Zoltu** (community) — micahzoltu.eth (Ethereum contributor ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/micahzoltu.eth
- `0xe340b00b6b622c136ffa5cff130ec8edcddcb39d`: **Miguel Piedrafita** (community) — m1guelpf.eth (builder ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/m1guelpf.eth
- `0xdf85ca6fd65e4b5a3dfa076b3f585437f3aabd18`: **Mikhail Kalinin** (community) — mikhailkalinin.eth (consensus researcher ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/mikhailkalinin.eth
- `0xeab841b49ea16eb9e66f4aacd1052ab8738e5d52`: **Moody Salem** (community) — moodysalem.eth (Uniswap eng ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/moodysalem.eth
- `0xb2ebc9b3a788afb1e942ed65b59e9e49a1ee500d`: **Nader Dabit** (community) — dabit.eth (developer relations ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/dabit.eth
- `0xb8c2c29ee19d8307cb7255e1cd9cbde883a267d5`: **Nick Johnson** (official) — ENS blog beginners guide cites nick.eth as Nick Johnson example — https://ens.domains/blog/post/beginners-guide-to-ethereum-and-ens
- `0x5554672e67ba866b9861701d0e0494ab324ad19a`: **nixo** (community) — nixo.eth (builder ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/nixo.eth
- `0xac469c5df1ce6983ff925d00d1866ab780d402a4`: **norswap** (community) — norswap.eth (builder ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/norswap.eth
- `0x8dbd1b711dc621e1404633da156fcc779e1c6f3e`: **Odysseas** (community) — odysseas.eth (builder ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/odysseas.eth
- `0x20f41376c713072937eb02be70ee1ed0d639966c`: **Patrick Collins** (community) — patrickalphac.eth (Cyfrin / education ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/patrickalphac.eth
- `0xe9fa0c8b5d7f79dec36d3f448b1ac4cedede4e69`: **pcaversaccio** (community) — pcaversaccio.eth (security researcher ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/pcaversaccio.eth
- `0xa3eac0016f6581ac34768c0d4b99ddcd88071c3c`: **pet3rpan** (community) — pet3rpan.eth (self-used public ENS; community attribution caveat) — https://app.ens.domains/pet3rpan.eth
- `0x0a13fa23a5ccbabb3817cff029b9b8e843d59f72`: **Peter Szilagyi** (community) — karalabe.eth (go-ethereum lead ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/karalabe.eth
- `0xdf6c53df56f3992fc44195518a2d8b16306af9ff`: **Piper Merriam** (community) — pipermerriam.eth (Ethereum tooling ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/pipermerriam.eth
- `0x7eae9e62add4f023cc521e2c5de1b6527a395cd2`: **Potuz** (community) — potuz.eth (consensus client researcher ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/potuz.eth
- `0xf71e9c766cdf169edfbe2749490943c1dc6b8a55`: **Preston Van Loon** (community) — prestonvanloon.eth (Prysm ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/prestonvanloon.eth
- `0xb21c33de1fab3fa15499c62b59fe0cc3250020d1`: **protolambda** (community) — protolambda.eth (Ethereum researcher ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/protolambda.eth
- `0x3ed7bf997b7a91e9e8ab9ee2f7ce983bd37d6392`: **Raul Jordan** (community) — rauljordan.eth (Prysm ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/rauljordan.eth
- `0x932f1d969f13d314f3d0a234a3ffcc88372cdff1`: **rekmarks** (community) — rekmarks.eth (MetaMask eng ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/rekmarks.eth
- `0x5555763613a12d8f3e73be831dff8598089d3dca`: **Richard Moore** (community) — ricmoo.eth (ethers.js ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/ricmoo.eth
- `0x64dcbead3b25b94c1c07158c8a6ad6517b95513e`: **Robert Leshner** (community) — rleshner.eth (Compound founder ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/rleshner.eth
- `0xf65475e74c1ed6d004d5240b06e3088724dfda5d`: **Rune Christensen** (community) — rune.eth (MakerDAO founder ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/rune.eth
- `0xc95c558daa63b1a79331b2ab4a2a7af375384d3b`: **samczsun** (community) — samczsun.eth (security researcher ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/samczsun.eth
- `0x337280867ea1feaf9a47c79dc853dcf785bdd16d`: **Scoopy Trooples** (community) — scoopy.eth (Alchemix founder ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/scoopy.eth
- `0xa87922d0074bcd82ac82816633cce68472548955`: **shemnon** (community) — shemnon.eth (Besu / client ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/shemnon.eth
- `0x374bd185ee19fd9f8682eb875e5d0546a8d58cdd`: **Simon de la Rouviere** (community) — simondlr.eth (builder ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/simondlr.eth
- `0x3171ee768024dc298808d900df37f4e9e1cb9b87`: **soska** (community) — soska.eth (self-used public ENS; community attribution caveat) — https://app.ens.domains/soska.eth
- `0x2e21f5d32841cf8c7da805185a041400bf15f21a`: **Stani Kulechov** (community) — stani.eth (Aave founder ENS; community attribution caveat) — https://app.ens.domains/stani.eth
- `0xb5ce0a850edaffe5457e715def728835d3345968`: **Tarun Chitra** (community) — tarunchitra.eth (Gauntlet ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/tarunchitra.eth
- `0x481f50a5bdccc0bc4322c4dca04301433ded50f0`: **Taylor Monahan** (community) — tayvano.eth (MyCrypto founder ENS; community attribution caveat) — https://app.ens.domains/tayvano.eth
- `0xb2fba7f4384c517e1524846aba89393b3ef42042`: **Terence Tsao** (community) — terence.eth (Prysm ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/terence.eth
- `0x10f5d45854e038071485ac9e402308cf80d2d2fe`: **Tim Beiko** (official) — timbeiko.eth Mirror author identity (self-attributed ENS) — https://tim.mirror.xyz/
- `0x7ae7d67ff01e8cc30ab8e534c2466b031f6b2b91`: **transmissions11** (community) — t11s.eth (Solmate / Solady author ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/t11s.eth
- `0x5531db3f21a1723e6f4d95f93bc8220c6e9cffa2`: **Trent Van Epps** (community) — trent.eth (Protocol Guild ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/trent.eth
- `0x1f5d295778796a8b9f29600a585ab73d452acb1c`: **Vectorized** (community) — vectorized.eth (Solady author ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/vectorized.eth
- `0xd8da6bf26964af9d7eed9e03e53415d37aa96045`: **Vitalik Buterin** (official) — public — https://vitalik.ca
- `0x7bfaf4c59aa4f011672b8e77789e1eb41abd654d`: **William Schwab** (community) — wschwab.eth (builder ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/wschwab.eth
- `0x3e331406313e4b79a0bf8486428e65df19dd8d80`: **yupuday** (community) — yupuday.eth (builder ENS; self-used public ENS; community attribution caveat) — https://app.ens.domains/yupuday.eth

### ENS person expansion counts (2026-09-07)

- Before: total=5469 official=1127 community=4342 person=12
- After: total=5554 official=1129 community=4425 person=95
- New person rows: 83 (community ENS); Protocol Guild tip jars: 2 official protocol
- Method: curated seed -> ENS resolve -> dedupe (official wins) -> ASCII labels
- Person set kept quality-gated: ENS-only resolutions stay community-caveated; unresolved/ambiguous names omitted.

### Source families (this pass)

- RAILGUN docs: https://docs.railgun.org/wiki/learn/helpful-links
- Privacy Pools deployments: https://docs.privacypools.com/deployments
- ZKsync L1 contracts: https://docs.zksync.io/zksync-network/environment/l1-contracts
- Starknet addresses: https://github.com/starknet-io/starknet-addresses
- Linea contracts: https://docs.linea.build/network/build/contracts
- Scroll contracts: https://docs.scroll.io/en/developers/scroll-contracts/
- Mantle v2 deployments: mantle-xyz/mantle-v2 `mantle-mainnet`
- Mode L1/L2 contracts: https://docs.mode.network/user-guides/mainnet-contract-addresses/l1-l2-contracts
- Blast contracts: https://docs.blast.io/building/contracts
- Circle CCTP V2: https://developers.circle.com/cctp/evm-smart-contracts
- Maker/Sky chainlog: https://chainlog.sky.money/
- Euler post-mortem: https://www.euler.finance/blog/war-peace-behind-the-scenes-of-eulers-240m-exploit-recovery
- Harmony Horizon summary: https://medium.com/harmony-one/summary-of-the-harmony-horizon-bridge-incident-f9bd87c0c68e
- Poly Network attacker IDs (via Chainalysis citing Poly): https://www.chainalysis.com/blog/poly-network-hack-august-2021/
- ENS beginners guide (nick.eth): https://ens.domains/blog/post/beginners-guide-to-ethereum-and-ens

### Deliberate gaps remaining

- Flashbots/beaverbuild/rsync/Titan **fee-recipient EOAs** still rotate; no stable published identity list beyond BuilderNet (already included).
- ScamSniffer skipped (GPL-3.0). CoinGecko dumps skipped. No Coinbase PoR inventing.
- Nomad 2022 was a copycat free-for-all; only the bridge contract is labeled, not a long exploiter dump.
- Ronin primary exploiter already present as OFAC Lazarus sanctions; not duplicated as exploit.
- Person set kept quality-gated: many public figures lack first-party tip-jar posts; ENS-only resolutions without documentation stay community-caveated or omitted.
- Maker Pause Proxy / some PSM variants not added without a live chainlog JSON snapshot in this pass (UI-only registry).

### Counts

- Before: total=5389 official=1046 community=4343
- After: total=5469 official=1127 community=4342
- Merge stats: {"incoming": 96, "added": 80, "added_official": 66, "added_cat_mixer": 7, "added_cat_protocol": 61, "upgraded_to_official": 15, "added_community": 14, "added_cat_exchange": 1, "same_tier_kept": 1, "added_cat_person": 11}
- Incoming by family: {"privacy": 12, "l2": 50, "stable": 16, "exploit": 4, "mev_skipped": 0, "person": 12, "other": 2}
- Category totals after: {"sanctions": 192, "mixer": 108, "gambling": 153, "exchange": 629, "shop": 171, "protocol": 4204, "person": 12}
- New person rows added this pass: 11
  - Nick Johnson (`0xb8c2c29ee19d8307cb7255e1cd9cbde883a267d5`, official)
  - Tim Beiko (`0x10f5d45854e038071485ac9e402308cf80d2d2fe`, official)
  - 6529 (`0xfd22004806a6846ea67ad883356be810f0428793`, community)
  - Anthony Sassano (`0x648aa14e4424e0825a5ce739c8c68610e143fb79`, community)
  - Brantly Millegan (`0x983110309620d911731ac0932219af06091b6744`, community)
  - Danny Ryan (`0x6c73e9148ac9acd1a96d554b6b20905414f8696f`, community)
  - Griff Green (`0x839395e20bbb182fa440d08f850e6c7a8f6f0780`, community)
  - Hayden Adams (`0x50ec05ade8280758e2077fcbc08d878d4aef79c3`, community)
  - pet3rpan (`0xa3eac0016f6581ac34768c0d4b99ddcd88071c3c`, community)
  - Stani Kulechov (`0x2e21f5d32841cf8c7da805185a041400bf15f21a`, community)
  - Taylor Monahan (`0x481f50a5bdccc0bc4322c4dca04301433ded50f0`, community)
- Community->official upgrades: 15

### Notable upgrades (community -> official)

- `0xe76c6c83af64e4c60245d8c7de953df673a7a33d`: 'Rail (RAIL)' (Etherscan label (octal mirror) / DeFi) -> 'RAIL Token' (RAILGUN RAIL token overview)
- `0xae0ee0a63a2ce6baeeffe56e7714fb4efe48d419`: 'StarkNet: StarkGate ETH Bridge' (Etherscan label / Bridge) -> 'StarkGate ETH Bridge' (starknet-io bridged tokens mainnet)
- `0xf6080d9fbeebcd44d89affbfd42f098cbff92816`: 'StarkNet: StarkGate USDC Bridge' (Etherscan label / Bridge) -> 'StarkGate USDC Bridge' (starknet-io bridged tokens mainnet)
- `0xbb3400f107804dfb482565ff1ec8d8ae66747605`: 'StarkNet: StarkGate USDT Bridge' (Etherscan label / Bridge) -> 'StarkGate USDT Bridge' (starknet-io bridged tokens mainnet)
- `0x283751a21eafbfcd52297820d27c1f1963d9b5b4`: 'StarkNet: StarkGate WBTC Bridge' (Etherscan label / Bridge) -> 'StarkGate WBTC Bridge' (starknet-io bridged tokens mainnet)
- `0x659a00c33263d9254fed382de81349426c795bb6`: 'StarkNet: StarkGate DAI Bridge' (Etherscan label / Bridge) -> 'StarkGate DAI Bridge (legacy)' (starknet-io bridged tokens mainnet)
- `0x0a59649758aa4d66e25f08dd01271e891fe52199`: 'Maker: PSM-USDC-A' (Etherscan label / Maker) -> 'Maker PSM-USDC-A' (Maker/Sky community label upgraded; canonical Maker module (chainlog registry))
- `0x79a0fa989fb7adf1f8e80c93ee605ebb94f7c6a5`: 'Maker: GUSD PSM' (Etherscan label / Maker) -> 'Maker PSM-GUSD-A' (Maker/Sky community label upgraded; canonical Maker module (chainlog registry))
- `0xa950524441892a31ebddf91d3ceefa04bf454466`: 'Maker: MCD Vow' (Etherscan label / Maker) -> 'Maker Vow' (Maker/Sky community label upgraded; canonical Maker module (chainlog registry))
- `0x373238337bfe1146fb49989fc222523f83081ddb`: 'Maker: DSR Manager' (Etherscan label / Maker) -> 'Maker DSR Manager' (Maker/Sky community label upgraded; canonical Maker module (chainlog registry))
- `0x5ef30b9986345249bc32d8928b7ee64de9435e39`: 'Maker: CDP Manager' (Etherscan label / Maker) -> 'Maker CDP Manager' (Maker/Sky community label upgraded; canonical Maker module (chainlog registry))
- `0x35d1b3f3d7966a1dfe207aa4514c12a259a0492b`: 'Maker: MCD Vat' (Etherscan label / Maker) -> 'Maker Vat' (MakerDAO Multi-Collateral Dai core (Sky chainlog))
- `0x19c0976f590d67707e62397c87829d896dc0f1f1`: 'Maker: MCD Jug' (Etherscan label / Maker) -> 'Maker Jug' (MakerDAO Multi-Collateral Dai core (Sky chainlog))
- `0x9759a6ac90977b93b58547b4a71c78317f391a28`: 'Maker: MCD Join DAI' (Etherscan label / Maker) -> 'Maker DaiJoin' (MakerDAO Multi-Collateral Dai core (Sky chainlog))
- `0x197e90f9fad81970ba7976f33cbd77088e5d7cf7`: 'Maker: MCD Pot' (Etherscan label / Maker) -> 'Maker Pot (DSR)' (MakerDAO Multi-Collateral Dai core (Sky chainlog))
