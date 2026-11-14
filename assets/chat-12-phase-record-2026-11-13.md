# Chat-12 phase record — 2026-11-13

**Suite 398 → 402.** Three commits, all from two sweeps and the audit that broke
them. Nothing was built that moved a release gate.

---

## What the phase did

Chat-11 left a ladder of seven; five were blocked outside the repository. Chat-12
took the two that were not: **rung 3** (benchmark the two invented numbers) and
**rung 4** (sweep for false presence claims). The first produced a measurement
that corrected a decision paper's reasoning; the second produced one real defect;
a third sweep, on behavioural claims, produced a second.

| Commit | Effect |
|---|---|
| `70077a8` | Measured gpg signing cost; corrected the paper's disposition-rate claim from "invented" to "stated in B01 §6"; corrected D09 §5.2's admin-purge claim |
| `fe3a7c1` | Set WAL, which four docket statements had claimed since chat-3 and the code never did |
| `250dce8` | Nine repairs from the independent audit, including a fix `70077a8` claimed but did not make |

---

## The three findings worth carrying

**1. A commit message is a claim, and it can be false.** `70077a8` said the D09
termination sentence was corrected. It was not — the sentence sat three lines
below the paragraph announcing its removal, renumbered and unedited, still citing
D07 §15.5 as the authority for an obligation §15.5 does not contain. The commit
message asserted a fix the diff did not contain, and only an adversarial audit
found it. **The lesson is not "check your work" — it is that the commit message is
part of the artifact and needs the same verification as the diff.** A reader who
trusted the message would have shipped the contradiction.

**2. A measurement can be right and its explanation wrong, and the explanation is
what gets cited.** The benchmark reported 299.3 ms for a protected-key signature
and then said the cost was "gpg-agent plus pinentry startup, not key derivation."
The number reproduced on re-run; the sentence did not. The auditor isolated it to
iterated S2K three independent ways (stubbed pinentry moved it 18 ms; `--s2k-mode
0` is 4.5 ms against 326 ms at mode 3; agent CPU 420–456 ms while gpg itself used
0.00 s). **A wrong mechanism attached to a right number is more dangerous than a
wrong number, because the number survives checking and carries the explanation
with it.**

**3. The benchmark cleared the objection it was asked to clear and overturned the
conclusion it was asked to support.** The paper argued per-row signing was
unaffordable on latency. At 10.2 ms unprotected it is not unaffordable on latency
at all. What still rules per-row out is the structural point the paper made and
then did not lean on: `save_disposition` attests inside the write transaction, so
any signature there holds the SQLite write lock. **The recommendation stands; the
reason for it changed.** A decision paper whose conclusion survives on a different
argument from the one it gave is a paper that was right by accident.

---

## Defects found, all repaired

Docket:

