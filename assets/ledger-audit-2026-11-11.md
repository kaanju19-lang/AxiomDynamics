# Independent Audit — Ledger, Export and Replication, 2026-11-11 (chat-5)

**Docket position:** None. **Internal — not for customer distribution.**

**Companion documents:** `ledger-export-build-2026-11-09.md` (the original
build and its first audit), `ledger-replication-build-2026-11-10.md` (the series
and its two audits), B01 §4.5a and §7 item 8, D09 §4.4–4.5.

---

## 1. Why this audit happened, and why it was run this way

The chat-4 handoff named signer attribution as the next code item and described it
as "much larger than it looks." Before starting a large change to code three
audits had already blessed, the sensible move was to check whether the blessing
was deserved.

**The method matters as much as the result.** The agent was instructed to falsify,
not to confirm, and was given the list of already-known defects *and* the disclosed
limits so it would not spend its budget re-reporting things already written down.
It was told a clean report is only useful if it actually tried to break things.

That is now four audits of this subsystem in three sessions. **Every one found
material defects. The suite was green before every one of them.** That is the
finding underneath the findings, and it is the reason this document exists.

## 2. What was found — four defects, one critical

### Finding 1 (CRITICAL) — a rewritten history verified against a bundle you hold

`no_truncation` compared **ids only**. An attacker with file access and **no key**
could rewrite every record, recompute the chain and export honestly: the ledger
still ended at the same id, all 18 checks passed, and the recipient holding the
earlier bundle was told continuity was intact.

Reproduced end to end before the fix: three `flag` dispositions became `CLEARED`
and verification returned `ok: True`.

**Why it matters.** B01 §4.5a item 1 listed "that the ledger was never rewritten
before export" as something the series constrains. It did not. The sentence was
false, in a customer-facing document, about a control a railroad buyer would
reasonably rely on. That is the worst category of defect this project produces:
not a bug in code, but a document asserting a guarantee the code does not provide.

**Fix.** `history_continues` requires bundle N+1 to carry the record bundle N ended
at, hashing to the same value. `no_row_deletion` catches a count that fell while
the head id stayed put. Both in `backend/ledger_export.py` and the standalone
verifier, which must agree.

**Scope of the fix, stated honestly in B01.** It checks **one anchor record**. A
party who rewrites records the held bundle did not end at, and leaves that record
intact, is not caught. The exposure is narrowed, not eliminated. A proper Merkle
accumulator root would close it and is the same work as AD-2 — so it is recorded
with AD-2 rather than pretending to be done.

### Finding 2 (HIGH) — a mid-chain deletion was invisible to the whole series

Delete a middle row, relink the chain. Head id unchanged, so `no_truncation`
passes; row count one lower, but nothing compared counts. `inspect` returned
`ok: True`, and the standalone verifier exited 0.

**Fix.** `no_row_deletion` compares `ledger_rows` against the previous bundle.

### Finding 3 (HIGH) — `INSERT OR REPLACE` defeated the append-only triggers

`INSERT OR REPLACE` resolves a conflict by deleting the existing row and inserting
a new one, and **the implicit delete does not fire a DELETE trigger**. Both guards
missed it. Every row of a live ledger was rewritten to a different disposition
with both triggers installed and `verify_chain()` reporting `ok`.

**This is the defect that most deserves to be remembered**, because the module
docstring says *"the Python layer is not the guarantee; the schema is."* The schema
was not the guarantee. The claim was one level of abstraction too confident.

**Fix.** A `BEFORE INSERT` trigger with `WHEN EXISTS (... WHERE id = NEW.id)`
refuses the insert before conflict resolution can happen.

**Also noted:** the triggers are DDL created by `init_db()`, not part of the table
definition, so a `.db` restored by any path that does not run `init_db()` has none
until one does. `main.py` re-runs the DDL on start, which covers the application
path but not an operator restoring a file and inspecting it directly. **Left as a
disclosed characteristic rather than changed**, because moving triggers into the
schema changes the migration shape and that needs its own audit.

### Finding 4 (MEDIUM) — duplicate JSON keys: two readers, one file, different records

`json.load` keeps the **last** duplicate key. A bundle carrying
`"disposition": "CLEARED"` and then `"disposition": "FLAGGED"` is read one way by
the verifier and the other by a first-key-wins viewer — same bytes, no check fails.

Same class as the `bundle_no_extras` defect found at chat-4's close: the parser,
not the schema, decided what the bundle meant.

**Fix.** Both CLIs load through an `object_pairs_hook` that refuses duplicate keys.

## 3. Lower-severity findings — recorded, not fixed

