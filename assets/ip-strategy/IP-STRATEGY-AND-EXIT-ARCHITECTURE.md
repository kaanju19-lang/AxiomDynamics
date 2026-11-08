# IP Strategy & Exit Architecture

**Internal only.** Commercial strategy, not legal advice. Every structure below requires counsel before it is written into a contract.

**Decision recorded 2026-11-08:** AxiomDynamics retains all IP for the first five years. No sale of IP rights to any party in that window. Only licences.

This closes the open question in `LIBRARY-RECONCILIATION.md` §3 and unblocks C01 and the D-series legal drafts.

---

## 1. The staged structure, as directed

| Stage | Window | Structure | Our position |
|---|---|---|---|
| **I — Prove** | Y1–Y5 | Licence only, BNSF first client | 100% IP |
| **II — Brand** | Y5–Y8 | Exclusive white-label: BNSF logo/theme on our build | 100% IP, premium tier |
| **III — Review** | Y8 | Joint assessment with BNSF; competitive landscape read | 100% IP |
| **IV — Open** | Y8+ | Joint IP options with majority retained; legacy vendors admitted as bidders | Majority IP or exit |
| **V — Auction** | When triggered | Sole buy-out of all IP, open bid floor, all players | Exit, cash |

The escalation logic is sound: each stage raises information about the asset's real value, and the auction at the end is held from a position of demonstrated results rather than a pitch.

## 2. Defect one — the exclusivity contradiction

**Stage II grants BNSF exclusive white-label rights. Stage III assumes UP and NS are "owning and operating our build" by then.**

These cannot both be true. If BNSF holds exclusivity and we licence UP during the window, we are in breach on day one, and the resulting litigation destroys the Stage V auction before it starts. A buyer will not pay a premium for an asset with contested title.

**Resolution — separate brand exclusivity from use exclusivity:**

| Dimension | BNSF exclusive | Everyone else |
|---|---|---|
| Logo and visual theme | **Yes** — their brand throughout | No — unbranded or their own |
| Named reference rights | **Yes** — they are the cited deployment | No |
| Priority support tier | **Yes** | Standard |
| **Right to operate the platform** | **No** — non-exclusive | **Non-exclusive** |
| Territory / segment | Their network only | Their networks |

BNSF gets what they actually want — to be *the* railroad with a branded version of the platform, and to be the case study — without giving them a veto on our other customers. Rail carriers care far more about being first and being cited than about denying a rival a bearing-prediction tool they have no way to police anyway. Detector software installed on a competitor's private network is not observable; exclusivity is unenforceable in practice at exactly the level of granularity they would be buying.

**Price the exclusivity separately.** Do not bundle it into a licence rate. A brand exclusivity grant is a distinct asset with a distinct price — a one-time fee plus an annual premium, or a straight uplift of a defined percentage on the band rate. Bundling it hides its value and makes it impossible to withdraw later.

## 3. Defect two — "quietly" is not available

The plan assumes we can observe the market quietly, escalate pricing at intervals, and trigger an auction without the buyer set knowing. In this industry that premise fails for three specific reasons:

**Price discovery is effectively transparent.** There are six Class I carriers. Their procurement, safety and mechanical officers sit on the same AAR committees, attend the same conferences, and move between companies. Contract confidentiality is achievable; the fact that BNSF pays $X for a bearing platform will be known inside the industry within a quarter.

**Public-company disclosure.** BNSF is a Berkshire Hathaway subsidiary. A material acquisition or a material licence commitment gets disclosed in periodic reporting. At the scale we are aiming for, the transaction surfaces regardless of intent.

**The auction requires a bid floor, and a bid floor requires telling people there is an auction.** Every stage after III is inherently public to the participants.

**What "quiet" should mean instead:** no marketing, no press, no visible competitive signalling, and strict contractual confidentiality — but an internal assumption that every carrier knows roughly what the others pay. Price accordingly. Never quote BNSF a number you would be embarrassed to defend to CSX.

## 4. The legal trap — joint IP does not mean what it sounds like

Stage IV contemplates "joint IP rights while still owning them as majority owner."

**Under US law, joint owners of a copyright or patent can each exploit the asset independently, and license it to third parties, without the consent of, or accounting to, the other owner** — unless a written agreement says otherwise. "Joint ownership with majority retained" is not a recognised legal structure. Majority ownership of *what*? There is no shareholding to be a majority of.

