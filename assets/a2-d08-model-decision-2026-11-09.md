# A2 / D08 Model Decision — 2026-11-09 (chat-3)

**Purpose.** The arithmetic pass of the same date found two claims in A2 and D08
that do not reproduce from the model the docket ships. It recorded them and left
them open, correctly, because resolving them means choosing which model governs
and that is an owner decision. This document exists to make that choice small.

It does three things the pass record did not: it identifies the *one* parameter
that separates the two findings, it shows that D08 contradicts **itself** —
independently of A1 and of A2 — and it prices each option so the decision is a
comparison rather than a research question.

**Read the pass record first:** `assets/a2-d08-arithmetic-pass-2026-11-09.md`.
Everything below assumes its 78-of-78 arithmetic result and does not repeat it.
Re-run both checks with:

```
python3 -I assets/a2-d08-arithmetic-pass.py
python3 -I assets/a2-d08-model-decision.py
```

---

## 1. The decision in one paragraph

Four different numbers for the probability that a missed bearing defect becomes a
catastrophic event are in circulation. **0.05%** in the A1 workbook, whose own
note calls 2% physically impossible. **2%** in `backend/roi.py`, whose own note
calls that value conservatively low. An implied **0.04%–0.07%** behind A2's
2.0x/4.1x anchors, on a frame the documents never state. And **0.8%–1.4%** implied
by D08's headline benefit figures. On top of that, the two files disagree about
the contained-failure base cost — $500,000 in A1, a $9.25M midpoint in `roi.py` —
so `roi.py` values a missed defect at **29×** A1's figure.

Every finding in the pass record traces to those two choices: which probability,
applied to which cost. Choose them and Findings 1 and 2 close in one edit pass
across four files.

**Recommendation: A1's 0.05% governs, the contained cost stays at A1's $500,000,
the anchors are restated from that model, and `roi.py` is brought into line.** The
reasoning is in §7. The case against it is in §7 and it is not weak — read it
before agreeing. One thing should happen first: value the cost components A1
omits, which may raise the benefit figure honestly and make the choice easier
(§7, final paragraph).

---

## 2. What the pass record established, and what it did not

Established, and independently reconfirmed here: 78 of 78 figures in A2 and D08
recompute correctly. The band structure, the worked examples, the pilot build-up,
the three-year cost table, the performance caps, the cumulative schedule and the
5% escalation are all arithmetically sound. Nothing in either document is a
miscalculation.

Not established, and this is what changes the picture:

1. The pass record concluded no parameter set reproduces both anchors. That is
   true *on the two cost bases it tested*. On a third basis — a four-year cost
   including the pilot and three full production years at list, no conversion
   credit — both anchors reproduce from a **single** value of the catastrophic
   probability, to within 1.8%. The anchors are not arbitrary. They are
   recoverable, and §3 shows how.

2. The pass record compared D08 §5–§6 against A1 and against the fee schedule,
   but never against **D08 §4** — the section immediately above it in the same
   document. §4 prices a prevented failure at roughly $993,000. §5 prices the
   same prevented failure at $8.6M–$11.4M. That is a contradiction inside one
   document, and it does not depend on A1 being right about anything.

---

## 3. Finding 1, restated precisely

**The claim.** A2 §3.2: the customer's modelled return rises "approximately 2.0x
at 500 axles, rising to about 4.1x at 10,000." D08 §3 restates both figures,
dropping the hedges: "2.0x at 500 axles rising to 4.1x at 10,000."

**What the model is.** Three-year net benefit, linear in axles, using A1's
inputs: 0.7 defects missed per 500 axles per year (AxiomDynamics catches 2.1, a
legacy network catches 1.4), $1,500 per false alarm, and a per-missed-defect
value of `(1−p)·$500,000 + p·$1,000,000,000`.

**Why the anchors looked unreproducible.** The pass record tested the A2 basis
(pilot + credit + three production years, $1,180,000 at 500 axles) and the A1
basis ($285,000 + two production years, $885,000). Neither works. But the ratio
the anchors require is fixed by the linear model:

