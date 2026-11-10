# A2 / D08 Arithmetic Pass — 2026-11-09 (chat-3)

**Scope.** Every fee figure, band rate, cumulative total, performance cap, and
modelled return in `A2-RATE-CARD-AND-BAND-DEFINITIONS.md` and
`D08-MASTER-LICENSING-AND-LIABILITY.md`, recomputed from its stated source
equation rather than re-read. Both documents were last touched at `cf2e6ba`;
this is the first figure-by-figure re-derivation since.

**Method.** `assets/a2-d08-arithmetic-pass.py` computes each figure independently
and compares it to the value as written. It exits non-zero on any mismatch, so
the pass is repeatable rather than a claim. Run it with:

```
python3 -I assets/a2-d08-arithmetic-pass.py
```

**Result: 78 of 78 computed figures agree with the documents.** No arithmetic
error was found in either document. Every band total, worked example, site-fee
product, payment split, conversion credit, three-year row, performance cap,
cumulative schedule, and five-percent escalation is correct as written.

Two claims did **not** reproduce. They are not arithmetic errors — the arithmetic
inside each is sound — but the model each rests on does not agree with the model
the rest of the docket uses. They are recorded below as open items and were
**not** silently rewritten, because correcting them means choosing which model
governs, and that is an owner decision.

> **BOTH FINDINGS CLOSED 2026-11-10, and this record is otherwise unchanged.**
> The owner delegated the decision; **A1 now governs**, expressed as Option D in
> `assets/a2-d08-model-decision-2026-11-09.md`. A2 §3.2, D08 §3, §5 and §6 were
> restated and `backend/roi.py` corrected the same day. **The figures in the two
> sections below are the pre-decision values, deliberately left standing** — this
> document records what was found on 2026-11-09, and rewriting it to match the fix
> would destroy the only account of what the defect looked like before it was
> closed. The script now runs **89 checks** and asserts both findings closed
> against the restated documents; it no longer reports them as open. See
> `project-logs/CURRENT-STATE.md`, "Model decision".

---

## What was checked and confirmed

**A2 §3.1–§3.3 — the band structure.** Band 1 at $600 to $300,000; Band 2
cumulative at $1,050,000; Band 3 at $2,175,000 at 5,000 axles and $4,050,000 at
10,000. All three worked examples (A: $300,000; B: $550,000 + $90,000 =
$640,000; C: $2,175,000 + $855,000 = $3,030,000) recompute correctly. The
marginal structure is genuinely marginal — no band charges for axles already
priced in a lower band.

**A2 §3.3 — the corridor site count.** 2,200 miles at 40-mile spacing is 55
sites, at 64-mile spacing 34.4. Site fees at 55 sites are $2,430,000, correctly
described as roughly half the $2,175,000 licence. The claim holds.

**A2 §5.1 — the pilot.** The five components sum to $370,000. The 40/30/30 split
is $148,000 / $111,000 / $111,000 and sums back to $370,000 exactly. The
conversion credit is 50% × $180,000 = $90,000.

**A2 §9 and D08 §5 — the rollover.** Year 1 production at $300,000 less the
$90,000 credit is $210,000 net; three years at 210 + 300 + 300 = $810,000;
four-year commitment $1,180,000. Both documents agree.

**D08 §3.1 — the three-year cost table.** All four rows recompute, including the
cost-per-axle column. The stated finding — that holding axles constant and
spreading across eleven sites raises cost 114% and more than doubles unit cost
from $2,360 to $5,060 — is arithmetically exact. So is the $135,000 three-year
charge per additional site.

**D08 §4 — performance component.** 33% caps of $99,000 / $181,500 / $346,500 at
500 / 1,000 / 2,000 axles are correct. The 1,000-axle worked example is right:
3% of $1,390,000 is $41,700, below the $181,500 cap, total $591,700. The earlier
draft's "$41.8K" was indeed rounded the wrong way; the current text is correct.