If we grant BNSF "joint IP rights," the default legal position is that **BNSF may license our jointly-owned technology to CSX, or to a vendor, without our permission and without paying us.** That is the opposite of the intended outcome, and it is the single most dangerous idea in the current plan.

**Three structures that achieve the actual intent:**

1. **Co-ownership agreement with explicit consent clauses.** Joint title plus a contract barring independent licensing, requiring written consent for any third-party grant, and defining revenue splits. Workable, but every future licence becomes a negotiation with BNSF.
2. **Equity, not co-ownership.** BNSF takes a minority stake in a holding entity that owns the IP. We retain majority equity. Clean, standard, keeps title in one place, and makes the eventual buyout a share purchase rather than an IP assignment.
3. **Field-of-use licence.** BNSF gets exclusive rights in a defined domain (e.g. their own network, a named commodity, a specific service), we keep everything else outright. Simplest to administer, weakest for BNSF, usually enough.

**Recommendation: never co-own. Use equity (2) or field-of-use (3).** If BNSF insists on "joint IP" language, that is a signal they intend to exploit it, and the price must reflect that — or the answer is no.

## 5. What actually creates the buyout premium

Not the code. Not the physics. **The evidence base.**

By year 8 the assets that justify a premium bid are: documented prevented failures across multiple carriers, a hash-chained disposition ledger that a regulator accepts, a track record the buyer cannot replicate by hiring engineers. A competitor can rebuild the equations in eighteen months. They cannot reconstruct eight years of corroborated outcomes.

This is why E01 (Evidence Register & Hash Manifest) and E02 (Chain of Custody) in the reconciliation are not compliance paperwork. **They are the asset being sold.** Every disposition record, every corroborated prevention, every signed audit export increases the exit valuation. Every missing one reduces it.

The corollary is uncomfortable: if we sell a platform whose evidence discipline is weak, we are selling software, and software gets valued at a multiple of revenue. If we sell one with an unimpeachable evidence trail, we are selling a regulatory moat, and moats get valued strategically.

## 6. The buyer universe — and why the auction works

| Category | Candidates | Motivation |
|---|---|---|
| **Class I — US** | BNSF, CSX, UP/NS (post-merger) | Deny a rival; control a safety technology; integration standard |
| **Class I — Canada/Mexico** | CN, CPKC | Same, plus tri-country exposure |
| **Wayside / inspection OEMs** | Wabtec, Siemens Mobility, Alstom, Hitachi Rail, Progress Rail, Mermec, Duos Technologies | Product line extension, distribution |
| **Component makers** | Amsted Rail, Timken, SKF, NSK, Schaeffler | Move from parts to outcomes; defensible margin |

**The structural dynamic that drives the price:** once one carrier operates the platform and two others licence it, every remaining carrier faces a choice between being the last without it and being the one that owns it. **A railroad does not want its safety vendor owned by a competitor.** That fear is worth more than any feature we ship.

**And the legacy vendor is simultaneously the best and worst buyer.** Best for distribution and immediate global reach. Worst for the carriers, because they would be buying their safety assurance from the company that also sells them the detectors — and pricing that has to pass through a supplier they already negotiate with. Carriers may bid defensively to prevent exactly that outcome. **Admitting vendors to the auction is what turns a carrier negotiation into a genuine contest.** The directed strategy is right on this point.

## 7. Valuation arithmetic — the floor to hold

Illustrative only; assumptions are ours and must be replaced with real numbers as they arrive.

**The annuity being given up.** If by Y8 three carriers are licensed at a blended $6M/year, that is $18M/year of high-margin recurring revenue. At a 75% contribution margin and a 12× multiple — reasonable for vertical industrial software — the standalone business is worth roughly **$160M**. Ten years of discounted cash flow is in the same range.

**The strategic premium.** A sole buyer acquires a moat and denies it to five rivals. Historically that justifies 2–3× on top of standalone value where the buyer set is small and the asset is concentrated. That puts a credible auction range in the **$300M–$500M** band.

**The rule I would hold to:** do not entertain a sole buy-out below the NPV of the annuity plus a strategic premium. Below that line, selling is worse than continuing — and continuing raises the floor every year, because the evidence base compounds. **The strongest negotiating position at Stage V is being visibly willing to keep operating.**

**Tax note:** structure the exit as a sale of the holding entity rather than an assignment of IP where possible. Same commercial outcome, materially better treatment, and cleaner for the buyer.

## 8. Terms that must be written in from Stage I

