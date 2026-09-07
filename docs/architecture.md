# Architecture

Alchemy transfers to Spark transforms to ontology to OSDK desk to TypeScript functions.
Not a SuperRepo. No invented risk scores as the product.

## Data flow

```mermaid
flowchart LR
  UI[OSDK desk] --> Open[openInvestigation]
  Open --> Case[InvestigationCase]
  Case --> Req[ingestion_requests]
  Req --> Alc[Alchemy transfers]
  Alc --> Clean[clean datasets]
  Pack[known_entities.csv] --> Clean
  Clean --> Addr[Address and txs]
  Addr --> UI
  UI --> Label[label-address]
  Label --> Addr
```

## Window to fromBlock

Lookback days (clamped 1-365) become:
fromBlock = hex(latest - lookback_days * blocks_per_day)
toBlock = latest
Ethereum about 7200 blocks/day; L2s about 43200. Hop 1 only.

## Identity vs membership

- Address = global wallet identity (chain:0x)
- Case Address = membership in this case
- Investigation Case = session (seed, chains, window)
