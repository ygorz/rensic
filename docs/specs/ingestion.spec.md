# Spec: ingestion

Repo: rensic-ingestion. Production runs on Foundry Spark builds.

## Lookback windows

- UI choices: 7, 30, 90, 365 days. Default 30.
- Clamp lookback to [1, 365].
- fromBlock = latest - lookback_days * blocks_per_day
- ETH blocks_per_day=7200; typical L2s=43200; BSC/Avalanche=28800; Robinhood=864000.

## Orchestrator

1. Snapshot InvestigationCase materialization to ingestion_requests (ontology type name).
2. For each request: eth_blockNumber then getAssetTransfers.
3. Two directions per chain: fromAddress and toAddress (hop 1).
4. Page cap 100 pages x 1000 = 200k worst case.

## known_entities join

- snapshot_known_entities writes clean/known_entities.
- clean_to_ontology left-joins names onto Address.
- chain and address lowercased/stripped on snapshot.

## Chains

`config.CHAINS` registry: ethereum, base, arbitrum, polygon, optimism, bsc, robinhood, avalanche.

Alchemy subdomains: eth-mainnet, base-mainnet, arb-mainnet, polygon-mainnet, opt-mainnet, bnb-mainnet, robinhood-mainnet, avax-mainnet.

blocks_per_day: ethereum 7200; base/arbitrum/polygon/optimism 43200; bsc/avalanche 28800; robinhood 864000 (~0.1s blocks).

UI `chains.ts` must stay aligned. Pipeline only succeeds for networks with a configured Alchemy key in Chain Configuration.