```
r(10,000) / r(500)  =  20 · cost(500) / cost(10,000)  =  4.1 / 2.0  =  2.05
therefore            cost(10,000) / cost(500)         =  9.76
```

The A2 basis gives 10.53. The A1 basis gives 9.47. **A four-year cost including
the pilot and three full years at list, with no conversion credit, gives 9.86** —
close enough that a single probability satisfies both anchors.

| Basis | cost(500) | cost(10,000) | ratio | vs required 9.756 | p from 2.0x | p from 4.1x | spread |
|---|---:|---:|---:|---:|---:|---:|---:|
| **Pilot + 3 full yrs, no credit** | $1,270,000 | $12,520,000 | **9.86** | **+1.0%** | **0.0714%** | **0.0727%** | **+1.8%** |
| Pilot + 3 yrs, with credit | $1,180,000 | $12,430,000 | 10.53 | +8.0% | 0.0629% | 0.0718% | +14.3% |
| A1 as-built ($285k + 2 yrs) | $885,000 | $8,385,000 | 9.47 | −2.9% | 0.0348% | 0.0323% | −7.0% |
| Three production years only | $900,000 | $12,150,000 | 13.50 | +38.4% | 0.0362% | 0.0691% | +91% |

At **p = 0.0714%** the first basis produces **2.00x at 500 axles and 4.06x at
10,000** against stated claims of 2.0x and 4.1x. **That is consistent with the
anchors having been computed on this frame — but it is not proof that they were,
and the paper should not claim it.** The reason is in the next paragraph, and it
is the reason Finding 1 stays open rather than being closed as solved.

The cost ratio the anchors demand is a property of the *pricing*, not of the
benefit model, so it is fixed regardless of any probability: `cost(10,000) /
cost(500)` must equal 9.756. That is why the first row's two implied probabilities
agree — the ratio is doing the work, and any `p` on that basis fits both anchors
to within a few percent. But the *absolute level* of `p` depends on the benefit
horizon, which the document never states. Put three years of benefit against the
four-year cost and `p` = 0.0714%; put four years of benefit against it and
`p` = 0.0412%, which **also** satisfies both anchors (spread 2.3%). Both are
defensible readings of an undescribed frame.

So the honest finding is narrower than "this is where the numbers came from":

> The anchors are mutually consistent with a single linear model on a
> pilot-plus-three-years cost basis. They cannot be reproduced to a stated frame
> because no frame is stated, and the undisclosed parameter that fits them is
> between 0.04% and 0.07% — an order of magnitude below the 2% `roi.py` uses and
> close to A1's 0.05%, but not the value A1 ships.

That is still a disclosure defect, and it still needs fixing. It is not a
fabrication, and the paper should not accuse the earlier drafter of one.

Note what the last two columns do. The first row is the only one where a single
probability satisfies both anchors — the two implied values differ by 1.8%, which
is rounding. Every other basis demands two different probabilities, by 7% to 91%.
That asymmetry is the signature of a number computed once, on one basis, and then
requoted as though it were a property of the rate card.

**Why they still cannot ship as written.** Three reasons, in ascending severity:

1. **The basis is not the one the docket states.** Both documents present the
   multiple as a property of the rate card. It is a property of one particular
   four-year frame — pilot plus three full years at list, no conversion credit —
   and the buying decision D08 describes elsewhere is a *three-year* commitment
   after conversion on which the same benefit is 1.77x and 3.36x. No document
   names the frame, so the number cannot be audited without reverse-engineering
   it, which is what §3 above had to do.

2. **0.07% contradicts both models in the repository.** A1 ships 0.05% and its
   B17 note states that even 2% "would imply dozens of billion-dollar events
   annually nationwide — physically impossible." `roi.py` ships 2% and its own
   note calls that value "set conservatively low." **The two files do not merely
   differ; they disagree about which direction is conservative.** Both cannot be
   right, and neither is labelled as the descoped opinion. 0.07% is a third value
   used in customer-facing material and disclosed in neither file — the worst
   placement of the three, because unlike the other two it is not marked as an
   assumption anywhere.

