# F00 — Forms Register & Documentation Policy

**Docket position:** F00. The index and the policy for every executable form in the AxiomDynamics documentation system.

**Classification:** Client-facing.

---

## Part 1 — The documentation policy

These seven rules apply to every form, every agreement, and every record we produce. They are not stylistic preferences. They are the reason a small company can be trusted with a Class I carrier's operating risk.

### Rule 1 — Every commitment is in a document, and every document has a number.

Nothing is agreed by conversation. If a promise matters, it appears in a numbered document with a version and a date. A verbal assurance is not a commitment, and we do not act on one. This protects the customer as much as it protects us: a commitment they cannot point to is a commitment they cannot enforce.

### Rule 2 — Every form has exactly one purpose.

A form that does two things will eventually do both badly. The Change Order changes scope; the Acceptance form accepts a deliverable; the Travel form claims expenses. They do not substitute for each other. Where a process needs two of them, it uses two.

### Rule 3 — Every form states who signs and what happens if nobody does.

An unsigned form with no default is a process that stops. Every form in this register specifies the signatory and the consequence of silence. Where silence has a consequence, it is stated on the form itself, in plain words, not buried in a master agreement.

### Rule 4 — Plain language, with the technical term in brackets when one is needed.

We write "we" and "you" where the meaning is clear, and use the defined terms where precision requires it. Legalese is not a sign of professionalism; it is a sign the drafter could not decide what the sentence meant. Enterprise-grade means a document a Chief Engineer can read without calling legal.

Square brackets in this docket mean **one thing only: a defined term or an editorial substitution being offered to the reader**, as in "[the mediation rules of the chosen provider]". Brackets are never used to mark a blank to be filled in. Blanks are underscores (Rule 7). This distinction exists because the two were previously mixed, and a bracketed placeholder that is neither a definition nor a blank is a sentence nobody can act on.

### Rule 5 — Records are retained, and retention is stated on the record.

Every executed form is retained for the period stated in its own header. Nothing is discarded because it became inconvenient. The disposition ledger, the order register, and the certification registry are the three records that make everything else defensible.

### Rule 6 — A form records an event. It never varies a term.

**No form in this register can amend, override, or set aside A2 (Rate Card), D02 (Pilot Agreement), D03 (MSA) or D07 (Master Contract).** Where a completed form appears to conflict with one of those instruments, **the instrument governs and the form is corrected.**

This is the most important rule in this policy, because it is the one most likely to be broken by accident. A payment schedule that quietly restates a fee, a change order that alters liability, an acceptance that waives a warranty — each of these is a form doing something only a signed agreement may do. The forms exist to *evidence* what the agreements already permit; they are not a second, informal contract that bypasses the first.

### Rule 7 — A blank and a decision are different things, and the document says which it is.

Every unfilled field in this docket is one of exactly two kinds, and the drafter must know which before writing it:

**A fill-in blank** is a value that exists and will be entered at execution — a party name, a date, an amount agreed in the Order, an address for notices. It is written as underscores `________`, and it is safe to leave because the process that fills it is defined and the consequence of it staying empty is stated (Rule 3).

**An unmade decision** is a question the docket has not answered — which law governs, which arbitration seat, which entity form. It is **never** written as a blank, because a blank implies "we know that this will be filled in." An unmade decision is written as an **explicit open item**: the section states what has to be decided, who must decide it, and what happens in the meantime. A decision left unmade is a defect; a decision labelled as unmade is a work item. The difference between the two is the difference between a document that is quietly incomplete and one that is honestly incomplete.

**The prohibited pattern.** Never write a clause that points to a field which no document actually contains. An earlier draft of D07 §14.3 sent dispute venue to "[the courts / arbitration seat] stated in the Order signature block" — and no Order template has that field. The clause therefore described a decision as though it had already been made somewhere else, which is worse than either leaving it blank or admitting it was open: it read as complete to every person who did not go and check, and there was nothing to check. Where a term belongs in a separate instrument, the clause cites that instrument and section by number (Rule 1), not a field whose existence nobody has verified.

The lawful scope of each form is narrow and worth stating:

| Form | What it may decide | What it may never do |
|---|---|---|
| F02 Configuration Attestation | The date commissioning was completed and what the Customer certified | Change the term, the fee, or the acceptance standard |
| F03 Change Order | Scope, schedule, and price of one Order, with both signatures | Alter liability, IP, insurance or confidentiality — those are D07 and D03 only |
| F05 Payment Terms | The instalment split and invoice dates for one Order | Restate or discount a fee set by A2 |
| F06 Deliverable Acceptance | That a deliverable was accepted or rejected | Waive a warranty or a limitation of liability |
| F09 Disposition Record | What a reviewer decided, and when | Constitute regulatory evidence of inspection (D12 §3) |
| F11 Site Visit Report | What was observed, and what boundary was held | Create an obligation or a scope of work |

### The one rule that governs the others

**If a form does not exist for the thing you are about to do, stop and create the form. Do not do the thing and document it afterwards.**