- **D09 §5.2 promised a deletion capability the schema forbids** — "purge records
  via an admin interface or SQL". No admin interface exists and `BEFORE
  DELETE`/`UPDATE` triggers raise `ABORT`, so the SQL path does not exist either.
  A security addendum offering a deletion route the schema refuses is exactly what
  a rail auditor would find, and it would be fatal.
- **The same paragraph required database destruction on termination**, citing
  D07 §15.5, which contains no such term — and destruction would destroy the audit
  trail §4.5 exists to preserve.
- **F00 was misquoted** in the repair itself: F00 names the disposition ledger,
  the *order* register and the certification registry; the correction substituted
  the account register and attributed the list to F00.
- **"A deployment may purge detector traces"** was a fresh presence claim of the
  kind being removed — no purge path exists for those either.
- **WAL was claimed in four places** (B01 §4, B01 §5, B02's diagram, B01's ASCII
  architecture) and never set. `init_db()` on a fresh path reported
  `journal_mode=delete`; B01 §5's "edge box loses power: WAL recovers committed
  dispositions" was a benefit attributed to a mode the file was not in.

Code:

- `_configure()` sets `journal_mode=WAL`, `synchronous=FULL`, `busy_timeout=30s`
  on every ledger connection. **FULL, not NORMAL** — under WAL+NORMAL a power cut
  loses the most recent commit while leaving the file consistent, and the docket
  says committed audit records survive.
- `accounts._atomic` and `attribution._atomic` now pass `timeout=30`; they had
  been using sqlite3's 5 s default on the same file the ledger waited 30 s for, so
  the shorter fuse errored first under contention — the hole the WAL commit
  claimed to close.

Tests:

- `test_ledger_actually_runs_in_wal_mode` asserts the **property** — a reader
  succeeding while a writer holds `BEGIN IMMEDIATE` — not the pragma string, and
  fails for the right reason when the pragma is removed.
- `test_docket_currency.py` gained the opposite direction: a claim of **presence**
  the code does not support. Its first version was close to inert (see below).

---

## The audit, and why it is the part to keep

An independent agent was told to falsify the two commits. It found **nine
defects**, four material, in work that had a green suite of 400 behind it.

The worst three were all mine and all in the checker or the prose rather than the
code:

- **The presence guard's skip list searched for bare words** — "corrected",
  "previous", "does not" — and swallowed five realistic false claims, including
  one written *into a correction line*, which is precisely where a false claim
  would hide. It now skips only a phrase inside quotation marks, counted across
  line breaks because the real retraction wraps.
- **`_no_admin_purge_route` looked for two literal route names the author chose.**
  A route named `route_delete_dispositions` would have passed. It now looks for a
  `DELETE FROM dispositions` or a dropped trigger, with comments and strings
  stripped — and **its first run failed on the ledger's own comment explaining
  that `DROP TRIGGER` is possible**, which is the same lesson in miniature: a
  substring test reads prose as capability.
- **`_no_issued_gpg_key` globbed for a filename nothing in the project produces**,
  so it could never return False. It now inspects file contents for PGP private
  key material.

**A guard that cannot fail is worse than no guard, because it is cited.** All
three passed their own tests.

One defect was not repaired because it cannot be: `70077a8`'s message says "29
iterations" and both JSON files say 25. Corrected in the record, not rewritten.

---

## Master % Tracker at chat-12's close

Basis and per-row scoring unchanged: `assets/master-tracker-rubric-2026-11-13.md`.
Re-derived at this close from the files, not quoted from the open.

| Bucket | Weight | Chat-11 close | Chat-12 close | Δ |
|---|---|---|---|---|
| Docket documents (37) | 40 | 40.0 | 40.0 | — |
| B01 §7 gap rows (12) | 30 | 16.0 | 16.0 | — |
| Core software (8) | 20 | 20.0 | 20.0 | — |
| Release readiness (5) | 10 | 2.4 | 2.4 | — |
| **Total** | **100** | **78.4** | **78.4** | **—** |

**Zero movement for the second chat running, and it is the correct reading.**
Measuring a number, correcting a false claim and setting a pragma the docket
already promised are all real work. None of them moves a row from "built, not
applied" to "applied", which is the only transition this matrix scores.

**A caveat this phase makes worth stating:** the docket-documents bucket scores 37
documents existing, and chat-12 corrected **five distinct false claims across
three document classes** while that bucket sat still at 40.0/40. The rubric
measures existence, not accuracy, and a chat that spent its whole budget making
existing documents true would score zero movement. **That is a defect in the
rubric, not in the chat, and it should be considered before the next re-base** —
but changing a denominator in the same chat that scores well by changing it is the
error chat-10 was caught making, so it is recorded and not acted on.

---

## What chat-13 opens with

1. **The dashboard has never been seen by anyone.** *(low, owner)* Four chats now.
   `python3 -m backend.main`, then `http://127.0.0.1:8420/`. Also
   `frontend/render/panel.html`, committed 2026-11-13 with the note "not yet
   verified visually" — this environment has no renderer, confirmed twice.
2. **The `gnupg` / `dirmngr` decision.** *(low to decide, blocks the asymmetric
   build)* Unchanged by chat-12's benchmark. The measurement cleared the cost
   objection; the air-gap question is commercial and is the owner's.
3. **The rubric's existence-versus-accuracy gap.** *(low to decide)* See above.
   Recorded here, deliberately not acted on.
4. **Real detector payload schema** — blocked on the Railroad.
5. **Apply the supply-chain tools** — blocked on a release host and key custody.
6. **D07 §14.5 governing law** — counsel.

**Do not open chat-13 by assuming there is code to write.** Chat-12 found three
defects by grepping, which is cheap and repeatable, but three sweeps in one chat
is where a sweep starts finding what it is looking for. If a fourth is run, it
should be against a different class of claim — the remaining untested direction is
*documents disagreeing with each other*, which is where the D10 and D09 defects
both lived.
