# AxiomDynamics — Current State

**Last updated:** 2026-11-13 (**chat-9 closed**). Next session: read
`CURRENT-STATE.md`, then `project-logs/chat-9/CARRY-FORWARD.md`. Suite **370**,
mutation driver **24 mutations, 24 killed**. Chat-9 closed item 1's last
software half: **a disposition cannot exist without an attestation**.
Account: `assets/attestation-at-entry-build-2026-11-13.md`.

**The buildable queue inside this repository is near-empty.** Three of chat-9's
six rungs are blocked outside it: the real payload schema needs the Railroad, the
supply-chain application needs a release host and a GPG key with custody, and
D07 §14.5 needs counsel. Chat-10 should start by re-deriving the ladder rather
than assuming there is code to write.
**Repository:** `C:\Users\RGV\AxiomDynamics`
**Remote:** `github.com/kaanju19-lang/AxiomDynamics` (private)
**Push state:** `git log --oneline origin/main..HEAD` is the only answer that
counts. As last confirmed the local remote-tracking ref stood at `bb99cdd`; the
first commit after it is `893096e`. Never trust a hash written in this file
— check with git, because this file's own commit moves the top of the branch
every time it is edited. Run `PUSH-TO-GITHUB.bat` in the repo root. The sandbox
cannot reach GitHub: `git push` and `git fetch` both fail with HTTP 403 from the
proxy, so a local `origin/main` ref is not proof of what the remote holds.

---

## Chat-6 build — authenticated disposition entry (AD-2 entry half), 2026-11-11

**Built and committed in chat-6: commits `db569a4` and `83010d0`. Suite
238 → 315, all green. Not yet pushed.** Full account:
`assets/session-entry-build-2026-11-11.md`.

The gap chat-5 left: `POST /api/warrant/<id>/disposition` read `reviewer_name`
and `cert_id` out of the request body, so the name on a decision was a claim even
though the registry could verify one after the fact. `backend/accounts.py` now
binds an account to a live certification record and gates entry on a bearer
token; identity comes from the resolved session and a body carrying either field
is **refused**. `resolve_session` re-checks the certificate, and a second check
runs inside the ledger's write transaction so a revocation landing between
resolve and INSERT cannot record a decision. With no account enrolled the path is
**closed (503)** rather than reopened to free text. `tools/seed_demo_account.py`
is the deliberate act that opens it. The frontend now signs in; the reviewer and
certification boxes are gone because they would be a lie about what the row says.

**The audit is the part worth reading.** An independent agent told to *falsify*
the claim found the transaction guard **inert** — it *returned* a boolean and the
caller discarded it, so a certificate revoked in the resolve-to-INSERT window
still produced HTTP 200 and a row. 310 tests were green. They missed it because
the test simulated the race with a guard that *raised*, which is not the guard
the route installs. A guard whose only tested failure mode is one the caller does
not use is not a guard — the same shape as the vacuous ledger and ROI tests.
Fixed, with the exploit reproduced verbatim against the fix's removal.

Also fixed from the hostile-input sweep: two 500s on malformed bodies
(`note` as an object, `disposition` as a list).

Still open: **key custody and joiner/mover/leaver** (a written procedure), a
**signed key directory**, and requiring an **attestation** at entry as well as a
session. Entry proves a credential was presented; it does not prove a person.

## Chat-8 phase one — the four mutation survivors are closed, 2026-11-11

Commit `a4ccc0b`. **Driver: 18 mutations, 18 killed, 0 survived. Suite 346 → 351.**
Account: `assets/mutation-survivors-closed-2026-11-11.md`.

M5 and M9 were the straightforward coverage gaps the carry-forward described.
M3 needed a case nothing had: a garbage body **plus an unknown token** — with
the resolve failure swallowed, that is the one shape where a row reaches the
ingest log while the status stays 401. **M2 was not the gap it was reported to
be**; I first decided it was an equivalent mutant and was wrong, because the
status and the row count match but the **error text does not**. The test now
asserts the message.

**Two defects in the driver itself were found by an independent audit after
every mutation was green**, and both matter more than the tests:

- An `EQUIVALENT` table I added was keyed by mutation **index**. The auditor
  put a genuine survivor in that slot and the driver printed "equivalent" and
  exited **0**. It would have absorbed any real survivor landing there.
  Removed; a survivor now always prints `ALIVE`.
- The pycache isolation was **inert**: the suite runs under `-I`, and `-I`
  sets `sys.pycache_prefix` to `None`, discarding `PYTHONPYCACHEPREFIX`.
  Bytecode still reached the source tree. Now `-X pycache_prefix=...`, which
  `-I` honours — both claims verified rather than assumed.

**Importing `backend.main` runs `store.init_db()`** against the repo root, so a
test that imports it before setting `AXIOM_DB_PATH` creates an `axiom.db` there
and dies with `disk I/O error` on this mount. `tests/test_ingest_auth.py` now
sets it first.

**`project-logs/close-gate.sh` carries chat-7's session path** and will fail
from any other session. Fix its paths before chat-8 closes.

## Chat-8 phase two — the AD-2 custody procedure, 2026-11-11

Commit `3de44cf`. B01 §7 item 1 has been open on "key custody and
joiner/mover/leaver — a written procedure, not code" since chat-6. It is now
**D09 §8.4**, eight subsections, beside §4.5 which already does the same job for
the export key. Account: `assets/key-custody-procedure-2026-11-11.md`.
**Suite 351 → 359.**

**Writing the procedure down exposed three things the code did not support, and
no test found any of them.** That is the part worth carrying:

- **A key could be registered to a second reviewer, and the second one won.**
  `register` refused only a key revoked *anywhere* in its history; a *live* key
  presented under a different reviewer was accepted, and because `attest`
  resolves the newest entry for a `key_id` — deliberately, so renewal works —
  the second reviewer took the key over and the original holder was locked out
  of their own key. The register is append-only, so the binding could never be
  removed. Now refused at the write. A renewal under a new certificate for the
  **same** reviewer still works; my first attempt refused that too and would
  have broken rotation to fix sharing.
- **A refused key directory still handed back bindings** — `ok=False` alongside
  `bindings={'<key>': 'Hoffman'}` for the directory it had just refused. Now
  `{}`.
- **The procedure named a step nobody could perform.** The only code that made
  a reviewer key was `seed_demo_account.py`, which generates one and discards
  it. `tools/issue_reviewer_key.py` is the joiner step: generate, register,
  print the `key_id`, never the key, refuse to overwrite an existing key file.

Every mechanism claim in §8.4 was executed rather than reasoned about. Both new
guards are mutation-tested — each fails exactly one test when removed.
**Item 1 is not closed:** a credential holder is not a person, the HMAC scheme
is symmetric, a demo cannot attest, and every step but revocation is performed
by a human. What changed is that the item is now auditable under D09 §10.1, and
B01 §7 item 1 says that rather than implying a document settles it.

## Chat-9 — attestation at entry, and a generator defect four chats old, 2026-11-13

Commits `0916bc0`, `e2bdf6d`, `fec966b`. **Suite 359 → 370.** Three rungs landed
and three are blocked outside the repository.

**Attestation at entry closes B01 §7 item 1's last software half.** A disposition
now requires the session token **and** a registered reviewer key, and the
attestation is written **inside the ledger's own transaction** — so a refused key
rolls the whole write back and no row can exist that no key vouched for. The
design was forced, not chosen: the registry stores only the 16-hex `key_id`, an
attestation is an HMAC the server must compute, and it covers `recorded_at`,
`prev_hash` and `supersedes_id`, none of which exist until the row is built. The
key is therefore presented per request in `X-Reviewer-Key`. Making it the login
credential was rejected because it would put the attestation secret in the
session store and its backups. **Item 1 is still open** — a credential holder is
not a person — and B01 says so in its own words.

**Two defects this exposed, both mine.** `seed_demo_account.py` generated the
reviewer key and discarded it, so after the change a seeded operator could sign
in and have every write refused — the same "procedure naming a step nobody can
perform" shape as chat-8. `--key-file` now writes it 0600.

