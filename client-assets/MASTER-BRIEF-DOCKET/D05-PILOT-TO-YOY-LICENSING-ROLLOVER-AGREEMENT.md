# D05 — Pilot to YoY Licensing Rollover Agreement

**Docket position:** D05. The conversion mechanics. Executed concurrently with D02 (Pilot Agreement); governs what happens when the pilot ends.

> **Drafting status:** Commercial grade. Requires counsel and CFO review. Fee schedules must be confirmed against A2 before execution.

---

## 1. Purpose and scope

This Agreement defines the automatic conversion (if desired by the Railroad) of a pilot licence (D02) into a production licence (D08) and the first year of production operations. It eliminates the "rollover cliff"—the arbitrary jump in cost and terms that would otherwise occur at day 366 of a pilot.

**This Agreement is executed at the same time as D02.** Both parties agree to the rollover terms before the pilot begins, eliminating surprise negotiations at conversion.

---

## 2. Conversion window and decision points

### 2.1 Conversion window

The Railroad has **ninety (90) calendar days after the pilot term expires to elect conversion** to a production licence. Election is made by written notice to Supplier (Form F12).

> **Corrected: after expiry, not after the Commissioning Date.** An earlier draft said "after the Commissioning Date," which would give the Railroad a 90-day window starting at commissioning — i.e. the election deadline would fall *before* the pilot had been running long enough to evaluate anything. The window runs from pilot expiry, and the example below is consistent with that.

**Conversion trigger date:** if the Railroad elects to convert, the conversion becomes effective **on the day after the pilot term expires** (day 366 of the pilot).

**Example:** Pilot begins 2026-06-01, Commissioning Date is 2026-07-01. Pilot term is 12 months, expiry is 2027-07-01. Railroad has until **2027-09-29** to elect conversion (90 calendar days after 2027-07-01). If it elects, conversion takes effect 2027-07-02.

### 2.2 Non-election: what happens if the Railroad declines

If the Railroad does **not** elect to convert within the 90-day window, the pilot licence terminates at expiry. The Railroad:
- Ceases all use of the Platform.
- Exports its data in usable format (per D07 §15.6).
- Receives 90 days of transition assistance at no charge.
- May not re-engage the Platform unless a new engagement is executed under a new SOW or master agreement.

**The Railroad has no right to continue operating the Platform beyond the pilot term unless it elects conversion or executes a separate agreement.**

### 2.3 Pilot fee credits

If the Railroad elects to convert within the 90-day window, **fifty percent (50%) of the pilot licence fee is credited against the first production licence fee**, as stated in D02 §3.3.

**Pilot licence fee:** $180,000 (per D02 §3 and **A2 §5.1** — confirmed, no longer illustrative).
**Credit:** $90,000.

The credit applies only to the licence component of the first production year, not to implementation, training, or support.

---

## 3. Production licence terms: first year (Year 1)

### 3.1 Scope and pricing

Upon conversion, the Railroad receives a **twelve (12) month production licence** for the pilot site, covering the same scope as the pilot: one (1) site, at **the axle count stated in D02 §1**.

**Production licence fee (Year 1):** $300,000 at 500 axles (A2 §3.1: 500 × $600).
**Site platform fee (Year 1):** $0 — the first site is included in the base licence (A2 §4).
**Annual support (included):** per D06.
**Subtotal:** $300,000.
**Less pilot credit (50% of pilot licence):** –$90,000.
**Net Year 1 production fee:** **$210,000**.

> **Worked example at 500 axles, one site.** Figures scale by the marginal bands in A2 §3.1 — the calculation method does not change. A2 §9 sets out the full three-year arithmetic. **Where a figure here differs from A2, A2 governs.**

### 3.2 Price protection: Years 2–3

The Railroad's production licence fees are **locked** for the first three (3) years of production:

| Year | Licence fee | Site fee | Total | Change |
|---|---|---|---|---|
| Year 1 (starting conversion) | $300,000 | $0 | **$210,000 net** | after $90,000 pilot credit |
| Year 2 | $300,000 | $0 | $300,000 | 0% increase |
| Year 3 | $300,000 | $0 | $300,000 | 0% increase |
| Year 4+ | $315,000 max | $0 | $315,000 max | max 5% annual increase (A2 §8) |

