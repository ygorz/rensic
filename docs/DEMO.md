# Rensic desk demo

ASCII only. This is the 30-second path for a quiet wallet and the copy that must not lie.

Why this path exists, and how ingest / pack / ontology back it: [README.md](README.md). Full analysis writeup: [analysis.md](analysis.md).

## Quiet wallet (30 seconds)

1. Header: + New investigation.
2. Title anything (e.g. Quiet mixer hop).
3. Seed: 0x6d77695feba33e2e2fdd435997dc4f9ba8bfd532
4. Chain: ethereum.
5. Lookback: 365 days (quiet wallets). Do not leave 30 selected; a 30d window misses a 4 May 2026 inbound.
6. Create. The form writes Investigation Case + seed Case Address. Alchemy ingest still runs from the pipeline, not this popover.
7. After ingest: one inbound 0.013 ETH from Tornado Cash on 4 May 2026. Addresses should show the mixer on top of unlabeled flow. Transactions sentence uses the pack name, not only the hex.

365d covers ~122 days from 4 May 2026 to 3 Sep 2026. 30d is the demo default for busy seeds such as Vitalik, not a complete chain history.

## Lookback choices

The popover is a closed set: 7 / 30 / 90 / 365. Default 30 (demo). 365 is for quiet wallets. The case window is a fact: the desk says Nd, and ingest bounds Alchemy with fromBlock/toBlock. It does not scrape unbounded history.

## What unlabeled means

Unlabeled means the public pack has no name for that hex, and no investigator Flag has been written. It is not a risk score and not "unknown entity" from a vendor. Pack chips (sanctions, mixer, protocol, person, exchange) never get overwritten by Flag. Flag writes Address.addressLabel via the existing Label Address action; the desk shows pack name first, then `my note: ...` beside it.

## Page-cap note

If transactionCount is 200000 or more, ingest hit Alchemy's page cap. That banner is a stress-test warning, not a complete history. A 30d Vitalik slice can hit the cap. A quiet 365d wallet with one hop will not.

## Working set

The Addresses tab is seed + top 100 by ETH in this window, with pack-labeled and investigator-labeled rows sorted above unlabeled flow. Fund flow Vertex opens the selected Address RID and lists seed + every labeled hop-1, then fills remaining slots by ETH flow up to 16. It is not a dump of every case address.
