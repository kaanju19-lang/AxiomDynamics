# B04 — Technology Stack Disclosure

**Docket position:** B04. Prepared for the Railroad's IT security review and open-source licence compliance. Pairs with B05 (data flow) and D10 (third-party component register).

**Verified against:** the repository as built. Every claim below was checked against the code, not asserted from memory.

**Headline: the platform has exactly one non-stdlib dependency.**

---

## 1. Runtime

| Component | Version | Licence | Notes |
|---|---|---|---|
| Python | 3.11.9 (pinned) | PSF License 2.0 | Permissive, no copyleft obligation |
| numpy | ≥1.26 | BSD-3-Clause | The only third-party runtime dependency |
| SQLite | Bundled with CPython (`sqlite3` module) | Public domain | No separate install, no licence obligation |
| OS base image | `python:3.11-slim` (Debian) | Debian Free Software Guidelines | Container base only |

**No web framework.** HTTP is served by `http.server` from the Python standard library. No FastAPI, Flask, Django, uvicorn, gunicorn, nginx, or reverse proxy. This is stated because it is unusual and the reviewer will ask why: **it exists to demonstrate that a predictive-maintenance platform does not require a software supply chain to operate.** Fewer components, fewer CVEs, fewer things to patch on an air-gapped box.

## 2. Application components

| Layer | File | Lines | Language |
|---|---|---:|---|
| HTTP server + routing | `backend/main.py` | 826 | Python |
| Physics engine | `backend/physics.py` | 500 | Python + numpy |
| Fleet simulation | `backend/simulate.py` | 299 | Python + numpy |
| Return-on-investment model | `backend/roi.py` | 222 | Python |
| Disposition persistence | `backend/store.py` | 461 | Python + sqlite3 |
| Account and session authentication | `backend/accounts.py` | 696 | Python |
| Reviewer attestation registry | `backend/attribution.py` | 639 | Python |
| Sensor ingest validation | `backend/ingest.py` | 381 | Python |
| Collector authentication | `backend/ingest_auth.py` | 368 | Python |
| Signed ledger export | `backend/ledger_export.py` | 955 | Python |
| Replication series | `backend/ledger_replication.py` | 810 | Python |
| Signed key directory | `backend/key_directory.py` | 227 | Python |
| Warrant construction | `backend/warrants.py` | 158 | Python |
| Dashboard logic | `frontend/app.js` | 595 | Vanilla JavaScript |
| Dashboard styling | `frontend/style.css` | 803 | CSS |
| Dashboard markup | `frontend/index.html` | 111 | HTML |
| Dashboard icon sprite | `frontend/icons.js` | 207 | Vanilla JavaScript |
| **Total** | | **8,258** | |

**Seven of these modules did not exist when this table was first written**, and
it did not change when they did. That is the defect this revision corrects: the
previous version listed nine files totalling 2,695 lines and described itself as
"verified against the repository as built, every claim checked against the
code." The gap was not arithmetic. A document whose job is to tell an IT
security reviewer what the stack contains was missing `ledger_export.py`,
`attribution.py`, `accounts.py`, `ingest.py`, `ingest_auth.py`,
`ledger_replication.py` and `key_directory.py` — the seven files that implement
the cryptographic and authentication surface a security review spends its time
on.

`tools/` is listed separately in §7 rather than folded into the total above,
because no tool ships inside the runtime image. It is 2,090 lines across ten
tools and it is what builds the SBOM, pins the dependencies and signs releases.

**No frontend framework, no build step, no bundler, no npm.** The browser loads `index.html`, which loads `style.css`, `icons.js` and `app.js` from the same box. There is no transpilation, no minification pipeline, and no package manager in the frontend path.

## 3. Third-party components — complete register

| Name | Version | Licence | Purpose | Data exposure |
|---|---|---|---|---|
| numpy | ≥1.26 | BSD-3-Clause | Numerical arrays, FFT for acoustic analysis | None — processes data in-memory locally |

That is the entire list. **Zero JavaScript dependencies. Zero CSS dependencies. Zero fonts, analytics, tag managers, or CDN references.**