**Rationale:** price protection allows the Railroad to forecast and budget. After Year 3, fees may increase to reflect inflation, enhanced models, or expanded functionality, but no single year increase exceeds 5%.

### 3.3 Auto-renewal for Years 2–3

The production licence **automatically renews** for Year 2 and Year 3 at the locked fee, unless either party provides **written notice of non-renewal at least ninety (90) days before the anniversary date**.

**Year 1 anniversary:** day 365 of Year 1 production.
**Year 2 anniversary:** day 365 of Year 2 production.

On the Year 3 anniversary, the parties may renegotiate (see §4).

---

## 4. Continuation beyond Year 3: renegotiation

### 4.1 Renegotiation window

Beginning **120 days before the Year 3 anniversary**, the parties may enter discussions about continuation. Either party may propose:
- Expanded scope (additional sites, additional axles at the pilot site).
- Enhanced service levels (premium support, priority patching).
- Model improvements or proprietary customizations (billable).

### 4.2 Terms offered

If continuation is desired:
- **Option A (Standard):** Year 4 fees may increase up to 5% from Year 3 rates. All other terms remain unchanged.
- **Option B (Expansion):** if the Railroad adds sites or axles, pricing for the expansion follows A2 (Rate Card) and is added to the existing Year 3 baseline (which remains protected at 0% increase).
- **Option C (Enhanced service):** premium support, SLAs, or features are offered as separate add-on contracts.

### 4.3 No agreement = continuation on standard terms

**Silence does not terminate the licence.** If the parties have not agreed different Year 4 terms by the Year 3 anniversary, the licence **continues automatically at the Year 3 rate increased by no more than 5%** (A2 §8), and either party may then terminate on the notice period in §9.1.

> **Corrected: this clause used to read that the licence "terminates automatically at the Year 3 anniversary."** That was wrong in three ways at once. It contradicted A2 §8, which provides for a Year 4 increase capped at 5% — you cannot have a Year 4 price unless there is a Year 4. It contradicted §9.1, which gives a 180-day post-Year-1 termination notice. And commercially it made a customer's refusal to negotiate **cheaper than agreeing**, since it handed them an exit at no transition cost. **Auto-termination on silence is never the right default: it turns administrative drift into a service outage.**

---

## 5. Scaling and expansion within the pilot scope

### 5.1 Axle count adjustments

If, during the pilot or Year 1–3 production, the Railroad's axle count at the pilot site changes materially (e.g., due to seasonal changes, consist reallocation, or equipment lifecycle), the parties may adjust the licence scope:

**Increase in axle count:** the Railroad notifies Supplier of the new count. Pricing is adjusted pro-rata for the remainder of the year, effective the first day of the following month.

**Example — the incremental arithmetic, not a re-charge of the whole base.** Year 1 starts with 500 axles at Band 1 ($600) = $300,000, already invoiced. In month 6 the count rises to 600. The **additional 100 axles are Band 2** — the marginal band, $500 per axle (A2 §3.1), not $600. For the remaining 7 months: 100 × $500 × 7/12 = **$29,167**. The full-year price at 600 axles is 500 × $600 + 100 × $500 = $350,000, of which $300,000 has been billed; the pro-rata increment of $29,167 is added to the final invoice.

> **Corrected twice.** The earlier draft charged the 100 new axles at **$600** — the Band 1 rate — when axles 501–600 sit in Band 2 at $500, so it over-billed the customer by $5,833 on this example and would have over-billed every expansion. It then computed "($600 × 600 × 7/12) = $210,000," which re-charges the entire axle base for the remaining months on top of the $300,000 already invoiced. **An expansion clause that double-charges is the one that gets found** — by an AP clerk with a spreadsheet, in the first quarter it applies.

**Decrease in axle count:** pricing is not retroactively reduced; the Railroad continues to pay for the licence period. The decrease takes effect for the next renewal term.

### 5.2 No expansion to additional sites during pilot or Year 1–3

