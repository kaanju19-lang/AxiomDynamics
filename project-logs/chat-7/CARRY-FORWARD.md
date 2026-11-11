# Chat-7 — Carry-Forward

**State at rollover:** HEAD `b829af4`. Suite **346 passed, 0 failed**. 4 commits
unpushed. Chat-7 built the two remaining AD-2 halves (ingest gating and the
signed key directory) and a mutation driver that found four gaps in its own
test coverage.

---

## Read in this order

1. `project-logs/CURRENT-STATE.md`
2. This file
3. `project-logs/chat-7/SUMMARY.md`
4. `assets/ingest-auth-build-2026-11-11.md` and `assets/key-directory-build-2026-11-11.md`

---

## What chat-7 built, in order

**1. Collector credentials — `backend/ingest_auth.py`.** `POST /api/ingest` had
no authentication; anyone reaching the port could append rows to the ingest log.
Collectors now get a credential deliberately **separate** from reviewer accounts:
a collector is scheduled software, not a person. Enrollment is by name with no
certification binding, the token is 32 random bytes returned once (only the
SHA-256 digest is stored), it has **no TTL**, and revoking an enrollment does not
invalidate tokens already issued — it stops new ones, which is what an operator
actually wants. The register is append-only and hash-chained with UPDATE/DELETE
triggers.

**2. The ingest gate — `backend/main.py`.** The credential is checked **before
the body is read**. The first draft authenticated after parsing and still logged
unparseable bodies, so an anonymous caller could write to the ingest log by
POSTing garbage — the write predated the check. This is chat-6's inert-guard
lesson in a different costume: the control existed, it was in the wrong place
relative to the thing it protected. Missing/dead token → 401; nothing enrolled →
503. A test posts garbage with no token and asserts the log stays empty.

**3. Signed reviewer key directory — `backend/key_directory.py`.** The HMAC over
an attestation does not cover the reviewer name, so a recipient had to be told
which key belonged to whom, by hand, on the command line. The directory publishes
the bindings as a signed document carrying **no key material** (a key_id is a
truncated digest). `tools/verify_key_directory.py` is the recipient-side
verifier and imports nothing from `backend/`. Because the signature is
**symmetric**, the load-bearing check is *consistency*, not the signature: one
key_id may name exactly one reviewer for its whole life, and a directory forged
and re-signed by the attacker is still refused.

**4. Mutation driver — `assets/mutation-ingest-auth.py`.** 18 mutations against
the ingest gate and the directory: **14 killed, 4 survived.**

---

## The four surviving mutations — fix these first in chat-8

A surviving mutation means a guard can be deleted and the suite stays green.
These are **test gaps, not code defects** — the guards are in the code, they are
simply not covered.

| # | Mutation | What is missing |
|---|---|---|
| M2 | Missing-token check removed from `do_POST` | No test sends a request with **no** Authorization header to a deployment that *has* a collector enrolled. (The 503 test runs before enrollment; the 401 test sends a bad token, not no token.) |
| M3 | `resolve_token` failure ignored in `do_POST` | No test drives `resolve_token` raising inside the handler. Add an unknown-token POST and assert 401 with the log empty. |
| M5 | `route_post_ingest_authenticated`'s re-resolution removed | Nothing calls the route **directly** with a bad/missing header. The re-check exists so a direct call cannot bypass the gate; add a test that calls the route function with `headers={}` and expects 401. |
| M9 | `entry_hash` comparison removed in `verify_chain` | `test_the_chain_catches_a_forged_append` trips the **prev_hash** check (M10), not the hash check. Add a row whose `prev_hash` is correct but `entry_hash` is wrong. |

**How to verify a fix:** re-run `python3 assets/mutation-ingest-auth.py`; it
exits 0 only when every mutation is killed. If a run is cut off mid-mutation the
tree may be left modified — `python3 assets/mutation-ingest-auth.py --restore`
puts the pristine copies back from `/tmp/mutation-ingest-snapshot`. **Never
`git checkout --` to recover** — that has destroyed uncommitted work here.

---

## A defect in this chat's own bookkeeping, for the audit to keep in mind

Two test files (`test_ingest_auth.py`, `test_key_directory.py`) were first
written without the house `@test` decorator and `main()`. The runner imports
modules and looks for `main()`, found none, and printed the section header with
**zero tests under it** — while the aggregate total rose. The suite went green
on tests that never ran. It was caught by reading the per-file output, not by
the exit status. Both files are now in the house pattern and both run (15 + 15).
**Any future test file must be checked by its own per-file PASS count, not by
the suite total moving.**

---

## Still open after chat-7

**AD-2 (B01 §7 item 1):**
- Key custody and joiner/mover/leaver — a written procedure, not code.
- Attestation at entry — entry requires a live session, not an attestation.
- Export/certificate identity is still symmetric HMAC (item 11): the directory
  proves the export-key holder authored the bindings, not that they were entitled to.

**Ingest (B01 §7 item 5):**
- The real payload schema is still a demonstration schema.

**Supply chain (B01 §7 item 7):** SBOM, hash pinning, GPG signing are **built,
not applied** — Q1–Q2 2027 targets.

**Counsel:** D07 §14.5 governing law/seat/forum blocks first execution.

---

## Standing instructions, unchanged

- All project work written **directly into `C:\Users\RGV\AxiomDynamics`**, first
  pass, committed in the same pass. No drafts in the sandbox.
- **Verify against the file, then write.** Never cite from memory.
- **125K tokens per chat.** At the cap, alert and roll over.
- **Every build phase opens with a low→high priority ladder**, worked one item at a time.
- **Independent adversarial audit** whenever I author both the artifact and its
  checker. Fresh agent, told to *falsify*.
- **Never `git add -A`.** Stage named files; check with `--ignore-cr-at-eol`.
- **Never `git checkout -- <file>`.** Use `/tmp` or the mutation driver's `--restore`.
- Extract and commit the transcript at close, raw `.jsonl` included, snapshot
  taken *after* the last exchange.

## Push required

4 commits unpushed (`826fabd`, `1b76ba7`, `1f25f9a`, `b829af4`) plus the chat-7
close commits. Run `PUSH-TO-GITHUB.bat`. The sandbox cannot reach GitHub —
`git push` and `git fetch` both fail HTTP 403 from the proxy.