3. **2.0x is not conservative or aggressive — it is unanchored.** At 500 axles
   A1's defaults produce 2.32x on an annual basis (benefit against the $300,000
   licence), 2.58x on three-year benefit against the three-year fee excluding the
   pilot, and 1.77x on three-year benefit against the four-year commitment. The
   anchor sits in the middle of that spread and matches none of them, because the
   spread is produced by three defensible definitions of "return" and the
   document never says which one it means. That is the actual defect: not that
   the number is too high or too low, but that it is not attributable to a stated
   frame. A procurement analyst who runs the arithmetic gets a different answer
   depending on the frame they pick, and cannot tell which frame the document
   intended — which is precisely the objection the paragraph exists to pre-empt.

**The monotonic claim is true on every basis tested.** It should survive. The
numbers attached to it should not.

---

## 4. Finding 2, restated precisely

**The claim.** D08 §5: $6M–$8M of avoided damage in the pilot year, 16x–22x the
$370,000 fee. $14M–$20M over four years, 12x–17x. §6: $40M–$60M over six years,
20x–30x.

### 4.1 D08 is internally inconsistent, before A1 is involved

Section 4, immediately above, works a transparent example: at 1,000 axles the
corroborated prevented cost is **$1,390,000**, and the performance fee is 3% of
it. At 1.4 missed defects per 1,000 axles that is **$992,857 per prevented
failure**.

Section 5 then prices the same kind of prevented failure at $6M/$0.7 =
**$8,571,429** to $8M/$0.7 = **$11,428,571**. A ratio of **8.6x to 11.5x**.

**One honest qualification first.** §4's figures are *corroborated* prevented
cost — a subset gated by the customer's own root-cause analysis — while §5's are
*modelled* avoided damage across the whole fleet. Those are not strictly the same
quantity, and a careful reader could argue §4 prices the subset that got
proven while §5 prices the expected total. So the word "contradiction" slightly
overstates it.

But the objection does not rescue the document, for three reasons. The ratio
survives the comparison per axle rather than per defect ($1,390 per axle against
$12,000–$16,000 per axle, still 8.6x–11.5x), so it is not an artefact of the
defect rate. It is visible to any reader who reads D08 in order, without the
workbook. And it is load-bearing in the wrong direction: **§4's performance fee
is computed on the low valuation while §5's headline benefit is computed on the
high one.** A customer who elects the component agrees to a fee calculated on a
prevented failure worth about $993,000, having been sold the product by a section
that values the same failure at $8.6M–$11.4M. If §4's $993,000 is right, §5 is
roughly ten times too high; if §5 is right, the performance fee is roughly a
tenth of what the customer's own act of corroboration is worth.

**And §4's number is essentially A1's.** $992,857 against A1's $999,750 at
0.05% — a 0.7% difference, well inside the rounding of an illustrative example.
That is the most useful fact in this document: **D08 already contains an
A1-consistent valuation, in §4, four pages before the section that abandons it.**

### 4.2 The three periods do not reconcile with each other either

Hold the customer fixed — 500 axles, one site, same fleet, same defect rate — and
read the three periods as a single consistent model:

| | Low case | High case |
|---|---:|---:|
| Pilot year | $6.0M | $8.0M |
| Four-year total | $14.0M | $20.0M |
| → implies years 2–4 | $2.67M/yr | $4.00M/yr |
| → that is this share of the pilot year | **44%** | **50%** |
| Six-year total | $40.0M | $60.0M |
| → implies years 5–6 | $13.0M/yr | $20.0M/yr |
| → that is this share of the pilot year | **217%** | **250%** |

The same fleet is modelled as producing less benefit per year *after* the pilot
than during it, and then more than twice as much again in years five and six.
Neither trend is explained. Neither is in A1 — A1 is flat-linear in axles and
years. A reader who does the subtraction will ask what changes in year five, and
there is no answer, because nothing does.