These are cheap now and very expensive to retrofit. They belong in D02, D03, D05, D07 and D08 before anything is signed.

**1. Change-of-control and assignment.** Every licence must explicitly permit assignment to a purchaser of the IP or of the company. Without it, a buyer inherits contracts it may not be able to assume, and the auction price falls. Conversely, bar the *customer* from assigning their licence without consent — otherwise BNSF's licence travels with a merger we never priced.

**2. Escalation schedule, pre-agreed.** Put the Stage II white-label uplift and the Stage IV review trigger into the original agreement as options with formulaic pricing, not as future negotiations. Every stage that requires a fresh negotiation is a stage where we can be held up.

**3. MFN, carefully scoped.** BNSF paying a premium will demand most-favoured-nation protection to prove they are not overpaying. An unscoped MFN makes it impossible to price UP higher later and destroys the escalation plan. Scope it to *substantially similar deployments* and exclude white-label branding, early-adopter terms, and transaction-specific concessions.

**4. Renewal rights with a cap, traded for the exclusivity fee.** After three years of white-label, BNSF's switching cost is enormous — our leverage is real. They will want renewal rights at a capped price. Grant them at CPI-plus-a-band in exchange for the exclusivity premium, rather than conceding them for free.

**5. Escrow, insolvency-triggered only.** Release conditions: insolvency, cessation of support, or failure to deliver a security patch. Never triggered by ordinary commercial dispute.

**6. Anti-cloning and licence-scope limits.** Define what BNSF may not do with access to source under escrow: no derivative works in the field, no sublicensing, no reverse engineering for a competing product.

**7. Audit rights.** The right to verify axle counts and site counts — the entire pricing model depends on counts we cannot otherwise observe.

**8. ROFR vs. auction — pick one, deliberately.** A right of first refusal to BNSF caps the auction upside, because every other bidder knows their bid is really an option for BNSF to match. If the goal is a contested auction, grant no ROFR. If the goal is a guaranteed exit, grant one and price it.

## 9. Risks I would put on the table

**The horizon is a decade, and technology moats decay.** Eight to ten years is a long time for a mid-size software asset. The legacy vendors are already building physics-based detection — Mermec and Duos compete directly today. The plan should include a **faster trigger**: if a credible competing platform reaches the market, accelerate to Stage V rather than hold out for the full timeline.

**Antitrust and public-interest exposure on the buy side.** A technology that demonstrably prevents derailments, acquired exclusively by one carrier, is a safety-relevant concentration. Post-East Palestine, a regulator or a congressional committee could take an interest in six carriers' safety assurance being owned by one of them. This cuts both ways: it may cap the price, and it may compel a consortium or non-exclusive-licence condition on the buyer. A buyer will price that risk in. **Expect it, and consider a structure where the winner must license to the others at regulated terms** — which preserves the price and removes the objection.

**HSR filing.** A transaction in the low hundreds of millions exceeds the Hart-Scott-Rodino threshold, which adjusts annually and has sat in the $120–135M range recently. Expect a filing, a waiting period, and disclosure. Another reason "quiet" is not a plan.

**Key-person concentration.** A strategic buyer pays for the team as much as the code. Retention packages at Stage III–IV protect the price; losing the technical principals before the auction destroys it.

**Clean cap table and clean title.** Any unresolved co-ownership, any licence granted without assignment rights, any contractor who wrote code without an IP assignment, reduces the bid. **Every contributor must have signed an IP assignment from day one.** This is the most commonly discovered defect in a diligence process and it is fatal at the worst moment.

## 10. What changes in the docket

| Document | Change required |
|---|---|
| A2 Rate Card | Add white-label tier and a separate exclusivity fee line |
| D02 Pilot | Add assignment-on-change-of-control; IP retention clause |
| D05 Rollover | Add Stage II option with formulaic uplift, and the Stage IV review trigger |
| D07 Master Contract | Scope MFN carefully; add audit rights; add anti-cloning; confirm sole-owner IP title |
| D08 Licensing | Add the five-stage structure and the white-label definition |
| D12 Regulatory Status | Unchanged, but note that exclusivity does not transfer regulatory responsibility |
| New: D13 | IP Ownership & Escrow Schedule — the definitive statement of what we own, what transfers, and when |

---

*Commercial strategy. Not legal advice. The joint-ownership analysis in §4 and the HSR and antitrust points in §9 must be confirmed by counsel in the relevant jurisdiction before any structure is committed to a contract.*