And **three of six mutations survived the first run**, all three because the
assertion matched the wrong message: `"reviewer key"` also appears in the
*unregistered-key* message, the inner guard also names both reviewers, and every
route test was refused at the **early** check so the transactional layer was
never reached. **Two layers of one check cannot both be tested through the outer
layer.** Three direct `save_disposition` tests now reach the inner guard; all 24
mutations are killed.

**A generator defect four rebuilds old was found in the same pass.**
`inlineRuns()` and `PB()` both handled bold and code and **neither handled
single-asterisk italics**, so fifteen italic phrases rendered literally —
including in stages written four chats ago. It hid because there were two
near-identical tokenisers and the one with the gap was not the one every
paragraph used. Now a single `tokenize()`.

**Three documents still said entry was ungated** (D00's F08 row, D09 §4.4, F09
Part 7) after chat-6 closed that gap. Corrected; `close-gate.sh` greps for the
phrasing so the next one trips the gate.

## What this project is

Physics-first predictive maintenance for freight rail. Six named physical models
— thermodynamics with per-axle rolling z-score, peer median/MAD comparison,
kinematics, acoustics (BPFO/BPFI/BSF/FTF), same-axle left/right differential, and
an executive ROI panel — instead of black-box ML or fixed alarm thresholds.

The Master Brief Docket is in `client-assets/MASTER-BRIEF-DOCKET/`: 38 artifacts
— 36 Markdown documents, the A1 Excel model (with its build script beside it) and
the B03 HTML infographic — across A (commercial), B (technical), C (deployment)
and D (contractual) series plus F (forms).

## Build status

**38 artifacts on disk; 37 docket IDs on disk (A1 is a folder holding the `.xlsx`
and the builder, so it counts as one ID and two files).** The docket index (D00)
carries 37 ID rows; 34 are marked `**Built**` in bold, and B02 (.md) and B03
(.html) carry plain "Built" with a format qualifier. D00 Part IV is the authority
on status, not this file.

A long-form account of the whole build — every stage, every document, every
correction, and the loss and rebuild — is at
`project-logs/AxiomDynamics-Build-History-and-Working-Summary.docx` (46 pages,
measured from the rendered PDF at chat-10's open; carried through chat-9's
Stage 13). It is generated by
`project-logs/build-history-summary.js`; re-run
`node project-logs/build-history-summary.js` after a material change.

Open docket items are tracked in **D00 Part IV** — that table is the authority,
not this file.

## The largest known gap

**The ingest chain is built; nothing downstream is wired to it.** As of
2026-11-11 `POST /api/ingest` accepts a payload and applies schema → timestamp →
plausibility in that order: accepted for scoring (202), retained as suspect
without scoring (200), or refused with a named reason and logged (422). 24
tests. No outcome other than `accepted` emits an advisory.

Three parts remain open, disclosed in B01 §7 item 5 and B02 §2: the payload
schema is a **demonstration schema** (`axiom-detector-payload/v1`) and the real one
must be agreed with the Railroad; **the endpoint has no authentication**, which
makes it a data-poisoning route until AD-2 lands and is why it belongs on a
trusted segment; and **the demonstration fleet still scores synthetic traces** —
an accepted payload is validated and logged, not scored.

Every demonstration number therefore still demonstrates **the method**, not the
Railroad's data.

## Open items, in priority order

1. **D07 §14.5 — governing law and venue.** An open counsel decision, correctly
   labelled as open as of chat-2 (previously a blank pointing at an Order field
   that does not exist). Must be closed by signed addendum before first execution.
