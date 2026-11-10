# Chat-3 — Running Summary

Status: **in progress** as of 2026-11-09.
Opened with the chat-2 carry-forward. Its first act was to verify the inherited
state against the repository rather than trust the handoff, per the standing rule.

## Verification of inherited state (start of chat-3)

Read `CURRENT-STATE.md`, `chat-2/SUMMARY.md` and `project-logs/README.md`, then
checked the repo directly. Four things did not match the written record:

1. **Push state was stale in the carry-forward.** It named `785f335` and
   `ee9800c` as unpushed; both were already in `origin/main`, with `ee9800c` as
   the remote top. What was actually unpushed was the later transcript and
   handoff work — `3d773ac`, `36b43bd`, `d6f25ac`, `05b161d`.
2. **`chat-2/SUMMARY.md` still read "in progress"** and still claimed "Neither is
   pushed" about `f58b07c`/`c9b32bd`. Finalized and corrected.
3. **57 "modified" files were a line-ending artifact.** CRLF working tree against
   LF blobs; `--ignore-cr-at-eol` returned empty. Not content. Recorded in
   `CURRENT-STATE.md` so the next session does not re-investigate it.
4. Everything else was intact: 37 docket documents, `assets/`, and the chat-2
   transcript with three raw `.jsonl` files (5.8 MB).

## Work done in chat-3

### A2 / D08 arithmetic pass — complete

The highest-value item from both the carry-forward and `CURRENT-STATE.md`, and
untouched since `cf2e6ba`.

Built `assets/a2-d08-arithmetic-pass.py`: it recomputes every figure in A2 and D08
from its stated source equation and compares it to the document, exiting non-zero
on any mismatch. **78 of 78 computed figures agree.** No arithmetic error exists
in either document — every band total, worked example, site-fee product, payment
split, conversion credit, three-year row, performance cap, cumulative schedule and
the 5% escalation is correct as written.

Two *claims* did not reproduce. Both are model divergences rather than arithmetic
errors, and both are left open because fixing them means choosing which model
governs — an owner decision, not an editorial one:

- **Finding 1.** A2 §3.2 and D08 §3 claim ~2.0x at 500 axles rising to ~4.1x at
  10,000. The shipped models produce 1.77x/3.36x on the A2 cost basis, or
  2.36x/4.99x on A1's. No parameter set in the repository reproduces both anchors.
  The monotonic claim is true on every basis tested.
- **Finding 2.** D08 §5–§6 modelled benefits run 5x–14x above the $696,675 annual
  benefit A1 computes at identical inputs. D08 §5 states A1 must never be
  bypassed.

Full working, tables and recommended dispositions:
`assets/a2-d08-arithmetic-pass-2026-11-09.md`.

### A1 builder — two defects fixed

- The sheet-5 assumptions note attributed a **2%** catastrophic escalation rate to
  a model whose cell B17 has held **0.05%** since the correction. Corrected to
  name 0.05% and cite B17.
- The script saved to `/sessions/.../mnt/outputs/...`, a path inside the destroyed
  chat-1 sandbox, so running it raised `FileNotFoundError`. It now writes beside
  itself via `os.path.dirname(os.path.abspath(__file__))`.

The committed workbook was **not** regenerated: doing so would bake both open
findings into a new file before the model question is settled.

### Project logs corrected

`CURRENT-STATE.md` updated (push state, open items, the line-ending trap, the A1
builder fixes). `chat-2/SUMMARY.md` finalized and its push claims corrected.
`chat-2/CARRY-FORWARD.md` push numbers and "work waiting" section corrected.
`project-logs/README.md` tree now lists `chat-2/CARRY-FORWARD.md`, `chat-3/` and
`transcripts/raw/`.

## Verification performed

- Arithmetic: 78 figures computed independently in `assets/a2-d08-arithmetic-pass.py`,
  all matching. Script re-run from the committed tree and exits 0.
