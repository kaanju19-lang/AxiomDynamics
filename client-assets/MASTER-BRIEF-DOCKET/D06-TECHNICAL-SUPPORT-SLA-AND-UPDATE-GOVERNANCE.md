# D06 — Technical Support, SLA & Update Governance

**Docket position:** D06. Defines Supplier's support obligations, response times, patch cadence, security vulnerability handling, and false-positive cost regime. Incorporated by reference in D07 §4, D02, and all deployment orders.

> **Drafting status:** Commercial grade. Requires review by both parties' ops teams and legal counsel. Response time commitments must be confirmed against AxiomDynamics' actual support capacity and the Railroad's tolerance.

---

## 1. Support tier and scope

### 1.1 Support is included in the licence

Every active licence (D02 Pilot, D08 Production) includes technical support at no additional charge. Support is limited to:

- Defects in the Platform (code, documentation, or supplied models).
- Operational troubleshooting (deployment issues, configuration questions, integration problems).
- Update delivery and patch application assistance.
- Licence registry and certification administration.

### 1.2 Support does NOT include

- **Installation or deployment work by Supplier:** the Railroad performs all installation. Supplier provides advisory support only (D14 §3).
- **On-site visits or remote access to the Railroad's systems:** Supplier does not access the Railroad's environment except by read-only, time-limited session for verified diagnostics, with prior written authorization and under D09 security requirements.
- **Development of custom models or modifications:** additional physics models, proprietary rules, or customizations are billable professional services, not included support.
- **Regulatory compliance or audit support:** the Railroad is responsible for its own regulatory filings and audits. Supplier provides documentation and clarification on request but does not conduct regulatory work.
- **Operational decisions or train dispatching guidance:** the Platform is decision-support only. Supplier does not advise on operating procedures.

### 1.3 Support contact

Support is available via email and ticketed system. **Email:** support@axiom-dynamics.com (monitored during business hours). **Ticket system:** [URL]. **Emergency escalation:** [phone + out-of-hours contact]. See §2.2 for severity definitions and escalation thresholds.

---

## 2. Response time commitments (SLA)

### 2.1 Severity definitions

| Severity | Description | Examples | Response target |
|---|---|---|---|
| **Critical** | Platform is down or non-functional; production operations are blocked; data loss is occurring or imminent | API unresponsive; database corruption; all advisories fail to generate; security breach confirmed | 4 business hours |
| **High** | Platform is partially degraded; a material function is unavailable; workaround exists but is cumbersome | One API endpoint down; database queries slow; certification registry unreachable | 8 business hours |
| **Medium** | Feature is malfunctioning or degraded; operational impact is minor; workaround is straightforward | Incorrect ranking on a subset of advisories; UI is slow; patch deployment is blocked | 1 business day |
| **Low** | Documentation is unclear; cosmetic issue; feature request | Typo in user guide; minor UI inconsistency | Best effort, within 5 business days |

### 2.2 Response time definition

"Response time" means Supplier acknowledges receipt of the ticket, confirms the severity, and indicates what action will be taken (e.g., "We will investigate and provide a fix within three days," or "This is a product limitation; here is the workaround"). Response does not mean the issue is resolved; it means the Supplier has engaged.

### 2.3 Update to severity classification

Either party may request a severity re-classification. If the Railroad believes an issue classified as "Medium" is actually blocking production, it may escalate to "High" with justification. Supplier will review and confirm or clarify the classification within one business day.

### 2.4 Outside business hours

Support response times apply during **U.S. Eastern Time, Monday–Friday, 08:00–18:00 ET**, excluding federal holidays. Issues reported outside these hours are queued and responded to on the next business day. **Critical issues reported outside business hours will be acknowledged on the next business day, and on-call escalation is available at no additional charge if the issue remains critical and unresolved after the first response.**

---

## 3. Patch and release governance

### 3.1 Update categories

| Category | Trigger | Typical cadence | Deployment urgency |
|---|---|---|---|
| **Security patch** | Vulnerability in a dependency or the Platform itself | As discovered (no fixed schedule) | See §3.2 |
| **Defect fix** | Bug affecting functionality | Monthly (collected into releases) | Next planned release, or sooner if critical |
| **Minor release** | New feature or UX improvement | Quarterly | Opt-in; Railroad chooses when to deploy |
| **Major release** | Breaking change to API or schema | Annually (or longer between major versions) | Opt-in; Railroad plans migration window |