The pilot and production licence (Years 1–3) are scoped to the single pilot site only. **No expansion to other sites is permitted under this Agreement.** Additional sites require a separate SOW (D04) or a renegotiated licence (D08).

---

## 6. Data and intellectual property during rollover

### 6.1 Data ownership and retention

All data generated during the pilot (advisories, dispositions, detector logs) remains the Railroad's property. On conversion, the Railroad retains all historical pilot data and may query it, export it, or reference it in production operations.

### 6.2 IP ownership

As stated in D13: Supplier retains all IP in the Platform, models, and improvements. Conversion to production does not change ownership. The Railroad acquires no ownership interest in the Platform by converting.

### 6.3 Escrow remains in effect

The escrow arrangement in D13 §4 applies throughout the pilot and production terms. No new escrow deposit is required at conversion; the running version is deposited per the schedule in D13 §4.

---

## 7. Support and certification continuity

### 7.1 Certified Reviewers

Reviewers certified during the pilot (per C02) **remain certified** into Year 1 production. Their three-year certification term runs continuously from the date of issuance, not reset at conversion.

**Example:** Reviewer certified 2026-08-01 during the pilot remains certified through 2029-08-01, regardless of whether the pilot converted or not.

### 7.2 Support continuity

Support provided during the pilot (per D06) transitions seamlessly to production. No interruption in monitoring, ticket queues, or response commitments.

---

## 8. Regulatory and operating status

### 8.1 D12 status unchanged

Conversion to production does not change the Platform's regulatory status as a decision-support tool (D12). No new regulatory approval is required; the Railroad's own regulatory obligations remain unchanged.

### 8.2 Configuration Attestation remains valid

The Configuration Attestation signed at pilot Commissioning Date (D14 §6) remains valid into Year 1 production. If material configuration changes occur (e.g., detector replacement, OS upgrade), an updated attestation may be required; see D14 §6.

---

## 9. Termination and exit during rollover

### 9.1 Termination for convenience: Year 1 only

During **Year 1 only**, the Railroad may terminate the production licence for convenience on **sixty (60) days' written notice**, with **no penalty**. This grace period recognizes that Year 1 is a validation period for production operations.

**After Year 1**, termination for convenience requires **one hundred eighty (180) days' notice and payment through the end of the then-current term** (no early termination discount).

### 9.2 Termination for cause

Either party may terminate for material breach, uncured after thirty days' notice. See D07 §15.2.

### 9.3 Insolvency

Insolvency of either party triggers termination and escrow release per D13 §4 and D07 §15.3.

---

## 10. Commercial disputes and renegotiation

### 10.1 Price fairness

The parties acknowledge that Year 1 pricing includes a pilot fee credit ($90,000) and a price lock for Years 1–3. This structure is intended to provide cost predictability and reward pilot completion. Neither party may claim the pricing is unfair or may challenge it based on market conditions during this term.

### 10.2 Scope clarification

If a dispute arises about what is included in the pilot scope or production scope (e.g., whether a specific detector type or failure mode is covered), it is resolved by reference to B01 (System Blueprint) and D12 (Regulatory Status). B01 is the authoritative description of what the Platform does and does not do.

---

## 11. Dispute resolution

Disputes about rollover mechanics (conversion timing, fee calculations, scope boundaries) are addressed per D07 §14 (Dispute Resolution): negotiation → mediation → proceedings.

Either party may seek injunctive relief to prevent termination outside the specified windows.

---

## 12. General

- **Entire agreement:** this document with D02, D07, and incorporated schedules (A2, D08).
- **Precedence:** D07 governs generally; this document governs rollover mechanics.
- **Assignment:** per D13 §6.
- **Amendments:** only in writing, signed by both parties.
- **Severability:** if any provision is unenforceable, the remainder survives.
- **Notices:** in writing to the addresses in D02.

---

## Signatures

**AxiomDynamics**

Name: __________________  Title: __________________

Signature: __________________  Date: __________________

**Railroad**

Name: __________________  Title: __________________

Signature: __________________  Date: __________________

---

*This rollover agreement is a working document. Fee schedules are fixed by A2, which governs where any figure here differs.*