This is the failure mode the entire docket exists to prevent: work performed, commitment made, no document. A form created before the act is evidence. A form created after the act is a reconstruction, and reconstruction is what the other side's lawyer attacks.

---

## Part 2 — Forms register

| ID | Form | Used when | Signatory | Default if unsigned |
|---|---|---|---|---|
| **F00** | Forms Register & Documentation Policy | This document | — | — |
| **F01** | Site Readiness & Survey Questionnaire | Before any site deployment | Customer technical contact | No deployment scheduled |
| **F02** | Configuration Attestation | On commissioning at every site | Customer IT Director | **No Commissioning Date; pilot term does not start** |
| **F03** | Change Order | Any change to scope, price, schedule | Both authorised reps | Change does not take effect |
| **F04** | Travel Pre-Approval Request | Before booking any billable travel | Customer authorised rep | Travel is not billable |
| **F05** | Payment Terms Schedule | With every Order | Both parties | A2 §10 default terms apply |
| **F06** | Deliverable Acceptance | On delivery of a deliverable | Customer authorised rep | Deemed accepted after 10 Business Days |
| **F07** | Travel & Expense Claim | Within 14 days of travel | Supplier, countersigned by Customer | Not reimbursed |
| **F08** | Reviewer Certification Application | Before a reviewer is certified | Candidate + Customer sponsor | No certification issued |
| **F09** | Advisory Disposition Record | Every advisory, without exception | Certified Reviewer | **Disposition missing — D02 §5 obligation 5 breach** |
| **F10** | Security Incident Notification | On a reportable incident | Supplier or Customer | **Breach of D09 §6** |
| **F11** | Site Visit Report | After every on-site attendance | Supplier engineer | Visit undocumented; not billable |
| **F12** | Formal Notice | Contractual notices, termination, breach | Authorised signatory | Notice not effective |
| **F13** | Data Export & Transition Certificate | On termination or migration | Both parties | Data export not certified complete |

---

## Part 3 — How the forms fit together

### The pilot lifecycle

```
F01 Site Survey
   ↓
SOW-1 signed (D04)
   ↓
F04 Travel Pre-Approval (if on-site attendance)
   ↓
F11 Site Visit Report (after attendance)
   ↓
F07 Travel & Expense Claim (within 14 days)
   ↓
F02 Configuration Attestation  ←── THIS STARTS THE PILOT CLOCK
   ↓
F08 Reviewer Applications → certifications issued
   ↓
F09 Disposition Records (every advisory, throughout)
   ↓
F03 Change Order (if anything changes)
   ↓
F06 Acceptance (per deliverable)
   ↓
F05 Payment milestones
   ↓
Pilot evaluation report → D05 conversion election
```

### The three records that carry evidentiary weight

1. **F02 Configuration Attestation** — establishes the Commissioning Date and the configuration the Customer certified. Without it, there is no start date and no baseline for any later dispute about whether the environment changed.
2. **F09 Disposition Records** — the append-only ledger. Establishes what the human reviewer decided, when, and on what advisory. This is the record that answers "did someone look at this?" after an incident.
3. **F03 Change Orders** — establishes that scope moved deliberately rather than by drift.

**Note on F09 — current implementation gap.** The Platform's disposition write path currently overwrites records rather than appending (see B01 §7, blocking gap #2). Form F09 describes the required behaviour. Until the append-only ledger is implemented, the evidentiary claim in this docket is ahead of the code. That gap is disclosed in D09 §4.4 and must be closed before production deployment. **Do not represent F09 as append-only until it is.**

### The forms that protect the liability boundary

F11 and F09 together are what keep us on the right side of D14. F11 records what we observed and what we declined to advise. F09 records that a qualified human made the operating decision. Between them they answer the only two questions that matter after an incident: *what did the vendor say,* and *who decided to act.*

---

## Part 4 — Numbering and version control

**Form numbering:** F-prefix, sequential. Once issued, a number is never reused, even if the form is withdrawn.

**Order numbering:** `SOW-[template]-[YYYY]-[sequence]`. Example: `SOW-3-2026-004`.

**Version control:** every form carries a version and effective date in its header. A form is superseded, never edited in place. Superseded versions are retained — a dispute about a 2026 order is governed by the form in force in 2026, not the current one.

**Retention:** the period stated in each form's header. Where none is stated, seven years from the later of execution or the end of the engagement.

---

## Part 5 — What we do not have forms for, and why

Honesty about gaps is part of the policy.

1. **No purchase-order form.** The Customer's own PO process governs (D03 §4.1). We do not issue POs.
2. **No invoice template in this register.** Invoicing is a finance function; the payment terms are F05, and the invoice itself follows the Customer's AP requirements.
3. **No "letter of intent" or "MOU".** Either there is a signed Order or there is not. An LOI creates the appearance of commitment without the substance, and is the most common source of unpaid work.
4. **No verbal-agreement record form.** Verbal agreements are not recognised (Rule 1). There is deliberately no form to memorialise one.

---

*Documentation policy. Reviewed annually. Deviations require the written approval of the Principal Systems Architect.*