## 4. Cryptographic dependencies (production)

The production architecture (B01 §4) requires hashing for the disposition ledger and signing for the certification registry. Both will use **`hashlib` and `hmac` from the Python standard library** — SHA-256 based. No third-party crypto library is planned, and no OpenSSL dependency beyond what CPython itself links.

If the ledgers are later hash-chained, the chain digest uses the same primitives. No additional component.

## 5. External network references

**None at runtime.** The application makes no outbound network connection of any kind — verified by inspecting every module for `urllib.request`, `http.client`, `socket`, and requests-style calls. The only `http://` strings in the codebase are **source citations in docstrings** for ROI figures (NTSB, DOJ, AP reporting), which are documentation and are never resolved.

The frontend references **no external URLs**. No CDN, no Google Fonts, no analytics beacon. A browser loading the dashboard contacts nothing but the local box.

> **This is the single most important statement in this document for the Railroad's security review.** It means the platform is compatible with a genuinely air-gapped network, not merely "deployable on-premise." See B05 for the full data-residency analysis.

## 6. Container and privilege posture

- Base image: `python:3.11-slim` — minimal Debian, no compiler or build tooling in the final image.
- **Runs as a non-root user** (`axiom`), created at build time, `/bin/false` shell.
- Container never requires root, never needs privileged mode, and mounts no host paths.
- Healthcheck uses only stdlib `urllib` against localhost.
- No OS-level packages installed beyond the base image and numpy.

## 7. Build and supply chain

| Concern | Current state |
|---|---|
| Dependency pinning | **Tool built, not applied.** `numpy>=1.26` is still a floor, not a lock. `tools/pin_requirements.py` performs the pinning on a host with index access and **refuses to write a hash it did not observe in the same run**, so a pin cannot be fabricated. The Docker build installs with `--require-hashes` and therefore **fails by design** until the pins are written. |
| Hash verification | **Tool built, not applied.** The Dockerfile already carries `--require-hashes`; what is missing is the pinned file, which needs a host with index access. |
| SBOM | **Tool built, not applied.** `tools/sbom.py` generates CycloneDX 1.5 JSON **from an installation rather than from `requirements.txt`** — an inventory of what pip resolved, not a shopping list of what was requested. 15 tests. No SBOM accompanies a release yet. |
| Signed artifacts | **Tool built, not applied.** `tools/sign_release.py` writes a deterministic archive plus `MANIFEST.sha256`, signs it with a detached GPG signature and verifies against a supplied public key. 10 tests. **No GPG key exists and none is under custody**, so nothing has been signed. |
| Reproducible build | **Tool built, not applied.** The archive writer is deterministic; reproducibility has not been demonstrated across two independent hosts. |

**The distinction this section now draws is three-state, and it matters more
than the status column.** A control can be *not built*, *built but not applied*,
or *applied*. All five supply-chain controls moved from the first state to the
second during this project, and none has moved to the third. **A tool that
exists is not a control that operates** — and a document that says "not
produced" when a generator exists is now as wrong as one that says "signed"
when nothing has been. D09 §4.4 carries the same three-state wording per
control.

**None of the five blocks a demonstration. All five block a production
deployment into a Class I railroad**, because their security review will ask
for the SBOM and the signing chain, and a generator on a developer's laptop is
not an answer to either. What blocks them is organisational — a release host
with index access, and a GPG key under written custody — not engineering.

## 8. Open-source licence obligations

BSD-3-Clause (numpy) and PSF-2.0 (Python) impose **no copyleft obligations**. There is no requirement to publish our source, no licence-compatibility conflict with commercial licensing, and no attribution burden beyond preserving the licence text in distributions — which should be included in every shipped artifact as a NOTICE file.

**Nothing in this stack prevents AxiomDynamics from licensing the platform commercially while keeping its source proprietary.** That matters for D07 (IP ownership) and for the escrow arrangement contemplated in D00 §III.11.

---

*Verified against repository contents at time of writing. Any change to dependency inventory must be reflected here and in D10 before the next release.*
