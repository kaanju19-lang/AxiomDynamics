# Chat-13 — phase record

**2026-11-13.** Rung 4 of the ladder: the cross-document sweep — the one class
chat-12 named as untested and deliberately did not attempt.

Rolled over at the token cap before the independent audit rung could run. That
is recorded as an open item, not as done.

---

## What the sweep was for

Both serious document defects this project has found were a document
contradicting **another document**, never the code:

- chat-11, D10: called numpy "optional" while B04 and `requirements.txt` made it
  the only dependency.
- chat-12, D09: cited D07 §15.5 for an obligation §15.5 does not contain.

The code was right both times. The pair was wrong. Nothing tested the pair.

## The claim classes checked

Five classes were compared across the 37 docket documents. Three came back
clean and are recorded so a future chat does not re-sweep them:

| Class | Result |
|---|---|
| Section cross-references (`D07 §15.5` resolves to a real heading) | **clean** — 0 unresolved across 36 documents, now guarded by `tools/check_cross_refs.py` and 9 tests |
| Insurance limits (D03 §9 vs D07 §10.1 vs D00) | **clean** — $1,000,000 / $2,000,000 aggregate CGL, $2,000,000 Technology E&O in both; D07 §10.1 explains why the $5M figure was retired |
| Pricing (A2 rate card vs the derived totals quoted elsewhere) | **clean** — $370,000 pilot, $300,000 Band-1, $2,175,000 at 5,000 axles all reconcile |
| Capability state: ingest authentication | **defect — see 1** |
| Capability state: administrator authority | **two defects — see 2 and 3** |

---

## Defect 1 — B02 §2 contradicted itself four lines apart

`B02-FLOW-MAP.md` §2 opened with a block stating that a collector credential was
built 2026-11-11 — enrolled by name, bearer token, checked before the body is
read. Four lines below, the "Current state, stated plainly" paragraph listed the
three open items, and the second read:

> **authentication** on the endpoint does not exist, so it is safe only on a
> trusted segment until AD-2 lands

This is chat-7's defect recurring in the same document that chat-12 repaired for
a different sentence. B02 §9 was corrected (commit `d79827b`) to say ingest is
built; §2's status paragraph was left asserting the opposite. **The same
document, two sections, opposite claims.**

Corrected to state collector authentication as built, with the honest limit
retained: a collector credential establishes that a token was presented, not who
is behind it.

## Defect 2 — D09 §4.2 promised "exportable by an Admin"

The Audit logging row read: logs "are exportable by an Admin." No administrator
principal exists. `B01 §4.5a` states it in so many words — "the server has no
**administrator** credential — reviewer sessions and collector tokens exist, but
neither is the right principal to hand a full ledger export to." C01 §507
repeats it.

So D09 §4.2 promised an action to a role the blueprint says does not exist, and
the row's own status column said "Partial" without mentioning it. This is
precisely the "procedure naming a step nobody can perform" shape the project has
hit twice before.

Corrected: export is an operator action on the box, not over HTTP, and the
sentence now says why.

## Defect 3 — D09 §4.2 called role enforcement "Implemented per role model"

The Authorization row read:

> Role-based access (Operator, Reviewer, Administrator) per C02. Enforced by the
> Platform. | Implemented per role model

The `accounts` table in `backend/accounts.py` has no role column — the columns
are `id, username, reviewer_name, cert_id, key_id, salt, iterations, verifier,
created_at, revoked_at, note, prev_hash, entry_hash`. Nothing in `backend/`
branches on Operator, Reviewer or Administrator. The disposition path admits any
live session.

C02's role framework is a **certification and competency** document — its own
§3.1 assesses each role by examination, which is organisational. D09 turned that
into a software claim. The Platform does enforce *authentication* and does check
that an account's certification is still live; it does not enforce a role.

Corrected to say exactly that, and to name the residual as outstanding under B01
§7 item 1.

---

## A fourth defect — in the guard I wrote during this chat

