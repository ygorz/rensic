# Glossary

Words used in the Rensic guides, in the sense this project uses them.

**Action (Foundry)** -- A governed business operation that edits ontology objects (create case, label address). Not a Spark job. Not "set this one field" if you can name the operation.

**AIP** -- Palantir's LLM layer. In Rensic, later: paraphrase a grounded brief. Not a risk engine.

**Alchemy** -- RPC / `alchemy_getAssetTransfers` provider. Hop-1 in and out of the seed, windowed by block.

**Address** -- Ontology identity of a wallet or contract on **one** chain. Primary key `chain:hex`.

**Attribution** -- Putting a cited name on a hex. Pack + investigator notes. Not clustering.

**Case Address** -- Membership of an Address in an Investigation Case (hop, role, case-scoped ETH). Object-backed link, not extra fields on Address.

**Chain Configuration** -- Per-chain RPC settings the investigator saves. Keys live here, not in git.

**Classic Compass** -- Ontology lives in Ontology Manager, not in `ontology.mts`. Rensic is this. Opposite of SuperRepo for ontology source.

**Community (tier)** -- Unofficial nametags (Etherscan-style). Caveated chrome. Official wins on conflict.

**Direct exposure** -- Hop 1 intersect a pack category (usually sanctions/mixer). Not "somewhere in a rumor of hop 3."

**Function (Foundry)** -- TypeScript (here) logic: ontology edits, Vertex search-around, later AIP. Publish a **version**, then pin the action.

**Golden Hammer** -- Palantir anti-pattern: one tool for every job (e.g. an action that "syncs Alchemy"). Rensic split: pipeline ingest, action for decisions, function when two objects or live graph logic.

**Hop** -- Graph distance from the seed. 0 = seed, 1 = direct counterparty. Ingest is hop 1 only.

**Investigation Case** -- The file: seed, chains, window, status. The question, not the whole chain.

**Kitchen Sink** -- Palantir anti-pattern: every ETL column becomes a property.

**Kinetic** -- Actions + functions (how the ontology changes).

**Labeled risk (rail)** -- Count of working-set addresses tagged sanctions or mixer in the pack. Not a vendor score. Should prefer official-only.

**Lookback / window** -- 7/30/90/365 days on the case, applied as Alchemy `fromBlock`/`toBlock`.

**Magritte** -- Foundry data connection (egress to Alchemy). Not a git clone.

**Materialization** -- Dataset snapshot of ontology objects so Spark can read cases (including edits).

**Object-backed link** -- Relationship that has its own metadata (here: Case Address between Case and Address).

**Official (tier)** -- Cited pack lane (OFAC, FBI, protocol docs, PoR). Flag cannot rename.

**Ontology** -- Palantir's map of the business: object types, properties, links, plus actions/functions.

**OSDK** -- Ontology SDK. The React desk talks to Foundry through this, not through Workshop.

**Pack** -- `known_entities.csv` / JSON. Public names with sources. Dual-tier.

**Page cap** -- Alchemy pagination ceiling (~200k transfers). Banner, not complete history.

**Pin (action)** -- Point an action at a published functions version. Pushing git does not pin.

**Risk score** -- 0-100 vendor-shaped property on Address/Case. **Do not fill.** Unlabeled is not clearance.

**Semantic** -- Object types, properties, links (what exists).

**Seed** -- The wallet the investigator pasted. Hop 0. Pinned in the working set.

**Semantic vs kinetic** -- Palantir overview split. Types vs how they change.

**Spark / transforms** -- Python pipeline in `rensic-ingestion`. Builds run on Foundry.

**Stemma** -- Foundry git for code repositories. Remotes are not GitHub. Do not print them.

**SuperRepo** -- Ontology-as-code (`ontology.mts`). Rensic is not this yet.

**Tag (git)** -- How the OSDK app CI uploads the hosted site.

**Unlabeled** -- No pack row and no investigator Flag. Valid. Not "safe."

**Vertex** -- Foundry graph app. Rensic opens it on a small cast (cap 16), not the full case dump.

**Working set** -- Seed + top ~100 hop-1 counterparties by ETH, labeled first. The anti-Vitalik rule.

**Workshop** -- Palantir app builder. Not the Rensic product UI.
