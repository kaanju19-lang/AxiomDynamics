# Signed, off-box ledger export — build record

**Date:** 2026-11-09 · **Phase 4 · AD-3 part two**
**Code:** `backend/ledger_export.py`, `tools/verify_ledger_export.py`, `tests/test_export.py`
**Internal — not for client distribution.** The client-facing statement of the same material is B01 §4.5/§4.5a, D09 §4.4/§4.5, F09 Part 7, and C01 §E2a.

---

## 1. What was open, in the words the docket already used

D09 §4.4, before this pass: *"No signed, off-box export of the disposition ledger … A party with write access to the database file could drop the triggers, rewrite rows and recompute the chain. A lost disk loses the ledger."*

Two separate failures were bundled in that row, and separating them is what made it buildable:

- **Provability.** `verify_chain()` runs on the host that holds the database. It cannot distinguish an untouched ledger from a re-hashed one, because it is the same party doing the checking. Nothing left the box.
- **Durability.** A disk loss destroys the ledger, and no amount of hashing changes that.

This phase closes the first and does not close the second. That is stated in the code, in four docket documents, and below — because the phase that "replicates off-box" is a deployment feature, not something a library function can deliver.

## 2. The decision that had to be made first, and why it went the way it did

The obvious reading of "signed export" is a digital signature: a private key signs, a published public key verifies, and the signature proves *who*. That is what D09 §7.3 promises for release artefacts (GPG, Q2 2027).

**It is not what was built, because it cannot honestly be built here.** Python's standard library ships HMAC but no Ed25519 and no RSA signing primitive. The options were:

| Option | Honest? | Cost |
|---|---|---|
| Add `cryptography` / `pynacl` | Yes | Breaks the single-dependency rule (`requirements.txt` = numpy), and adds a compiled dependency to an air-gapped install with nothing to verify it against |
| Hand-roll Ed25519 | **No** | A home-made curve implementation in a product that tells CISOs it does not hand-roll crypto is the exact defect class this project keeps correcting |
| HMAC-SHA256, symmetric, limits stated | Yes | Cannot prove *who*, cannot prove *when* |

**Third option taken.** HMAC is a real cryptographic signature over the bundle; it is unforgeable without the key; and it has two specific, nameable limits. Those limits are now in the documents rather than in a footnote, because the entire value of this project's disclosure discipline is that a limit written down in advance is survivable and a limit discovered by a customer is not.

The upgrade path is registered as B01 §7 item 11, dependent on AD-2 and on a vetted asymmetric library. It is not a thing forgotten.

## 3. What was built

**`backend/ledger_export.py`** — build and verify.

- `build_bundle(key, from_id, to_id, after_id, previous_export_hash)` reads the slice under a single connection, computes the whole-ledger chain status, computes slice-local chain status independently, and signs `{format, manifest, records}`.
- The **manifest** carries: `exported_at`, database basename, schema version, `from_id`/`to_id`, `record_count`, `first_id`/`last_id`, `first_prev_hash`, `head_hash`, genesis hash, hash and signature algorithms, **the exact covered-field list**, **the canonicalisation rule**, the whole-ledger chain result, the slice result, and `previous_export_hash`.
- **The covered-field list and canonicalisation rule travel inside the signed manifest.** A verifier therefore reads the rule out of the bundle rather than trusting a document that might describe an older version. If the rule changes, the bundle says so, and an older verifier refuses on `format`.
- CLI: `keygen`, `export`, `verify`. `keygen` refuses to overwrite an existing key without `--force`, because silently replacing a signing key invalidates every bundle already issued.

**`tools/verify_ledger_export.py`** — the recipient's tool. Roughly 150 lines, stdlib only, and **imports nothing from `backend/`**. That is a tested property, not a claim: `test_standalone_verifier_runs_without_the_database_present` greps the source for `sqlite3`, `from backend`, `import backend` and `AXIOM_DB_PATH` and fails if any appears. It runs from an empty working directory under `-I` with no database.

**Thirteen checks**, all of which run — no short-circuit, so a recipient sees the whole picture rather than the first break: `format`, `signature_algorithm`, `key_id`, `signature`, `record_count`, `first_id`, `last_id`, `id_order`, `range_from`, `range_to`, `row_hashes`, `prev_hash_links`, `head_hash`, `genesis_hash`, `ledger_chain_ok`, and with `--previous-bundle`, `previous_export_link` and `no_regression`.

## 4. The design point that makes this different from a checksum

**`id` is not covered by the row hash.** That was true before this phase and was undocumented. `_row_payload()` covers `advisory_id, reviewer_name, cert_id, disposition, note, recorded_at, supersedes_id, prev_hash` — eight fields, not `id`, not `record_hash`.

The consequence is precise and was tested rather than reasoned about: **swapping two ids inside a bundle leaves every row hash valid** and is caught only by the export signature. A bundle that relied only on per-row hashes would pass a "verify the hashes" check on a bundle with relabelled records. `test_relabelled_id_within_the_bundle_breaks_the_signature` asserts both halves — that the signature fails *and* that `row_hashes` still passes — so the test records the weakness at the same time as the control.

