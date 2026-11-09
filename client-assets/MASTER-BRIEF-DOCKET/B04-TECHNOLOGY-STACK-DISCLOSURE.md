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
| HTTP server + routing | `backend/main.py` | 418 | Python |
| Physics engine | `backend/physics.py` | 500 | Python + numpy |
| Fleet simulation | `backend/simulate.py` | 299 | Python + numpy |
| Return-on-investment model | `backend/roi.py` | 190 | Python |
| Disposition persistence | `backend/store.py` | 79 | Python + sqlite3 |
| Warrant construction | `backend/warrants.py` | 157 | Python |
| Dashboard logic | `frontend/app.js` | 448 | Vanilla JavaScript |
| Dashboard styling | `frontend/style.css` | 538 | CSS |
| Dashboard markup | `frontend/index.html` | 66 | HTML |
| **Total** | | **2,695** | |

**No frontend framework, no build step, no bundler, no npm.** The browser loads `index.html`, which loads `style.css` and `app.js` from the same box. There is no transpilation, no minification pipeline, and no package manager in the frontend path.

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
| Dependency pinning | `numpy>=1.26` — **a floor, not a lock**. Production should pin exactly and vendor the wheel. |
| Hash verification | Not currently performed. Production should use `--require-hashes`. |
| SBOM | **Not produced.** A CycloneDX or SPDX SBOM should accompany every release (see D06). |
| Signed artifacts | Not currently signed. Required for offline updates (D06, C01). |
| Reproducible build | Not verified. |

**These four gaps are real and I am naming them rather than leaving them to be discovered.** None blocks a demonstration. All four block a production deployment into a Class I railroad, because their security review will ask for the SBOM and the signing chain and "we'll get to it" is not an answer.

## 8. Open-source licence obligations

BSD-3-Clause (numpy) and PSF-2.0 (Python) impose **no copyleft obligations**. There is no requirement to publish our source, no licence-compatibility conflict with commercial licensing, and no attribution burden beyond preserving the licence text in distributions — which should be included in every shipped artifact as a NOTICE file.

**Nothing in this stack prevents AxiomDynamics from licensing the platform commercially while keeping its source proprietary.** That matters for D07 (IP ownership) and for the escrow arrangement contemplated in D00 §III.11.

---

*Verified against repository contents at time of writing. Any change to dependency inventory must be reflected here and in D10 before the next release.*
