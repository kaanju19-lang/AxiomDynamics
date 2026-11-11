# Ingest authentication — collector credentials (2026-11-11, chat-7)

**What was open.** B01 §7 item 5's second half: `POST /api/ingest` had no
authentication. The CARRY-FORWARD put it plainly — *an unauthenticated ingest
route is a data-poisoning route.* Anyone who could reach the port could append
rows to the ingest log and, in principle, feed the physics engine.

**The decision that shaped the build.** The obvious shortcut was to reuse the
reviewer account table: chat-6 had just built session authentication for
dispositions, and a bearer token is a bearer token. It is the wrong shape, and
the reason is the domain. A reviewer is a person: their session expires in
hours, and the session dies if the certificate behind it is revoked, because a
reviewer who left should stop recording decisions immediately. A collector is
scheduled software on a wayside detector. It runs for weeks, nobody signed it
in, and revoking an enrollment because one detector was decommissioned should
not be able to break a running collector mid-shift without an operator deciding
to. One credential table for both would have made the two lifecycles share fate,
and an auditor asking "is this the same credential?" would have got "sort of."

So collectors get their own register, in `backend/ingest_auth.py`:

- enrollment is by name, with no certification binding;
- the token is 32 random bytes, returned once, of which only the SHA-256 digest
  is stored, so a database copy yields no usable token;
- **no TTL**, and revoking an enrollment does not invalidate tokens already
  issued — it stops new ones, which is the operation an operator actually wants;
- the register is append-only and hash-chained, with `BEFORE UPDATE` and
  `BEFORE DELETE` triggers, so an enrollment or a revocation cannot be edited
  out of history.

**The defect found while building it, and it was mine.** The first version of
the HTTP handler authenticated *after* reading and parsing the body, and it
logged unparseable bodies on the way in — that logging predated this build. The
combination meant an **anonymous caller could write rows to the ingest log just
by POSTing garbage**: send `<<<not json>>>`, the auth check is still downstream,
the malformed-JSON branch fires, a row lands. Adding authentication without
moving that branch would have left a write path open to anyone. The gate now
runs **before the body is read at all**, and there is a test that posts garbage
with no token and asserts the ingest log still holds zero rows. This is the same
shape as chat-6's inert guard: the control existed, it was simply in the wrong
place relative to the thing it was meant to protect.

**What is tested.** `tests/test_ingest_auth.py` covers enrollment, resolution,
revocation (including that a revoked enrollment's issued token still resolves —
deliberate, and asserted rather than assumed), idempotent revocation, the
auth-mode transition, chain verification, duplicate-name refusal, unknown-token
refusal, and the property that the plaintext token never appears in the database
file. `tests/test_ingest.py` gains an HTTP test that proves a missing token, a
wrong token and an untokened garbage body are all refused and write nothing,
and that a deployment with no collector is closed with 503. Suite 315 → 326.

**What this does not do.** It does not make the ingest schema the Railroad's —
the demonstration schema remains, and that is the other half of B01 §7 item 5.
It does not protect the token in transit (TLS is item 10). It does not prove the
machine is the machine it claims to be; possession of the token is the whole
credential. And key custody for these collector tokens is a written procedure
that does not exist yet, the same open item the reviewer keys carry.

## Files

- `backend/ingest_auth.py` — new: collector enrollment, tokens, revocation,
  auth mode, chain verification.
- `backend/main.py` — `POST /api/ingest` authenticates before reading; the
  route function re-resolves the token so a direct call cannot bypass the gate.
- `tools/seed_demo_collector.py` — new: the deliberate act that opens the path.
- `tests/test_ingest_auth.py` — new: 10 tests.
- `tests/test_ingest.py` — HTTP tests updated for the credential and extended
  with the unauthenticated-write test.
- `client-assets/MASTER-BRIEF-DOCKET/B01-SYSTEM-BLUEPRINT-AND-ARCHITECTURE.md`
  §7 item 5, and `D09` §4.3 — the authentication and data-validation rows,
  corrected (D09's authentication row still said accounts were not bound to the
  registry, which chat-6 had already fixed).