**A caveat on the comparison, in D08's favour.** This table holds the fleet at
500 axles throughout. D08 §2 describes the pilot as 100–200 axles, so the pilot
year's benefit in §5 may be computed on a different fleet than the production
figures that follow it, and mixing the two into one arithmetic series is my
assumption rather than the document's own claim. That said, the assumption makes
the document look *better* than it would at 200 axles: a 200-axle pilot producing
$6M–$8M would imply a per-defect value roughly two and a half times higher again.
So the trend artefact is real under the reading most favourable to D08, and the
finding stands either way — but it is the fleet-size ambiguity in §2, not the
period figures alone, that makes the three periods unreadable as one model.

### 4.3 Against A1, at identical inputs

A1 at 500 axles with default assumptions produces **$696,675 net annual
benefit**. D08's claims, and what they would have to become if A1 governs:

| D08 claim | Period | A1 produces | Ratio | Restated from A1 |
|---|---:|---:|---:|---:|
| $6M–$8M | pilot year | $696,675 | 8.6x–11.5x | **$696,675** |
| $14M–$20M | 4 years | $2,786,700 | 5.0x–7.2x | **$2,786,700** |
| $40M–$60M | 6 years | $4,180,050 | 9.6x–14.4x | **$4,180,050** |

And the returns those produce against the fees A2 actually charges — which is a
very different story from the one §5 and §6 tell:

| Frame | Fee | A1 benefit | Return |
|---|---:|---:|---:|
| Pilot year | $370,000 | $696,675 | **1.88x** |
| Four-year commitment | $1,180,000 | $2,786,700 | **2.36x** |
| Six-year commitment | $1,825,750 | $4,180,050 | **2.29x** |

**D08 currently promises 16x–22x and 20x–30x. The model it names as its own
instrument of record produces 1.9x–2.4x.** That is not a rounding difference.
It is the difference between a compelling business case and a marginal one, and
it is the single most consequential number in the docket.

### 4.4 The third divergence: the dashboard

`backend/roi.py` differs from A1 in **two** ways, not one, and the second is
larger than the first.

- **Probability.** `roi.py` uses 2%; A1 uses 0.05% — a 40× difference, and the
  divergence the README already discloses.
- **Contained-failure cost.** `roi.py` uses the **$9.25M midpoint** of the two
  sourced NTSB figures; A1 uses a **$500,000 typical** cost, deliberately, because
  A1's B14 note says the $5M/$13.5M bench figures are "an investigated,
  above-average event — do NOT use as your typical cost." So the two files
  disagree about which sourced number is the base case, not only about `p`.

The per-missed-defect values that result:

| Basis | Value per missed defect |
|---|---:|
| A1: contained $500k, p = 0.05% | $999,750 |
| A1's contained cost at roi.py's 2% | $20,490,000 |
| **`roi.py` as shipped: contained $9.25M, p = 2%** | **$29,065,000** |

So the live dashboard values a missed defect at **29.1×** A1's figure, and the
2% parameter alone accounts for only 20.5× of that — the rest is the contained-
cost disagreement. The dashboard is what a prospect actually sees in a demo, and
it is the artifact furthest from the workbook by a wide margin.

**An important limit on this comparison:** `roi.py` takes a list of warrants, not
an axle count, so it cannot be run "at 500 axles" directly — it prices whatever
warrants the current fleet snapshot produced. The figures above compare the two
files' *per-defect valuations*, which is the correct like-for-like comparison,
rather than pretending the dashboard produces an annual-fleet benefit number it
has no input for. Anyone quoting "the dashboard says $14.3M" has re-run A1's
formula at 2% and mislabelled it; that number appears in no file.

---

## 5. What the anchors look like under the recommendation

If A1 governs, the 2.0x/4.1x sentence is replaced by values the shipped model
produces. Net three-year benefit, A1 defaults, against the A2 four-year
commitment:

| Axles | 3-yr benefit | 4-yr commitment | Return |
|---:|---:|---:|---:|
| 500 | $2,090,025 | $1,180,000 | **1.77x** |
| 1,000 | $4,180,050 | $1,930,000 | **2.17x** |
| 2,000 | $8,360,100 | $3,430,000 | **2.44x** |
| 5,000 | $20,900,250 | $6,805,000 | **3.07x** |
| 10,000 | $41,800,500 | $12,430,000 | **3.36x** |

