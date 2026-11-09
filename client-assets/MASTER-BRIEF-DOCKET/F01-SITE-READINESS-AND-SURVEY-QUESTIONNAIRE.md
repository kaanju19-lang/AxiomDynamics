# F01 — Site Readiness & Survey Questionnaire

**AxiomDynamics LLC** · Form F01 · Version 1.0 · Effective ____________ · **Retain 7 years**

**Purpose:** to establish, in writing and before any deployment is scheduled, whether a site can support the Platform. This form is completed by the Customer's technical contact, not by us.

**Why this form exists:** every failed deployment we could avoid is one where the detector spacing was wrong, the server had no disk, the network path did not exist, or nobody had authority to sign. This questionnaire takes 90 minutes to complete and prevents all four.

**Return to:** [AxiomDynamics support address] **By:** ____________ (date)

---

## Section 1 — Site identification

| | |
|---|---|
| Customer legal name | |
| Site name | |
| Subdivision / district | |
| State / province | |
| Nearest milepost or station | |
| Site type | ☐ Wayside detector ☐ Classification yard ☐ Other: ______ |
| Completed by (name, title) | |
| Date completed | |

---

## Section 2 — Detector and data

**2.1** What detector types are installed at or near this site?

☐ Hot bearing detector (HBD) ☐ Hot wheel detector (HWD) ☐ Wheel impact load detector (WILD)
☐ Truck performance detector (TPD) ☐ Acoustic bearing detector (ABD) ☐ Other: ______________

**2.2** Detector spacing on this subdivision: ________ miles (average)

**2.3** Are the detectors owned and maintained by the Customer? ☐ Yes ☐ No — if no, by whom: ____________

**2.4** How is detector data currently delivered?

☐ Real-time feed ☐ Batched (interval: ______) ☐ Manual export ☐ Not currently retained

**2.5** Data format available: ☐ CSV ☐ JSON ☐ Database export ☐ Vendor-proprietary — specify: __________

**2.6** Historical data available: ______ months

**2.7** Is there a documented maintenance schedule for these detectors? ☐ Yes — attach or reference: __________ ☐ No

> **This matters contractually.** Under D07 §6 the Customer warrants its detector hardware is maintained to its own standards and AAR recommended practice. If the answer is "no schedule exists," that is not a reason to stop — it is a reason to record the position now, in writing, before a disputed advisory occurs.

---

## Section 3 — Edge compute

**3.1** Will the Platform run on dedicated hardware or existing infrastructure?

☐ Dedicated server ☐ Shared server ☐ Virtual machine ☐ Container on existing cluster

**3.2** Operating system: ________________ Version: ________

**3.3** Python version available: ________ (minimum 3.11)

**3.4** CPU: ______ cores · RAM: ______ GB · Free disk: ______ GB

> **Minimum reference specification:** 4 cores, 8 GB RAM, 100 GB free disk, Ubuntu 22.04 LTS or equivalent. The Platform is lightweight — these are floors, not recommendations. Under-specifying here is the most common cause of a slow commissioning.

**3.5** Is the host permitted to run a long-lived service (systemd unit or container)? ☐ Yes ☐ No — explain: __________

**3.6** Physical location of the server: ____________________

**3.7** Is physical access to the server controlled? ☐ Yes ☐ No

---

## Section 4 — Network and air-gap

**4.1** Does the Platform host have outbound internet access? ☐ Yes ☐ No

> **The Platform requires none.** B05 confirms zero outbound calls. If the answer is "Yes," it is permitted but not required — and it should be restricted unless there is a specific operational reason.

**4.2** Is inbound access to the Platform's port available on the local network? ☐ Yes ☐ No — port: ______

**4.3** If HTTPS is required, who provides the reverse proxy?

☐ Customer's infrastructure team ☐ Not required ☐ Undetermined

> **The Platform does not terminate TLS.** D09 §4.2 states this. If the Customer's security policy requires HTTPS, they place nginx or Apache in front of it. Confirm this now, not during a security review.

**4.4** Network path from detector feed to Platform host confirmed? ☐ Yes ☐ No — blocked by: __________

**4.5** Is this site required to remain fully air-gapped? ☐ Yes ☐ No

> If yes, installation uses C01 Part B (air-gapped method). That requires a sealed archive transfer, which adds roughly one week to the schedule. Plan for it.

---

## Section 5 — People

| Role | Name | Title | Email |
|---|---|---|---|
| Technical contact | | | |
| IT Director (signs F02) | | | |
| Pilot Sponsor | | | |
| Safety Officer | | | |

**5.1** How many personnel will review advisories? ______

**5.2** Will those personnel complete certification (C02) before commissioning? ☐ Yes ☐ No — explain: __________

**5.3** Who has authority to accept deliverables on the Customer's behalf? ____________

**5.4** Who issues purchase orders? ____________

---

## Section 6 — Existing systems and integration

**6.1** What system currently handles this monitoring function? ____________________

**6.2** Does the Customer require any integration with that system? ☐ No ☐ Yes — describe: __________

> **Default position: no integration.** The Platform runs as a separate overlay. It does not write to, read from, or influence any control, signal, or protection system (D02 §6). Any requested integration is a change: it requires Form F03 and a fresh liability review, because integration is how a decision-support tool becomes an operational dependency.

**6.3** Are there any existing vendor contracts that would be affected? ☐ No ☐ Yes — describe: __________

---

## Section 7 — Readiness determination

**Completed by AxiomDynamics after receiving the above:**

| Item | Status |
|---|---|
| Detector data available and format compatible | ☐ Ready ☐ Conditional ☐ Not ready |
| Edge compute meets minimum specification | ☐ Ready ☐ Conditional ☐ Not ready |
| Network path confirmed | ☐ Ready ☐ Conditional ☐ Not ready |
| Personnel identified and available | ☐ Ready ☐ Conditional ☐ Not ready |
| **Overall determination** | ☐ **Ready to schedule** ☐ **Conditional — see notes** ☐ **Not ready** |

**Notes / conditions:**

________________________________________________________________

**Reviewed by:** ____________________ (AxiomDynamics)  **Date:** __________

---

## Section 8 — Acknowledgement

By signing, the Customer confirms the information above is accurate to the best of its knowledge as at the date of completion. **The Customer remains responsible for the accuracy of its own site information** (D03 §6, D07 §6). If a condition changes materially before commissioning, the Customer will notify us.

**Customer representative:** ____________________  **Title:** __________  **Date:** __________

---

*Form F01. Uncontrolled when printed. Current version stated in the release notes accompanying the Order.*
