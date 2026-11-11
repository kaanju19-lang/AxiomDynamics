# Chat-6 — Summary

**When:** 2026-11-11. **Commits:** `db569a4`, `83010d0`, `e31acd4`. **Suite:** 238 → 315 tests.

---

## What was accomplished

**AD-2 entry half — authenticated disposition entry.** The reviewer registry and HMAC attestations existed (from chat-5); a disposition could be *bound* to a registered key and the binding *verified*. But `POST /api/warrant/<id>/disposition` read `reviewer_name` and `cert_id` directly from the JSON body, so the name on a decision was whatever the caller typed — unverified at entry and the largest remaining code item in B01 §7 item 1.

This gap is now **closed at the code level.** `backend/accounts.py` is new and implements the entry half:

- An **account** is bound at enrollment to a certification record already in the registry.
- Enrollment is refused for a certificate the registry does not have or has revoked.
- An account stores a **PBKDF2-HMAC-SHA256 verifier** (600,000 iterations, 16-byte salt) rather than a passphrase.
- A **session** is a 32-byte bearer token; only the SHA-256 digest is stored, so a database copy yields no usable token.
- `resolve_session` checks five things: issued here, not revoked, not expired, account still live, **certificate still live** (the expensive one to omit — a revoked certificate would otherwise keep authorising writes until the TTL ran out).
- The account register is append-only and hash-chained with the same trigger set as the reviewer registry.
- The route takes identity from the session and **nowhere else**. A body carrying `reviewer_name` or `cert_id` is **refused, not ignored** — silent dropping would ship code that names the wrong reviewer.
- With **no account enrolled the path is closed (503)**, not reopened to free-text behaviour.

**The audit found an inert guard,** and why the suite missed it:

`save_disposition` called `guard()` and **discarded the return value**, while the route installed `lambda: accounts.cert_is_live(...)` — which *returns a boolean*. The guard ran, computed `False`, and the row was written anyway. A certificate revoked between resolve and INSERT produced HTTP 200.

The suite missed it because the test simulated the race with a guard that **raised** — not the guard the route installs. **A guard whose only tested failure mode is one the caller does not use is not a guard.** This is the same shape as chat-3's vacuous ledger test and chat-4's ROI test. Fixed: the route now aborts on a falsy return (401 response). The new test revokes the certificate *inside* `resolve_session` through the real route and reverting the fix reproduces the exploit.

Two 500s from malformed bodies (hostile-shape sweep): `{"note": {…}}` raised `AttributeError` on `.strip()`, and `{"disposition": ["x"]}` raised `TypeError` on the hash key.

**What held under attack:** no credential path produced a write; a token for reviewer A could not record as B; nine alternative body field names changed nothing; duplicate JSON keys could not smuggle identity; exactly one call path reaches `store.save_disposition`.

**Updated documents:** B01 §7 item 1 now states entry is gated on an authenticated session. D09 §4.4, D09 §4.5, C01 §E2, F09 Part 7 all clarified with the same language. The distinction between *entry gating* (now closed) and *entry attestation requirement* (still open) is now explicit in every one.

---

## Still open after this build

From Part VI of D00:

1. **Key custody and joiner/mover/leaver** — a written procedure, not code.
2. **Signed key directory** — so a recipient knows which key belongs to whom without being told the name on the command line.
3. **Requiring an attestation at entry, not just a session** — entry proves a credential was presented, not that a person was at the keyboard.

From the largest gap (ingest):

4. **Ingest endpoint authentication** — currently unauthenticated, a data-poisoning route.
5. **Real payload schema** — the schema is still a demonstration schema; the Railroad's real payload is unspecified.

From supply-chain (tools built 2026-11-11, not applied):

6. **SBOM in releases** (Q1 2027 target).
7. **Hash pinning in dependencies** (Q1 2027 target).
8. **GPG-signed releases** (Q2 2027 target).

From counsel (not code):

9. **D07 §14.5 — governing law, seat and forum** — blocks first execution.

---

## Build records

- `assets/session-entry-build-2026-11-11.md` — full account of what was built and the defect.
- `assets/attribution-build-2026-11-11.md` — the adversarial audit from chat-5; one defect carried forward into chat-6.
- Chat-6 transcript at `project-logs/transcripts/` (will be extracted and committed at close).
- Build history regenerated and committed 2026-11-11 (Stage 10 added).

---

## Standing instructions for the next session

- **All project work is written directly into `C:\Users\RGV\AxiomDynamics`, first pass, and committed in the same pass.** No drafts in sandbox.
- **Verify against the file, then write.** Never cite from memory.
- **Independent adversarial audit** whenever both the artifact and its checker are authored by the same agent. Use a fresh agent instructed to *falsify*.
- **125K tokens per chat, starting from chat-6 onwards.** At the cap, alert and roll over.
- **Every build phase starts with a low→high priority ladder**, worked one item at a time.
- **Extract and commit the session transcript at close, raw `.jsonl` included**, snapshot taken *after* the last exchange.
- **Never `git checkout -- <file>`.** Use `/tmp` or the mutation driver's `--restore`.
- **Never `git add -A`.** Stage named files only; check with `--ignore-cr-at-eol`.

---

## What chat-7 should pick up

A proposed priority ladder (low → high, one at a time). This is a plan, not a
record — nothing below is done until it is committed to the repository.

**LOW:**
1. Confirm push status against `origin/main`, and regenerate the build-history
   `.docx` after any material change.

**MEDIUM:**
2. Add authentication to `POST /api/ingest` — gate on a valid session token
   resolved to an account (AD-2 dependency), the same pattern chat-6 applied to
   the disposition route.
3. Build a signed reviewer key directory — so a recipient can verify attribution
   without being told the name on the command line.

**HIGH:**
4. Apply the supply-chain controls — wire SBOM / hash pinning / GPG signing into
   the release process, then move them from "built" to "applied" in D09 §4.4.
5. Mutation-test the ingest guard — same shape as the account guard found inert
   in chat-6 (break it, confirm red, restore).

**Out of scope for code:** D07 §14.5 (counsel decision) and Phase 0 formation
(LLC, EIN, insurance, bank).
