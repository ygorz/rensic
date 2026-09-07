# How Palantir would describe Rensic (cheat sheet)

This is a one-page overlay of Palantir's public ontology language onto the desk. The long version is [ontology.md](ontology.md). Official sources:

- [Best practices](https://www.palantir.com/docs/foundry/ontology/ontology-best-practices)
- [Structural guidance](https://www.palantir.com/docs/foundry/ontology/ontology-structural-guidance)
- [Anti-patterns](https://www.palantir.com/docs/foundry/ontology/ontology-anti-patterns)

## Semantic / kinetic / interfaces

```
Semantic     Investigation Case, Address, Case Address, Transaction, ...
Kinetic      create-investigation, label-address, openInvestigation(), ...
Interfaces   none yet (too few types to extract; rule of three)
```

The React app is a **consumer** of that Ontology (OSDK). Workshop would also be a consumer. You picked OSDK. Vertex consumes the same objects on a slice.

## Domain-driven design (priority 1)

Palantir: objects are real-world concepts, not tables. "Ontologize this Alchemy JSON" is the trap.

| Alchemy JSON fields | Rensic types (split) |
|---|---|
| from, to | two Address identities + a Transaction observation |
| hash, value, block | Transaction (and maybe Token Transfer) |
| "I opened a case on this seed" | Investigation Case + Case Address hop 0 |

You already split identity (Address) from observation (Transaction, Case Address). That is the best-practice sentence: **separate identity from observation**.

## Object-backed link (structural guidance)

Palantir: if the relationship has role/dates/status, do not hang those fields on the identity.

`Employee --(role, startDate)--> Project` becomes an assignment object.

Rensic: `Investigation Case --(hop, role, case ETH)--> Address` becomes **Case Address**.

## Golden Hammer (anti-pattern you are mostly avoiding)

| Job | Palantir tool | Rensic |
|---|---|---|
| Flatten 100k transfers | Pipeline | Spark orchestrator + clean_to_ontology |
| Human opens a file | Action | create-investigation |
| Two writes in one submit | Function-backed action | openInvestigation |
| Live graph expansion | Function | Vertex search-around |
| Nightly fake risk | (don't) | Leave riskScore empty |

The functions file `analyzeRisk` **would** be Golden Hammer (LLM as score engine). Do not pin it. See [aip.md](aip.md).

## Action Sprawl (anti-pattern to watch)

Good: Close Investigation, Archive Investigation, Expand Investigation.

Overlap: `update-case-status` vs close/archive. Live with it. Do not add `Set Hop Distance` / `Set Seed Hex`.

Desk Flag is `label-address`, not `flag-for-review` (that one escalates the **case**).

## Kitchen Sink / leftover scores

You did not dump Alchemy `pageKey` onto Address. Good.

You did leave `riskScore`, `clusterId`, `overallRiskLevel`, `highRiskAddressCount` as empty/edit-only properties with vendor-ish descriptions. That is not Kitchen Sink; it is unused kinetic surface. **Do not fill.** Product copy on the desk is the real schema.

## Open/closed and rule of three

Do not pile AIP fields onto Investigation Case (path to God Object). Investigation Narrative is the extension type -- that matches "open for extension, closed for modification."

Do not add KnownEntity 1:1 with Address (two types for one wallet = System Silos). Join pack columns onto Address, or later add Named party (org) when you have three workflows that need an org page.

## Classic Compass vs SuperRepo

Palantir's ontology-as-code story is SuperRepo (`ontology.mts`). Rensic's ontology already has two-datasource types, Magritte, and Vertex. Stay classic until the domain stops moving. Git still owns **app, functions, transforms**.

## What "good" looks like in Object Explorer

Open a quiet-wallet case after ingest:

- One Investigation Case with a real window
- One seed Case Address hop 0
- A handful of discovered Case Addresses hop 1
- Address titles that are pack names where the CSV has a row
- Transactions linking those Address ids
- `riskScore` still empty

If that is true, the Ontology is doing its job even if AIP is off.
