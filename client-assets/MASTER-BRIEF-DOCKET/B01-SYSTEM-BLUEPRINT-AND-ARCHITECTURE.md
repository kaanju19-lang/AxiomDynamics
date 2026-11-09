# B01 — System Blueprint & Architecture

**Docket position:** B01. Descriptive annex to D07. B-series documents create no warranty unless D07 expressly incorporates them (Docket Index, Part IV, rule 5).

**Written against:** the production architecture, not the demonstration build. §7 lists every point where the two currently differ. Nothing in this document should be treated as describing the demo.

**Governing architectural decisions:**

- **AD-1 — Deployment: fully on-premise edge, zero outbound network.** No licence server, no telemetry, no update callback, no third-party cloud. The platform never initiates a network connection to anything outside the Railroad's network. Ever.
- **AD-2 — Reviewer identity: local accounts plus a signed certification registry**, administered by the Railroad. No dependency on Railroad directory services, no cloud identity provider.
- **AD-3 — The disposition ledger is append-only.** A disposition can be superseded but never overwritten, and never deleted.

AD-1 and AD-2 were chosen specifically so the platform remains deployable on an air-gapped network. Both have costs, stated in §8.

---

## 1. Purpose and boundary

The platform ingests wayside sensor signals from the Railroad's existing detector infrastructure, applies deterministic physics models to derive bearing and running-gear condition, and presents ranked advisory warrants to a certified reviewer who records a disposition.

**The platform does not decide anything.** It does not issue stop orders, does not communicate with train crews, does not influence signal systems, and does not actuate any equipment. It produces advisories for a qualified human being, who retains sole operating authority. This framing is deliberate and must be identical in B01, C02, D02, D07, D08 and D12. See D00 §III.1.

**In scope:** sensor ingestion, physics inference, warrant generation and ranking, reviewer disposition recording, audit export, ROI reporting.

**Out of scope:** detector hardware, network infrastructure, train control, crew communication, regulatory reporting to FRA/TC/ARTF on the Railroad's behalf.

## 2. Component inventory

| Component | Function | Technology |
|---|---|---|
| Signal ingest | Accepts wayside detector payloads in a defined schema | Python, file/socket ingest |
| Physics engine | Thermo, kinematic, acoustic models; deterministic, no learned parameters | Python + numpy |
| Warrant builder | Converts model output into ranked, cited advisories | Python |
| Identity & certification | **Local accounts, admin-issued credentials — operational today.** Signed certification registry: **designed, not built** (§7 item 1) | Python + SQLite |
| Disposition ledger | Record of reviewer decisions. **Append-only is the design; the current write path overwrites** (§7 item 2) | SQLite, WAL mode |
| API layer | Read APIs for fleet/alerts/ROI; write API for disposition | Python stdlib HTTP server |
| Presentation | Single-page dashboard, no external assets | HTML/CSS/JS, served locally |
| Audit export | Timestamped export with content hashes. **Not cryptographically signed** (§7 item 8) | Python |

**Total external dependency count: one** (numpy). Everything else is Python standard library. This is an architectural property, not an accident, and it is the platform's principal security argument — see B04.

## 3. Data flow

```
Wayside detector (HBD / WILD / ABD)
        │  sensor payload
        ▼
┌──────────────────────────────────────────────┐
│  RAILROAD EDGE BOX  —  no outbound network   │
│                                              │
│  ingest ──► physics engine ──► warrant       │
│              (deterministic)     builder     │
│                                    │         │
│                                    ▼         │
│                            reviewer queue    │
│                                    │         │
│                        [certified human]     │
│                                    │         │
│                                    ▼         │
│                        disposition ledger    │
│                         (append-only, WAL)   │
│                                    │         │
│                                    ▼         │
│                          audit export        │
└──────────────────────────────────────────────┘
        │
        ▼
Railroad's own reporting / regulatory process
```

**There is no line leaving the box.** That is AD-1 stated as a diagram.

## 4. The disposition ledger

The single most important component, because it is the artifact our regulatory argument rests on.

**Requirements (production):**

