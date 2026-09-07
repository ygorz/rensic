# Functions and actions (the kinetic layer)

Palantir splits the Ontology into **semantic** (types, links) and **kinetic** (actions, functions). Humans and agents change the world through actions. Functions hold logic that is awkward or illegal to put in a single "set property" rule.

Repo: `~/Documents/WilderformTools/rensic/rensic-foundry/functions-typescript/src`.

Ship rule: **git push is not enough**. Publish a functions **version** in Foundry, then **pin** Create / Expand / Close to that version.

## Why Create Investigation is a function

A Foundry action typically has one logic rule. Opening a case needs **two** writes:

1. Investigation Case (title, seed, chains, window, status `draft`)
2. Case Address membership (role `seed`, hop 0) per selected chain

`openInvestigation` in `ontology-edits.ts` does both. The desk calls the action `create-investigation`, which is backed by that function.

```typescript
@OntologyEditFunction()
public openInvestigation(
  caseTitle: string,
  seedWalletAddress: string,
  targetChains: string[],
  lookbackDays: Integer,
): void
```

If title, seed, or chains are empty, it returns without writing (no throw). The desk still validates the form.

Lookback days become `timeWindowStart` / `timeWindowEnd` on the case. Spark later turns that into Alchemy `fromBlock` ([ingestion.md](ingestion.md)).

## Ontology edit functions (the ones that match the desk)

Class `RensicOntologyEdits` (`ontology-edits.ts`):

| Function | Action | What it writes |
|---|---|---|
| `openInvestigation` | `create-investigation` | Case + seed Case Address(es) |
| `expandInvestigation` | `expand-investigation` | New membership role `expanded`; case status `active` |
| `closeInvestigation` | `close-investigation` | status `closed` |
| `archiveInvestigation` | `archive-investigation` | status `archived` |
| `deleteInvestigation` | `delete-investigation` | Cascade: CaseAddress + Narrative for case, then Case. Keeps Address / pack / ingest datasets. |
| `saveInvestigationNarrative` | `save-investigation-narrative` | Investigation Narrative row + copies body to `caseSummary` |

These are the kinetic core. They do **not** call Alchemy. They do **not** set `riskScore`.

Comment in the file still mentions Workshop. The product UI is the OSDK desk. Ignore the Workshop sentence.

## Label Address (no custom function)

Desk Flag calls the existing action `label-address` with `{ address, label }`. It writes `Address.addressLabel`. It does not change pack category. Official pack: UI sends the **note only** so the ledger title stays the pack name. Community: investigator name may override display; pack row remains.

This is an action-backed edit, not a Spark job. Correct Golden Hammer split.

## Vertex helpers (graph, not the product UI)

`vertex-search-around.ts` -- Vertex "Search Around" / fund-flow edges. Interface name `IGraphSearchAroundResultV1` is required for Vertex to discover it.

`vertex-derived-properties.ts` -- node colors/sizes. **Watch:** it has a `riskColor` path based on `Address.riskScore`. That property is empty on purpose. Do not start coloring nodes from a fake score. Chain color and ETH size are fine.

`vertex-cross-chain.ts` -- sequel. Same Address type, different `chainId`. Not the demo.

The desk does not embed Vertex. It builds a URL with the Address RID and a **cast** of at most 16 objects (seed + labeled hop-1, then ETH flow). See `vertexCast` in `rensic-app/src/desk.ts`.

## Intelligence functions (exist; do not treat as product)

`intelligence.ts` (`RensicIntelligence`) talks to Anthropic via Foundry models API:

- `generateNarrative` -- markdown report from case transactions
- `analyzeRisk` -- **assigns a 0-100 score** and hunts "red flags"
- `traceMultiHop` -- walks hop 2-3 from live object links (breadth-capped)

The file header says "no hallucinations" because it stuffs ontology fields into the prompt. That is necessary but **not sufficient**:

- `analyzeRisk` asks the model for a numeric score. Product rule: **do not invent `riskScore`.** This function is the wrong shape.
- Mixer detection uses a **two-address hardcode**, not the 100+ official mixer pack.
- `traceMultiHop` is hop-2+ -- out of demo scope; Vitalik will explode even with caps.
- The desk AI tab **does not call these**. It shows a JSON brief. Copy says AIP is not wired.

Keep the files. Do not pin `generate-narrative` to this `analyzeRisk` until [aip.md](aip.md) is implemented (grounded paragraph, no score).

## Actions that exist on the case (including ones the desk does not use yet)

From Ontology Manager on Investigation Case:

- create / expand / close / archive / delete
- `update-case-status`
- `flag-for-review` (case escalation -- not the address Flag button)
- `generate-narrative` (future AIP)
- `save-investigation-narrative`

Desk today: create + RPC config + address Flag (`label-address`) + Vertex link + delete investigation. Close/archive remain available as status-only paths.

## Function vs pipeline vs action (worked examples)

| Need | Put it here |
|---|---|
| Sum ETH in/out for all counterparties | Pipeline (`clean_to_ontology.py`) |
| Open a case + seed membership atomically | Function-backed action |
| Investigator names a gas station | Action `label-address` |
| Nightly "calculate regional risk" | **Do not build.** That is Golden Hammer toward Chainalysis. |
| Vertex fund-flow edges | Function (search around) |
| Paraphrase a brief into one paragraph | Function later, **after** the brief is only sourced fields |

## Index of the functions repo

```
functions-typescript/src/index.ts
  exports Vertex derived properties
  exports Vertex search around
  exports Intelligence          <-- do not pin to desk yet
  exports Cross-chain Vertex
  exports Ontology edits        <-- pin these
```

## After you edit functions

1. Commit and push Stemma (not GitHub).
2. In Foundry: publish a **new version**.
3. Point `create-investigation` (and friends) at that version.
4. Click Create in the desk and confirm a Case Address seed row exists **before** ingest.

If you skip pin, the hosted action still runs last week's function.