`tools/check_cross_refs.py` was written, run, and returned **0 unresolved across
36 documents**. It was then mutation-tested: two dangling references injected
into a copy of the docket, and the tool still returned 0.

The cause: `resolves()` compared section numbers with `cited.startswith(h)`, so
`14.7` "resolved" against a heading numbered `1`, and `99.9` against `9`.

Rewritten to compare segment by segment, with letter suffixes (`4.5a`) treated
as the same section. Now: 0 on the real docket, 2 on the injected copy, and both
directions are pinned by tests.

**This is the same defect chat-12's audit found three of, in the same chat that
was carrying the lesson forward.** The lesson was written down and did not
prevent it; only running the mutation did. Worth believing: writing a guard is
not the same act as testing one.

---

## Also in this chat

- **Chat-12's four commits were re-verified against their own messages**, because
  chat-12's headline lesson was that a commit message is a claim and can be
  false. All four check out, including the one they disclosed as unrepairable
  (`70077a8`'s message says 29 iterations; both benchmark JSONs say 25,
  confirmed).
- **Chat-12's close was never committed.** Five close artifacts — the
  `CURRENT-STATE.md` edit, the phase record, the carry-forward, the summary and
  both transcript files — were still untracked, and a stale `.git/index.lock`
  from that session blocked staging. Committed as `9c67de1`; a stray `oo.txt`
  (one pasted table row, referenced by nothing) was deleted rather than
  committed.

---

## Suite

**402 → 411.** Nine new tests in `tests/test_cross_refs.py`, all reaching.

The first version of that file was written as a `unittest.TestCase` class.
`tests/run_tests.py` collects module-level `test_*` functions, so the class file
imported cleanly, contributed **zero** tests, and the suite total printed 402 —
unchanged. Caught before commit; rewritten as plain functions. That is
[[axiomdynamics-silent-test-file]] recurring, and the only reason it was caught
is that the number did not move when it should have.

---

## Master % Tracker at chat-13's close

Re-derived from the files. Rubric unchanged:
`assets/master-tracker-rubric-2026-11-13.md`.

| Bucket | Weight | Chat-12 close | Chat-13 close | Δ |
|---|---|---|---|---|
| Docket documents (37) | 40 | 40.0 | 40.0 | — |
| B01 §7 gap rows (12) | 30 | 16.0 | 16.0 | — |
| Core software (8) | 20 | 20.0 | 20.0 | — |
| Release readiness (5) | 10 | 2.4 | 2.4 | — |
| **Total** | **100** | **78.4** | **78.4** | **—** |

**Zero movement for the third chat running, and this is now the third chat to
say so.** Three false claims were corrected across two documents and the matrix
did not record it, because the docket bucket scores documents *existing*. The
caveat chat-12 recorded is no longer a caveat — it is the demonstrated behaviour
of the measure across three consecutive chats.

That is the case for the re-base, and it is now stronger than the argument for
leaving it alone. **Disclosed here, not acted on here**, per the rule chat-10 was
caught breaking: a chat must not change the denominator it is scoring against.

---

## Open, and what chat-14 should do first

1. **The independent adversarial audit did not run.** The rung was in the ladder
   and the budget ran out first. Three document repairs and a rewritten guard are
   exactly the work that audit has found defects in twice. **Chat-14 opens with
   it**, before anything else, against commits from this chat.
2. **The dashboard has never been seen.** Five chats. Owner action.
3. **`gnupg` / `dirmngr`** — unchanged, owner decision, blocks the asymmetric build.
4. **The rubric re-base** — now disclosed twice. Chat-14 should propose the
   basis; chat-15 applies it.
5. Remaining claim classes not swept: capability state for the SBOM, hash
   pinning and release signing across B01/D09/D10/D00 (three documents describe
   three tools in three states, and that is the next most likely place for a pair
   to disagree).
6. Blocked externally: Railroad payload schema, release host and GPG custody,
   D07 §14.5 counsel.
