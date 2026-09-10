# Rensic Ingestion Pipeline

**On-chain wallet investigation data ingestion for Palantir Foundry.**

## Overview

This repository contains the data ingestion transforms for the Rensic investigation template. It fetches on-chain activity from EVM-compatible blockchains via RPC providers (Alchemy, Infura, etc.) and maps the data into the Rensic ontology schema.

## Architecture

```
┌─────────────────────────┐
│ Investigation Actions    │
│ (Create / Expand Case)   │
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│ Ingestion Requests       │  (pending_ingestion_requests dataset)
│ address, chain, window   │
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│ ingest_transfers.py      │  → raw_asset_transfers
│ (Alchemy API + pagination)│
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│ clean_to_ontology.py     │  → 4 ontology-mapped datasets
│  ├── build_addresses     │  → addresses (Address objects)
│  ├── build_transactions  │  → transactions (Transaction objects)
│  ├── build_token_transfers│ → token_transfers (TokenTransfer objects)
│  └── build_contract_interactions │ → contract_interactions (ContractInteraction)
└─────────────────────────┘
```

## Setup

### 1. Data Connection Source

Create a **REST API** Data Connection source:
- **URL**: `https://eth-mainnet.g.alchemy.com` (or your RPC provider)
- **Secrets**: Store API key as `API_KEY`
- **Egress**: Allow outbound to `*.alchemy.com` (or your provider domain)
- **Exports**: Enable exports and code repository usage
- Import the source into this repository

### 2. Configure Source RID

In `ingest_transfers.py`, replace `SOURCE_RID_PLACEHOLDER` with your actual source RID and uncomment the production transform.

### 3. Multi-Chain Support

For multi-chain investigations, either:
- Create one Data Connection source per chain (recommended for production)
- Use a single source and append chain-specific paths in the API calls

### 4. Output Datasets

Create output datasets and update the `Output()` paths/RIDs in each transform.

## Configuration

All configuration lives in `myproject/config.py`:
- `CHAIN_ENDPOINTS` — Chain-to-endpoint mapping
- `DEFAULT_LOOKBACK_DAYS` — Default time window (90 days)
- `MAX_RESULTS_PER_PAGE` — Alchemy page size (1000)
- `MAX_PAGES_PER_REQUEST` — Safety pagination limit (100)
- `TRANSFER_CATEGORIES` — Which transfer types to fetch

## Composite Key Convention

All primary keys use `chain:identifier` format for multi-chain support:
- Address: `ethereum:0xd8da6bf2...`
- Transaction: `ethereum:0xabc123...`
- Transfer: `ethereum:0xabc123...:42`
- Interaction: `ethereum:0xabc123...:0`

## Idempotency

The pipeline is idempotent:
- Re-running for the same address+chain produces the same output
- Deduplication is handled via `unique_id` (Alchemy's transfer UUID)
- Downstream transforms use deterministic composite keys

## Testing

The demo transform (`ingest_asset_transfers_demo`) generates sample data for testing the downstream pipeline without requiring API credentials.
