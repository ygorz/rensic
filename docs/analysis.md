# Analysis that a person can use

You already have the pipe: Alchemy JSON -> Foundry flatten -> ontology -> desk.
That is ingest. It is not analysis.

Analysis, for this demo, is one job (same as [why.md](why.md)):

> Sit a stranger in front of a wallet and, in about 30 seconds, tell them
> something true they could not have seen on Etherscan as fast.

If a number on the screen cannot be turned into that sentence, it is decoration.
Cut it.

You do not need a statistics class. Blockchain investigation shops start from
**names**, **hops**, and **a window**. This page is only that, applied to the
desk you already shipped.

Related: [scope.md](scope.md), [entity-pack.md](entity-pack.md), [desk.md](desk.md),
[DEMO.md](DEMO.md).

---

## 1. What you are not building

Not a BI dashboard. Not Chainalysis. Not a 0-100 risk score.

Etherscan already dumps transactions. If Rensic is "the same dump, darker,
inside Foundry," the demo dies the moment someone clicks Vitalik.

Chainalysis's moat is **attribution** plus clustering they will not give you.
You cannot fake the clustering. You **can** ship honest names and honest
exposure.

Rule: unlabeled is a valid answer. A missing label is not clearance.
Do not invent `riskScore`.

---

## 2. The three moves that actually count

### Attribution (who is this 0x?)

A hex string is not information. A name with a source is.

The pack is dual-tier now (counts move; see [entity-pack.md](entity-pack.md)):

| Kind | What it means in the demo |
|---|---|
| `sanctions` | Do not treat as ordinary. Show it first. Official OFAC / FBI / etc. |
| `mixer` | Privacy tool / laundering venue. Tornado ETH is mixer, not current SDN. |
| `protocol` | Infrastructure, not a person. |
| `person` | Known public figure, cited. |
| `exchange` | Venue. Official lane is PoR/cited only. Community numbered hot wallets are caveated. |
| `shop` / `gambling` | Cited or community-caveated. Do not promote junk to official. |

Two more label sources, and they are different:

1. **Pack labels** -- public, cited (or community-caveated), everyone sees the same pack row.
2. **Investigator labels** -- this user, Flag. Official pack cannot be renamed.

Never let a user label silently overwrite OFAC. Pack wins on category.
User text sits beside it.

### Hops (how far from the seed?)

```
hop 0  the seed you pasted
hop 1  anyone who sent to it or received from it (direct counterparty)
hop 2  counterparties of those counterparties
```

Your working set is hop 1, ranked by ETH flow, seed pinned, labeled first.
That is the right default.

Hop 2 is where vendor products live and where you will drown
(Vitalik: tens of thousands of hop-1 rows already). Do not go there until
hop 1 is legible. Indirect exposure ("two hops from a mixer") is a later
sentence, and you must say **direct** vs **indirect** out loud or you are lying.

### Window (which time is the question?)

A case without a time window is not a case. It is a scrape.

Lookback is stored on the Investigation Case **and** sent to Alchemy as
`fromBlock` / `toBlock`. Always say the window in the sentence:
"In the last 365 days, this seed..." not "this seed has..."

Demo default: 30 days on busy seeds. Quiet wallets often need 365 so a
spring inbound still appears in autumn.

---

## 3. The sentence is the product

Before you add a chart, write the sentence the desk should support.
If you cannot write it, you do not know what to compute.

Good sentences (true, short, sourced):

- "No labeled counterparties in this working set."
- "Direct to Tornado Cash (mixer, official pack, OFAC notice, not current SDN)."
- "Direct to an OFAC SDN address."
- "Seed is Vitalik. Working set capped; 200k transfer page limit."
- "Largest outbound in window: 0.0012 ETH to 0xfeee... (unlabeled)."

Bad sentences (do not build toward these):

- "Risk score 73."
- "This wallet is suspicious."
- "AI thinks this is a mixer."
- "91,786 addresses." as if that were insight

The AI analyst tab should eventually **emit the sentence**. The JSON brief
is the right intermediate: it is honest about what the slice contains.
AIP later: [aip.md](aip.md).

---

## 4. What to compute (and what to ignore)

### Compute, and put on the rail

