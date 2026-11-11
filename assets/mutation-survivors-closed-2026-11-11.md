# Closing chat-7's four mutation survivors — 2026-11-11

Internal build record. Chat-8, phase one.

## What was asked

`project-logs/chat-7/CARRY-FORWARD.md` left four mutations alive — M2, M3, M5,
M9 — and described all four as **test gaps, not code defects**: the guards were
in the code and simply not covered. That description was three-quarters right.

## The four, and what closing them actually took

**M5 — route skips its token re-resolution.** A genuine gap. Nothing called
`route_post_ingest_authenticated` directly, so its own re-check could be deleted
without a test noticing. Now called directly with `headers={}` and with an
unknown token. The enrolment matters: on a deployment with no collector the
route answers **503** before it looks for a token, so a 401 there would prove
nothing about the token check. Two tests in `tests/test_ingest_auth.py`.

**M9 — chain hash check removed.** A genuine gap, and a subtler one than the
carry-forward said. The existing forged-append test trips the **prev_hash**
comparison (M10) and never reaches the entry_hash comparison. The new test
appends a row whose `prev_hash` is the real predecessor's hash and whose
`entry_hash` is wrong, so the only check that can catch it is the one M9
removes. It asserts `"hash mismatch" in message`, not merely `ok is False` —
a bare falsiness assertion would pass if the row tripped some other check.

After the fix, M9 and M10 each fail **exactly one distinct test**. Verified by
applying each mutation alone.

**M2 — missing-token check removed.** The carry-forward was wrong to call this
a test gap in the way it meant, and I initially replaced that error with a
different one. I first concluded it was an *equivalent mutant*: an empty token
flows into `resolve_token`, which raises `ValueError("no ingest token
presented")`, so the same 401 comes back and nothing is logged. Same status,
same row count — no observable difference, so no test could kill it.

An independent audit falsified that. The **error text differs**. The handler
says "send 'Authorization: Bearer <token>' from the collector enrollment"; the
route says only "authentication required". Both are 401, both log nothing, and
a test that checks only those two things cannot tell them apart. Asserting the
handler's wording makes M2 die.

The lesson is about where the observable lives. "Identical status code and
identical side effects" was treated as "identical behaviour", and the message
body — which is the only thing the caller reads — was never compared.

**M3 — resolve failure ignored.** A genuine gap, and the sharpest of the four.
The existing test already sent a garbage body with **no token** and asserted
nothing was logged. The missing case was a garbage body with an **unknown
token**. With M3 in place, `resolve_token`'s failure is swallowed, the garbage
is parsed, an unparseable-body row is written to the ingest log, and the
request is refused only afterwards by the route's re-check — so the status is
still 401 and **only the log row betrays it**. That is why a well-formed body
cannot find this mutation: a failed re-check refuses it before any write, in
every version of the code.

## Two defects in the driver, found after the mutations were green

**1. The pycache isolation did not work.** `run_tests` ran the suite with
`-I` and set `PYTHONPYCACHEPREFIX` in the environment. **`-I` sets
`sys.pycache_prefix` to `None` and discards the variable**, so the redirect was
inert and bytecode still went to the source tree's `__pycache__`. Verified
both halves rather than assuming: under `-I` the value is `None`, and the temp
cache directory stays empty. `-X pycache_prefix=...` is processed after `-I`
and does survive. The driver now uses `-X`.

On this mount that matters more than usual — `__pycache__` in the tree cannot
be deleted, and a `.pyc` can outlive the source it was compiled from.

**2. An `EQUIVALENT` exemption I added was dangerous.** Having decided M2 was
equivalent, I added a table keyed by mutation **index** that printed the
mutation as "equivalent, not a finding" and let the driver exit 0. The auditor
demonstrated the failure directly: replacing the index-2 entry with a genuine
survivor (the untested 64 KiB size cap) printed `EQUIV 2` and exited **0**.
Any real survivor landing in that slot would be silently absorbed, and the
build would be called clean.

Removed. A survivor now always prints `ALIVE` with instructions to decide by
reading the code. This is the same family as the vacuous ledger test, the
self-referential ROI test and the inert guard: **a mechanism that turns a red
result green without changing the thing under test.**

## Result

| | Before chat-8 | After |
|---|---|---|
| Mutations killed | 14 | **18** |
| Survived | 4 | **0** |
| Test suite | 346 | **351** |

Per-file, run individually: `test_ingest.py` 25, `test_ingest_auth.py` 18,
`test_http_session.py` 9. The suite total moved by 5, which matches
2 + 3 tests added — checked against the per-file counts, not the aggregate.

## Two smaller things found in passing

**Importing `backend.main` runs `store.init_db()`** against `store.DB_PATH`,
which defaults to the repository root. A test module that imports `main`
before pointing `AXIOM_DB_PATH` somewhere else creates an `axiom.db` in the
repo — and on this mount it then dies with `disk I/O error`, because the
filesystem is not one SQLite can lock. `tests/test_ingest_auth.py` now sets the
environment variable before any backend import. `tests/test_http_session.py`
already did. A stray `axiom.db` created during this work was deleted after the
sandbox delete permission was granted.

**`save_snapshot` trusted an existing `/tmp/mutation-ingest-snapshot`.** In a
fresh session that directory is a chat-7 leftover owned by another user, and
writing into it raised `PermissionError`. Worse than the inert case: if a
previous run died mid-mutation, the snapshot on disk holds the **mutated**
tree, and `--restore` would restore the defect. It now overwrites, and the path
is overridable with `AXIOM_MUTATION_SNAPSHOT`.

## Carry forward

The close-gate script `project-logs/close-gate.sh` has **chat-7's session path
baked into it** (`/sessions/intelligent-admiring-cori/...`) and will fail from
any other session. It needs its paths derived at runtime before chat-8 closes,
or the close gate itself will be the thing that breaks.