The manifest additionally pins `first_id`, `last_id`, `record_count`, strictly increasing ids and the declared range, so a record cannot be moved across the bundle boundary unnoticed even before the signature is checked.

## 5. Chaining, which is what actually closes the rewrite case

A single bundle cannot detect a ledger that was rewritten *before* the export. An attacker with file access drops the triggers, rewrites every row, recomputes every hash; the host then sees a consistent ledger and signs a consistent bundle. `test_wholly_rewritten_ledger_exports_a_fine_bundle__disclosed_limit` performs exactly this attack and asserts that verification **passes** — a test that asserts a defective outcome on purpose, because the alternative is a caveat somewhere nobody reads.

What closes it is sequence. `signature_of(bundle)` digests the whole bundle including its signature; the next bundle carries that digest as `previous_export_hash`. If the ledger is rewritten between two exports, the next bundle either fails to extend the one the recipient holds, or does not claim to — and `previous_export_link` fails. The attacker cannot fix this by rewriting the ledger, because the digest the recipient holds lives on the recipient's machine.

### 5.1 The first version of this was wrong, and the audit found it

**Every claim in §4–§6 above was written before this section, and the first shipped version of the chaining did not work.** It is worth recording precisely, because the failure is instructive rather than embarrassing.

The attack is nine lines and needs no key: drop the delete trigger, `DELETE FROM dispositions`, then run the honest exporter with `--previous-export-hash`. What happened:

- `verify_chain()` truthfully reported `{"ok": True, "rows": 0}` — an empty ledger is a valid chain.
- The empty bundle was signed honestly.
- `no_regression` short-circuited: `m.get("first_id") is None or previous_bundle[...]["last_id"] is None or ...` — with no records there is no `first_id`, so the whole condition was `True`.
- The recipient was told **every check passed**, while five records of history they had been given had been destroyed.

The cause is a class of bug this project keeps meeting: **every check was individually correct and the combination proved nothing.** Each check asked "is this bundle self-consistent?" and none asked "is this bundle consistent with what the recipient already has?" The empty case is where the omitted question bites, because an empty bundle is trivially self-consistent.

I wrote the tests, they passed, and the tests could not have caught it — I had not thought of the attack, so I had not written it. The independent audit, prompted to *falsify* rather than confirm, found it in one pass.

### 5.2 The fix

Two additions, both mirrored in both verifiers:

- **`backend_head_id` / `backend_head_hash` in the manifest.** The database reports its own last row, independent of the slice. A later bundle must not report a shorter ledger than one already held — the `no_truncation` check.
- **`genesis_anchor`.** An unbounded (full) export must begin at the genesis hash. Without it, an attacker deletes rows from the front and exports "honestly" from row 5; every other check passes forever because nothing ties an unbounded export to the beginning.

Plus three narrower fixes the same audit produced: `empty_bundle_justified` (an empty slice is legitimate only when the ledger is empty or the slice is bounded from below), an inverted-range guard so `--after-id` past the end raises instead of signing an empty export, and the zero-record incremental path — **which was broken by the first fix and caught by the test written for it.** A quiet week produced a bundle that failed `range_from`. D09 §4.5.4 requires a weekly export, so the documented procedure failed on every quiet week until that was corrected.

**What remains undetectable, and is now documented as such:** a clean deletion of the newest rows leaves a valid chain and the host truthfully reports a shorter ledger. Nothing in a single bundle can see it. It takes a bundle already held — which is why D09 §4.5.4 makes retention a control and §4.5.5 states plainly that a first bundle after a wipe testifies to nothing about its own past.

**This makes bundle retention a security control, not archiving.** D09 §4.5.4 now says so explicitly, and says what forfeits it: overwriting last month's bundle with this month's.

## 6. What was deliberately not built

**No HTTP export route.** The server has no authentication (AD-2 unbuilt). An unauthenticated `GET /api/ledger/export` returning every disposition with reviewer name and cert ID would widen the data-handling surface in the act of closing an integrity gap. Export is an operator CLI action on the box; C01 §E2a documents it as a commissioning step. It becomes a route when an authenticated administrator session means something.

**No automatic replication.** Not implementable as a library function — it is a second host, a scheduler and a receipt. Recorded as B01 §7 item 12 and D09 §4.4, target Q2 2027. The export gives replication something worth replicating; it does not perform it.

**No asymmetric signature.** Section 2.

## 7. Verification

