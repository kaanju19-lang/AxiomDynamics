# Q6 — Entity Formation, Support Boundary, and Corridor Strategy

**Docket position:** None. **Internal analysis — not for customer distribution.** This document is reasoning for the Supplier's own decisions. It is deliberately *not* in `client-assets/`, and it should not be attached to any Order, brief, or proposal.

**Classification:** Internal. Commercially sensitive.

**Companion documents:** D04 (SOW-3 discovery terms) · D06 §1.4 (support boundary) · D13 (IP and assignment) · D14 §3 (what AxiomDynamics does not do)

---

## 1. The question, and the answer in one paragraph

Three linked questions get asked at the same time and pull in different directions: **what legal form should the company take, where should it be formed, and how does a support function operate without quietly becoming an operating one?** The answers are: a **Texas LLC** now, converting to a Delaware C-corporation only when a specific trigger fires; formation is **not** the main thing protecting the business and should not be treated as though it were; and the support boundary is a **language problem before it is a policy problem**, which is why §7 is built around sentences an engineer can actually say at 17:55 rather than around a policy document.

---

## 2. Entity form — LLC, and the reason is thinner than it looks

**Recommendation: form as a Texas limited liability company.**

The honest version of why: an LLC is the cheapest correct answer for a company that has not raised institutional money, and everything a C-corporation offers is either irrelevant now or purchasable later at a known price.

- **Pass-through taxation.** An LLC is taxed once, at the members. For a pre-revenue company whose near-term problem is runway, not distribution, this matters and a C-corp's double taxation does not.
- **Cheap to run.** No board, no formal minutes requirement imposed by statute, no shareholder register to maintain. An early-stage company that spends its governance budget on governance has spent it on the wrong thing.
- **Conversion is routine, not a rebuild.** Converting a Texas LLC to a Delaware C-corporation is a well-trodden path. It costs a few thousand dollars in legal and filing fees and is not a reason to form the wrong entity now. **A company that forms a C-corp to be "ready for investors" has paid for a structure it may never need.**

**What an LLC does not give you, stated plainly.** It does not protect against *personal* liability for the company's own torts committed by the member, it does not survive a failure to observe formalities, and — the point that matters most here — **it does not protect anything that a counterparty has made you personally guarantee.** See §4.

---

## 3. Where to form — Texas, not Delaware

**Recommendation: Texas.**

The generic advice is Delaware, and the generic advice is wrong here for reasons specific to this company rather than generic ones.

**The Delaware argument is about the Court of Chancery.** It is a specialist court for shareholder litigation — disputes among founders, between a board and its investors, over fiduciary duty. **AxiomDynamics, as an LLC with no outside investors, has none of that litigation.** Delaware's principal advantage is insurance against a risk the company does not currently carry.

**The Delaware argument is also about investor familiarity.** That is a real benefit, and it is the reason the conversion trigger in §5 exists. It is not a reason to pay Delaware's annual tax and registered-agent fees for years before the first institutional cheque.

**The Texas argument is about the counterparties.** This docket is written for Texas-headquartered Class I carriers. A Texas entity contracting with a Texas carrier is the least surprising arrangement to a procurement department, and if litigation ever happens, a Texas forum is where it would be least expensive to conduct. That is a modest advantage, but it is a real one and it points the same way as cost.

**On the corridor, not the registered office.** The customer relationships span multiple carriers across multiple states. Nothing about where the entity is registered changes the operating footprint. Registration is a legal address, not a market presence, and a Texas registration does not tilt the commercial strategy toward any one carrier.

### Verified formation and maintenance costs

Checked against official sources rather than recalled. Where a figure could not be settled, it says so.

| Item | Amount | Source | Status |
|---|---|---|---|
| Texas LLC Certificate of Formation (Form 205) | **$300** one-time | Texas Secretary of State, Form 205 instructions | Verified |
| Texas name reservation (optional) | $40 | Texas SOS | Verified |
| Texas franchise tax | **$0** below the no-tax-due threshold | Texas Comptroller, 2026 Form 05-915 | Verified — see below |
| 2026 no-tax-due threshold | **$2,650,000** annualized total revenue | Texas Comptroller 2026 instructions | Verified — up from $2.47M for the 2025 report |
| Texas foreign-entity registration (Form 304), if needed | **$750** | Texas SOS fee schedule (Form 806) | Verified |
| Delaware LLC annual tax | **$300 or $400 for 2026 — conflicting** | Delaware Division of Corporations | **Unresolved** — see below |

