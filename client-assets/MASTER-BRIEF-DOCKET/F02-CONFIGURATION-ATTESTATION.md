# F02 — Configuration Attestation

**AxiomDynamics LLC** · Form F02 · Version 1.0 · Effective ____________ · **Retain 7 years**

> **This is the single most important form in the docket.**
>
> It establishes the **Commissioning Date** — the day the pilot clock starts, the day the **second** payment milestone falls due (the first milestone is signature/NTP under A2 §5.1), and the day the 12-month term begins. It also establishes **what the Customer certified about its own environment**, which is the baseline against which every later question about configuration drift is answered.
>
> **One date does three jobs, and they must all be the same date.** The pilot clock, the second instalment, and the twelve-month evaluation period all start here. If they started on different dates, the customer would be paying against a clock that had not started, or evaluating against a clock that had already run. Signature is the first instalment (A2 §5.1: 40% on signature); **this form is the second (30%)**; month six completion is the third.
>
> **Signed by the Customer's IT Director. Never by us.** We have no authority to attest to the state of a system we do not operate (D14 §3).

---

## Part 1 — Site and order reference

| | |
|---|---|
| Customer legal name | |
| Site name and location | |
| Order number | SOW-____-________ |
| Configuration Attestation number | CA-______ (sequential per site) |
| Effective date of this attestation | |

---

## Part 2 — Attestation

I, the undersigned, being the IT Director (or equivalent officer with authority over the computing environment at this site) of the Customer named above, **certify on behalf of the Customer** that:

### 2.1 Installation

The AxiomDynamics Platform has been installed at this site by the Customer's own personnel, on ____________ (date), using the following method:

☐ **Standard** (C01 Part B)  ☐ **Air-gapped** (C01 Part C)  ☐ **Containerized** (C01 Part D)

### 2.2 Location and access

The Platform is running at:

| | |
|---|---|
| Hostname / IP | |
| Port | (default 8420) |
| Database path | (default `/var/lib/axiom`) |
| Access method | ☐ HTTP on local network ☐ HTTPS via Customer reverse proxy |

### 2.3 Configuration confirmed

I confirm that the installation matches the agreed architecture (B01, B05):

☐ The Platform makes **no outbound network connections**. I have verified this. ☐ Not verified — explanation: __________
☐ The Platform is bound to the address intended, not exposed beyond the local network: __________
☐ Database storage is on Customer-controlled media: __________
☐ Time synchronisation (NTP) is configured on this host. ☐ Not configured — explanation: __________

> **The time synchronisation line is not a formality.** Every disposition record carries a timestamp. If the host clock drifts, the ledger's chronology is unreliable, and chronology is what makes the record useful after an incident. D09 §4.2 lists NTP as a Customer responsibility.

### 2.4 Testing completed

☐ The test suite has been run and passed (C01 Part B §B4, or the equivalent step in Part C §C4 / Part D)
☐ The Platform is reachable and returning health responses
☐ A test advisory has been generated and dispositioned successfully
☐ Historical data has been loaded, at least in part

### 2.5 Personnel readiness

☐ Personnel who will review advisories have been identified (number: ______)
☐ Those personnel have completed or are enrolled in certification (C02)
☐ An Administrator has been designated and trained (C02 §2.3)
☐ A Safety Officer has been designated (C02 §2.4)

> **Certification need not be complete at commissioning.** The requirement is that reviewers are identified and enrolled. But **no disposition may be recorded by an uncertified reviewer** (C02 §2.2), and a pilot where advisories go undispositioned breaches D02 §5, obligation 5. If certification will take longer than four weeks, say so now.

### 2.6 Operational readiness

☐ The Customer's IT team is prepared to operate and maintain the Platform (C01 Part H)
☐ A backup routine is configured (frequency: ______)
☐ A named individual is responsible for the Platform: ____________________

### 2.7 Understanding of what is being certified

I understand and confirm that:

☐ The Platform is a **decision-support tool**, not a certified safety appliance (D12 §1).
☐ The Platform does **not** satisfy any requirement for a WDBD inspection or any other regulatory inspection (D12 §3).
☐ The Customer's **regulatory obligations remain entirely its own** and are unaffected by this deployment (D12 §5).
☐ **Operating decisions remain the Customer's**, made by its qualified personnel, and are not made by AxiomDynamics (D14 §4).
☐ **AxiomDynamics does not operate, monitor, or maintain this installation** (D14 §3).
☐ Any material change to this configuration requires an updated attestation (Part 4).

---

## Part 3 — Commissioning Date

**The Commissioning Date for this site is:** ____________________ (date)

> This date is the trigger for: the pilot term start (D02 §1), the second payment milestone (D02 §3.2), and the twelve-month evaluation period (D02 §8). It is set by the Customer's signature below, not by us.

---

## Part 4 — Configuration changes requiring a new attestation

A new attestation (CA-______-02) must be completed if any of the following occurs:

1. Platform software major version change
2. Operating system change or upgrade affecting the Platform
3. Host relocation or IP address change
4. Database path or storage change
5. Detector feed source change, or detector spacing change at this site
6. Change to the network exposure of the Platform
7. Any change that affects the answers in Part 2

**A material configuration change that is not re-attested means the baseline is stale.** In a dispute about whether an advisory was produced correctly, the current attestation is the first document examined. Keep it accurate.

---

## Part 5 — Signatures

**Customer — IT Director (or equivalent)**

Name: ____________________  Title: ____________________

Signature: ____________________  Date: ____________________

**Customer — Pilot Sponsor (acknowledging operational readiness)**

Name: ____________________  Title: ____________________

Signature: ____________________  Date: ____________________

**AxiomDynamics — witness (advisory only; does not attest to configuration)**

Name: ____________________  Title: ____________________

Signature: ____________________  Date: ____________________

> **Note on our signature line.** We sign as a witness that the form was executed. **We do not certify the configuration** — that is the Customer's attestation about its own environment. This distinction is deliberate and should not be blurred by anyone, in any meeting.

---

## Part 6 — Distribution

| Copy | Holder | Format |
|---|---|---|
| 1 | Customer — IT Director | Signed original |
| 2 | Customer — Pilot Sponsor | Signed copy |
| 3 | AxiomDynamics — contract file | Signed copy or scanned PDF |
| 4 | Platform records directory | PDF, referenced in the site record |

---

*Form F02. Uncontrolled when printed. This attestation creates no liability for AxiomDynamics as to the configuration it describes.*
