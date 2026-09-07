# Why would anyone care?

The pipe works: Alchemy JSON lands in Foundry, objects light up, the desk opens a case. That is ingest. It is not a reason to care.

The reason to care is one job:

> Sit a stranger in front of a wallet and, in about 30 seconds, tell them something true they could not have seen on Etherscan as fast.

That sentence is the product. Everything else (ontology, Spark, functions, Vertex, AIP) exists to make that sentence cheaper, sourced, and honest.

## What Etherscan already does well

Etherscan is a ledger. Paste a hex, get a dump: every transfer, every token, every contract call, newest first. Power users live there. You will not beat it at "show me the chain."

What Etherscan does **not** do in 30 seconds:

- Lock a **question** (this seed, this window, this hop-1 working set) so you are not staring at a universe.
- Put **cited names** on the counterparties that matter (OFAC SDN, Tornado mixer contracts, a Proof-of-Reserve exchange wallet) without you opening ten tabs.
- Keep **unlabeled** unlabeled. A missing name is not clearance. A 0-100 "risk" is not a substitute for a source.
- Hand you a **case file** you can come back to, flag a counterparty on, and open as a small graph in Vertex.

Rensic is that case file. The ontology makes the rows clickable. The pack makes hex into a name with a URL. The working set makes hop 1 legible.

## The 30-second feeling (two lessons)

Two cases. Use both. Do not demo Vitalik first.

### Quiet wallet (the walkthrough)

Seed: `0x6d77695feba33e2e2fdd435997dc4f9ba8bfd532`

Lookback **365 days** (a 30-day window can miss a May inbound). After ingest, the desk should be able to say something like:

> One inbound transfer, 4 May 2026, 0.013 ETH, from Tornado Cash (mixer, public pack, cited). Working set is tiny. No OFAC. Window was 365 days on the wire.

That is more impressive than a heatmap. It proves you will not invent a story, and that a mixer name with a source appears without hunting. Click-by-click path: [DEMO.md](DEMO.md).

### Vitalik 30-day (the stress test)

Busy public wallets blow Alchemy's **200k transfer page cap**. The lesson is **working set, not universe**. Pin the seed. Show ~100 counterparties by ETH, with pack/investigator labels above unlabeled flow. If ingest truncated, say so out loud. 91,786 case-address rows is not insight.

## The three moves that make the sentence true

Blockchain investigation shops do not start from regressions. They start from **names**, **hops**, and **a window**. Full writeup: [analysis.md](analysis.md).

```
hex string     ->  name + source + URL     (attribution)
universe       ->  hop 0 seed, hop 1 set   (hops)
all time       ->  7 / 30 / 90 / 365 days  (window)
```

Entity packs are not a side quest. They **are** the 30-second edge vs Etherscan, as long as they stay sourced and dual-tier (official vs community caveat). See [entity-pack.md](entity-pack.md).

## What "true" means here

True means:

- The window was actually sent to Alchemy as `fromBlock` / `toBlock` (it is, today).
- A name on screen has a `source` and `source_url`, or it is marked investigator, or it is unlabeled.
- "Direct to mixer" means hop 1, not "somewhere in a 3-hop story we imagined."
- Page cap is a banner, not a complete history.

False (do not build toward these):

- "Risk score 73."
- "This wallet is suspicious."
- "AI thinks this is a mixer."
- Treating community Etherscan nametags as Coinbase-official.

## Where AIP fits (later)

AIP should eventually **emit the sentence**, not a novel. First assemble a brief from objects that already exist (the AI analyst tab already dumps JSON). Then a model may paraphrase **only those fields**. If a fact is not in the brief, the model may not say it. Full rules: [aip.md](aip.md).

## One paragraph north star

Rensic is a **case file**. Alchemy fills it. The ontology makes the rows clickable. Analysis is **names you can cite**, **hops you can explain**, and **a window you actually applied**. The demo win is a quiet wallet that stays quiet except for the one sourced mixer hop, and a risky counterparty that cannot hide behind volume. Everything else is later.
