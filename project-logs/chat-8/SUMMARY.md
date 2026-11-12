# Chat-8 — Summary

**When:** 2026-11-11. **Commits:** `a4ccc0b` (survivors), `3de44cf` (custody
procedure), `1f1fce8` (record corrections), plus this close.
**Suite:** 346 → 351 → 359.

Worked a two-item ladder top-down: close chat-7's four mutation survivors
(known scope), then write the AD-2 custody procedure (open-ended). The second
item is where the chat earned its keep, because making the procedure's sentences
true required the code to change.

---

## 1. The four survivors, closed

M5 and M9 were the plain coverage gaps the carry-forward described. M3 needed a
case nothing had: a **garbage body plus an unknown token** — with the resolve
failure swallowed, that is the one shape where a row reaches the ingest log while
the status stays 401. **M2 was not the gap it was reported to be.** I first
declared it an equivalent mutant and was wrong; the auditor checked the error
text, which I had not. All four now have tests, and the driver reports
**18 mutations, 18 killed, 0 survived**.

## 2. Two defects in the driver itself

An independent audit ran after every mutation was green and found that the tool
certifying the tests was broken in two ways.

The first: an `EQUIVALENT` table I had added, keyed by mutation **index**. The
auditor put a genuine survivor into one of those slots and the driver printed
"equivalent" and exited **0**. It would have absorbed any real survivor that
landed there. Removed, with the survivor path now printing `ALIVE` and an
explicit prohibition on index-keyed exemptions.

The second: the pycache isolation was **inert**. The suite runs under `-I`, and
`-I` sets `sys.pycache_prefix` to `None`, which discards `PYTHONPYCACHEPREFIX`
entirely. Bytecode still reached the source tree. Now `-X pycache_prefix=…`,
which `-I` honours. Both directions verified rather than assumed.

Both are the same family as everything else this project keeps finding: a green
number that means less than it appears to.

## 3. The AD-2 custody procedure — D09 §8.4

B01 §7 item 1 had been open since chat-6 on "key custody and
joiner/mover/leaver — a written procedure, not code". It is now D09 §8.4, eight
subsections, beside §4.5 which already does the same job for the export key.

The design choice worth recording: **no new document and no new docket ID.**
D09 is the security addendum and already carries §4.5 for the export key and a
thin §8.1–8.3 on access control. A reviewer credential is the same class of
problem, so it belongs beside the one the docket already has.

## 4. Three defects the procedure exposed

None was found by a test. All three were found by trying to make a sentence in
the procedure true.

**A key could be registered to a second reviewer, and the second one won.** This
had been in the code since chat-6 and survived 346 tests and two adversarial
audits. `register` refused only a key revoked *anywhere* in its history; a
*live* key presented under a different reviewer was accepted. Since `attest`
resolves the newest registry entry for a `key_id` — deliberately, so a
certificate renewal works — the second reviewer took the key over and the
original holder was locked out of their own key. The register is append-only, so
the binding could never be removed. Now refused at the write. The narrowing
matters: my first fix also refused an ordinary renewal and would have broken
rotation to fix sharing. The rule is about the **reviewer** changing, not the
certificate.

**A refused key directory still handed back bindings.** `verify` returned
`ok=False` alongside `bindings={'<key>': 'Hoffman'}` for the very directory it had
just refused. Anything that checks `ok` late, or logs the bindings and carries
on, took a name from a failed document.

**The procedure named a step nobody could perform.** The only code that created a
reviewer key was `seed_demo_account.py`, which generates one and discards it —
correctly, but it means a demo can never attest. `tools/issue_reviewer_key.py`
is the missing joiner step, with 4 tests, including that a refused registration
leaves no key file behind.

## 5. What the stage does not claim

Item 1 is **not closed**, and B01 §7 item 1 now says so in its own words rather
than implying a document settles it. A credential holder is not a person, the
HMAC scheme is symmetric, a demo cannot attest, and every step except
certificate revocation is performed by a human. What changed is that the item is
now **auditable** under D09 §10.1.

## 6. Verification

Suite 346 → 351 → 359, re-run against HEAD at close: 359 passed, 0 failed.
Per-file counts checked individually — `test_ingest.py` 25, `test_ingest_auth.py`
18, `test_http_session.py` 9, `test_issue_reviewer_key.py` 4,
`test_attribution.py` 60, `test_key_directory.py` 17 — because the suite total
has lied before when a file silently ran zero tests. Both new guards are
mutation-tested in isolation. Every mechanism claim in §8.4 was executed: a
revoked certificate stopping a live session, a revoked account refusing
re-enrolment, `ledger_export.py keygen` writing 0600 and printing the `key_id`,
and the C01 command as written in the docket.
