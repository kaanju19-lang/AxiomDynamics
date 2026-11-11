# Chat-7 — Summary

**When:** 2026-11-11. **Commits:** `826fabd`, `1b76ba7`, `1f25f9a`, `b829af4`, `2fa4bc4` (close).
**Suite:** 315 → 346 (plus 30 tests that initially never ran — see the defect).

Worked a five-item ladder top-down, low complexity to high, one at a time.

---

## 1. Confirmed state before touching anything

Chat-6's work (`db569a4`, `83010d0`, `e31acd4`) was **already pushed** —
`git reflog show origin/main` recorded `e31acd4` as an `update by push`. Only the
chat-7 open commit `b02196f` was outstanding. Suite green at 315.

## 2. Read the modules before gating them

Read `ingest.py` end to end (three gates, fail-closed, unknown fields refused)
and the accounts session layer (five checks in `resolve_session`, including the
certificate re-check that stops a revoked cert mid-session). Skipping this step
is what produced the bad citations and the drawn-as-built ingest path earlier in
the project.

## 3. Ingest authentication — collector credentials

The decision that shaped it: **reuse the reviewer account table or separate
credentials?** Separate. A reviewer is a person — session expires in hours, dies
with the certificate. A collector is scheduled software — runs for weeks, and
revoking one decommissioned detector should not break a running collector
mid-shift. One table for both would have shared the two lifecycles' fate, and
"is this the same credential?" would have had no clean answer.

**The defect, found while building it.** The first HTTP handler authenticated
**after** reading and parsing the body, and the malformed-JSON branch logged the
body on the way in. An anonymous caller could therefore write rows to the ingest
log by POSTing `<<<not json>>>` — the write predated the check. The gate now runs
before the body is read at all, with a test that posts garbage with no token and
asserts the log holds zero rows. Same shape as chat-6's inert guard: the control
existed, it was in the wrong place relative to what it protected.

## 4. Signed reviewer key directory

Makes the key-to-name binding portable. Carries no key material — a key_id is a
truncated digest. Signed with the export key. Because that signature is
**symmetric**, the load-bearing check is *consistency, not the signature*: one
key_id names exactly one reviewer for its whole life, and a directory the
attacker forges and re-signs themselves is still refused, which is exactly the
test `test_one_key_cannot_name_two_reviewers_even_when_resigned`.

A control caught a test: `attribution`'s UPDATE trigger refused the first attempt
to tamper the registry in `test_a_broken_registry_refuses_to_build`, so the test
had to attack by forged append instead. Worth recording — the registry is
append-only in fact, not just in intent.

## 5. Mutation testing

`assets/mutation-ingest-auth.py` — 18 mutations, **14 killed, 4 survived**. The
four survivors (M2, M3, M5, M9) are test gaps, not code defects: the guards are
present, they are simply not exercised in the way the mutation disables them.
Each is written up in the carry-forward with the exact test to add.

---

## The defect in this chat's own bookkeeping

`test_ingest_auth.py` and `test_key_directory.py` were first written **without
the house `@test` decorator and `main()`**. The runner imports each module and
calls `main()`; these had none, so it printed the section header and **ran zero
tests**, while the aggregate total rose from 326 to 340 on tests that never
executed. Two commit messages quoted those inflated numbers.

It was caught by reading the per-file PASS counts, not by the exit status — the
suite said `340 passed, 0 failed`. Both files were rewritten in the house
pattern; they now run 15 + 15 and the corrected total is 346.

**The rule this adds:** a new test file is verified by its own per-file PASS
count, never by the suite total moving. This is the same family as the vacuous
ledger test, the self-referential ROI test and the inert guard — a green number
that means less than it appears to.

---

## Close-out audit

A pass over the whole repo before rolling over found the build itself sound and
the **documentation of it stale**. Five docket documents still told the client the
ingest endpoint had no authentication: B02 §2, D00 (twice) and B03's status
block. All now describe the collector credential and the gate-before-body-read.
B01's item-1 closing paragraph said the signed key directory *kept the item open*,
contradicting the same row's last column, which records it as built — fixed.

B01 and C01 declined an HTTP export route on the grounds that the server had "no
authentication". That was true when written and is now imprecise rather than
false: reviewer sessions and collector tokens exist, but neither is an
administrator principal, and a full ledger export should not go to either. Both
now say that instead, and the conclusion — no export route — is unchanged.

The two `assets/` build records were **annotated as historical, not rewritten**.
They are evidence of what was true when written; editing them would destroy that.
The defect in each got a strikethrough and a note naming the fix.

Verified at close: 346 tests green, every module counted by the runner, both
previously-silent test files reporting their own 15, mutation baseline still
18 / 14 killed / 4 alive, tree clean, transcript an exact prefix of the live log.

---

## What chat-8 picks up

Fix the four mutation survivors, then the independent adversarial audit of the
ingest and key-directory code, then apply the supply-chain controls.
