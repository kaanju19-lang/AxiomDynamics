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
| Disposition ledger | Record of reviewer decisions. **Append-only — built 2026-11-09** (§4.1, §4.6, §7 item 2) | SQLite, WAL mode; insert-only with guard triggers and SHA-256 chain |
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

1. **Append-only.** Each disposition is a new row. Supersede-and-insert, never `UPDATE`. **Built 2026-11-09:** the write path is insert-only, a correction carries a `supersedes_id` referencing the row it corrects, and database triggers `RAISE(ABORT)` on any `UPDATE` or `DELETE` against the table — so the guarantee is in the schema, not only in the application. Both the superseded and the superseding record survive with their own timestamps.
2. **Authenticated identity.** A disposition is only accepted from an authenticated session bound to an issued, unexpired, unrevoked certification record. Free-text name and cert ID are not acceptable in production. *Not built — AD-2, §7 item 1.*
3. **Immutable timestamps**, server-generated, not client-supplied. **Built:** `recorded_at` is written by the database at insert time and is covered by the row hash, so altering it breaks the chain.
4. **Retention** per the Railroad's records policy, specified in D09.
5. **Export** produces a signed bundle: partition boundary, record count, and a hash over the contents, so a regulator can verify nothing was removed. *Partly built:* the chain can be re-verified on demand and the result reported, but the exported bundle is not yet **signed**. See §7 item 6.
6. **Hash chaining.** Each record carries the hash of its predecessor, making retroactive alteration detectable. **Built 2026-11-09:** every row stores `prev_hash` (the previous row's hash, or 64 zeros for the first) and `record_hash`, a SHA-256 over its own content plus `prev_hash`. `store.verify_chain()` recomputes the whole chain and names the first row that fails.

**What the chain does and does not prove.** It detects a row edited in place (its own hash stops matching) and a row removed from the middle (the next row's `prev_hash` stops matching). It does **not** stop an attacker who has write access to the database file: such a party can drop the triggers, rewrite rows and recompute every hash. The chain is tamper-**evident**, not tamper-**proof**, and the difference is the reason off-box replication and signed export still matter (§7 items 6–7).

**Why this matters commercially:** the Canadian pitch rests on producing auditable evidence that a flagged bearing was reviewed and acted upon. A ledger that can be silently rewritten produces no such evidence. With §4.1, §4.3 and §4.6 now built, the ledger supports that claim at the level of *"the record cannot be silently altered by the application or by ordinary database access"* — it does not yet support *"the record is cryptographically signed and replicated off-box."* Do not overstate the second. The certification story in C02 still depends on §4.2.

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
| 2 | Ledger append-only | **Corrected 2026-11-09.** Insert-only write path; `supersedes_id` for corrections; `BEFORE UPDATE`/`BEFORE DELETE` triggers abort; SHA-256 chain across rows | Built — superseded decisions retained, chain verified on demand |
| 3 | Timestamps | SQLite `datetime('now')` default | Server-generated with NTP-synced clock |
| 4 | Storage durability | The demonstration environment's storage is ephemeral — the demo database is lost on spin-down | Persistent volume on Railroad hardware |
| 5 | Sensor ingest | **No inbound route exists.** Signals are generated from physics equations on synthetic traces; there is no endpoint, schema validation, timestamp check or plausibility filter in shipped code | Real detector payload schema, defined and versioned, **and the validation chain built and tested against it** |
| 6 | Time source | Host clock, unsynchronized | NTP to Railroad-approved source |
| 7 | Update mechanism | None; deploys via git | Offline signed update packages, see D06 |
| 8 | Audit export | Not implemented | Signed export bundle per §4.5; the re-verifiable chain now exists, the signature does not |
| 9 | Repo hygiene | `axiom.db` and `__pycache__` were committed | Corrected; `.gitignore` added |
| 10 | TLS on the box | Plain HTTP | TLS or network isolation; Railroad's internal standard |

Items 1 and 5 are **blocking** — the certification and detection claims cannot be made until they close. Items 3, 4, 6, 7 and 8 are required before a production licence, not before a demo. Items 2 and 9 are corrected. Item 10 is specific to the demonstration host and does not arise where the Platform runs on the Railroad's isolated network.

**Item 2, closed and what that changes.** The append-only guarantee is now enforced by the database, not by convention, and it is tested: a suite of 17 adversarial tests attempts an `UPDATE`, a `DELETE`, a second disposition, a tampered row and a removed row, and asserts each either fails or is detected. What remains open under items 3, 6 and 8 is the *provability* layer — a trusted clock and a signed, off-box export — not the append-only behaviour itself.

## 8. Costs of the architectural choices

Stated plainly, because the Railroad's IT team will find them anyway and it is better that we said it first.

**AD-1 (zero outbound) costs us:** no remote diagnostics — every support case needs the Railroad to export logs and send them; no usage telemetry, so our own product analytics are blind; updates must be shipped as signed offline packages and applied by Railroad staff (C01); licence enforcement must be offline (see D08/A2 — enforcement is contractual and cryptographic, not online).

**AD-2 (local accounts) costs the Railroad:** a second credential set alongside their directory, an admin who must issue and revoke certifications, and a joiner/mover/leaver process integration that is manual. In exchange, the platform has no path to their directory and cannot be used to pivot into it.

**These are the correct trade. A platform selling to a Class I railroad should be inspectable, offline, and boring.**

---

*Descriptive annex. Creates no warranty. Every item in §7 must be closed and re-verified against the running system before B01 is cited in an executed agreement.*
