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

**One Python distribution, and seven libraries inside it.** This part previously
said "the complete inventory … one component", which was wrong in a way that
mattered: the numpy binary wheel does not ship one library. It bundles OpenBLAS,
LAPACK, a GCC Fortran runtime (`libgfortran`), `libquadmath`, `lapack-lite`,
`dragon4` and `libdivide`. These execute inside the Platform's own process. A
register that stops at the package name tells a security reviewer that we ship
one thing when we ship eight, and the eight are what a dependency-substitution
attack would actually target.

| Component | Version | Licence | Purpose | Source | Shipped as |
|---|---|---|---|---|---|
| **numpy** | per `requirements.txt` | **BSD-3-Clause** | Numerical array operations for the physics computations | PyPI | Python wheel (platform-specific) |

Bundled inside the numpy wheel, and therefore inside the artefact we hand over:

| Bundled library | Licence | What it is |
|---|---|---|
| **OpenBLAS** | BSD-3-Clause | The BLAS/LAPACK implementation numpy links against |
| **LAPACK** | BSD-3-Clause-Attribution | Linear-algebra routines, compiled into the OpenBLAS build |
| **GCC Fortran runtime** (`libgfortran`) | **GPL-3.0 with the GCC Runtime Library Exception** | Fortran runtime the compiled BLAS needs; the Exception is what permits distribution inside a proprietary product |
| **`libquadmath`** | **LGPL-2.1-or-later** | GCC quad-precision maths library, linked by `libgfortran` |
| **`lapack-lite`** | BSD-3-Clause | numpy's fallback linear-algebra path |
| **`dragon4`** | MIT | Float-to-string conversion |
| **`libdivide`** | Zlib | Fast integer division |

**On the GPL and LGPL entries, because a reader will stop there.** Neither imposes
a copyleft obligation on the Platform. `libgfortran` is conveyed under GPL-3.0
*with the GCC Runtime Library Exception*, which exists specifically to permit
compiling and distributing proprietary software against the GCC runtime. The
`libquadmath` LGPL is satisfied by dynamic linking, which is how it is shipped.
The warranty at D07 §3.4 stands: no component requires disclosure of
AxiomDynamics source code or restricts the licensing model in D07 §3.1.

**These are disclosed from the installed wheel, not from its metadata page.**
`tools/sbom.py` reads `numpy.libs/` on the machine and records a SHA-256 for each
binary it finds, so this table can be regenerated rather than trusted. The
platform-specific wheel on the Railroad's target architecture may differ from the
one inspected here — that is what the SBOM is for.

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

## Part 5 — Supply-chain controls and what remains open

Disclosed in D09 §4.4 and B01 §7. Restated here because this is the register a
security reviewer will read alongside them.

**Three tools exist as of 2026-11-11. Two of them are complete; one needs the
release host to finish a step.** This part previously listed all three as gaps
with 2027 targets and stated nothing about them being built. The distinction
below is the one that matters: a tool that exists is not the same as a control
that is applied, and the row says which is which.

| Control | State | What it does, and what it does not |
|---|---|---|
| **SBOM** | **Built** — `tools/sbom.py` | Generates a CycloneDX 1.5 document from the *installed* tree: component, exact version, a SHA-256 over every installed file, and the bundled native libraries from Part 2. `verify` recomputes the tree digest on the Railroad's machine and fails on a substituted wheel, a changed version, a declared-but-absent component and an installed-but-undeclared one. **Scoped to a requirements file**: an unscoped run describes the build host, not the release, and the tool says so. |
| **Hash pinning** | **Built, not yet applied** — `tools/pin_requirements.py` | Pins each requirement to the digests the index actually served, so `pip install --require-hashes` refuses a substituted file under a matching version. **`requirements.txt` is still a range**, because the pin step needs index access and the build sandbox has none. The Dockerfile and the release path now pass `--require-hashes`, so an unpinned file **fails the build** rather than shipping with a flag that reads as a control and is not applied. The release host runs `--write` once and commits. |
| **Signed releases** | **Built** — `tools/sign_release.py` | Builds a deterministic, reproducible archive (gzip header mtime pinned, uid/gid normalised, one fixed mtime), writes the `MANIFEST.sha256` C01 Part C2 already expects, signs it with a detached GPG signature, and verifies against a supplied public key rather than a local trustdb. **No key is issued and no release has been signed as of 2026-11-13** — D09 §7.3 and B04 §7 both say so, and this row previously claimed the opposite. What exists is the tool: generate the key, write its custody procedure and publish the public half by a route the Railroad trusts. **The tool runs on the release host, not inside the shipped image**, which installs no `gnupg` (B04 §6) — so "Built" here means the signing path exists, not that the Platform can sign anything it ships. Once issued, the signature will prove authorship only to the extent the Railroad trusts the path the public key arrived by. That limit is in D09 §7.3. |

**Why pinning is not simply "applied".** Writing a hash nobody verified is worse
than writing none: `--require-hashes` then rejects every real download, and the
control fails at release time on the Railroad's machine. The pin step therefore
runs where the index is reachable, and the tool refuses to write a digest it did
not observe in the same run.

**What still mitigates the residual risk:**

1. **One runtime distribution.** A supply-chain attack surface of one package is
   materially easier to assess than one of forty — though Part 2 makes clear it
   is not one *library*.
2. **No automatic update mechanism.** Nothing in the Platform fetches anything (B05).
3. **Air-gapped transfer.** Where the Customer uses the sealed-archive method (C01 Part B), the dependency set is transferred together with a SHA-256 manifest we generate, so the Customer verifies what they received against what we said we sent — and since 2026-11-11 that manifest can be signed.
4. **Customer-controlled installation.** The Customer installs from source they have inspected. We never push anything into their environment.

**What remains genuinely open:** the release host must run the pin step and
commit the result; a GPG key must be generated, its custody procedure written and
its public half published by a route the Railroad trusts; and the SBOM must be
generated on the target architecture, not the build architecture, because the
numpy wheel is platform-specific. None of these is a code change.

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
