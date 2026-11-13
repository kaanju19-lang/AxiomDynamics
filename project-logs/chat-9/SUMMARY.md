# Chat-9 — Summary

**When:** 2026-11-11 open, closed 2026-11-13. **Suite:** 359 → 370.
**Commits:** `0916bc0` (Stage 12 + stale gating claims), `e2bdf6d` (attestation
at entry), `fec966b` (Stage 13), plus this close.

Three rungs of a six-rung ladder landed. The other three are blocked on
something outside this repository, which is the fact chat-10 has to start from.

---

## 1. Stage 12, and an italics defect four chats old

The build history had no Stage 12 for chat-8. Adding it also surfaced a defect
in the **generator**: `inlineRuns()` and `PB()` both handled `**bold**` and
`` `code` ``, and **neither handled single-asterisk italics**. Fifteen italic
phrases across the document rendered as literal asterisks, including in stages
written four chats earlier.

It survived four rebuilds because there were **two near-identical tokenisers**
and the one with the gap was not the one every paragraph used. Replaced with a
single `tokenize()` handling three markers, ordered so the single-star pass
cannot eat a double-star pair. Two legacy `P()` calls were also converted.

That is the general shape worth carrying: a duplicated formatter is a defect
that hides from the check applied to the copy you happen to read.

## 2. Three documents still said entry was ungated

D00's F08 row, D09 §4.4's authentication row, and F09 Part 7 all still said
disposition entry was not gated. It has been gated since chat-6. Written to be
*honest about a gap*, they became false the moment the gap closed.

Each now states the gate and separates it from what remains open. `close-gate.sh`
greps for the old phrasing so the next occurrence trips the gate.

## 3. Attestation at entry — the last software half of B01 §7 item 1

The obvious design is impossible, and the three reasons are in the source:

- the registry stores the **16-hex `key_id`**, never the key;
- an attestation is an **HMAC the server must compute**;
- it covers `recorded_at`, `prev_hash`, `supersedes_id` — **none of which exist
  until the row is built**.

So a client cannot pre-compute one and the server cannot verify one without the
key. **The key is presented per request** in `X-Reviewer-Key` (base64) and the
attestation is written inside the ledger's own transaction.

Making the key the login credential was **rejected on a property**: it would put
the attestation secret in the session store and its backups, so a stolen session
could forge attestations — exactly what the mechanism exists to deny. Recorded
in D09 §8.4.2a.

### Two defects this exposed, both mine

**The demo became unusable.** `seed_demo_account.py` generated the reviewer key
and discarded it — correct before, fatal after. An operator could seed, sign in,
and have every write refused. Same shape as chat-8's "procedure naming a step
nobody can perform". `--key-file` now writes it 0600; the no-flag path warns.

**Three assertions were too loose to fail.** Six mutations, three survived the
first run, all three because the assertion matched the *wrong message*:

| Mutation | Why it survived |
|---|---|
| M19 route's key requirement removed | `"reviewer key"` also appears in the *unregistered-key* message |
| M20 route's `resolve_live_key` removed | the inner guard names both reviewers too |
| M22–M24 inner reviewer / revocation / certificate | every route test refused at the **early** check, so the inner layer was never reached |

**Two layers of one check cannot both be tested through the outer layer.** Three
direct `save_disposition` tests now reach the inner guard. All 24 mutations in
the driver are killed.

## 4. Verified end to end

Seed `--key-file` → 0600 key → sign in → write with key → 200 + `attested_by` →
`verify_attestations` ok → `verify_chain` ok → write **without** key → 401.
Mutation anchors checked to match their file exactly once, so none is a no-op.

## 5. What this does not claim

Item 1 stays **open**: a credential holder is not a person. Transport is plain
HTTP (item 10). The server holds the key in memory for one request. The export
signature is still symmetric (item 11).