2. **Session-bound disposition entry, export-key identity and off-box carriage**
   — the signed export landed 2026-11-09, the **series build landed 2026-11-10**,
   and **per-disposition attribution landed 2026-11-11**
   (`backend/attribution.py`: append-only,
   **hash-chained** reviewer registry, HMAC attestations over each row's
   `record_hash` carried inside exported records, checked by both verifiers).
   What that closes: a bundle can now say which *registered reviewer key*
   attested a row, and a recipient can verify it. What remains: the *export*
   signature is still symmetric, so a bundle names no export signer;
   attribution is about a key holder, not a person, and a recipient given no
   reviewer key cannot tell an honest attestation from a fabricated one; entry
   is now gated on a **live session** but not on an attestation, so an attested
   row is still the reviewer's choice; nothing proves when a bundle was made; a ledger wiped
   before the first bundle in a series stays invisible; and **nothing carries
   the produced series off the box** — deliberate, because D09 §3.2 promises no
   outbound network, so carriage is the Railroad's physical step under §3.3.
   D09 §4.4–4.5, B01 §4.5a and §7 items 1 and 11–12. **Attribution and
   session-bound entry are no longer AD-2 dependencies; export-key identity,
   key custody and joiner/mover/leaver still are.**
   An independent adversarial audit found nine defects in this build after the
   suite was green — the worst of them let a registered key relabel another
   reviewer's row and pass both verifiers. 40 mutations, 40 killed. See
   `assets/attribution-build-2026-11-11.md`.
3. **D09 §4.4 supply-chain gaps** — SBOM (Q1 2027), hash verification of
   dependency downloads (Q1 2027), GPG-signed releases (Q2 2027). All three now
   have **tools built 2026-11-11**; none is **applied**, and D09 §4.4 carries the
   three-state distinction per control.

## Model decision — A1 governs, decided 2026-11-10 (chat-4)

The owner delegated the choice ("you decide"). **A1 governs the commercial
numbers, expressed as Option D in `assets/a2-d08-model-decision-2026-11-09.md`**:
0.05% escalation probability, $500,000 typical contained cost, $1.0B catastrophic.

What changed in the docket, all on 2026-11-10:

- **A2 §3.2 and D08 §3** anchors restated from the withdrawn 2.0x/4.1x to
  **1.77x at 500 axles, 3.36x at 10,000**, with the cost basis stated in the text
  instead of left to inference. The pilot year is charged in full and credited with
  no benefit in that calculation — the conservative frame.
- **D08 §5 restated** from A1: pilot year at the **200 axles §2 actually scopes**
  ($278,670 modelled benefit, **0.75x** the $370,000 fee — the pilot does not pay
  for itself and the document now says so); production years at 500 axles
  ($696,675/yr); four-year return **2.01x**.
- **D08 §6 restated**: six-year return **2.06x**. Close to flat against the
  four-year figure, because fee escalation from Year 4 offsets the dilution of one
  weak pilot year across more production years. It does **not** fall.
- **`backend/roi.py`** corrected: `P_CATASTROPHIC_GIVEN_MISSED_DEFECT` 2% → 0.05%,
  and the per-missed-defect value now blends the **$500,000 typical** cost rather
  than the $9.25M midpoint of the two NTSB severe benchmarks. Expected cost per
  missed defect is now **$999,750**, identical to A1's B22; the 29x overstatement is
  gone. The severe benchmarks survive as `SEVERE_FAILURE_COST_*`, explicitly
  reference-only, and the dataclass field renamed `severe_cost_range_usd` so no
  reader mistakes them for the typical case again.
- Checkers updated rather than left certifying stale text: the arithmetic pass is
  now **89 checks** and reports both findings **closed and checked**, not merely
  recorded. The decision paper's **65 checks** still reproduce (it documents the
  withdrawn figures, which is its job).

**Two things a future reader will otherwise trip over.** First, A2 §3.2 says 1.77x
at 500 axles and D08 §5 says 2.01x — different questions on the same inputs (A2
charges the pilot with no benefit; D08 credits the 200-axle pilot with its actual
benefit). A2 §3.2 now states that difference explicitly. Second, **D08 §2 scopes the
pilot at 100–200 axles**, so any pilot-year benefit computed at 500 was contradicting
the document's own scope. That defect was mine, introduced in the first restatement
and caught before commit.

## Ledger replication series — built 2026-11-10 (chat-4)

`backend/ledger_replication.py` executes the cadence D09 §4.5.4 already
specified: monthly full, weekly incremental, every bundle chained to the
previous by `previous_export_hash`, zero-record weeks kept, nothing overwritten.
`inspect` opens every bundle, recomputes its digest, verifies it against the
predecessor, and reports a missing period. 32 tests; full suite **112**.