- **`--to-id` produces a bundle that cannot verify.** The slice must end at the
  ledger head, so `--to-id` on a longer ledger can never satisfy
  `backend_head_consistent`. The option is offered and broken. **Not fixed**:
  either it is intended and the check is wrong, or it is not intended and the
  option should go. That is a design question, and guessing would repeat the
  mistake of changing a thing without knowing why it was built.
- **Normative manifest fields are not type-checked**, so a string `from_id` raises
  `TypeError` instead of producing a named failure — contrary to the stated promise
  that a malformed bundle yields named failures, never a traceback. **Not fixed**:
  a proper fix is a schema pass over the manifest, which is a larger change than a
  cast, and the audit could not show it being exploited.
- **`ledger_replication.inspect` takes no lock and bundles are written with
  `open(...,'w')`**, so a concurrent reader could see a truncated file. The window
  is real but was not reproduced inside the audit's time budget. **Recorded as
  suspected, not as confirmed** — the distinction is the point.
- **`produce()` called directly twice in one week** creates duplicate periods;
  the cadence is only enforced through `run_due`.

## 4. Tests that could not fail

Mutation-tested by the auditor, and this is the fourth session running that an
audit found one.

| Test | Mutation applied | Result |
|---|---|---|
| `test_inspect_notices_a_record_edited_inside_a_written_bundle` | digest check → `if False:` | **114 passed** — does not guard what its name says |
| `test_inspect_notices_a_missing_cadence_period` | `verify_bundle` disabled | **114 passed** |
| `test_count_inflated_in_manifest_is_detected` | `record_count` check deleted | **passed** — caught by `signature` instead |

By contrast, disabling `genesis_anchor` and `no_truncation` did fail tests. Those
guards were real.

**These three tests were not fixed in this pass.** They are recorded here so the
next session does not mistake a green run for coverage of those three behaviours.
Fixing them means deciding what `inspect` is actually contracted to detect, which
is a design question about the D09 §4.5.4 cadence, not a one-line change.

## 5. What could not be broken

Worth recording, because it bounds how bad this can get:

- **Canonicalisation is sound for the obvious cases.** `1`/`1.0`/`True`/`"1"` all
  hash differently; NFC ≠ NFD; NaN round-trips.
- **The key is never in the bundle** — only `key_id`, by design.
- **Signature comparison uses `hmac.compare_digest`**, so no timing leak.
- **Re-signing under a second key fails under the first.**
- **The standalone verifier imports only** `argparse`, `hashlib`, `hmac`, `json`,
  `sys`, and runs from an empty directory under `-I`.
- **Concurrency of `save_disposition` across six processes** produced 240 rows and
  a clean chain.
- **Reordering bundles, state tampering and a truncated file were all detected.**

## 6. Verification of the fixes

- Suite **114 → 119**, all green. Five tests added: rewritten history caught
  in-repo, same attack caught standalone, mid-deletion caught by row count,
  duplicate key refused by both CLIs, `INSERT OR REPLACE` refused by the schema.
- **Each new guard mutation-tested individually**: neutering `history_continues`,
  `no_row_deletion`, or the `no_replace` trigger turns exactly the intended test
  red and nothing else. Two tests needed tightening first — one could pass because
  a different check fired, and one was masked by the anchor check. **A test that
  passes when its own guard is removed is not a test**, and both were that.
- The fix files confirmed byte-identical to their pre-mutation state afterwards.
- The end-to-end attack re-run after the fix: `ok = False`, `failed =
  ['history_continues']`, with the specific record and both hashes named.

## 7. The lesson this pass adds

**Three audits had already passed this code, and the third found the worst defect
of the three.** "Audited" is not a state a subsystem reaches; it is something that
has to be re-done when the shape of the threat is revisited. The two earlier audits
were competent — they found nine defects between them — and both asked "does this
bundle verify correctly?" The question this one asked was **"can I make a
dishonest ledger verify correctly?"**, and it is a different question.

The second lesson is narrower and more actionable: **when a document promises a
control, the test for that control has to be written against the promise, not
against the implementation.** B01 §4.5a item 1 said a rewrite between exports is
detectable. No test asserted that sentence. Three tests asserted things *near* it.

## 8. Still open after this pass

1. **The three tests in §4** that pass for the wrong reason.
2. **The lower-severity items in §3**, each with the reason it was not fixed.
3. **The one-record scope of `history_continues`** — a Merkle root closes it, and
   that is AD-2 work.
4. **Triggers as DDL rather than schema** — a restored file has none until
   `init_db()` runs.
5. **`inspect` has no lock and bundles are not written atomically** — suspected
   only, not reproduced.

---

*Internal. Reviewed when the export format changes or when a new audit supersedes
this one.*
