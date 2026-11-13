# Attestation at entry — build record (chat-9, 2026-11-13)

**What closed:** B01 §7 item 1's last software half. A disposition row cannot
exist without an attestation from a live, correctly-bound reviewer key.
Suite **359 → 370**.

---

## 1. The constraint that decided the design

The obvious shape — "the client sends an attestation, the server checks it" —
cannot be built. Three facts, each verified in the source rather than assumed:

- The registry stores `key_id`, the first sixteen hex of the key's SHA-256.
  **The key itself is never stored** (`backend/attribution.py`, `key_id()` and
  the `reviewer_keys` schema).
- An attestation is `HMAC(key, "axiom-attestation/v1:" + record_hash)`
  (`attestation_value`).
- `record_hash` covers `recorded_at`, `prev_hash` and `supersedes_id`, none of
  which exist until the row is built inside the write transaction.

So a client cannot compute an attestation for a row it has not created, and the
server cannot verify one without the key bytes. Either the key is presented, or
the attestation is a server-side assertion with no new information.

**Decision: the key is presented per request** in `X-Reviewer-Key`, base64, and
the attestation is computed and written **inside the ledger's own transaction**.

The alternative — make the reviewer key the login credential — was rejected on a
property, not a preference. It would put the attestation secret on the server for
the life of every session and every backup of the session store, so a stolen
session could forge attestations. That is exactly what the attestation exists to
deny. Recorded in D09 §8.4.2a, because it is the question a security reviewer
will ask first.

---

## 2. What was built

`backend/main.py`

- `_reviewer_key(headers)` parses `X-Reviewer-Key`, base64, returning `b""` for
  absent or malformed — a half-parsed credential becomes "no credential", never
  a partial identity.
- `route_post_disposition` refuses (401) when no key is present, then calls
  `attribution.resolve_live_key` for the four checks the operator can act on:
  unregistered, wrong reviewer, wrong certificate, revoked.
- The successful response now carries `attestation: {key_id, value}`.

`backend/attribution.py`

- `resolve_live_key(db_path, key, reviewer_name, cert_id)` — the early check.
- `stamp_attestation(conn, row, key)` — the in-transaction check and write. Takes
  the caller's connection so the attestation commits or rolls back with the row.

`backend/store.py`

- `save_disposition(..., attest=None)` calls `attest(conn, rec)` **after INSERT,
  before COMMIT**. `store` does not import `attribution`; the route supplies the
  callable. The ledger stays the lower module.

`tools/seed_demo_account.py`

- `--key-file` writes the generated key mode 0600 instead of discarding it.

---

## 3. Two defects this exposed, both mine

**The demo became unusable.** The seeder generated the reviewer key and threw it
away — correct before this change, fatal after it. An operator could seed, sign
in, and then have every write refused, because the only copy of the key no longer
existed. This is the same defect the AD-2 custody procedure exposed in chat-8: a
procedure naming a step nobody can perform. Fixed with `--key-file`, and the
no-flag path now prints an explicit warning that no disposition can be recorded.

**Three assertions were too loose to fail.** Mutation testing killed M19 only
after the assertion was tightened, and M2 (route pre-check) survived twice:

| Mutation | Why it survived | Fix |
|---|---|---|
| Route's early key check removed | `"reviewer key" in error` matched the *unregistered-key* message too | assert `"reviewer key required"` |
| Route's `resolve_live_key` removed | the inner guard names both reviewers, so asserting both names matched | assert the phrase unique to the route: `"a reviewer signs decisions with their own key"` |
| M22–M24 (inner reviewer / revocation / certificate checks) | every route test was refused by the *early* check, so the inner layer was never reached | three direct `save_disposition` tests that bypass the route |

The last row is the structural lesson. **Two layers of the same check cannot both
be tested through the outer layer.** The early check is wanted for a clean 401
without opening a write transaction; the inner one is wanted because it holds the
write lock. Each needs a test that reaches it.

---

## 4. Mutation results — all six killed, each by exactly one test

Driver extended to 24 mutations across five targets.

| # | Mutation | Result |
|---|---|---|
| M19 | entry stops requiring a reviewer key | KILL |
| M20 | route stops pre-verifying the key | KILL |
| M21 | `save_disposition` ignores the attest callback | 5 tests red |
| M22 | `stamp_attestation` stops checking the reviewer | KILL, one test |
| M23 | `stamp_attestation` stops checking revocation | KILL, one test |
| M24 | `stamp_attestation` stops checking the certificate | KILL, one test |

Anchors verified: all 24 replacement strings match their target file exactly once,
so none is a silent no-op.

---

## 5. Verified end-to-end, not just unit-tested

```
seed_demo_account --key-file → key written (0600)
route_post_session           → 200, token
route_post_disposition + key → 200, attested_by 9f87f9c7596698ce
verify_attestations          → ok: True
verify_chain                 → ok: True
route_post_disposition w/o key → 401 "reviewer key required"
```

---

## 6. What this still does not claim

- **A credential holder is not a person.** The key proves which registered
  identity attested, not who was at the keyboard. Item 1 stays open on that.
- **The transport is not protected.** B01 §7 item 10; plain HTTP on the demo host
  means the key and the token are both on the wire.
- **The server holds the key in memory per request.** A host owner reading
  process memory during a write can capture it — same exposure class as D09
  §8.4.8.
- **The export signature is still symmetric.** Attestation is about a row; it does
  not name the export signer (B01 §7 item 11).