- Every A1 figure cited in the pass record was read from the built workbook
  (`openpyxl`, `data_only=True`), not from the builder source — the two differ on
  the pilot cost line.
- A2 and D08 confirmed untouched: `git diff --ignore-cr-at-eol` on both returned
  empty after the pass.
- Commit inspected for line-ending churn. The first attempt rewrote the builder to
  CRLF and produced 1,248 changed lines for a 2-line fix; reset and recommitted so
  the commit shows 420 insertions and 2 deletions.

## The build history document

Requested by the owner because chat-1's conversation no longer exists and the
build needed a readable record of itself. Produced as
`project-logs/AxiomDynamics-Build-History-and-Working-Summary.docx` — 29 pages
when first written, 32 after the 2026-11-10 revision — eight parts plus an
appendix, with its generator committed beside it at
`project-logs/build-history-summary.js` so it can be rebuilt after a change.

Contents, in order: what the product is and why physics rather than ML; the six
models; the build stages across all 50 commits with every correction; the
38-artifact docket document by document plus the D00 Part IV precedence ladder;
the loss of chat-1's work, its mechanism and its cost; what chat-2 rebuilt and
how it verified it; internal strategy in `assets/`; the open items including both
chat-3 modelling findings; how to resume; and an appendix with the repository
map, the full commit chronology and a status table. The revision added Stage 6
(the rebuild and its rules), Stage 7 (the three chat-3 builds and the decision
paper), and the three working papers added to `assets/`.

**The revision found a defect worth recording.** Part VII still carried the
arithmetic pass's conclusion on Finding 1 — that no parameter set reproduces the
2.0×/4.1× anchors — when the decision paper had since shown that one does, on an
unstated cost basis. The stale conclusion had been left in a document that was
otherwise the project's most careful account of itself. It is the same defect
class the project keeps correcting: a claim that was true when written, never
revisited when the evidence moved.

Written from the repository, not from recollection. Layout verified by rendering
to PDF and reading the pages: 29 pages, no overflow, tables within margins,
numbering restarting per list. Two defects were found and fixed in that pass —
all numbered lists shared one continuous sequence (Part VIII opened at "10."),
and the Word TOC field rendered empty in a converter that does not update
fields, so a static Parts table now carries the navigation.

## Commits

`ed78962` — the arithmetic pass, check script, pass record and builder fixes.
`a3ba43f` — the build history document and its generator.
`b3dcda4` — `CURRENT-STATE.md`: points at the summary, corrects the artifact
count, and replaces the hardcoded unpushed-hash list with an instruction to check
`git log origin/main..HEAD`.

**Push required.** Run `PUSH-TO-GITHUB.bat` in the repo root, then confirm with
`git log --oneline origin/main..HEAD` rather than trusting any hash written here.

## Phase 2 — append-only disposition ledger (AD-3), committed `209efe6`

Chosen as the next build because it was the one open code control that needed no
commercial decision from the owner, and because the docket's most legally
significant record was overstating what the code did.

**The defect, confirmed before touching it.** `backend/store.py` used
`advisory_id` as PRIMARY KEY with `INSERT ... ON CONFLICT DO UPDATE`. A second
disposition on the same advisory overwrote the first — its reviewer, its note
and its `recorded_at` all gone. F09 described an append-only record; the code
produced one row that could be rewritten. Six documents disclosed the gap.

**What was built.**

- Insert-only writes. A correction is a new row carrying `supersedes_id`; the
  corrected row keeps its own content and timestamp.
- `BEFORE UPDATE` / `BEFORE DELETE` triggers that `RAISE(ABORT)`, so the
  guarantee is in the schema rather than in application convention.