**On the franchise tax.** A Texas LLC below $2.65M in annualized total revenue owes no franchise tax. It still files the Public Information Report annually to remain in good standing. A new entity is not required to file a No Tax Due Report in its first five years. Reports are due **15 May**. **The obligation to file does not disappear because the tax is zero** — the most common way a small company loses good standing is by treating "no tax due" as "no filing."

**On the Delaware figure, honestly.** Sources conflict for tax year 2026: the Division of Revenue's older guidance and several guides still state a flat **$300**, while recently published sources and the Division of Corporations' own LLC/LP/GP instructions page reference **$400**. I am not going to pick one to make the table look tidy. The correct action is to read `corp.delaware.gov` at the moment of decision, and the table above should be read as "a few hundred dollars a year, confirm before relying on it." **This does not affect the recommendation**, because the recommendation is not to register in Delaware at all.

**Additional real costs not in the table**, because they are not government fees and vary too much to state usefully: registered agent (roughly $50–$300/year in Texas), and counsel review of the operating agreement, which is the item worth actually paying for. The filing fee is the cheapest part of forming a company and the least important.

---

## 4. The thing that will actually erase the protection

Formation is not the main risk to the liability shield, and treating it as though it were is the most common mistake in this analysis.

**The most likely way to lose the protection on the largest exposure is a personal guarantee.** A Class I carrier's procurement function will, on a vendor with no balance sheet, ask the principal to guarantee obligations personally — payment, indemnity, or performance. A guarantee converts a limited liability company into a personal exposure for exactly the obligations that matter most. **No amount of correct entity formation survives it.** A signature on a guarantee is the single most consequential document this company will sign, and it is usually signed by someone who thinks of it as paperwork.

The position:

- **A guarantee of payment obligations should be refused** wherever possible. If a carrier requires assurance, offer instead: a larger pilot credit, a performance bond, an escrow, or a staged payment schedule that limits the carrier's exposure to value not yet delivered.
- **A guarantee of indemnity for third-party personal injury is the one to think hardest about.** It is also the one a carrier will press hardest for. It should never be signed without counsel, and never as a schedule to an Order signed by an engineer.
- **Whoever signs must know they are signing personally.** A guarantee signed on the assumption that "it's the company's contract" is a guarantee that will be enforced against a person who did not understand it.

The second way the shield fails is **commingling and informality** — paying company expenses from a personal account, no operating agreement, no separation of records. This is cheap to avoid and expensive to discover. The single highest-value spend in the formation process is a proper operating agreement reviewed by counsel, not the filing fee.

**This is not legal advice, and it should not be treated as a substitute for counsel admitted in the relevant jurisdiction.** The specific question of whether a guarantee is enforceable in a given form, against a given signatory, in a given state, is precisely what counsel is for.

---

## 5. When to convert to a Delaware C-corporation

Concrete triggers, so the decision is made by an event rather than by a feeling:

1. **An institutional equity round is being raised.** Convert before the term sheet, not after — the round documents will assume a Delaware C-corp.
2. **A stock-based option pool is wanted for employees.** LLC profits interests can work but are awkward; a C-corp with options is the conventional instrument.
3. **An acquisition approach arrives.** A buyer will usually want a C-corp; conversion is fast, but it is faster if planned.

Absent one of these, the LLC is the correct and cheaper structure. **Do not convert in anticipation of a round that has no lead investor.**

---

## 6. What this section does not decide

- The **operating agreement's** specific terms — vesting, transfer restrictions, deadlock, member departures. Those need counsel.
- **Whether the founder should hold IP personally or assign it.** D13 §9 already requires contributor assignment; the operating agreement must not contradict it.
- **Insurance.** Entity form does not substitute for the E&O cover discussed at D03 §9 and D07 §10. A shield and a policy do different jobs and both are needed.

---

## 7. The support boundary — the part that has to work at 17:55

This is the section with the most operational consequence, and it belongs in Q6 because it is the same problem as the entity question: **what does the company do, and what has it decided not to do.** D06 §1.4 states the boundary and D14 §3 states what the company does not do. What neither contains, and what an engineer actually needs, is **a sentence to say instead.**

The failure mode is not malice or a policy violation. It is a tired engineer on a call at 17:55 with a worried customer, asked a direct question, giving a helpful answer. The helpful answer is the expensive one. **A policy is read at induction; a substitution table is used in the moment.** This is that table.