### 3.2 Security patch response

**For vulnerabilities affecting the Platform directly** (code, models, or direct dependencies):

- **Critical severity (CVSS 9+, or affects confidentiality/integrity/availability):** Supplier releases a patch within **five (5) business days** and notifies the Railroad with severity, impact, and instructions. The Railroad is expected to apply the patch within **thirty (30) days** (see §3.3).
- **High severity (CVSS 7–8.9):** patch released within **ten (10) business days**; Railroad applies within **forty-five (45) days**.
- **Medium severity (CVSS 4–6.9):** patch included in next monthly or quarterly release; Railroad applies within **ninety (90) days**.
- **Low severity (CVSS 0–3.9):** included in next scheduled release; no urgency.

**For vulnerabilities in transitive dependencies** (libraries used by libraries): Supplier assesses whether the Platform is actually exposed. If not exposed, the vulnerability does not require action. If exposed, it is treated as a direct vulnerability per the severity bands above.

### 3.3 Patch application by the Railroad

The Railroad applies patches by:
1. **Testing:** deploy the patch to a test environment; run the test suite (C01 Part B §B4) and exercise the Platform with historical data.
2. **Validation:** confirm that existing dispositions are unaffected and that the Platform behaves as before.
3. **Deployment:** apply to production at a scheduled maintenance window.

**The Railroad is responsible for patch testing and deployment.** Supplier provides the patch and guidance, but the Railroad makes the go/no-go decision and bears the risk of any unintended consequences in their environment.

If the Railroad has not applied a critical patch within **sixty (60) days**, Supplier may escalate to the Railroad's CTO/Chief Engineer to confirm the delay is intentional or to offer remediation assistance.

### 3.4 End-of-life (EOL) policy

- **Current major version:** receives security patches and critical defect fixes for three (3) years from its release date.
- **Previous major version:** receives security patches only for two (2) years after the current major version is released.
- **Older versions:** receive no patches. Customers are expected to upgrade.

Example: If v1.0 is released on 2026-01-01 and v2.0 is released on 2029-01-01, then v1.x receives patches through 2029-01-01 (3 years), and security patches only through 2031-01-01. After 2031-01-01, v1.x is unsupported and users must upgrade to v2.x or later.

### 3.5 Upgrade path

The Railroad may upgrade to a new major version at any time. Upgrades are handled as a **Statement of Work (D04)** with a defined scope: data migration, schema updates (if any), testing, and cutover planning. Upgrades are not included in standard support and are billable.

---

## 4. False-positive cost regime — the service credit schedule

### 4.1 Definition of a false positive

A **false positive** is an advisory that the Platform generates and a Certified Reviewer records a disposition of "reject" (meaning the Platform assessment was incorrect or did not warrant action), **and** the false positive was not caused by:
- Detector data anomalies or miscalibration (warranted by the Railroad per D07 §6).
- Configuration error by the Railroad (e.g., wrong detector spacing, stale maintenance records).
- Use of the Platform outside its intended scope (e.g., a detector type the Platform was not trained on).

In other words: a false positive is a Platform defect, not a data quality or deployment issue.

### 4.2 Measurement and reporting

The Railroad tracks false positives by:
1. **Recording the disposition** in the Platform (Reviewed, Rejected, with brief note).
2. **Monthly reporting:** the Railroad submits a summary to Supplier of the count of rejected advisories by site, severity tier, and (if known) bearing type or failure mode.

Supplier and the Railroad reconcile false-positive counts quarterly. Where counts differ, they investigate the categorization (was it truly a false positive, or a data issue?).

### 4.3 Service credit schedule

False-positive credits apply **only to production licences (D08), not to pilot agreements (D02).**

Measured over a **calendar quarter** (Q1=Jan–Mar, Q2=Apr–Jun, Q3=Jul–Sep, Q4=Oct–Dec):

| False-positive rate (as % of total advisories generated) | Service credit |
|---|---|
| 0.0–0.5% | None |
| 0.5–1.0% | 5% of platform fee for that quarter |
| 1.0–2.0% | 10% of platform fee |
| 2.0–5.0% | 25% of platform fee |
| > 5.0% | 50% of platform fee; Supplier must issue a fix or accept termination for cause |

