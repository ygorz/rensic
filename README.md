# Rensic

On-chain **case file** on Palantir Foundry. Paste a wallet, pull a bounded window of hop-1 activity, see counterparties as ontology objects with **meaningful labels** — not fake risk scores.

North star: sit a stranger in front of a wallet; in about **30 seconds**, tell them something true they could not have seen on Etherscan as fast.

This folder is the tidy project home for docs + the three Foundry stemma checkouts. **Not a SuperRepo.**

## Layout

```
rensic/
  README.md  CONTRIBUTING.md  docs/
  rensic-app/  rensic-foundry/  rensic-ingestion/
```

Each package keeps its own .git and Foundry stemma origin. Do not squash histories. Do not rewrite remotes. Do not print remote URLs.

## Packages
- rensic-app: OSDK React desk
- rensic-foundry: TS Functions v1
- rensic-ingestion: Python Spark transforms

## Foundry enrollment

- Host: georgegorzhiyev.usw-17.palantirfoundry.com
- Project: /George Gorzhiyev-a8216a/Rensic
- Remotes: Foundry Stemma (not GitHub)
- Never commit env files or secrets

## Docs

Start at docs/README.md
- docs/architecture.md — data flow
- docs/why.md, scope.md, map.md
- docs/specs/ — entity-pack, ingestion, desk, functions
- docs/archive-notes.md — retired study guide RIDs

## How a change ships

1. App: commit, push, git tag for hosted site.
2. Functions: commit, push, publish version, pin actions.
3. Ingestion: commit, push, Foundry pipeline build.

Pushing master alone is not enough for production layers.