- **42 export tests**, all passing, in `tests/test_export.py`. Full suite 80 (21 physics + 17 ledger + 42 export), `python3 -I tests/run_tests.py`.
- **Tamper cases covered:** edited note, disposition, timestamp and reviewer; swapped ids within the bundle; removed middle record; truncated tail; added forged record with correct hashes and updated manifest; reordered records; inflated record count; tampered manifest; swapped signature value; stripped signature block; unknown format version.
- **Erasure cases covered** (added after the audit): total wipe detected when chained; head rows deleted detected by the genesis anchor; clean tail deletion asserted as a disclosed limit when unchained but caught when chained; zero-record incremental verified by both implementations; inverted range refused; malformed bundles returning verdicts rather than tracebacks.
- **Key cases:** wrong key is reported as `key_id` mismatch with a readable message rather than a bare signature failure; short key file is refused rather than hashed and used; `keygen` refuses to clobber; `keygen --force` leaves the key at 0600 (it did not before — `os.open`'s mode argument is ignored for an existing file).
- **Cross-implementation agreement:** the standalone tool checks `genesis_hash` too, and `test_standalone_verifier_and_backend_agree_on_genesis_hash` plus `..._on_every_case` assert the two never diverge. They did diverge before the audit on that one field.
- **End-to-end on a live server**, not just unit tests: started `backend.main` against a throwaway database, recorded three dispositions through `POST /api/warrant/{id}/disposition` including a genuine supersede, confirmed `/api/ledger/verify` returned `{ok: true, rows: 3}`, generated a key, exported, and verified the bundle from a **different working directory with `-I`** using only the standalone tool. All checks passed.
- **The erasure attack re-run against the fixed standalone tool:** deleted every row, exported chained — `FAIL no_truncation — the ledger has SHRUNK since the bundle you hold: this export ends at id None, the previous one ended at id 4. Records have been removed.` Exit 1.
- **`.gitignore` extended** for `*.key`, `signer.key` and `ledger-export*.json*`. A committed signing key makes every bundle it signed forgeable by anyone who can read the repo, which inverts the control.

## 8. Docket amended in the same commit

The rule is that a gap closes only when the code changes and the disclosing documents change with it.

- **B01** §4.5 rewritten (built); **new §4.5a** stating what the signature does and does not prove, in the form a CISO reads; §4 last paragraph rewritten; §7 item 8 rewritten and **items 11 and 12 added** (key provenance, replication); the closing paragraph of §7 rewritten.
- **D09** §4.4: the single "no signed, off-box export" row split into two accurate rows — signature cannot name the signer, and no automatic replication. §4.2 audit-logging row rewritten. **New §4.5** custody procedure (key handling, `key_id`, rotation, export schedule, what a receipt establishes, what to do on a verification failure). §5.3 notes retained bundles are not deleted with the host. §6.2 makes key compromise and a failed verification reportable incidents. §7.3 scoped explicitly to software releases so "every artefact is unsigned" does not read as contradicting §4.5.
- **F09** Part 7: third disclosure added — verifiable bundle is not a certificate of authorship; footer rewritten.
- **F13** Part 4: bundle fields, `key_id` row, customer-side verification on a disconnected machine, and a note on what the pass does not establish.
- **B02** §175 rewritten from "not yet signed" to built-with-limits.
- **C01** new **§E2a** commissioning procedure: keygen, record `key_id`, baseline export, verify elsewhere, keep every bundle.
- **D00** Part V: gap row replaced; "architectural decisions locked" paragraph corrected; closure note added explaining why the row was rewritten rather than deleted.
- **Root README**: file tree, test count, next-steps list; `backend/store.py` docstring.

## 9. What is still open

1. **Key provenance** is a written procedure, not a cryptographic fact, until AD-2 binds the key to an issued certification record — B01 §7 item 11.
2. **Automatic replication** to a second host with receipt — item 12.
3. **The A2/D08 model decision**, deferred by the owner on 2026-11-09. Unchanged by this phase; the two are independent.
4. **D07 §14.5** governing law and venue — counsel decision, unchanged.
5. **D09 §4.4** SBOM, dependency hash pinning, GPG release signing — unchanged.

## 10. The thing worth remembering

Two things, and the second is the one that cost something.

**The failure mode this project keeps having is a document claiming more than the code delivers.** The new risk introduced by this phase is the mirror image: code that delivers something real, described in a way that sounds like it delivers more. HMAC is a genuine signature and a reviewer who hears "signed" will assume attribution until told otherwise. That is why §4.5a of B01 exists as its own section rather than as a sentence inside §4.5, and why two tests assert that verification *succeeds* on attacks that succeeded. A limitation you have written a test for is a design decision. One you have only mentioned is a defect waiting for a customer.

**The first version of the chaining did not work, and my own tests could not have caught it.** Every check was individually correct: content hashes valid, ids ordered, count matching, signature good. None of them asked whether the bundle agreed with one the recipient already had, and the empty-bundle case — where a total wipe produces a trivially self-consistent export — is exactly where that omitted question decides the answer. The tests passed because I wrote tests for the attacks I had thought of, and I had not thought of that one.

The lesson is narrower than "test more". It is that **a suite written by the author of a mechanism tests the author's model of the threat, not the threat.** For anything that makes a security claim, the falsification has to come from outside — a fresh reader prompted to break it, not to check it. That is now a standing rule for this project, recorded in memory, and it has earned its cost twice.
