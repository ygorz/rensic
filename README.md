# Rensic

**Look at one crypto wallet over a stretch of time. See who it traded with, with names you can cite, instead of spelunking Etherscan.**

Rensic is built on **Palantir Foundry**. Paste a wallet, pick a time window, pull hop-1 activity through Alchemy, and open a **file**: named addresses, fund flow, ledgers, and a short grounded summary.

The win is speed to a true sentence. Sit someone in front of a wallet and, in about 30 seconds, tell them something they could not have seen on Etherscan as fast. No invented risk scores.

## Demo

<!-- Add the walkthrough video here when ready.
[Watch the walkthrough](docs/demo.mp4)
-->

**Walkthrough video coming soon.** Until then, the story is: one wallet, one window, named addresses, digestible fund flow.

## What you get

- **Fund flow** between the file wallet and each address it touched
- **Addresses** ranked for a working set (seed pinned, labeled first, then by ETH moved)
- **Transactions** and **token transfers** as quiet ledgers for that wallet and window
- **Summary**: a short read from transfers and public names, nothing invented
- A **sourced entity pack** so hex becomes a name with a citation when we have one

## Stack

| Layer | What |
|---|---|
| Platform | Palantir Foundry (classic Compass ontology, not a SuperRepo) |
| UI | OSDK React (Vite), hosted on Foundry |
| Functions | TypeScript Functions v1 (create / expand / label / delete) |
| Ingest | Python Spark transforms, Alchemy `getAssetTransfers` |
| Names | Dual-tier public pack (~5.5k rows: official + community) |
| Scope | Hop-1 activity for one wallet window, multi-chain keys (`chain:0x...`) |

## Honest about Foundry

This is a **portfolio writeup**, not a clone-and-run OSS app. The live ontology, datasets, secrets, and hosted site live on a Foundry enrollment. The three code packages (`rensic-app`, `rensic-foundry`, `rensic-ingestion`) are browsable here as snapshots. They ship to production through Foundry Stemma remotes, not this GitHub remote.

If you are reading this as a recruiter or hiring manager: the code is real and ran end to end. Reproducing it needs Foundry access, Alchemy keys, and the enrollment that holds the ontology.

## Read next

- **[Architecture](docs/architecture.md)**: how Alchemy, Spark, ontology, functions, and the UI fit together
- [docs/](docs/): short index and specs

## Layout of this repo

```
rensic/
  README.md
  AGENTS.md
  docs/
    architecture.md
    specs/
  rensic-app/         # OSDK React UI (snapshot)
  rensic-foundry/     # TypeScript Functions v1 (snapshot)
  rensic-ingestion/   # Python Spark transforms + entity pack (snapshot)
```

The folders above are **read-only snapshots** of the Foundry Stemma checkouts so you can browse the code. Real ship remotes stay on Foundry. Local auth files (`.npmrc` with registry tokens) are not included.

## What we refuse

- Fake 0-100 risk scores
- Hop-2 product surface for a busy wallet demo
- Treating community nametags as official exchange identity
- AI that invents counterparties or hop stories not in the facts

Built by George Gorzhiyev as a first serious Foundry portfolio piece.