**It deliberately does not transmit.** D09 §3.2 promises the Platform has no
outbound network, so the series accumulates in `--series-dir` on the box and
carrying it to backup media is the Railroad's step under §3.3. The owner chose
this over a network push on 2026-11-10; the reasoning is in
`assets/ledger-replication-build-2026-11-10.md`.

**Two audits found nine material defects before this was called built** — the
count is in the assets file rather than here, but the shape is worth carrying:
the release verifier rejected every full export, `inspect` could not see
tampering or gaps, the period walker hung on a 53-week ISO year, concurrent runs
duplicated bundles, and one test passed only because the check it guarded was
absent. A green suite of 108 preceded all of it.

## Export hardened at chat-4's validation pass, 2026-11-10

Found by attacking the artifact rather than re-reading it, when the owner asked
for the completed work to be validated: **a written bundle accepted any extra
top-level field and both verifiers still returned `ok=True`.** The signature
covers a selected tuple and the digest names its fields, so a key added beside
them was unsigned — changeable after signing, and readable by a recipient as
though the bundle attested it.

Both `backend/ledger_export.py` and `tools/verify_ledger_export.py` now reject a
bundle whose top level is not exactly `format` / `manifest` / `records` /
`signature`, with the check named `bundle_no_extras`. The signing construction is
unchanged: a named field list is the correct way to sign, because it puts the
covered set in code rather than in the document. The gap was the absence of a
check on what else the document contains. One test added and mutation-tested in
both files; suite 113 → **114**.

## Status at close — every completed task re-verified against the repository

Not re-read. Executed: the suite (114/0), the arithmetic pass (97/97), the
decision paper (65/65); the withdrawn 2.0×/4.1× pair confirmed absent as a live
claim in both documents; `roi.py` constants read back from the module ($999,750
expected cost, 4.8/1.5 h MTTD); the replication module built a real series and
`inspect` verified it, then **detected** both a manifest edit and the extra-field
case; the rebuilt workbook reopened and its cached values checked ($370,000
pilot, ROI 2.0653).

**The workbook swap was completed on 2026-11-10 after Excel released its lock.**
`AxiomDynamics-ROI-Calculator.xlsx` in the docket is now the corrected file —
$370,000 pilot year, three-year ROI 2.0653×, agreeing with A2 §5.1. The
intermediate `…rebuilt.xlsx` and `REPLACE-WORKBOOK.bat` were deleted once the
swap was confirmed byte-identical, because a second copy of the same workbook
under a different name is how the staleness got missed in the first place.

## Transcript — chat-4 extracted and committed at close, 2026-11-10

The standing rule is that a phase is not finished until its assets and its
conversation are in this repository. Chat-4's raw log was extracted at close:
5,667 events, 12 MB, into
`project-logs/transcripts/raw/2026-11-10-chat-4-snapshot.jsonl`, with the
readable extract at `project-logs/transcripts/2026-11-10-chat-4.md` — 704 turns
of which **six are the owner's**.

**A defect in the extractor was fixed in this pass.** `extract_transcript.py`
wrote a hard-coded `"# Chat-3"` heading into every extract regardless of which
session it was processing, so chat-4's file opened under the wrong title. It now
derives the heading from the output filename (`…-chat-4.md` → `# Chat-4`) and
falls back to the filename stem otherwise.

**Build history regenerated at 39 pages (chat-6).** Stage 10 was added for
chat-6 — authenticated disposition entry and the inert guard the audit found —
and Part VII's two entry-gating rows were rewritten rather than left to contradict
the code. The paragraph below records the chat-5 revision. Stage 9 was added for
chat-5 — the ledger audit, the ingest path, the supply-chain tools and
attribution — and Part VII's gap register was rebuilt rather than patched: the
ingest row, the attribution row and the supply-chain rows all described states
that chat-5 changed, and three of them had drifted into claiming more than the
code did. The earlier revision, at chat-4's close, is recorded above: Part VII
still described Findings 1 and 2 as open, which had been true when written in
chat-3; both are now closed with their resolution kept rather than deleted. Stage 8 was extended to carry the model
decision, and the status-at-a-glance table was corrected — its test count, its
replication row and its commercial-numbers row were all stale.