**D08 §6 — cumulative and escalation.** $370,000 / $580,000 / $880,000 /
$1,180,000 cumulative correctly. Year 5 at 5% is $315,000 and Year 6 $330,750,
cumulative $1,495,000 and $1,825,750, so "~$1.83M" is right.

**D06 §6 — the quarterly fee.** ($1,050,000 + 12 × $45,000) ÷ 4 = $397,500, and a
5% credit is $19,875. Correct; no change needed there.

---

## Finding 1 — the modelled-return claim does not reproduce

A2 §3.2 states the customer's modelled return rises "approximately 2.0x at 500
axles, rising to about 4.1x at 10,000." D08 §3 repeats both figures verbatim.

Recomputed with A1's own default assumptions (0.05% catastrophic rate, $500,000
typical failure, $1.0B catastrophic, 2.1 vs 1.4 defects caught per 500 axles,
$1,500 per false alarm), the three-year return is:

| Axles | 3-yr benefit | A2/D08 cost basis | A1 workbook basis |
|---:|---:|---:|---:|
| 500 | $2,090,025 | 1.77x | 2.36x |
| 1,000 | $4,180,050 | 2.17x | 3.02x |
| 2,000 | $8,360,100 | 2.44x | 3.51x |
| 5,000 | $20,900,250 | 3.07x | 4.51x |
| 10,000 | $41,800,500 | 3.36x | 4.99x |

Neither basis produces 2.0x at 500 and 4.1x at 10,000. A sweep across plausible
per-defect valuations found no parameter set in the repository that reproduces
both endpoints. The *direction* of the claim is correct — return does improve
monotonically with fleet size on either basis — but the two anchor values are not
derivable from the model the docket ships.

**Why this matters and why it was not fixed here.** The sentences carrying these
numbers are also the document's defence against a "flat tier cliff" objection, and
D08 §3 already labels them "a pricing hypothesis validated only against modelled
return, not against a real procurement conversation." Replacing 2.0/4.1 with
1.77/3.36 would be defensible; so would restating the claim without anchor values.
Choosing between those is a commercial decision about what the first real
conversation opens with, and it changes a client-facing sentence in two documents.
It should be decided, not quietly edited.

**Recommended disposition:** strike the two anchor multiples from A2 §3.2 and D08 §3
and keep the monotonic claim, which is true on every basis tested. If anchors are
wanted, use values the shipped model actually produces and say which basis.

> **Update, same day — see `assets/a2-d08-model-decision-2026-11-09.md`.** The
> statement above that "no parameter set in the repository reproduces both
> endpoints" is correct only for the two cost bases tested here. A third basis —
> a four-year cost including the pilot and three full production years at list,
> with no conversion credit — reproduces both anchors from a single value of the
> catastrophic probability, **0.0714%**, to within 1.8%. So the anchors were not
> invented; they were computed on an unstated frame at an undisclosed third value
> of the parameter. That makes Finding 1 a disclosure defect rather than a
> fabrication, and the disposition above still stands: state the frame or strike
> the numbers. The decision paper carries the full table.

---

## Finding 2 — D08's modelled benefits exceed what A1 produces

D08 §5 says a 500-axle customer sees $6–8M of avoided damage in the pilot year
and $14–20M over four years; §6 says $40–60M over six years and a 20x–30x return.

A1 at 500 axles with default assumptions produces **$696,675 net annual benefit**.
The comparison:

| D08 claim | Period | A1 produces | Ratio |
|---|---:|---:|---:|
| $6M–$8M | pilot year | $696,675 | 8.6x – 11.5x higher |
| $14M–$20M | 4 years | $2,786,700 | 5.0x – 7.2x higher |
| $40M–$60M | 6 years | $4,180,050 | 9.6x – 14.4x higher |

The returns quoted in D08 (16–22x for the pilot year) are internally consistent
with D08's own benefit figures divided by the $370,000 fee — that is checked and
passes. The problem is upstream: D08's benefit figures are roughly an order of
magnitude above the benefit A1 computes from the same fleet inputs. Any
per-defect valuation that would support D08's pilot figure lands near $8.6M–$11.4M
per prevented defect, against A1's $999,750.

