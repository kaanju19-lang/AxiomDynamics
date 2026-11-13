# The Master % Tracker, and the rubric that produces it

**Chat-11, 2026-11-13.** Rung 1 of the ladder.

---

## Why this file exists

The Master % Tracker has been reported at every phase open and close since
chat-9, as the owner instructed. Three of its four buckets have never had a
written rubric. The gap-row bucket was carried at **16.7** through chat-9's close
and chat-10's open and close without anything on disk that reproduces the number,
which means it could not be checked and would not be noticed if it drifted.

This file fixes that. It states the basis, scores every row against it, and
shows the arithmetic, so the next chat can **re-derive** the figure instead of
quoting a number out of a handoff.

## A correction to chat-11's own opening message

At the open of chat-11 I reported **16.4** for the gap-row bucket and **78.8**
total. I had not derived either — I adjusted chat-10's 16.7 by an impression and
wrote it down. Scoring the rows properly gives **16.0** and a total of **78.4**.

The error is small and the total barely moves, which is exactly why it needed
saying: the habit that produces a two-tenths error by impression is the same
habit that produced a 29x ROI error and a nine-defect audit in earlier chats.
**Derive, then write. If a number is in the message before it is in a table, the
order was wrong.**

---

## Basis — unchanged

| Bucket | Weight | What it counts |
|---|---|---|
| Docket documents | 40 | 37 docket IDs in D00 Part IV |
| B01 §7 gap rows | 30 | the 12 rows of B01 §7 |
| Core software | 20 | 8 named components |
| Release readiness | 10 | 5 named gates |
| **Total** | **100** | |

---

## Bucket 1 — Docket documents, 40.0 / 40

D00 Part IV is the authority. Read on 2026-11-13: **37 ID rows, all 37 carrying a
Built status** (34 as `**Built**`, B02 and B03 as `Built (.md)` / `Built (.html)`
with a format qualifier, A2 among the bold set). 37/37 → **40.0**.

This bucket cannot move. It measures documents existing, not documents being
correct.

## Bucket 2 — B01 §7 gap rows, 16.0 / 30

**The rubric.** Each of the 12 rows is scored 0–10 against one question: *how
much of the "Required for production" column exists?* The scale:

- **10** — the required state exists in the repository and is tested
- **7–9** — exists and is tested, with a named residual limit
- **4–6** — substantially built, the remaining part is blocked outside the repo
- **1–3** — the demo state is honest but the production state is untouched
- **0** — nothing

Each row carries `30 / 12 = 2.5` points at full score.

| # | Row | Score | Why |
|---|---|---|---|
| 1 | Reviewer authentication | 6 | Session-gated entry, attestation at entry, signed key directory, custody procedure written. Held below 7 because "a credential holder is not a person" is a limit code cannot lift, and the signature is symmetric |
| 2 | Ledger append-only | 10 | Insert-only, triggers abort update/delete, SHA-256 chain, `INSERT OR REPLACE` refused. Built and attacked |
| 3 | Timestamps | 3 | Still SQLite `datetime('now')`; NTP is a host-level production step |
| 4 | Storage durability | 2 | Demo storage still ephemeral; persistent volume is Railroad hardware |
| 5 | Sensor ingest | 6 | Three gates, collector auth, fail-closed. Held below 7 because the payload schema is a demonstration one and nothing downstream scores an accepted payload |
| 6 | Time source | 2 | Host clock, unsynchronised |
| 7 | Update mechanism | 5 | `sign_release.py` builds a reproducible signed archive and verifies it; no GPG key, no custody, requirements unpinned, so the Docker build fails by design |
| 8 | Audit export | 9 | Signed, independently verifiable, chained, truncation- and rewrite-detecting, 48 adversarial tests. Held off 10 by the trust-anchor item |
| 9 | Repo hygiene | 10 | `.gitignore` present, `axiom.db` and `__pycache__` not tracked |
| 10 | TLS on the box | 2 | Plain HTTP on the demo host |
| 11 | Export signing key provenance | 3 | Symmetric; any verifier can forge; names no signer |
| 12 | Off-box replication | 6 | The cadence is built and `inspect` verifies it; carriage is the Railroad's physical step and nothing has moved |

**Sum 64 / 120 = 53.3% → 16.0 points.**

Cross-check on the shape rather than the digits: rows 2, 8 and 9 are the built
ones and score 29 of the 64; the six rows scoring 3 or below are all host-level,
organisational or blocked-externally. That distribution is the same story the
repo tells everywhere else, which is weak evidence the scoring is at least not
invented.

## Bucket 3 — Core software, 20.0 / 20

The eight components, named so the count is checkable rather than asserted:
physics engine (`physics.py`), ROI model (`roi.py`), fleet simulation
(`simulate.py`), warrant/advisory flow (`warrants.py`), disposition API and
frontend (`main.py` + `frontend/`), append-only ledger (`store.py`),
account/session auth (`accounts.py`), attribution registry
(`attribution.py`). All eight exist and are tested. 8/8 → **20.0**.

**A caveat worth writing down:** this bucket is generous. Five further modules
(`ingest.py`, `ingest_auth.py`, `ledger_export.py`, `ledger_replication.py`,
`key_directory.py`) also exist and are not counted, because the eight were fixed
in an earlier chat and silently re-basing the denominator upward would look like
progress. If a future chat wants them counted, that is a re-base and must be
disclosed as one, the way chat-10 disclosed its own.

## Bucket 4 — Release readiness, 2.4 / 10

The five gates, likewise named: SBOM generated, dependency downloads
hash-pinned, releases GPG-signed, transport secured (TLS or network isolation),
deployed on Railroad hardware. **None of the five is applied.** The 2.4 is
credit for the tools existing behind two of them (SBOM 15 tests,
`sign_release` 10) — 12% of the bucket, or about 0.6 of 5 gates.

That is deliberately stingy. Chat-9 scored "tool built, not applied" more highly
and chat-10 re-based down and disclosed it. This keeps chat-10's reading.

---

## The matrix

| Bucket | Weight | Open | Close | Δ |
|---|---|---|---|---|
| Docket documents (37) | 40 | 40.0 | 40.0 | — |
| B01 §7 gap rows (12) | 30 | 16.0 | 16.0 | — |
| Core software (8) | 20 | 20.0 | 20.0 | — |
| Release readiness (5) | 10 | 2.4 | 2.4 | — |
| **Total** | **100** | **78.4** | **78.4** | **—** |

Against chat-10's close of 79.1, this is **−0.7 with nothing built in between**.
The movement is entirely my scoring of the gap rows: chat-10 carried 16.7
without a rubric, I re-derived 16.0 with one, and then corrected my own opening
figure of 16.4 to match. **A number that moves when nothing is built is a number
that was never derived.**

---

## What a future chat must do with this file

Do not quote 78.4. Re-score the 12 gap rows against the rubric above, at the
phase's open, and report what you get. If it differs from 78.4 and nothing was
built, the difference is the disagreement, and it is worth more than the number.
