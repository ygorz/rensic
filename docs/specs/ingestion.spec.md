# Spec: ingestion

Repo: rensic-ingestion. Production runs on Foundry Spark builds.

## Lookback windows

- Desk choices: 7, 30, 90, 365 days. Default 30.
- Clamp lookback to [1, 365].
- fromBlock = latest - lookback_days * blocks_per_day
- ETH blocks_per_day=7200; L2s=43200.

## Orchestrator

1. Snapshot InvestigationCase materialization to ingestion_requests.
2. For each request: eth_blockNumber then getAssetTransfers.
3. Two directions per chain: fromAddress and toAddress (hop 1).
4. Page cap 100 pages x 1000 = 200k worst case.

## known_entities join

- snapshot_known_entities writes clean/known_entities.
- clean_to_ontology left-joins names onto Address.
- chain and address lowercased/stripped on snapshot.

## Chains

`config.CHAINS` registry: ethereum, base, arbitrum, optimism, polygon, zksync, scroll, linea, blast.

Alchemy subdomains: eth-mainnet, base-mainnet, arb-mainnet, opt-mainnet, polygon-mainnet, zksync-mainnet, scroll-mainnet, linea-mainnet, blast-mainnet.

Desk `chains.ts` must stay aligned. Pipeline only succeeds for networks with a configured Alchemy key in Chain Configuration.
