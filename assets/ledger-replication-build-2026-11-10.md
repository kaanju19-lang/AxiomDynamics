# Ledger replication — build record, 2026-11-10 (chat-4)

Internal account of the phase that produced `backend/ledger_replication.py`. Not
client-facing. The docket wording it justifies is in B01 §7 item 12, D09 §4.4 and
§4.5.4, and C01 §E2.

## What was built

The signed export (`backend/ledger_export.py`) produced **one** bundle when
asked. Nothing produced bundles *on a cadence*, which is the gap B01 §7 item 12
and D09 §4.4 had disclosed since `cf2e6ba`: a week nobody remembered to export
was a week with no evidence, and a lost disk lost the ledger no matter how well
past bundles were signed.

`backend/ledger_replication.py` executes the cadence D09 §4.5.4 already
specified — monthly full, weekly incremental, every bundle naming the previous
one's `signature_of()` as `previous_export_hash`, zero-record weeks kept, nothing
overwritten — and adds `inspect`, which verifies a series and reports gaps.

New tests: `tests/test_ledger_replication.py`, 32 cases. Full suite 80 → 112.

## The design decision that shaped everything: the air gap

D09 §3.2 promises the Platform has "no mechanism to send data to Supplier or any
external service", and B02 repeats that the supplier cannot reach the box. So
"off-box replication" cannot mean the box pushes bundles over a network without
contradicting a customer-facing promise to close a control gap.

The owner chose **on-box scheduling, physical carriage**: the Platform produces
and verifies the series; moving it to backup media stays the Railroad's step
under D09 §3.3. That is why the module has no network code at all and why both
docket rows now say *carriage* remains open rather than claiming replication is
done.

## What the two audits found, and why it matters

This phase was audited twice, and between them the audits found nine material
defects. The pattern is the one the project keeps meeting: **internally
consistent, externally wrong.**

**First audit (five material).**

1. The `no_regression` fix landed in `backend/ledger_export.py` but not in
   `tools/verify_ledger_export.py` — the tool D09 §4.5.4 tells the Railroad to
   run quarterly. That verifier rejected every legitimate chained full export.
   The in-repo fix passing its own test proved nothing about the contract's own
   verification tool.
2. `inspect()` never opened a bundle. It compared filenames and recorded digests,
   so a record edited inside a signed bundle came back "series is continuous".
   The tool meant to expose tampering could not see it.
3. `inspect()` could not see a missing cadence period.
4. A lost `series.json` silently restarted the series, while the docstring
   promised a refusal. The test asserted the silent restart under a name claiming
   the opposite.
5. Concurrent `produce()` calls stranded signed bundles the state never recorded,
   because `write_state` used a fixed `.tmp` name.

**Second audit (four more, after the first round of fixes).**

6. `_missing_periods` **hung forever**: the week increment rolled over at
   `w == 53` but never emitted 53, so a 53-week ISO year (2026 is one) followed by
   W01 looped indefinitely. A quarterly tool that never returns.
7. The same walker could not see a deleted **latest** month, because it walked
   `min..max` of the recorded periods and a deleted last period shrinks the range.
8. `due_exports` read the state **outside** the lock, so concurrent `run_due`
   calls all produced the same periods — duplicate bundles the cadence says must
   not exist. The concurrency test called `produce` (which is locked) and so
   proved the wrong thing.
9. `test_the_standalone_verifier_accepts_a_chained_full_export` was **vacuous**:
   `assert "no_regression" not in stdout.replace("PASS  no_regression", "")`
   passes when the check is deleted entirely. The `.replace` was backwards.

Nine defects, and a green suite of 108 before any of them were found. The lesson
is unchanged and now has five sessions of evidence behind it: a suite written by
the author of a mechanism tests the author's model, not the mechanism.

## What the code does and does not prove

**Does:** the series is produced on the documented cadence; every bundle chains
to its predecessor; a zero-record week is kept and does not rewind the id cursor;
nothing is overwritten; concurrent runs neither duplicate nor orphan; a lost
state refuses rather than restarts; `inspect` opens every bundle, recomputes its
digest, verifies it against the predecessor, and reports missing periods.

**Does not:** move anything off the box (§3.2 forbids it, by design). Detect a
ledger wiped before the first bundle in a series. Name the signer or date a
bundle — both are AD-2. Verify the continuity of bundles that predate a
re-anchor: `--reanchor` rejoins the chain, and `inspect` keeps reporting the
weaker evidence, which is the point.

## Open after this phase

- **Off-box carriage** — the remaining half of B01 §7 item 12. No commercial
  decision and no new dependency; it is an operational step for the Railroad plus,
  arguably, a documented copy procedure.
- Signer attribution (`--reanchor` neighbour) remains an AD-2 dependency and is
  deliberately not started: it needs real local accounts with a key per reviewer.
- `run_due` is documented as safe to invoke repeatedly; it is now locked, but
  nothing prevents two *processes* both deciding the month is due within the same
  lock acquisition — the lock serialises them, so the second sees the first's
  write and does not duplicate. Confirmed at 12 concurrent threads. A multi-host
  deployment is out of scope (one box, §3.1).

## Commits

See `git log --oneline` for this phase's hashes. None is written here, because a
hash written into a document goes stale the moment the document is committed and
this project has been misled by that more than once.
