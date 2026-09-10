# Spec: UI (OSDK React)

Repo: rensic-app. Vite + React + OSDK.

Product noun in chrome: **file**. Ontology types may still say Investigation* (see architecture naming note).

## Flag / labelAddress

- Action `label-address` writes Address.addressLabel.
- Official pack: rename blocked; note only.
- Community: a user-set label may override display; pack stays on hover.
- Unlabeled: write a name; optional note.
- Pack category is never overwritten.

## Lookback picker

Home create form: 7 / 30 / 90 / 365. Default 30.
Quiet wallets often need 365.

## Hover cards and ranking

- Hover shows pack name, tier, source, user note.
- Working set: seed pinned, labeled first, then ETH flow; cap 100.
- Official sanctions/mixer sort above unlabeled volume.

## Chains

Shared module: `rensic-app/src/chains.ts` (single source for Home pickers + explorers).

UI list matches ingest `CHAINS`: ethereum, base, arbitrum, polygon, optimism, bsc, robinhood, avalanche.

Chains only work if an Alchemy key/network is configured in Foundry Chain Configuration for that network.

## Delete file

Rail control deletes the open file (confirm). Calls function-backed `delete-investigation` (leftover action id).

Cascades CaseAddress + InvestigationNarrative for that caseId, then the InvestigationCase.
Does not delete global Address objects, known_entities, or shared ingest datasets.
After success, navigates home.
