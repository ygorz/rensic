# AGENTS.md — Rensic (Cursor / Grok)

Solo portfolio project home. **Not** an open-source contribute flow. Read this before editing docs or any nested package. Prefer product truth over polish.

## What Rensic is

On-chain **case file** on Palantir Foundry. Paste a wallet, pull a bounded hop-1 window, see counterparties as ontology objects with **meaningful labels** — not fake risk scores.

North star: sit a stranger in front of a wallet; in about **30 seconds**, tell them something true they could not have seen on Etherscan as fast.

If a change does not help that sentence, cut it or park it under "later" / "never" in `docs/scope.md`.

## Layout

```
rensic/
  README.md
  AGENTS.md
  docs/
  rensic-app/          # OSDK React desk (own .git / stemma)
  rensic-foundry/      # TS Functions v1 (own .git / stemma)
  rensic-ingestion/    # Python Spark transforms (own .git / stemma)
```

This umbrella is **not** a SuperRepo. Nested package dirs are gitignored here; each package keeps its own stemma origin.

### Umbrella git rules

- Tracks docs / README / AGENTS (and similar project-home files) only.
- Do **not** squash histories or rewrite remotes.
- **Never print remote URLs** (they embed tokens).
- Do not casually `git remote -v` into chat or logs.

`rensic-foundry/AGENTS.md` is the Palantir template sibling for Functions workflow; keep umbrella guidance here, Foundry-function specifics there.

## Locked product constraints

Do not "improve" past these without an explicit product decision:
1. **Layer 1 first** — pack CSV + desk JSON + Spark name join. Ontology/AIP chrome is not a substitute for a true, cited label.
2. **Official vs community** — dual-tier is honest only if official wins on conflict, community is caveated, and community never drives the scary sentence alone. Do not promote community nametags to official without a real citation.
3. **Person = first-party only** — person category needs a first-party citation (e.g. vitalik.ca). No Arkham dumps. Prefer few official persons.
4. **No Etherscan scrape as official** — do not grow community toward "we have Etherscan at home," and never treat scraped nametags as the official lane.
5. **ASCII UI** — Foundry hosting mangling fancy unicode; stick to ASCII in UI copy (e.g. `...`).

Also: hop-1 only for ingest; working set is seed + top ~100 by ETH (labeled first); Vertex cast is seed + labeled hop-1 then fill by flow, cap 16.

## Never commit

Across umbrella and packages:

- `.env`, `.env.*` (including `.env.development`)
- `Untitled/`
- `node_modules/`
- `.maestro/`
- `*.tsbuildinfo`
- Generated `vite.config.js` / `vite.config.d.ts`
- Secrets, tokens, Alchemy keys, Foundry remote URLs

## Local app

- Foundry npm token lives in the user's ~/.npmrc — do not invent or commit tokens.
- After dependency changes: `pnpm approve-builds` as needed (esbuild / native builds).
- Dev server: `cd rensic-app && pnpm run dev`

## Tests (before push)

| Package | What to run |
|---|---|
| **rensic-app** | vitest, tsc typecheck, eslint |
| **rensic-foundry** | Jest under functions-typescript (or Gradle check) |
| **rensic-ingestion** | pytest under transforms-python |

Fix failing tests that encode dual-tier / pack merge rules before changing merge behavior.

## How a change ships

1. **App** — commit, push to stemma, **git tag** for the hosted site.
2. **Functions** — commit, push, **publish** a Functions version, then pin actions.
3. **Ingestion** — commit, push, Foundry **pipeline build**.

Pushing `master` alone is not enough for production layers.

Do **not** casually rebuild `seed_rpc_config` — that is sensitive config; only touch when the change explicitly requires it.

## Docs map

Start at `docs/README.md`.

| Doc | Use |
|---|---|
| `docs/why.md` | 30-second sentence / why anyone cares |
| `docs/scope.md` | now / later / never fence |
| `docs/map.md` | three clones + how a change ships |
| `docs/architecture.md` | data flow |
| `docs/ontology.md` | objects, links, case vs address |
| `docs/entity-pack.md` + `docs/specs/entity-pack.spec.md` | dual-tier pack rules |
| `docs/ingestion.md` + `docs/specs/ingestion.spec.md` | hop-1 Spark pipe |
| `docs/functions-and-actions.md` + `docs/specs/functions.spec.md` | kinetic layer |
| `docs/desk.md` + `docs/specs/desk.spec.md` | OSDK UI |
| `docs/DEMO.md` | quiet-wallet click path |
| `docs/status.md` | wired vs leftover |
| `docs/archive-notes.md` | retired RIDs / study-guide leftovers |

Project path on this machine: `~/Documents/WilderformTools/rensic/`.
