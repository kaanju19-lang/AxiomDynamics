# Chat-5 — Summary

Status: **closed 2026-11-11.** Handoff for the next session is
`project-logs/chat-6/CARRY-FORWARD.md`. Opened with the chat-4 carry-forward.

The owner's instruction for the whole session, given at the start: *"work from
Low → High progressively one at a time. When build is complete wrap all assets
and chat logs in our folder disk and we will shift to new chat-6."* That framed
five tasks, taken in the priority order `CURRENT-STATE.md` carries rather than
in order of difficulty — the earlier question *"are all the tasks numbered a low
medium complex tasks?"* had already established that the numbers are priority,
not effort, and this session is the proof. The second one is the largest thing
built here.

## Verification of inherited state (start of chat-5)

The carry-forward named 114 tests and one owner action. Both checked out, which
is the first time in five sessions a written push list was still accurate at the
next open. The CRLF trap was still present and still not a content change: `git
status` listed 27 files modified, `git diff --ignore-cr-at-eol` returned empty
for all but the real ones.

## Task 1 — D07 §14.5, governing law and venue

`e0ae738`. A counsel brief and a Phase 0 formation checklist, written so that a
lawyer is answering a specific question rather than being handed the problem.
The venue question is deliberately left **open** rather than guessed: it is a
counsel decision and the docket now says so in the place a reader will hit it
first.

## Task 2 — the independent ledger audit

`fa847a2`, record in `assets/ledger-audit-2026-11-11.md`. A fresh agent was
given the ledger, the export and the replication series and told to **falsify**
them. It found four defects, one of them critical: a rewritten chain verified
against a bundle already held, because the previous-bundle comparison checked
the slice it was given rather than the one it should have. Also a mid-chain
deletion invisible to the whole series, `INSERT OR REPLACE` defeating the
append-only triggers on the disposition table, and duplicate JSON keys reading
as two different records to two different parsers.

**One of the four was a false claim in a customer-facing document** — B01 §7 item
8 asserted a property the code did not have. That is the category of defect that
matters most in this project, because it is the one a customer could verify
against us and be right to complain.

## Task 3 — the detector ingest path

`7ea4a5c`, record in `assets/ingest-path-build-2026-11-11.md`. `POST /api/ingest`
applies the three-gate chain B02 §2 has specified since the flow map was drawn:
schema, then timestamp, then plausibility, refusing with a named reason or
holding as suspect. This narrows what D00 calls "the largest gap in this table" —
but does not close it. The schema is a demonstration schema, the endpoint has no
authentication, and no accepted reading is scored. **Building the validator did
not put a Railroad reading behind any number**, and the record says so in those
words rather than letting "ingest path built" imply otherwise.

## Task 4 — supply chain

`c401616`, record in `assets/supply-chain-build-2026-11-11.md`. Three tools:
`tools/sbom.py`, `tools/pin_requirements.py`, `tools/sign_release.py`. The
distinction this task turned on is the project's three-state discipline —
**absent, built, applied** — and all three are **built, none applied**. A
disclosed gap that is "built but not applied" is still a gap, and D09 §4.4 now
carries the state per control instead of collapsing them into one word.

## Task 5 — reviewer attribution (AD-2, part)

`2c2ee60`, record in `assets/attribution-build-2026-11-11.md`. The largest task
of the session and the one the owner explicitly delegated: asked which
attribution claim the Platform should be able to make, they answered *"unsure.
take your best approach for this build and i fully trust your experience and
expertise."*

`backend/attribution.py` adds a per-reviewer registry — append-only,
hash-chained, with `BEFORE UPDATE`/`BEFORE DELETE`/`INSERT OR REPLACE` refused —
and HMAC attestations over each disposition's `record_hash` that travel **inside
the exported record** rather than as a top-level block, because a top-level block
would fail `bundle_no_extras` and loosening that check would trade a security
property for layout. `attest()` refuses an unregistered key, a revoked key, a
key registered to a different reviewer, and a key registered under a different
certificate; `register()` refuses a key revoked anywhere in its history.

**The audit found nine defects after the suite was green, and one of them
justified the audit on its own.** The `reviewer` label in an exported
attestation was not covered by the HMAC — the message is
`axiom-attestation/v1:` plus the row hash, nothing else — so a holder of *any*
registered reviewer key could relabel another reviewer's row, re-sign the
bundle, and **both verifiers returned a pass**. That is the class of defect a
green suite cannot find, because the suite was written by the person who
believed the label was covered. The fix requires the verifier be told which
reviewer each key belongs to; the other eight are §4 of the build record.

## What the session as a whole shows

Five tasks, and **three of them ended with an audit finding something the
author's own tests could not**. Every session in this project has now had that
happen. The pattern is not that the code is careless; it is that *the person who
writes the claim writes the test that agrees with it*, and no amount of care
inside that loop breaks the loop. The standing rule — a fresh agent told to
falsify — is what has been doing the work.

The second thing worth carrying: **most of the corrections this session made were
to documents, not to code.** The registry was repeatedly called "signed" when it
is hash-chained; a customer document claimed a property the export did not have;
the revision card priced a registry as unbuilt that is now partly built. Code is
verifiable by running it. Prose is not, and prose that overstates a control is
worse than prose that undersells one.

## Commits

```
2c2ee60  Attribution: per-reviewer attestations over the disposition ledger (AD-2, part)
c401616  Build the supply-chain controls D09 §4.4 disclosed as gaps
7ea4a5c  Build the detector ingest path (B02 §2)
fa847a2  Close four audit findings; one was a false claim in a customer document
e0ae738  D07 §14.5 counsel brief and Phase 0 formation checklist
```

plus this session's transcript snapshot and handoff at close.
