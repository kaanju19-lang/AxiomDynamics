# D10 — Subprocessor & Third-Party Component Register

**Docket position:** D10. The register of every third party that touches Railroad data or ships inside the Platform.

**Classification:** Client-facing. Provided to the Customer's security review and maintained per release.

> **Why this document exists:** D02 §11, D07 §3.4, D13 §8 and B04 §7 all incorporate it by reference. A contract that incorporates a register that does not exist is a dangling obligation — and the first security auditor who asks to see it will discover the gap. This closes it.

---

## Part 1 — Subprocessors: none

**AxiomDynamics uses no subprocessors to process Railroad Data.**

There is no cloud hosting, no analytics vendor, no outsourced data processing, no third-party support desk, and no managed service provider with access to any deployment.

This is not a policy choice that could change quietly — it is a consequence of the architecture. Under AD-1 (B01), the Platform is fully on-premise and makes zero outbound network connections (B05, verified against code). Data that never leaves the Customer's network has no path to a subprocessor.

**Current subprocessor count: zero.**

| Subprocessor | Purpose | Data accessed | Location | Status |
|---|---|---|---|---|
| — | — | — | — | None |

### If a subprocessor is ever added

Per D09 §7.1:

1. **30 days' advance written notice** to affected Customers.
2. The subprocessor is bound by confidentiality and security obligations **no less stringent than D09**.
3. The Customer **may object** within 30 days.
4. If the objection is unresolved, the Customer **may terminate the affected order without penalty**.

**Any change to this register is a contract-level event, not an administrative update.** It triggers notice under D09 §7.1 and appears in the release notes.

---

## Part 2 — Third-party runtime components

The complete inventory of third-party code that executes as part of the Platform. **One component.**

| Component | Version | Licence | Purpose | Source | Shipped as |
|---|---|---|---|---|---|
| **numpy** | per `requirements.txt` | **BSD-3-Clause** | Numerical array operations for the physics computations | PyPI | Python wheel |

**No component in this inventory:**

- Requires disclosure of AxiomDynamics source code
- Restricts the licensing model in D07 §3.1
- Imposes copyleft obligations on the Platform
- Transmits data anywhere

**Warranty (D07 §3.4, D13):** the Platform contains no component whose licence would require disclosure of AxiomDynamics' source code or restrict the licensing model, on any basis. Any change to this inventory that would affect that warranty is disclosed **before release**, not after.

---

## Part 3 — Standard-library-only components

The Platform is written to run with minimal external dependencies. Everything below is part of the Python standard library and carries the PSF licence that ships with the interpreter. **These are not third-party components in any commercial sense** — they are part of the runtime the Customer installs — but they are listed for completeness because a security reviewer will ask.

| Area | Standard library modules |
|---|---|
| HTTP server | `http.server`, `socketserver` |
| Database | `sqlite3` |
| Data formats | `json`, `csv`, `datetime` |
| System | `os`, `sys`, `pathlib`, `argparse`, `logging`, `signal` |
| Hashing | `hashlib` |

**Deliberately absent:** any HTTP client library, any telemetry or analytics SDK, any cloud SDK, any auto-update mechanism. Their absence is the structural guarantee behind the air-gap claim in B05.

---

## Part 4 — Development and build-time dependencies

**Not shipped to the Customer.** Listed for supply-chain transparency (D09 §4.3).

| Tool | Purpose | Licence | Ships to Customer? |
|---|---|---|---|
| Python 3.11+ | Runtime interpreter | PSF | Customer installs separately |
| `pip` | Package installation | MIT | Customer's own |
| `pytest` *(optional)* | Test framework where available | MIT | No — `tests/run_tests.py` is dependency-free by design |
| Git | Version control | GPL-2.0 | No |

> **Note on the test runner.** `tests/run_tests.py` exists precisely so that an air-gapped deployment with no pytest available can still run the full suite (C01 Part B §B4). A test framework you cannot install on the target machine is not a test framework.

---

## Part 5 — Known supply-chain gaps

Disclosed in D09 §4.4 and B01 §7. Restated here because this is the register a security reviewer will read alongside them.

| Gap | Risk | Target |
|---|---|---|
| **No SBOM artefact in releases** | Customer cannot independently verify the dependency chain | Q1 2027 |
| **No hash pinning of dependencies** | A compromised package index could serve substituted code | Q1 2027 |
| **No signed release artefacts** | A release archive could be replaced in transit | Q2 2027 |

**What mitigates these today:**

1. **One runtime dependency.** A supply-chain attack surface of one package is materially easier to assess than one of forty.
2. **No automatic update mechanism.** Nothing in the Platform fetches anything (B05).
3. **Air-gapped transfer.** Where the Customer uses the sealed-archive method (C01 Part B), the dependency set is transferred together with a SHA-256 manifest we generate, so the Customer verifies what they received against what we said we sent.
4. **Customer-controlled installation.** The Customer installs from source they have inspected. We never push anything into their environment.

**These mitigations reduce the risk; they do not eliminate it.** The gaps are real and are stated as gaps.

---

## Part 6 — Licences and compliance

| Licence | Component | Obligation on us | Obligation on the Customer |
|---|---|---|---|
| BSD-3-Clause | numpy | Retain copyright notice and licence text | None |
| PSF | Python standard library | Retain licence notice | None |

**No GPL, LGPL, AGPL, or other copyleft component ships in the Platform.** If one were ever introduced, it would be disclosed here and in the release notes before delivery, because a copyleft component in an on-premise deployment has consequences for the Customer that they are entitled to know about in advance.

---

## Part 7 — Verification procedure

A Customer security reviewer can verify this register independently:

1. **Inspect the installed dependencies:** `pip list` on the Platform host, or `pip freeze` against `requirements.txt`.
2. **Compare against Part 2.** Any package present that is not listed is a discrepancy — notify support and it is investigated within 30 days (D09 §10.2).
3. **Verify outbound isolation:** confirm the host makes no outbound connections (B05), by firewall rule or network capture.
4. **Confirm no subprocessors:** there is nothing to confirm beyond the architecture — with no outbound path, no third party can receive data.

**Discrepancy process:** reported discrepancies are investigated and remediated within thirty days, with the register corrected and the correction disclosed in the release notes (D09 §10.2).

---

## Part 8 — Maintenance

**This register is reviewed and reissued with every release.** A register that drifts from the shipped inventory is worse than no register, because it creates the appearance of verification without the substance.

| Version | Date | Change | Released with |
|---|---|---|---|
| 1.0 | ____________ | Initial register | Platform v______ |

**Next scheduled review:** with the next release.

---

*Register. Verified against repository contents at the date of issue. Any change to the dependency inventory must be reflected here and in B04 before the next release.*