Monotonic, as the claim requires: 1.77x → 3.36x. The sentence survives; only the
two numbers change. This is the better outcome for the document as an argument,
because the trend is the point and the anchors were decoration.

---

## 6. The options

### 6.1 Option A — A1 governs, anchors restated, `roi.py` corrected ★ recommended

`p = 0.05%` and contained cost $500,000 become the single basis — matching A1 as
it ships. 2.0x/4.1x becomes 1.77x/3.36x. D08 §5–§6 headline benefits are restated
from A1. `roi.py` moves from 2% to 0.05% *and* from the $9.25M midpoint to a
contained cost consistent with A1's B14 note, so the dashboard stops valuing a
missed defect at 29× the workbook's figure.

**What it costs.** The pitch becomes materially weaker. D08's story changes from
"20x–30x return" to "~2.3x over six years." Some prospects will not proceed on
that number. This is the honest cost and it is large.

**What it buys.** Every number in the dossier reconciles to one model, one
parameter, and one cited source. The document survives its own audit. D14 §8
identifies the gap between the sales description and the contract as the
product's largest liability, and explicitly the one that is "fully controllable
and therefore inexcusable if it occurs" — this option is the only one that
closes it.

**One thing to understand before choosing it:** 2.3x is what the model produces
*because the product is priced near the value it creates*. That is not a defect
in the arithmetic. A 20x return on a $370,000 fee would imply the fee is roughly
a tenth of what the product is worth, and would invite exactly the question a
procurement analyst asks next: why is it so cheap.

### 6.2 Option B — D08's figures stand, A1 is recalibrated upward

If D08 is right, the per-missed-defect valuation is wrong and `p` rises from
0.05% to roughly **0.8%–1.4%**. A1's B17 is edited, and everything downstream
recomputes — including the 2.0x/4.1x anchors, which would then need restating
anyway.

**The problem.** A1's B17 note already argues against this: 2% would imply dozens
of billion-dollar events annually nationwide, which is physically impossible
given one occurred in 2023. At 0.8%–1.4%, the implied national rate is still far
above anything observed. Choosing this option means deleting an argument from the
workbook that the workbook is correct to make, and replacing it with an
assumption the document itself calls implausible. **This option can be chosen,
but it cannot be defended in the same breath as A1's note.**

### 6.3 Option C — one model, a stated range, no anchor multiples

Keep A1's 0.05% and its outputs; strike the multiples entirely from A2 §3.2 and
D08 §3, §5 and §6; replace them with the method and the sensitivity range, and
let the customer's own inputs produce their own figure.

**Why this is not merely Option A with fewer words.** D08 §5 already says "do
not present a multiple to a customer as an expected outcome — present the
method, the inputs, and the sensitivity." Option C makes the document do what it
says. It removes the exposure without asserting a number the first procurement
conversation will test.

**The cost.** A dossier with no headline number is harder to sell, and the sales
process will reintroduce one informally the first time a prospect asks "so what's
the ROI?" — at which point an uncontrolled number is worse than a controlled one.
This is the argument against C and it is real.

### 6.4 Option D — split the difference: keep one conservative anchor

State a single range — "roughly 1.8x at entry, improving to 3.4x at network
scale" — which is A1's output, keeps the monotonic claim visible and concrete,
and gives the sales conversation a number to hold without overstating.

This is Option A with the anchors retained rather than struck, and it is probably
the practical version of A. §5's table is already what it would say.

---

## 7. Recommendation and the case against it

**Take Option A, expressed as Option D.**

1. `p = 0.05%` in A1 becomes the single governing value. It is the only one with
   a written argument behind it, and that argument — implied national frequency —
   is checkable.
2. A2 §3.2 and D08 §3 carry **1.77x at 500 and 3.36x at 10,000**, labelled as
   three-year benefit against the four-year commitment.
3. D08 §5 and §6 restate benefits from A1: $696,675 pilot year, $2,786,700 over
   four years, $4,180,050 over six. Returns become 1.88x, 2.36x, 2.29x.
4. `roi.py` moves to 0.05% **and** to a contained cost consistent with A1's B14
   note, so the dashboard stops valuing a missed defect at 29× the workbook.
