# AD-2, entry half — authenticated disposition entry

**Built 2026-11-11 (chat-6).** Commits `db569a4` and `83010d0`.
Suite 238 → 315. This record is internal: it belongs in `assets/`, not the
client docket.

## What the gap was

Chat-5 built the reviewer registry and HMAC attestations. A disposition could be
*bound* to a registered reviewer and the binding *verified* by a recipient of an
export. But `POST /api/warrant/<id>/disposition` still read `reviewer_name` and
`cert_id` out of the JSON body, so the name on a decision was whatever the caller
typed. B01 §7 item 1 carried this as the largest remaining code item: the claim
that a reviewer made a decision was verifiable but not **enforced at entry**.

## What was built

`backend/accounts.py` is new and does the entry half.

An **account** is bound at enrollment to a certification record already in the
reviewer registry, and enrollment is refused for a certificate the registry does
not have or has revoked. The account stores a **PBKDF2-HMAC-SHA256 verifier**
(600,000 iterations, 16-byte per-account salt) rather than a passphrase. A
**session** is a 32-byte bearer token of which only the SHA-256 digest is stored,
so a copy of the database yields no usable token.

`resolve_session` checks five things: the token was issued here, the session is
not revoked, it has not expired, the account is still live, and the **certificate
behind it is still live**. The fifth is the one that is expensive to omit — a
certificate revoked at 09:00 would otherwise keep authorising writes until the
TTL ran out, each attributed to a certificate that no longer exists.

The account register is append-only and hash-chained with the same trigger set as
the reviewer registry (`BEFORE UPDATE`, `BEFORE DELETE`, `BEFORE INSERT … WHEN
EXISTS` to refuse `OR REPLACE`). The hash **covers salt, iteration count and
verifier**: a host owner who could swap a verifier would own the account and every
session it issued, so a value the hash does not cover would be a value somebody
can change.

The route takes identity from the session and **nowhere else**. A body carrying
`reviewer_name` or `cert_id` is **refused, not ignored** — an integrator whose
field is silently dropped would ship code that names the wrong reviewer for a
year. With **no account enrolled the path is closed (503)**, not reopened to the
old free-text behaviour; the fallback would make the gate only as strong as
somebody remembering to enrol. `tools/seed_demo_account.py` is the deliberate act.

`store.save_disposition` grew a `guard` callable run inside its write
transaction. The certificate liveness re-check belongs there because the ledger's
write lock is the only instant at which "still live" and "still unwritten" are
both true — the same race that made `attest()` re-read under its lock in chat-5.

## The defect the audit found, and why the suite missed it

An independent agent was told to **falsify** the claim, not review the code. It
falsified the first half.

**The revocation guard was inert.** `save_disposition` called `guard()` and
**discarded the return value**, while the route installed
`lambda: accounts.cert_is_live(...)` — which *returns a boolean*. So the guard ran,
computed `False`, and the row was written anyway. A certificate revoked between
resolve and INSERT produced HTTP 200, a row, and a reviewer name under a
certificate that no longer existed.

The suite missed it because the test simulated the race with a guard that
**raised**. That is not the guard the route installs. The general lesson, and it
is the same shape as chat-3's vacuous ledger test and chat-4's ROI test rebuilt
from its own constants: **a guard whose only tested failure mode is one the
caller does not use is not a guard.** The fix aborts on a falsy return and the
route turns that into a 401. The new test revokes the certificate **inside**
`resolve_session` — the real race, through the real route — and reverting the fix
reproduces the exploit verbatim.

Two 500s from malformed bodies, both found by a hostile-shape sweep:
`{"note": {…}}` raised `AttributeError` on `.strip()`, and
`{"disposition": ["x"]}` raised `TypeError` because `list in dict` hashes the key.

## What held under attack

No credential path produced a write: absent header, bare token, `Basic`, the
token replaced by its own digest, expired, signed out, account revoked. A token
for reviewer A could not record a decision as B, and nine alternative body field
names (`username`, `reviewer`, `name`, `account`, `cert`, `who`, `identity`,
`reviewed_by`, `user`) changed nothing. Duplicate JSON keys could not smuggle
identity. `grep` confirms exactly one call path reaches `store.save_disposition`;
`ingest`, `ledger_export` and `ledger_replication` only read the ledger.

## What this does not claim

Stated in the module docstring and the docket, not buried:

- It does not prove a **human** was at the keyboard. It proves a credential was
  presented. Key custody and joiner/mover/leaver are a procedure, not a function.
- It does not protect the **token in transit**. The demo host is plain HTTP
  (B01 §7 item 10); a bearer token there is a shared secret on the wire.
- It does not strengthen **attestation**. A signed-in session authorises a write;
  the attestation is still the reviewer's own HMAC key, which the server never
  holds. Passing the HMAC key as the login credential was rejected precisely
  because it would put the attestation secret on the server.
- A host owner with **database write access** can hand-insert a session row or
  rewrite an expiry. The design does not claim to survive that, and says so.
- Entry still requires a live **session**, not an **attestation**. An unattested
  row is an honest state, not an error.

## Still open after this build

Key custody and joiner/mover/leaver (a written procedure); a signed key directory
so a recipient knows which key belongs to whom; requiring an attestation as well
as a session at entry. D07 §14.5 venue remains a counsel decision and still
blocks first execution.