## Signed ledger export — built 2026-11-10 (AD-3 part two), commit `d9c83d4`

`backend/ledger_export.py` builds an HMAC-SHA256-signed bundle: manifest (id
range, record count, head hash, the ledger's own head, covered-field list,
canonicalisation rule, chain status, previous bundle digest), every record in
canonical form, and a signature over the whole. `tools/verify_ledger_export.py`
verifies it **without importing anything from `backend/`**, from an empty
directory, with `-I` — the recipient needs the bundle, the key, and a Python
standard library, nothing else.

**Why HMAC and not Ed25519:** the stdlib has no asymmetric primitive, and
hand-rolling one in a product that tells CISOs it does not hand-roll crypto
would be worse than the gap. The two limits — cannot name the signer, cannot
date itself — are stated in B01 §4.5a rather than footnoted.

**The audit caught a serious hole, and this is the part worth remembering.**
The first version let a total wipe verify green: delete every row, export
honestly, and a recipient holding the previous bundle was told everything
passed. Each check was individually correct; none compared the bundle against
one already held. Fixed by recording the ledger's own head in every bundle and
failing when a later bundle reports a shorter ledger (`no_truncation`), plus
`genesis_anchor` for rows deleted from the front. Export tests are now 43; the
suite at the time of that build was 80. Three tests assert a failure to detect on purpose, recording disclosed
limits rather than hiding them.

**What it does not do:** detect a ledger wiped before the first bundle in a
series; replicate off-box on a schedule; name the signer. D09 §4.5 makes bundle
retention and a written key-custody procedure the controls that carry that
weight.

Internal account: `assets/ledger-export-build-2026-11-09.md`.

## Transcript — re-snapshotted and committed 2026-11-10, commit `53ad93a`

The standing rule is that a phase is not finished until its assets and its
conversation are in this repository. The chat-3 raw log was re-snapshotted at
close (5,032 events, 17.1 MB) into
`project-logs/transcripts/raw/2026-11-10-chat-3-snapshot.jsonl`, and the
readable extract rebuilt from it — 641 turns, of which **ten are the owner's**;
everything else is assistant text and tool calls.

The mid-session snapshot was deleted rather than kept: it was byte-for-byte a
prefix of the new one, so keeping it would have added 13 MB and no information.
The extractor now lives in the repo at `project-logs/extract_transcript.py`
instead of a shell heredoc, with the rules and the trap that cost a cycle on the
first attempt written into it — the role is the top-level `type` field, not
`message["role"]`.

## Append-only disposition ledger — built 2026-11-09 (AD-3)

The gap that had been disclosed in six documents since `cf2e6ba` is closed at
the code level.

- `backend/store.py` rewritten. Records are inserted, never updated. A second
  decision on an advisory is a new row carrying `supersedes_id`; the earlier row
  keeps its content and timestamp. `BEFORE UPDATE` and `BEFORE DELETE` triggers
  `RAISE(ABORT)`, so the guarantee lives in the schema rather than in convention.
  Every row stores `prev_hash` and `record_hash` — a SHA-256 over its own
  canonical content plus the predecessor's hash — and `verify_chain()`
  recomputes the whole chain and names the first row that fails.
- Migration from the v1 one-row-per-advisory table runs inside `init_db()`,
  preserves the surviving decision and its original timestamp, and does not
  fabricate history that the old schema had already destroyed.
- 17 adversarial tests in `tests/test_store.py`: an UPDATE, a DELETE, a second
  disposition, a tampered row, a removed row, and two migration shapes. Each
  asserts the attempt fails or is detected. `tests/run_tests.py` now discovers
  every `test_*.py`, so the total suite is 38.
- New routes: `GET /api/warrant/{id}/disposition` (full trail, with `chain_ok`)
  and `GET /api/ledger/verify`. The dashboard shows the decision trail under the
  form and marks a corrected decision as superseding an earlier record.

**What it does not prove, and the docket now says so in these words:** the chain
is tamper-*evident*, not tamper-*proof*. A party with write access to the
database file can drop the triggers, rewrite rows and recompute every hash. That
is why items 6 and 8 above stay open.