**Example:** A site generates 10,000 advisories in Q1. The Railroad records 75 rejections (0.75% false-positive rate). The platform fee for that site in Q1 is $45,000 (per A2). The credit is 5% × $45,000 = $2,250. The Railroad's next invoice is reduced by $2,250.

### 4.4 Credit application

- **Automatic:** credits are calculated by Supplier based on the Railroad's monthly reports.
- **Applied to the next invoice** for the same site or rolled forward to the following quarter if no further invoices are due.
- **Capped at full fee:** credits never cause a negative balance or a refund; they reduce the fee to zero and stop.
- **Non-transferable:** credits apply only to the site where the false positives occurred, not to other sites or carriers.

### 4.5 Exclusions and limitations

Credits do **not** apply to:
- Pilot agreements or evaluation licences.
- Sites where the Platform has been in operation for less than **sixty (60) days** (ramp-up period; data quality and tuning are still in progress).
- False positives caused by detector data quality (the Railroad's responsibility per D07 §6).
- False positives caused by configuration changes the Railroad made without notifying Supplier (D07 §5.8).

**The service credit schedule is the Railroad's sole remedy for false positives.** It does not constitute a guarantee of detection accuracy, does not permit the Railroad to withhold payment of the full fee, and does not create a right to terminate the licence.

---

## 5. Performance reporting and continuous improvement

### 5.1 Quarterly performance report

Supplier provides the Railroad with a quarterly report covering:
- Uptime (% of time the Platform was accessible and responsive).
- Advisories generated and dispositioned (count by severity tier).
- False-positive rate (measured per §4.2).
- Critical or high-severity issues reported, root causes, and resolutions.
- Any changes to the underlying models or detection thresholds (and the rationale).
- Recommended operational changes or tuning based on observed patterns.

### 5.2 Incident post-mortems

If a critical or high-severity issue occurs, Supplier and the Railroad schedule a joint post-mortem within **ten (10) business days** of resolution. The post-mortem covers:
- What happened and when.
- Impact (how many advisories, which sites, how long).
- Root cause.
- Corrective actions already taken.
- Preventive measures going forward.

Post-mortem findings are documented and retained for twelve months.

### 5.3 Model tuning and continuous improvement

The Platform's models are fixed at deployment but may be refined based on observed data. **Any model change requires:**
1. Analysis by Supplier demonstrating a statistically significant improvement in detection accuracy or false-positive reduction.
2. Written notification to the Railroad at least **fourteen (14) days** before deployment.
3. The Railroad's right to defer the change for one quarter if operational circumstances warrant.

Model changes that increase detection sensitivity (more advisories) are always opt-in (the Railroad agrees before deployment). Changes that reduce false positives are deployed automatically but can be rolled back on the Railroad's request within 30 days.

---

## 6. Escalation and dispute resolution

### 6.1 Support escalation path

**Tier 1 (first response):** Support team confirms receipt and severity (see §2).

**Tier 2 (investigation):** Engineering team investigates and proposes remediation or workaround (within response time + 2 business days).

**Tier 3 (escalation):** if the issue remains unresolved after Tier 2, the Railroad may escalate to Supplier's VP of Operations and the Railroad's CTO. Both commit to a joint call within **five (5) business days** to agree on a resolution path.

### 6.2 Escalation triggers

Either party may escalate to Tier 3 if:
- A Critical issue is unresolved after **ten (10) business days**.
- A High issue is unresolved after **twenty (20) business days**.
- False-positive rate exceeds 5% for two consecutive quarters.
- A security patch is not available within the SLA window (§3.2).

### 6.3 Dispute over severity classification

If the parties disagree on severity, they classify the issue at the higher suggested level and proceed with that response time. Re-classification can occur after the initial response.

---

## 7. Support staffing and continuity

### 7.1 Support team

Supplier maintains a support team of at least **[2–3]** full-time staff dedicated to customer support (including AxiomDynamics' own internal use). Team members receive training on the Platform, the railroad domain, and troubleshooting procedures.

### 7.2 On-call coverage

For **Critical** issues reported outside business hours (see §2.4), an on-call engineer is available to respond within **4 hours**. On-call is staffed by a rotation of senior engineers; contact details are provided separately under confidentiality.

### 7.3 Key person dependency

Supplier will not allow more than one person to be the sole expert on any critical function (e.g., security patch development, database schema management). Cross-training and documentation are maintained to ensure continuity.

---

## 8. Support termination and wind-down

If the licence is terminated (D07 §15), support ceases at the termination date. Supplier provides **90 days of transition assistance at no charge** (D07 §15.6), including data export and operational guidance, after which support is discontinued.

If Supplier ceases business or stops supporting the Platform (insolvency, or intentional discontinuation), the license terms in D07 §15.3 and the escrow terms in D13 §4 are triggered.

---

## 9. Support communications and records

### 9.1 Confidentiality of support tickets

All support communications are subject to D11 (Mutual NDA). Support tickets may contain sensitive information about the Railroad's operations, detector data, or internal procedures. Supplier treats all support information as confidential and does not use it for any purpose other than resolving the issue and improving the Platform (subject to D13 §2, which permits aggregated, non-attributable learning).

### 9.2 Support ticket retention

Support tickets are retained by Supplier for **two (2) years** and then purged, unless the ticket relates to a security incident or contractual dispute, in which case retention continues per D09 and D07 §7.

### 9.3 Ticket access

The Railroad may request a read-only audit log of all support tickets and their resolution status at any time. Ticket contents are summarized (not full text) to protect other customers' confidential information.

---

## 10. Monitoring and audit

### 10.1 SLA compliance audit

Once per calendar year, the Railroad may audit Supplier's compliance with this SLA. Audit scope is limited to:
- Response time adherence (sample 5–10 tickets; did we respond within the stated window?).
- Patch release and notification procedures (did we release security patches within the stated window?).
- Support team competency and training records (anonymized).

Audit is conducted by the Railroad or a third-party auditor bound by confidentiality. Supplier provides documentation and, if requested, interviews with support staff.

### 10.2 Metrics dashboard

Supplier provides the Railroad with a live, read-only metrics dashboard showing:
- Current uptime (%) for the past 30 days.
- Mean time to first response (for all tickets in the current month).
- Mean time to resolution (for closed tickets).
- Count of open tickets by severity.

Dashboard access is via a web portal with Railroad-specific credentials.

---

## 11. Scope exclusions and service limitations

### 11.1 Not covered by support

Supplier is not responsible for:
- The Railroad's failure to apply a security patch within the stated window (the Railroad bears the risk of unpatched systems).
- The Railroad's misconfiguration of the Platform (the SOP in C01 is the configuration baseline; deviations are the Railroad's responsibility).
- Third-party software or infrastructure issues (OS bugs, database engine issues, network failures) not introduced by the Platform.
- Performance degradation caused by the Railroad's excessive data volume or inefficient queries.

### 11.2 Support capacity limits

Supplier maintains support for up to **[X]** concurrent licensees. If demand exceeds capacity, Supplier will hire additional staff within **two (2) quarters** or offer commercial support tiers (premium support contracts) to manage load. Until additional capacity is added, support response times may be extended by up to **50%** but will not exceed **twice** the stated SLA window.

---

## 12. Service credits and remedies

### 12.1 Service credits for SLA breach

If Supplier fails to meet a stated response time in §2, the Railroad may claim a service credit:

| SLA missed by | Credit |
|---|---|
| 1–24 hours | 2% of annual platform fee |
| 1–5 days | 5% of annual platform fee |
| > 5 days | 10% of annual platform fee |

Credits accumulate quarterly and are applied to the next invoice. **Total credits in any 12-month period cannot exceed 15% of the annual platform fee.**

### 12.2 Limits on service credits

- Service credits are the **sole remedy** for SLA breaches; they do not permit fee withholding, termination for convenience, or damages claims.
- Service credits do not apply if the delay was caused by the Railroad (e.g., Railroad did not provide necessary diagnostic information, or did not authorize access to systems).
- Service credits do not apply during circumstances beyond reasonable control (force majeure per D07 §17.11).

### 12.3 No guarantee of uptime

While Supplier will use reasonable efforts to maintain continuous operation, **no uptime percentage is guaranteed.** The Platform is provided "as is" with no SLA guarantee of 99%, 99.9%, or any other percentage. The metrics dashboard is informational only.

---

*This SLA is a working document and will be reviewed annually with the Railroad. Material changes require joint amendment.*
