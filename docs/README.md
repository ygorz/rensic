# Rensic study guides

This folder is a temporary classroom. You will replace it later. Until then, it is the one place that explains **what Rensic is**, **why anyone would sit down for 30 seconds**, and **how the three code repos plus Foundry actually fit**.

Read in this order if you are coming back cold:

1. [why.md](why.md) -- why anyone cares (the 30-second sentence)
2. [scope.md](scope.md) -- what stays in, what is later, what is never
3. [map.md](map.md) -- three local clones, Foundry-native pieces, how a change ships
4. [ontology.md](ontology.md) -- objects, links, Palantir best practices applied to this desk
5. [palantir-practices.md](palantir-practices.md) -- one-page Palantir language overlay
6. [status.md](status.md) -- what is wired vs leftover (honest)
7. Then the layer that matches the work in front of you:
   - [ingestion.md](ingestion.md)
   - [functions-and-actions.md](functions-and-actions.md)
   - [desk.md](desk.md)
   - [entity-pack.md](entity-pack.md)
   - [aip.md](aip.md) -- tightly scoped, later, no hallucination
8. [analysis.md](analysis.md) -- names, hops, window, the sentence
9. [DEMO.md](DEMO.md) -- click path for the quiet-wallet walkthrough
10. [glossary.md](glossary.md) -- words used in these pages

The older filename [rensic-analysis-study-guide.md](rensic-analysis-study-guide.md) redirects here so nothing in chat history 404s.

## Snapshot (so numbers in other files stay honest)

Written against the local clones and Foundry ontology as of **2026-09-06**. Counts move. If a number disagrees with the CSV or Ontology Manager, trust those.

| Piece | What it is today |
|---|---|
| Product | On-chain **case file** on Palantir Foundry. Not Chainalysis. Not Etherscan with a dark theme. |
| UI | OSDK React desk in `rensic-app`. Workshop is not the product. Vertex is a button. |
| Ingest | Python Spark in `rensic-ingestion`. Alchemy `alchemy_getAssetTransfers`, hop 1, windowed. |
| Kinetic | TypeScript Functions v1 in `rensic-foundry`. Create/expand/close are function-backed actions. |
| Ontology | Classic Compass (Ontology Manager). **Not** a SuperRepo. No `ontology.mts`. |
| Pack | `known_entities.csv`: **5469** rows. **1127 official**, **4342 community**. Dual-tier. |
| Demo | Quiet wallet in ~30s. Vitalik 30-day is a **stress test** (Alchemy 200k page cap). |

Project home: ~/Documents/WilderformTools/rensic/

- Architecture: [architecture.md](architecture.md)
- Specs: [specs/](specs/)

## Three local folders

```
~/Documents/WilderformTools/rensic/rensic-app          Vite + React OSDK desk     (tag to host)
~/Documents/WilderformTools/rensic/rensic-foundry      TypeScript Functions v1    (publish version, then pin action)
~/Documents/WilderformTools/rensic/rensic-ingestion    Python transforms          (Foundry build)
```

Git remotes are Foundry Stemma, not GitHub. Do not print remotes, tokens, or Alchemy keys. Do not commit `.env.development`.

## The test that every new idea has to pass

Sit a stranger in front of a wallet. In about **30 seconds**, tell them **something true** they could not have seen on Etherscan as fast.

If the new idea does not help that sentence, it is decoration. Cut it, or park it in [scope.md](scope.md) under "later" / "never".