5. D08 §5 gains one sentence reconciling it to §4, which already prices a
   prevented failure at an A1-consistent $993,000. §4.2's period comparison is
   removed or rebuilt on A1; the 44%/217% artefact disappears with the restatement.

**The case against, stated fairly.** The restated figures describe a product
returning roughly 2x, which for a Class I railroad is a modest business case and
may not justify a procurement cycle. If the real economics are better than A1
models — because the avoided cost is not one bearing derailment but the service
disruption, the regulatory exposure and the reputational cost that follow one —
then A1's `$500,000 typical` and `$1B catastrophic` are too narrow, and Option B
is right on the economics even though its probability is indefensible. **That
possibility is real and it is the owner's to weigh, not mine.**

If that is the view, the correct move is not to raise `p`. It is to add the cost
components A1 omits — service disruption, lading loss, regulatory penalty — to
B14, where they are visibly sourced, and to keep `p` at 0.05%. That is a
different edit from Option B and it reaches a higher benefit figure honestly.
**That path is worth pricing before Option A is locked in**, and it is the one
thing in this document I would slow down for.

---

## 8. What changes once the option is chosen

| Artifact | Change under Option A/D | Change under Option B |
|---|---|---|
| `A1-ROI-MODEL/build_roi_calculator.py` | B17 stays 0.05%; regenerate workbook from corrected builder | B17 → ~0.8–1.4%; delete the "physically impossible" note |
| `A1-ROI-MODEL/AxiomDynamics-ROI-Calculator.xlsx` | Regenerate — currently carries a $285,000 pilot ($180,000 licence + $65,000 hardware integration + $40,000 training) against A2's $370,000, and has no conversion-credit line. Its platform-fee row exists but is inert at one site. | Same regeneration |
| `A2-RATE-CARD…md` §3.2 | 2.0x/4.1x → 1.77x/3.36x | Recompute anchors at new `p` |
| `D08…md` §3 | Same sentence | Same |
| `D08…md` §5, §6 | Benefits and returns restated from A1; period table rebuilt | Figures stand; §4 valuation recomputed upward to match |
| `backend/roi.py` | `P_CATASTROPHIC_GIVEN_MISSED_DEFECT` 0.02 → 0.0005 | Unchanged, or aligned to new `p` |
| `assets/a2-d08-arithmetic-pass-2026-11-09.md` | Findings marked closed, with the deciding basis recorded | Same, different resolution |
| `project-logs/CURRENT-STATE.md` | Open items 1 and 3 closed | Same |
| `D00` Part IV | Two open rows closed | Same |

One further item, independent of the choice: **the committed workbook is stale**
in a way the pass record noted and did not fix. It structures the pilot as
$285,000 — a $180,000 licence plus $65,000 hardware integration plus $40,000
training — against A2's $370,000, which has no hardware line at all and adds
$35,000 validation support and $50,000 pilot support. It also has no conversion-
credit line, so Year 1 production is $300,000 rather than the $210,000 A2 §9
produces. Its platform-fee row (row 10) exists and works, but reads $0 at one
site, which is correct and easy to mistake for a missing line. **The workbook
disagrees with A2 §5.1 and §9 regardless of which model wins**, and must be
regenerated in the same pass as whichever option is chosen, not before and not
after.

---

## 9. If no decision is made

The state a month from now, unchanged: A2 and D08 carry two numbers that do not
reproduce, D08 prices a prevented failure at about $993,000 in §4 and
$8.6M–$11.4M in §5, `roi.py` values a missed defect at 29× what A1 does, and the
workbook disagrees with the rate card on both the pilot fee and the conversion
credit. Every one of those is discoverable by a competent procurement analyst in
an afternoon, and each one is more damaging found by them than stated by us.

That is the actual cost of leaving it open, and it is why this is the priority
ahead of the signed ledger export.

---

*Internal analysis. Lives in `assets/` by standing instruction. Not client-facing.
The figures here are re-derivations, not quotations — every one is reproducible
with `assets/a2-d08-model-decision.py`.*