- SHA-256 chain: `prev_hash` (predecessor's hash, 64 zeros at the start) and
  `record_hash` over canonical content plus `prev_hash`. `verify_chain()`
  recomputes and names the first failing row.
- `BEGIN IMMEDIATE` on writes, so two concurrent appends cannot both read the
  same `prev_hash` and fork the chain.
- Migration inside `init_db()` from the v1 table, preserving the surviving
  decision and its original timestamp without fabricating lost history.

**What it does not do, and the docket now says so in these words.** The chain is
tamper-*evident*, not tamper-*proof*. Whoever holds the database file can drop
the triggers, rewrite rows and recompute every hash. Signed, off-box export
stays open in D09 §4.4; the gap narrowed, it did not vanish. Recording that
distinction was the point — the failure mode this project keeps having is a
document claiming more than the code delivers.

**Verification.**

- 17 new adversarial tests in `tests/test_store.py`, each attempting to destroy
  an earlier decision: an `UPDATE`, a `DELETE`, a second disposition, a tampered
  row, a removed row, trigger survival across re-init, and two migration shapes.
- `tests/run_tests.py` was loading only `test_physics.py`, so the new module
  would never have run in CI. Rewritten to discover every `test_*.py`. Suite is
  now 38, all passing.
- End-to-end against a live server: two dispositions on one advisory produce
  two records, the second names the first as superseded, `/api/warrant/{id}/disposition`
  returns both with `chain_ok: true`, `/api/ledger/verify` returns
  `{ok: true, rows: 2}`, the alert carries "supersedes 1 earlier record", and
  empty reviewer input is rejected with 400.
- No headless browser in this environment, so the UI change was verified by
  `node --check` plus inspecting the served DOM construction rather than by
  screenshot. **The history panel has not been seen rendered.** Worth a look on
  first run.

**Docket corrected in the same commit** — the rule is that a gap closes only
when the code changes and the disclosing documents change with it: B01 §4.1,
§4.5, §4.6, §7 items 2 and 8 and the component table; D09 §4.4 and the
audit-logging row; F09 Parts 6 and 7 and its footer; F00; B02; C02; D12; D14 §5;
D00 Parts V and VI; and the root README.

**Two defects found in the root README while correcting it,** neither related to
the ledger: it opened "three named physical models" then listed seven; it had
two items numbered `7.`; and it described the 2% catastrophic-escalation
placeholder as current when `roi.py` uses 2% but the A1 workbook uses 0.05%.
All three fixed, and the 40× divergence now points at
`assets/a2-d08-arithmetic-pass-2026-11-09.md` instead of being restated as if
settled.

## Next

1. Decide Finding 1 — strike or restate the 2.0x/4.1x anchors.
2. Decide Finding 2 — which model governs, A1 or D08 §5–§6.
3. Then regenerate the A1 workbook and re-run the check script.
4. D07 §14.5 governing law and venue remains open, unchanged by this pass.
5. Signed, off-box ledger export — the natural successor to this phase, and the
   half of AD-3 that "tamper-evident" still does not cover.

## Phase 3 — the A2/D08 model decision, priced (committed `b23d0c7`)

Chosen ahead of the signed ledger export, and the reason is worth recording:
the ledger phase fixed a document claiming more than the code did, and these two
findings are the same defect class — except they sit in the money documents a
customer's procurement team will run, and D14 §8 names the gap between the sales
description and the contract as the product's largest liability. A missing
signature on a ledger is a production requirement. A rate card that contradicts
its own ROI model cannot be sent out at all.

**What was built.** No code changed in the product. `assets/a2-d08-model-decision-2026-11-09.md`
plus `a2-d08-model-decision.py` (65 reproducible checks) price both answers so the
owner's decision is a comparison rather than more research.

**Three findings the arithmetic pass did not have.**

1. **The 2.0x/4.1x anchors are recoverable.** The pass record tested two cost
   bases and concluded no parameter set reproduces both. On a third — pilot plus
   three full years at list, no conversion credit — one value of the catastrophic
   probability fits both, because the ratio the anchors demand
   (cost(10k)/cost(500) = 9.756) is a property of the *pricing*, not the benefit
   model. So this is a disclosure defect, not a fabrication. The level of p is
   not unique — a four-year benefit horizon gives 0.0412% and also fits — which is
   why the finding stays open.
2. **D08 contradicts itself.** §4 prices a prevented failure at ~$993,000; §5 at
   $8.6M–$11.4M. Holds per axle as well as per defect. And §4's figure is within
   0.7% of A1's $999,750 — the document already contains an A1-consistent
   valuation four pages before abandoning it.
3. **`roi.py` is further from A1 than the README says.** Two disagreements, not
   one: 2% vs 0.05%, and a $9.25M contained cost vs A1's $500,000. Per-missed-
   defect values are $29,065,000 vs $999,750 — 29×, of which probability accounts
   for 20.5×.

**What the independent audit caught, and this is the part worth keeping.** I wrote
the paper and then wrote its checker, which is exactly the arrangement where a
shared assumption passes unnoticed. A separate agent with no stake in it found
four errors:

- **The dashboard figure was not roi.py's output.** I had computed $14,339,850 by
  re-running A1's formula at 2% and labelled it as the dashboard. `roi.py` takes
  warrants, not axles — "at 500 axles" was never computable. Corrected to a
  per-defect comparison, which is the right like-for-like and a *larger* gap.
- "D08 repeats it verbatim" — it does not; two sentences are reworded. Corrected.
- "That is where the numbers came from" — overstated derivation from consistency.
  Corrected, with the horizon ambiguity shown rather than buried.
- "no site-fee line" in the stale workbook — wrong, the row exists and is inert at
  one site. Corrected, and the real disagreement (a $285,000 pilot built from
  hardware + training against A2's $370,000 with no hardware at all) stated.

Lesson for the next phase: when I produce both an analysis and the script that
checks it, a second reader is not optional. The checker validated my mistake
because I wrote it to.

## Next

1. Decide Finding 1 and Finding 2 — options priced in the decision paper §6,
   recommendation in §7. **This is the only blocking item that needs the owner.**
2. Worth pricing before locking Option A: adding the cost components A1 omits
   (service disruption, lading loss, regulatory penalty) to B14 at 0.05%, which
   may raise the benefit figure honestly.
3. Then regenerate the A1 workbook from the corrected builder and re-run both
   check scripts and the unit suite.
4. D07 §14.5 governing law and venue remains open, unchanged.
5. Signed, off-box ledger export — the next *build*, now unblocked by priority
   but not by dependency; it does not touch any of the above.

## Phase 4 — the signed ledger export (committed `d9c83d4`)

Deferred the A2/D08 decision at the owner's instruction ("will defer now and just
focus on next phase build") and built the signed export instead. It is the second
half of AD-3 and the last item in D09 §4.4 that could be closed without a
commercial decision or a new dependency.

**What was built.** `backend/ledger_export.py` writes an HMAC-SHA256-signed
bundle — manifest, records, signature. `tools/verify_ledger_export.py` verifies
it with **no import from `backend/`**, from an empty directory under `-I`, so a
regulator, auditor or successor vendor can check a bundle without running,
trusting or even having the exporting software. Bundles chain via
`previous_export_hash`. CLI: `keygen`, `export`, `verify`; `keygen` refuses to
clobber a key and forces mode 0600.

**Why HMAC, stated because it is the kind of choice this project documents.**
The stdlib ships HMAC but no Ed25519. Adding a compiled crypto dependency to an
air-gapped single-dependency install, or hand-rolling a curve, were both worse
than a symmetric signature with its limits spelled out. A symmetric signature
cannot name the signer — any verifier can also forge — and cannot prove when it
was made. Both limits are now sections, not footnotes: B01 §4.5a exists solely
to state them.

**The audit found a serious hole, and this is the part worth keeping.** The
first version let a **total wipe verify green**. Delete every row with file
access, run the honest exporter, and a recipient holding the previous bundle
was told every check passed — five records gone, no warning. Each check was
individually correct: hashes valid, ids ordered, count matching, signature good.
None compared the bundle against one the recipient already held, and an empty
bundle is trivially self-consistent. My own 33 tests passed because I had not
thought of the attack, so had not written it.

Fixed by recording the ledger's own head (`backend_head_id`) in every bundle
and failing when a later bundle reports a shorter ledger (`no_truncation`), plus
`genesis_anchor` for rows deleted from the front. The same audit produced four
smaller findings, all fixed: a `genesis_hash` check that only the standalone
verifier performed (so the two implementations disagreed); a false claim in the
`covered_fields` comment; tracebacks instead of verdicts on malformed bundles;
and `keygen --force` leaving an existing key world-readable because `os.open`'s
mode argument is ignored for an existing file.

**A second bug found by the tests written for the first one:** the erasure fix
broke the zero-record incremental export — a quiet week produced a bundle that
failed `range_from` — and D09 now requires a weekly export, so the documented
procedure would have failed every quiet week.

**Verification.** 42 export tests (up from 33), full suite 80. The erasure
attack re-run against the fixed standalone tool now exits 1 with `no_truncation`.
Live end-to-end: real server, three dispositions including a supersede, exported,
verified from a different directory with `-I`. Three tests assert a *failure to
detect* on purpose, recording disclosed limits rather than hiding them.

**Docket amended in the same commit:** B01 §4.5/§4.5a/§7 items 8 and 11–12, B02,
C01 §E2a (commissioning procedure), D00 Part V, D09 §4.2/§4.4/§4.5/§5.3/§6.2/§7.3,
F09 Part 7, F13 Part 4, root README, `.gitignore`. Internal account in
`assets/ledger-export-build-2026-11-09.md`.

**Lesson, recorded in memory.** A suite written by the author of a mechanism
tests the author's model of the threat, not the threat. For anything making a
security claim, falsification must come from outside — a fresh reader prompted
to break it, not check it. It has now earned its cost twice.

## Phase 5 — the transcript, at close (committed `53ad93a`)

The standing rule the owner restated in the message that opened this phase:
"upon each build completion you will store its assets/files and complete chat
logs in our Local disk project folder."

Re-snapshotted the live session log at 5,032 events (17.1 MB) into
`project-logs/transcripts/raw/2026-11-10-chat-3-snapshot.jsonl` and rebuilt
`project-logs/transcripts/2026-11-09-chat-3.md` from it: 641 turns, of which
**ten are the owner's** and the rest are assistant text and tool calls.

The mid-session snapshot was deleted rather than kept. Verified line by line
first that it was byte-for-byte a prefix of the new one, so keeping it would
have added 13 MB and no information. A snapshot is worth keeping only when it
shows a state the final one cannot.

**What cost a cycle, and is now written into the tooling.** The first extract
returned zero turns and no error: it read `record["role"]`, but the role in this
log format is the top-level `type` field. The extractor is therefore committed at
`project-logs/extract_transcript.py` rather than living in a shell heredoc, with
that trap and the three extraction rules in its docstring.

**Also in this commit:** a `.gitignore` entry for Excel lock files (`~$*`) after
one appeared beside the A1 workbook, and the build history document regenerated
at 32 pages to cover Stages 6 and 7.

**One defect found while regenerating it.** Part VII still carried the
arithmetic pass's conclusion that no parameter set reproduces the 2.0×/4.1×
anchors, when the decision paper had since shown that one does on an unstated
cost basis. The claim had been true when written and was never revisited when
the evidence moved — the same defect class the project keeps correcting. Fixed,
and it is now recorded in the summary as well as in the document.

## End of chat-3

Three build phases, one analysis phase and a transcript phase, across commits
`209efe6` through `53ad93a`. Two of the four substantive phases were materially
repaired after an independent audit: the decision paper (four errors) and the
signed export (the total-erasure hole). Both repairs are in the record rather
than tidied out of it, because the pattern — *I wrote the checker, so the checker
agreed with my mistake* — is the most transferable thing this session produced.

**Push required.** `PUSH-TO-GITHUB.bat`. Three commits were ahead of the local
`origin/main` ref at close: `893096e`, `d9c83d4`, `53ad93a`.