Docket corrected in the same commit: B01 §4 and §7 items 2/8, D09 §4.4 and the
audit-logging row, F09 Part 6 and Part 7, F00, B02, C02, D12, D14 §5, D00 Part V
and Part VI, and the root README.

## A1 builder — fixed in chat-3

Two defects in `A1-ROI-MODEL/build_roi_calculator.py`, both cosmetic to the
workbook but both real if anyone runs it:

- The sheet-5 assumptions note attributed a **2% catastrophic escalation rate** to
  a model whose cell B17 has held **0.05%** since the correction. A reader
  reconciling the sheet against its own footnote would find a ten-fold conflict.
- The script saved to `/sessions/.../mnt/outputs/...`, a path inside the destroyed
  chat-1 sandbox, so running it raised `FileNotFoundError`. It now writes beside
  itself.


## Git state

The sandbox **cannot reach GitHub** — `git push` and `git fetch` both fail with
HTTP 403 from the proxy. Its `origin/main` ref therefore only advances when the
owner pushes and the sandbox is told the result. Do not trust it as evidence of
remote state without checking the commits page.

**Pushing is done by the owner**, with `PUSH-TO-GITHUB.bat` in the repo root. It
prints the commits waiting to go up and verifies afterwards.

**Last confirmed pushed state, 2026-11-10:** the owner's push moved the remote to
`bb99cdd`. Everything after it is local and waiting, and every edit to this file
adds to the queue — so the count is deliberately not written here. Run
`git log --oneline origin/main..HEAD`.

**The host repo at `C:\Users\RGV\AxiomDynamics` is authoritative for push state.**
Verify by opening the commits page.

**The line-ending trap.** `git status` in this repo lists nearly every tracked file
as modified on a fresh Windows checkout. It is CRLF working-tree content against
LF blobs, not a content change — `git diff --ignore-cr-at-eol` returns empty.
There is no `.gitattributes` and `core.autocrlf` is unset. **Always check with
`--ignore-cr-at-eol` before believing a diff stat**, and never let an editor
rewrite a whole file's endings into a commit: doing so once during chat-3 turned a
two-line fix into 1,248 changed lines, which had to be reset and recommitted.


## What was lost in the chat-1 → chat-2 transition

Recorded here so nobody goes looking for it:

- Three commits built at the end of chat-1 (`0b66d21`, `cb4f74d`, and the
  F00/D07/Q6 work) existed only in the old sandbox. **`F00` Rule 7, the D07 §14
  rewrite and Q6 were rebuilt into the repository in chat-2.** The project-logs
  structure was rebuilt. The transcripts were not and cannot be — see
  `README.md`.
- Because the rebuild is a reconstruction rather than a recovery, the wording may
  differ from what chat-1 wrote. The *decisions* are identical; the prose is not
  guaranteed to be. Do not treat the current text as a restoration of an earlier
  draft.

## Standing instructions

- **[WORK LOCATION] All project work is written directly into this repository, first pass, and committed in the same pass.** No drafts in sandbox scratch space — that is how chat-1's final phase was lost.
- Keep the same concept throughout — consistency of framing across every document.
- Internal analysis goes in `assets/`, never `client-assets/`.
- Verify against the file before writing the claim.

## Why chat-1's work was lost — the mechanism

Not a deletion. The work was never on the owner's machine.

Chat-1 built the repo inside a temporary sandbox container. To get anything out
it bundled the repo, embedded the bundle in a `.bat`, and the owner ran it once —
which is how `de9b245` reached GitHub. **Everything chat-1 did after that push
stayed in the container**, including the F00 Rule 7 work, the D07 §14 rewrite, Q6
and the transcripts. The bundle was never remade. When the session ended the
container was destroyed and took all of it.

The failure was treating "committed" as "safe." Inside that container it only
meant "saved somewhere that is about to be emptied."

**The rule that follows:** there is no automatic export. A commit in the sandbox
is not durable until it is in `C:\Users\RGV\AxiomDynamics` and pushed. Never tell
the owner work is saved without saying where it physically is.
