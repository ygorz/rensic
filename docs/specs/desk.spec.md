# Spec: desk (OSDK UI)

Repo: rensic-app. Vite + React + OSDK.

## Flag / labelAddress

- Action label-address writes Address.addressLabel.
- Official pack: rename blocked; note only.
- Community: investigator name may override display; pack on hover.
- Unlabeled: write a name; optional note.
- Pack category is never overwritten.

## Lookback picker

Home create form: 7 / 30 / 90 / 365. Default 30.
Quiet wallets often need 365.

## Hover cards and ranking

- Hover shows pack name, tier, source, investigator note.
- Working set: seed pinned, labeled first, then ETH flow; cap 100.
- Official sanctions/mixer sort above unlabeled volume.

## Chains

Shared module: `rensic-app/src/chains.ts` (single source for Home pickers + CaseView explorers).

Desk list matches ingest `CHAINS`: ethereum, base, arbitrum, polygon, optimism, bsc, robinhood, avalanche.

UI note: chains only work if Alchemy key/network is configured in Foundry Chain Configuration for that network.

## Delete investigation

Case rail "Delete investigation" with confirm. Calls function-backed `delete-investigation`.
Cascades CaseAddress + InvestigationNarrative for that caseId, then the InvestigationCase.
Does not delete global Address objects, known_entities, or shared ingest datasets.
After success, navigates home.