| The customer asks | Do not say | Say instead |
|---|---|---|
| "Should I pull this car?" | "I would." / "I wouldn't worry." | "The Platform scored this axle at [X] against its own baseline. Whether to pull the car is your operating decision under your rules. I can walk you through how the score was computed." |
| "Is this a false alarm?" | "Probably." / "I doubt it's real." | "I can't characterise it as a false alarm — that's a judgement about the asset, and it isn't mine to make. What I can tell you is what the model saw and how confident it is." |
| "Would you treat it as a defect?" | "Yes, I'd flag it." | "The Platform has flagged it, and here is the evidence behind the flag. What your inspection finds is the answer to whether it's a defect." |
| "What does the regulation require here?" | Anything that sounds like an answer. | "That's your regulatory obligation under your rules, and I'm not able to interpret it. Your compliance group is the right call." |
| "Just tell me what to do." | Any instruction. | "I know that's the frustrating answer. I can't make the call for you — but I can get you everything the Platform computed so your call is fast." |
| "Can you approve this record?" | Any signature or co-signature. | "I can't sign or co-sign your record. I can confirm what the Platform reported, in writing, in the ticket." |
| "Can we talk this through on the phone?" | Substantive advice, verbally. | "Happy to triage on the phone. For anything substantive I'll put it in the ticket so there's a record of what was said — that protects you as much as me." |

**Three disciplines that make the table usable:**

1. **Record the declination verbatim.** Every ticket touching an advisory closes with the sentence actually used. A consistent pattern of declination across hundreds of tickets is the most persuasive evidence of the operating boundary in any later examination of a decision (D06 §1.4).
2. **Written, not verbal.** A ticket proves what was said *and what was not said*. A phone call proves neither.
3. **Nobody is the sole responder for two carriers at once** (D06 §7.4). The 17:55 problem is a staffing problem as much as a language problem; the substitution table does not fix a company that has one engineer covering four time zones.

**Why this is worth the space.** The boundary is the commercial asset. A support engineer who gives one helpful opinion about one train converts a decision-support product into an advisory service, and an advisory service to a Class I carrier about a train is a regulated activity the company is not structured, insured, or staffed to perform. **The sentence is the product boundary, not the policy document.**

---

## 8. Corridor strategy — sequencing, not geography

The corridor question is really a sequencing question: which customer first, and what does the first one buy that the second one cannot.

**Sequence by failure mode, not by carrier size.** The right first customer is the one with a failure mode that the three physical models actually address and data that exists. A Tier 1 carrier with a well-instrumented route and a known bearing problem is worth more as a reference than a larger carrier whose pain point is one the platform cannot see.

**The discovery visit is the unit of commitment, and it is priced accordingly.** SOW-3 (D04) is the Feasibility & Physics Assessment at **$45,000–$75,000**, and its structure is deliberate: the deliverable permits "no, and here is why," which is what makes it honest and what makes it sellable. A discovery engagement that can only conclude "yes" is a sales call with an invoice.

**What the first customer must produce, in order:** a signed F02 (which starts the pilot clock), a disposition ledger with actual reviewer decisions in it, and a reference the second carrier's Chief Engineer will take a call about. The reference is the asset. The revenue is not, at this stage.

**What not to do:** do not run two first customers simultaneously. The support boundary in §7 depends on an engineer who is not spread across two carriers' operating cultures at once, and the first pilot's real output is a set of sentences and processes that the second pilot reuses. Two at once produces two half-built playbooks.

---

## 9. Summary of recommendations

| Decision | Recommendation | Confidence |
|---|---|---|
| Entity form | Texas LLC | High |
| State of formation | Texas | High — Delaware's advantage is litigation the company does not have |
| Conversion trigger | Institutional round, option pool, or acquisition approach | High |
| Largest threat to the shield | Personal guarantee, not formation mechanics | High — and under-weighted in earlier analysis |
| Support boundary | Substitution table, written record, staffing discipline | High |
| First corridor | Choose by failure mode and data availability, not carrier size | Medium — depends on which conversations are live |

**Two things this document cannot tell you:** which carrier to approach first, because that depends on relationships this document does not see; and the correct venue and governing law, which is D07 §14.5 and is an open counsel decision, not a formation question.

---

*Internal analysis. Reviewed when the entity form changes, when a guarantee is requested, or annually. Not for customer distribution.*