| Signal | How you get it | What it is for |
|---|---|---|
| Seed in / out / tx count **in this case** | Case Address / case fields | The size of the question |
| Window | Case `timeWindow*` (applied on the wire) | The question itself |
| Direct exposure | Hop-1 working set intersect pack (`sanctions`, `mixer`) | The punch -- prefer **official** |
| Top counterparties by native ETH | Rank on Addresses | Where to click next |
| Unlabeled share | hop-1 with no pack and no user label | Honesty |

### Do not compute for the demo

- PageRank, Louvain, t-SNE, "entity clustering"
- USD prices
- Token-balance history as the hero metric
- Behavioral score, velocity, peeling-chain detectors
- Cross-chain until ETH hop-1 is sharp
- AIP narrative that invents facts not in the brief

Those are real techniques. They are also how you hide that the labels are
thin. Get the labels and the sentence right first.

---

## 5. How a 30-second demo should feel

### Quiet wallet (`0x6d77...d532`)

Click path: [DEMO.md](DEMO.md). 365-day lookback.

The lesson is **restraint plus one sourced name**. After ingest you should
be able to say the inbound Tornado hop without opening Etherscan. If the
desk shows a wall of metrics and hides the mixer, you failed the demo.

### Vitalik 30-Day

The lesson is **working set, not universe**. Pin the seed. Keep ~100
counterparties. Page cap is a banner. Success is a true sentence about
**this window**, not 200,000 rows.

If a sanctions or mixer chip appears in hop 1, it should be impossible to
miss: danger outline, near the top, rail sentence changes. You do not need
a new metric. You need **sort + chrome**. `rankAddresses` already puts
labeled above flow. Keep it.

---

## 6. Ontology, used as analysis (not as a schema museum)

You have objects. Analysis is walking them with a question.
Full type guide: [ontology.md](ontology.md).

```
InvestigationCase
  └── Case Address (membership: seed vs discovered, hop)
        └── Address (label from pack + Flag)
              └── Transaction (from / to, value, time)
```

Questions the objects should answer without a new dataset:

- Who is hop 0? (`Case Address` seed)
- Who did they touch? (transactions in this case, other side)
- Which of those have names? (pack + `addressLabel`)
- Did we touch sanctions or a mixer **directly**?
- What is the largest native movement in the window?

Vertex is for the slice (seed + labeled, cap 16), not the 91k dump.

---

## 7. A practice loop

Do not read a textbook. Run the desk.

**Day 1 -- Quiet wallet.** Write the sentence by hand before you look at
the rail. Then see if the rail matches. Note every chip, sort, and empty
state that got in the way.

**Day 2 -- Vitalik 30-Day.** Same sentence exercise. You will want more
metrics. Write them down. Cross out any you cannot explain in one breath.

**Day 3 -- Hypothetical OFAC hit.** Pick one SDN address from the CSV.
Imagine it appears as hop 1 with 0.0003 ETH. What should the desk do?
(sort, chip, rail sentence, Vertex cast). That spec is the next ticket if
anything still hides.

**Day 4 -- User label.** You decide an unlabeled hop is "gas station from
the intake form." Where does it live? Who sees it? Does it change
exposure? (It should not change `sanctions`. It may change the sentence:
"unlabeled except my note.")

**Day 5 -- Window.** 7-day vs 30-day vs 365 on the same seed. If the story
changes, the window belongs in the sentence (it already belongs on the wire).

That is data analysis training for this project.

---

## 8. Short reading (only if a ticket needs it)

- `SOURCES.md` next to the CSV. Attribution bible.
- OFAC SDN FAQ + the 2025-03-21 Tornado deletion notice. "Was designated"
  vs "is designated."
- Alchemy `alchemy_getAssetTransfers` -- you call `fromBlock` / `toBlock`.
- Palantir ontology best practices / structural guidance / anti-patterns
  (linked from [ontology.md](ontology.md)). Workshop is not the product.
- Optional, later: vendor **marketing** posts about direct vs indirect
  exposure. Steal the language, not the scores.

Skip: random crypto data-science courses, Kaggle, graph neural nets.

---

## 9. North star, in one paragraph

Rensic is a **case file**. Alchemy fills it. The ontology makes the rows
clickable. Analysis is **names you can cite**, **hops you can explain**,
and **a window you actually applied**. The demo win is a quiet wallet that
stays quiet except for the one sourced mixer hop, and a risky counterparty
that cannot hide behind volume. Everything else is later.