D08 §9.1 already instructs: "Recalculate against the final A2 rate card before any
customer sees it." This is that check, and it does not pass.

**Why this matters.** These are the headline numbers in the document a CFO reads.
A1 is named as the instrument of record in both D08 §5 and §9, and D08 §5 states
that "A1 produces the customer's figure from the customer's data; this document
must never be used to present one." The two disagree by nearly an order of
magnitude at identical inputs, which is exactly the contradiction the sentence is
trying to prevent.

**Recommended disposition:** one of the two models is wrong and it needs a decision
on which. If A1 is the instrument of record — as D08 says twice — then §5 and §6
must be restated from A1's output. If D08's figures are right, A1's per-defect
valuation or defect-frequency assumption is too conservative and the workbook is
the thing to fix. Deciding this changes what the pilot pitch asks a customer to
believe, so it is left open deliberately.

> **Update, same day — see `assets/a2-d08-model-decision-2026-11-09.md`.** This
> section compares D08 §5–§6 against A1 and against the fee schedule, but not
> against **D08 §4**, which sits immediately above it and prices a prevented
> failure at about $993,000. §5 prices the same prevented failure at
> $8.6M–$11.4M. That is a contradiction inside one document and it does not
> depend on A1 being correct about anything. The decision paper also shows that
> the three periods fail to reconcile with each other: read as one model, they
> imply years 2–4 producing 44%–50% of the pilot year, then years 5–6 producing
> 217%–250% of it, with nothing in the model to explain either turn.

---

## Corrections made in this pass

Three edits, all in `A1-ROI-MODEL/build_roi_calculator.py`, none altering any
figure in A2 or D08:

1. **Stale attribution corrected.** The assumptions note on sheet 5 still said
   "the 2% catastrophic escalation rate" while cell B17 has held 0.05% since the
   correction. The note now reads "the 0.05% catastrophic escalation rate (cell
   B17)". A reader reconciling the sheet against its own footnote would have
   found a ten-fold discrepancy that no longer exists.

2. **Sandbox output path removed.** Line 621 saved the workbook to
   `/sessions/ecstatic-gifted-bell/mnt/outputs/...` — a path inside a destroyed
   sandbox, from before the write-in-repo rule. Running the builder would have
   raised `FileNotFoundError`. It now writes beside the script via
   `os.path.dirname(os.path.abspath(__file__))`.

3. **Import added** for the above (`import os`).

The committed workbook at `A1-ROI-MODEL/AxiomDynamics-ROI-Calculator.xlsx` was
**not** regenerated. Regenerating it would bake Finding 1 and Finding 2 into a new
file before the model question is settled. The workbook on disk still carries the
$180,000 pilot licence with no conversion credit and no site-fee line, which
disagrees with A2 §5.1 and §9 — that is a third instance of the same model
divergence and is covered by Finding 2's disposition.

---

## What to do next

1. Decide Finding 1 — strike or restate the 2.0x/4.1x anchors. **Options priced in
   `assets/a2-d08-model-decision-2026-11-09.md` §6.**
2. Decide Finding 2 — which model governs, A1 or D08 §5–§6. **Same document, §6.**
3. Then regenerate the A1 workbook from the corrected builder and re-run this
   script; it will hold as long as no figure moves.
4. D07 §14.5 governing law and venue remains open, unchanged by this pass.
5. **New, found while costing the decision:** `backend/roi.py` uses a 2%
   catastrophic rate and `roi.py`'s own note calls that "conservatively low",
   while A1's B17 note calls 2% "physically impossible". Both files are wrong
   about the other being wrong. This third divergence belongs in the same
   decision — see the decision paper §4.4.

*This record is internal analysis and lives in `assets/` by standing instruction.
Nothing here is client-facing.*
