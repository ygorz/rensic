# Keep it tight

You scoped Rensic so it does not compete with Chainalysis, TRM, or Etherscan nametags. This page is the fence. If a ticket is not on "now" or "later," it is out.

## What Rensic is

An investigation **desk** for one seed wallet on Ethereum (multi-chain is already in the ontology, not in Magritte yet):

- Create a case (title, seed, chain, lookback).
- Ingest hop-1 transfers in that window.
- Show a working set: seed pinned, top counterparties by ETH, **labeled rows first**.
- Name counterparties from a **sourced public pack** (official vs community).
- Let the investigator Flag a note / override community display. Official pack names cannot be renamed.
- Open a **small** Vertex graph (seed + labeled hop-1, fill remaining slots by flow, cap 16).
- Stay honest when unlabeled.

## What Rensic is not

| Not this | Why |
|---|---|
| Chainalysis / TRM | Their moat is proprietary clustering and attribution. You cannot fake it. Unlabeled is valid. |
| Etherscan clone | They already dump the chain. A darker dump inside Foundry dies on Vitalik. |
| BI dashboard | Counts without a sentence are decoration. |
| Workshop app | The product UI is the OSDK desk. Vertex is a deep-link. |
| 0-100 `riskScore` | Missing label is not clearance. Do not fill `riskScore`, `overallRiskLevel`, or `highRiskAddressCount`. |
| Hop-2 product | Vitalik already has tens of thousands of hop-1 rows. Hop 2 is where you drown. |
| SuperRepo (now) | Classic Compass + three Stemma clones is the ship loop. Do not start `ontology.mts` to feel more Palantir. |

## Now / later / never

### Now (makes the 30-second sentence sharper)

1. Keep official pack **cited** and refreshable (OFAC, FBI/IC3, protocol docs, PoR). Do not grow community further as the main workstream.
2. Investigator Flag is wired to `label-address`. Keep official rename blocked. Prefer notes on the membership later if Address-global labels get messy.
3. Lookback is already on the Alchemy wire. Keep saying the window in the UI.
4. Risk-first chrome: sanctions/mixer must be impossible to miss (sort + chip). "Labeled risk" should eventually count **official** sanctions/mixer only, not community mixers.
5. One-paragraph brief on the AI tab assembled from objects -- no model required.

### Later (after hop-1 is a sentence)

- Tight AIP: model paraphrases a grounded brief only. See [aip.md](aip.md).
- Join pack **category / source / URL** onto Address in Spark (today Spark joins **name** only; the desk reads the JSON pack for the rest).
- Named party object (Tornado Cash the **org** -> many addresses) if a party page is truly needed. Not a 1:1 Known Entity type.
- Cross-chain ingest (ontology already has `chain:address` keys). Magritte Alchemy host is ETH-mainnet today.
- Status / close / archive from the desk (actions exist).
- Export the case slice.

### Never (for this demo / this resource level)

- Invented behavioral scores, peeling-chain detectors, PageRank, Louvain, t-SNE.
- USD prices as a product surface (they rot; ETH units are enough).
- Feeding Vertex the 91k dump.
- Treating community nametags as official exchange identity ("Coinbase 15" is a caveat, not PoR).
- AIP that assigns risk scores or traces hop-3 stories not in the brief.
- Growing the community lane toward "we have Etherscan at home."

## Dual-tier is a compromise, not the destination

Pack today: **1127 official** / **4342 community**.

Official is the useful set for a 30-second demo (sanctions, mixers, cited protocols, a few PoR exchange wallets). Community is Etherscan-style nametags with a caveat so a Vitalik working set is not a wall of hex. Dual-tier is honest **if**:

- Official wins on conflict.
- Community never drives the scary sentence by itself (or is clearly caveated).
- You stop adding community as the default next task.

Details: [entity-pack.md](entity-pack.md).

## Enrollment junk is not Rensic

The Foundry enrollment also has example types and actions (`[George] Create Patient`, sample alerts, shipments). Ignore them. Do not model Rensic after them. Search Ontology Manager by `Investigation`, `Address`, `Case Address`, `Chain Configuration`.

## The "would anyone care" check for a new ticket

Write the sentence the ticket enables. Examples that pass:

- "Direct to Tornado Cash (mixer, pack, cited)."
- "No labeled counterparties in this working set."
- "Official pack: OFAC SDN. Investigator note: payment from ticket 441."

Examples that fail:

- "We now have 8,000 more community protocol tags."
- "Risk score filled from an LLM."
- "Hop 2 available in the rail."
