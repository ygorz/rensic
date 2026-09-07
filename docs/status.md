# What is wired vs leftover

Honest snapshot as of 2026-09-06. Unfinished is fine. Filling leftover scores is not.

## Wired (you can demo this)

| Piece | Where | Notes |
|---|---|---|
| Create case | Desk -> `create-investigation` -> `openInvestigation` | Writes Case + seed Case Address. Does not call Alchemy. |
| Lookback on Alchemy | Spark orchestrator | `fromBlock` / `toBlock` from case window |
| Hop-1 ingest | Alchemy in + out of seed | No hop 2 |
| Pack names on Address | Spark left join | **Name only** |
| Pack category/source/tier in UI | `knownEntities.json` | Dual-tier chrome, Flag rules, exposure line |
| Working set rank | `desk.ts` | Seed pinned, labeled first, cap 100 |
| Flag | `label-address` | Official rename blocked; community display can yield |
| RPC key | `configure-chain-rpc` | Then rebuild ingest |
| Vertex button | URL with Address RID + cast 16 | Graph lives in Foundry |
| Delete investigation | Desk -> `delete-investigation` | Cascades case memberships + narratives; keeps Address/pack/ingest |
| Multi-chain picker | `chains.ts` aligned with ingest CHAINS | Needs Alchemy network configured per chain |
| AI tab JSON | CaseView `brief` | Not a model |
| Page-cap banner | `transactionCount` >= 200000 | Vitalik stress test |

## Exists on Foundry, thin or unused in the desk

| Piece | Status |
|---|---|
| Expand / close / archive actions | Functions exist; desk does not drive them yet |
| `flag-for-review` | Case escalation. Easy to confuse with address Flag |
| `save-investigation-narrative` | Object type + function ready; AIP not feeding it |
| `generate-narrative` action | Placeholder |
| Token Transfer / Contract Interaction tabs | Data is a projection of Alchemy categories, not full ABI decode |
| Vertex search-around / derived props | In functions repo; Vertex UI wiring is Foundry-native |
| Cross-chain config in Python | Magritte host is ETH-mainnet; sequel |
| `highRiskAddressCount` / `overallRiskLevel` / `riskScore` / `clusterId` | Properties exist. **Leave empty.** |
| Enrollment Patient / example actions | Not Rensic |

## In the functions repo, do not pin to the product yet

| Function | Why it waits |
|---|---|
| `generateNarrative` (Claude) | Long report, not the 30-second sentence |
| `analyzeRisk` | Invents 0-100 scores; two hardcoded mixer addresses |
| `traceMultiHop` | Hop 2-3; out of demo scope |

Plan: [aip.md](aip.md).

## Pack vs Foundry "knowing"

After a CSV change, Foundry knows the **name** once Spark builds. The desk knows **category/source/URL/tier** once JSON is in the app bundle and tagged. Do both.

Community lane is large (4342). Official (1127) is the 30-second set. Do not grow community as the default next task.

## The loop that still surprises people

```
Create in desk  ->  objects exist  ->  tabs empty
Foundry build   ->  hop-1 rows     ->  desk has a working set
```

If the quiet wallet shows nothing, ingest did not run, the RPC key is missing, or lookback is 30d and the inbound is older than that (use 365). [DEMO.md](DEMO.md).
