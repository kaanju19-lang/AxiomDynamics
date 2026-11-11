# Chat-6 — Carry-Forward

Handoff from chat-5, closed 2026-11-11. Read this first, then confirm every
claim below against the repository. **Nothing in this document is authority.**
The repository is. Written push lists in this project went stale four sessions
running before chat-5, where the inherited list was accurate — which is a reason
to keep checking, not a reason to stop.

**State at handoff:** clean tree apart from the CRLF illusion described below.
Suite **238 tests, all green**. 40 attribution mutations, 40 killed, 0 survived.
**One owner action: push.**

---

## Read in this order

1. `project-logs/CURRENT-STATE.md` — what is built, what is open.
2. This file — where chat-5 stopped and what it left waiting.
3. `project-logs/chat-5/SUMMARY.md` — the reasoning behind each task.
4. `project-logs/AxiomDynamics-Build-History-and-Working-Summary.docx` — the
   whole build, readable cold. Regenerate with
   `node project-logs/build-history-summary.js` after any material change; do
   not hand-edit the .docx.
5. `client-assets/MASTER-BRIEF-DOCKET/D00-DOCKET-INDEX.md`, Part IV and Part VI —
   the authority on docket status and the gap register.

## Confirm state, do not assume it

```bash
git log --oneline -8                            # where chat-5 stopped
git log --oneline origin/main..HEAD             # what is actually unpushed
git diff --ignore-cr-at-eol --stat              # real changes only
python3 -I tests/run_tests.py                   # 238 passed at close
```

**The line-ending trap.** `git status` lists most tracked files as modified on
this checkout. It is CRLF working-tree content against LF blobs, not content:
`git diff --ignore-cr-at-eol` returns empty for those. There is no
`.gitattributes` and `core.autocrlf` is unset. Always check with
`--ignore-cr-at-eol`, stage named files only, and **never `git add -A`**.
`git status --ignore-cr-at-eol` is not a valid flag — only `git diff` has it.

**Recovering a killed mutation run.** `assets/mutation-attribution.py` writes a
pristine copy to `/tmp/mutation-attribution-snapshot` before it starts and has a
`--restore` flag. A run cut off mid-mutation leaves a file mutated; `--restore`
puts it back. Do not reach for `git checkout -- <file>` — that is how an hour of
uncommitted work was lost in an earlier session.

## What chat-5 did

Five tasks, in priority order, per the owner's instruction to work
"Low → High progressively one at a time":

- **D07 §14.5** — counsel brief and Phase 0 formation checklist. The venue
  question stays **open and labelled open**; it is a lawyer's answer, not mine.
- **Independent audit of ledger, export and replication** — four defects, one
  critical. One of the four was a **false claim in a customer-facing document**.
- **Detector ingest path** — three-gate validation at `POST /api/ingest`. Narrows
  the largest gap; does not close it.
- **Supply chain** — SBOM, hash pinning, signed releases. All three **built,
  none applied**. D09 §4.4 now carries that distinction per control.
- **Reviewer attribution (AD-2, part)** — per-reviewer hash-chained registry and
  HMAC attestations inside exported records. **Nine defects found by an
  adversarial audit after the suite was green.**

## The one thing to read before touching the attribution code

**The `reviewer` label in an exported attestation is not covered by the HMAC.**
The signed message is `axiom-attestation/v1:` plus the row's `record_hash` — the
name is not in it. What stops a key holder relabelling their own attestation with
somebody else's name is that **the verifier is told which reviewer each key
belongs to** and compares. Consequence, and it is deliberate:

- A verifier given a key **and a name** catches the relabelling.
- A verifier given a key **with no name** recomputes the HMAC and warns that it
  could not check the identity. That is a weaker check and it says so.
- A verifier given **no key at all** cannot distinguish an honest attestation
  from a fabricated one, because HMAC is symmetric. D09 §4.5.5 and the build
  record both state this.

Do not "fix" this by hashing the reviewer name into the attestation message. It
makes the attestation non-transferable: the recipient then needs the name to
recompute, which is the same problem one step later. The key-to-name binding
belongs in a directory the recipient controls, which is a real deliverable and
is on the open list below.

## What is still open — the real list

1. **D07 §14.5 — governing law, seat and forum.** Open counsel decision. Blocks
   first execution. Not a formation question; entity choice does not answer it.
2. **Session-bound disposition entry (AD-2 remainder).** The registry and
   attestations exist; **entry is still not gated on either**. A disposition can
   be written with a self-asserted cert ID and no attestation. This is now the
   blocking half of B01 §7 item 1 and the largest remaining code item.
3. **Reviewer key directory.** Attribution is only as strong as the recipient's
   ability to know which key belongs to whom. Right now that is a name typed on
   the verifier's command line. A signed directory is the missing piece.
4. **Phase 0 formation**, if a real customer conversation is closer than a code
   milestone. Texas LLC, $300 filing, operating agreement worth paying for.
5. **Off-box carriage of the replication series** — open by design, the
   Railroad's physical step under D09 §3.3.
6. **Supply-chain controls applied**, not just built — SBOM generation in the
   release process, pinned hashes used by the installer, GPG signing actually
   performed. Q1–Q2 2027 targets, all disclosed in D09 §4.4.

## The largest gap in the product, narrowed but not closed

**The ingest endpoint now exists and validates; no Railroad reading has ever
entered it.** The schema is a demonstration schema (`axiom-detector-payload/v1`),
the endpoint has **no authentication**, and no accepted reading is scored. Every
demonstration number still demonstrates **the method**, not the customer's data.

Two sub-gaps remain and both are blocking: the real payload schema must be agreed
with the Railroad, and the endpoint must be authenticated (AD-2) before it is
reachable by anything but their own collector on a trusted segment. **An
unauthenticated ingest route is a data-poisoning route.**

## Standing instructions, unchanged

- **All project work is written directly into `C:\Users\RGV\AxiomDynamics`, first
  pass, and committed in the same pass.** No drafts anywhere else. A whole phase
  was lost to sandbox storage in chat-1.
- **"We will keep this same concept throughout."** The physics-first framing, the
  document structure and the numbering discipline do not vary between documents.
- **"Strictly goes in our assets folder."** Internal analysis in `assets/`, never
  in `client-assets/`. Client-facing material is the docket only.
- **Verify against the file, then write.** Never cite from memory and check
  afterwards. Nearly every bad citation in this project came from that habit.
- **Extract and commit the session transcript at close, raw `.jsonl` included**,
  snapshot taken *after* the last exchange.
- **Independent adversarial audit** whenever I author both an artifact and its
  checker. Use a fresh agent instructed to *falsify*, not to confirm.
- **At 150K tokens in a chat, alert the owner and roll over to a new chat** — with
  the transcript, `CURRENT-STATE.md` and this file committed first.
- **Never `git checkout -- <file>` to undo a test mutation.** Copy to `/tmp`, or
  use the mutation driver's `--restore`.
- **Never `git add -A`.** Stage named files only, check with
  `--ignore-cr-at-eol`.

## Push required

`PUSH-TO-GITHUB.bat`, then confirm on the commits page. The command environment
cannot reach GitHub — `git push` and `git fetch` both fail HTTP 403 from the
proxy. Until it runs, everything is durable only on this disk, and the local
`origin/main` ref is not evidence of what the remote holds.