1. **Append-only.** Each disposition is a new row. Supersede-and-insert, never `UPDATE`. The current demo uses an upsert that silently overwrites — that is a defect against AD-3, not a design choice.
2. **Authenticated identity.** A disposition is only accepted from an authenticated session bound to an issued, unexpired, unrevoked certification record. Free-text name and cert ID are not acceptable in production.
3. **Immutable timestamps**, server-generated, not client-supplied.
4. **Retention** per the Railroad's records policy, specified in D09.
5. **Export** produces a signed bundle: partition boundary, record count, and a hash over the contents, so a regulator can verify nothing was removed.
6. **Hash chaining** (recommended, not required at v1): each record carries the hash of its predecessor, making retroactive alteration detectable.

**Why this matters commercially:** the Canadian pitch rests on producing auditable evidence that a flagged bearing was reviewed and acted upon. A ledger that can be silently rewritten produces no such evidence. Until the ledger meets §4.1–4.3, the certification story in C02 cannot be told, and the demo must not describe it as certification.

## 5. Failure modes

| Failure | Behavior | Consequence |
|---|---|---|
| Detector feed stops | Platform flags data staleness; advisories marked stale | No false reassurance — staleness is surfaced, not hidden |
| Physics engine error | Request fails, logged; no advisory emitted | Fails closed on that unit, not silently degraded |
| Edge box loses power | SQLite WAL recovers committed dispositions | Committed audit records survive |
| Disk full | Ingest rejects; dashboard alarms | Fails visibly |
| Clock drift | Timestamps become unreliable | **Requires NTP against Railroad's own time source — see §7** |
| Cert registry unavailable | New dispositions rejected | Fails closed — no unauthenticated decisions |

**Fails closed everywhere.** Where the choice exists, the platform refuses to act rather than acting unverified.

## 6. Scale envelope

Per edge box, designed for: one to six detector feeds, up to ~5,000 monitored axles, sub-second inference per unit, disposition volume in the low hundreds per day. Beyond that, additional boxes — which is exactly what the per-site platform fee in D08/A2 prices.

## 7. Production decisions required — where the code differs today

**This section is the honest gap list. It must be emptied before any contract cites B01.**

| # | Item | Current state | Required for production |
|---|---|---|---|
| 1 | Reviewer authentication | Free-text name + cert ID, unverified | AD-2: local accounts + signed cert registry |
| 2 | Ledger append-only | `INSERT ... ON CONFLICT DO UPDATE` — overwrites | Append-only with supersede semantics |
| 3 | Timestamps | SQLite `datetime('now')` default | Server-generated with NTP-synced clock |
| 4 | Storage durability | The demonstration environment's storage is ephemeral — the demo database is lost on spin-down | Persistent volume on Railroad hardware |
| 5 | Sensor ingest | Synthetic traces generated from physics equations | Real detector payload schema, defined and versioned |
| 6 | Time source | Host clock, unsynchronized | NTP to Railroad-approved source |
| 7 | Update mechanism | None; deploys via git | Offline signed update packages, see D06 |
| 8 | Audit export | Not implemented | Signed export bundle per §4.5 |
| 9 | Repo hygiene | `axiom.db` and `__pycache__` were committed | Corrected; `.gitignore` added |
| 10 | TLS on the box | Plain HTTP | TLS or network isolation; Railroad's internal standard |

Items 1, 2 and 5 are **blocking** — the certification and detection claims cannot be made until they close. Items 3, 4, 6, 7 and 8 are required before a production licence, not before a demo. Items 9 and 10 are corrected or Railway-specific.

## 8. Costs of the architectural choices

Stated plainly, because the Railroad's IT team will find them anyway and it is better that we said it first.

**AD-1 (zero outbound) costs us:** no remote diagnostics — every support case needs the Railroad to export logs and send them; no usage telemetry, so our own product analytics are blind; updates must be shipped as signed offline packages and applied by Railroad staff (C01); licence enforcement must be offline (see D08/A2 — enforcement is contractual and cryptographic, not online).

**AD-2 (local accounts) costs the Railroad:** a second credential set alongside their directory, an admin who must issue and revoke certifications, and a joiner/mover/leaver process integration that is manual. In exchange, the platform has no path to their directory and cannot be used to pivot into it.

**These are the correct trade. A platform selling to a Class I railroad should be inspectable, offline, and boring.**

---

*Descriptive annex. Creates no warranty. Every item in §7 must be closed and re-verified against the running system before B01 is cited in an executed agreement.*
