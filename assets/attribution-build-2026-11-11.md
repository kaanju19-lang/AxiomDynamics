# Reviewer Attribution — Build Record, 2026-11-11 (chat-5)

**Docket position:** none directly. This closes the *attribution* half of
B01 §7 item 1 (AD-2) and the disposition half of D09 §4.4's signer row.
**Internal — not for customer distribution.**

**Companion documents:** B01 §4.5, §4.5a and §7 items 1 and 11–12; D09 §4.4,
§4.5.5; D00 Part VI; `backend/attribution.py`, `backend/ledger_export.py`,
`tools/verify_ledger_export.py`, `tests/test_attribution.py`.

---

## 1. What was open, exactly

D09 §4.4 has carried one row since the export was built: *"The ledger export
signature cannot name the signer."* Three different things were bundled in that
sentence and they have different answers:

| Question | Answer before | Answer now |
|---|---|---|
| Which reviewer decided this row? | Nothing. Free text in a hash. | **Verifiable.** A registered key attests the row's `record_hash`. |
| Who exported this bundle? | Nothing. HMAC is symmetric. | **Nothing.** Unchanged, and it is not what this build set out to close. |
| When was anything signed? | Nothing. | **Nothing.** No timestamping authority exists on an air-gapped box. |

Collapsing those three into "attribution is unbuilt" is why the item sat for two
sessions looking larger than it was. Splitting them made the first answerable
and left the other two honestly open.

## 2. The design, and the alternative that was rejected

**Per-reviewer HMAC keys, an append-only hash-chained registry, and attestations
that travel inside exported records.**

Two decisions are worth arguing about.

**Symmetric keys rather than Ed25519.** AD-2 as specified in B01 calls for a
signed certification registry, and the obvious reading is an asymmetric scheme.
There is no vetted Ed25519 implementation in this deployment's dependency set,
and hand-rolling curve arithmetic in a product whose pitch includes *"we do not
hand-roll crypto"* is a worse gap than a symmetric attestation whose limits are
written down. The algorithm here is the HMAC the export already uses and already
trusts; what is new is that the key is per-reviewer and that the identity is
registered. The cost is stated in the module docstring and in D09 §4.4: a holder
of reviewer A's key can attest as A, so the claim is *"A's key was used"*, and
custody under §4.5 is what binds that key to A.

**Attribution inside each record, not as a top-level bundle block.** A top-level
`attribution` field would have failed `bundle_no_extras` in both verifiers —
the check that exists because before 2026-11-10 an added top-level key rode
along **unsigned**. The tidier shape would have required loosening that check,
which is trading a security property for layout. Inside `records`, the block is
covered by the bundle signature automatically, and `row_hash()` ignores it
because `row_hash()` selects `COVERED_FIELDS` by name — so adding attribution
did not change a single `record_hash` and did not invalidate any existing chain.

Storage is beside the ledger, in its own tables. No migration of `dispositions`,
no change to the write path, and an attestation cannot alter what the row hashes.

## 3. Five defects found while building, four of them by writing the tests

This is the part of the record that matters, because each of these was invisible
to reading the code.

**3.1 `attest()` accepted a certificate mismatch that the verifier rejects.** The
first draft checked reviewer name but not `cert_id`. The verifier checked both.
So a key could record an attestation that no verifier would ever accept —
producing a bundle that fails for the recipient and passes on the machine that
made it, which is the worst possible direction for a control to disagree with
itself. Found by a test that registered Hoffman on one certificate and attested a
row recorded under another. `attest()` now refuses with a message naming both.

**3.2 `registered_at` was not in the registry entry hash.** The DDL supplied it by
default and the in-memory entry never held it. Two consequences: `register()`
returned a dict without the field at all, and — more seriously — the registration
date was outside the chain, so a host owner who dropped the update trigger could
shift it. The registration date is the boundary the ordering check compares
`attested_at` against; a date the hash does not cover is a date that can be moved
to make a backdated attestation plausible. Now produced in code, hashed, and
covered by a test that shifts it and expects the chain to break.

**3.3 `verify_attestations`' revocation check could never fire.** A revoked key has
two registry entries — the registration and the revocation. The function kept
only the first (correctly, for `registered_at`) and then read `revoked_at` off
that same entry, whose `revoked_at` is null by definition. The branch was dead
code that read as a control. Now the registration and the revocation are tracked
separately, and a test rewrites a row's `recorded_at` past the revocation and
expects the row to be named. **This one was found by mutation testing, not by
reading, and it is the clearest argument for mutation testing in the record so
far.**

**3.4 `ATTESTATIONS` had no `INSERT OR REPLACE` guard.** SQLite does not fire a
`BEFORE DELETE` trigger for `INSERT OR REPLACE` unless `recursive_triggers` is
on. The registry table had the guard; the attestations table did not, so an
attestation could be overwritten in place while all three of its triggers read as
present. Found by writing the test, which is exactly the order the supply-chain
pass recommended.

**3.5 The export reported a revocation entry's `registered_at` as the
registration.** When a key had been revoked, `attribution_for_export` took the
newest registry entry, which is the revocation — so the exported `registered_at`
was the moment of revocation. Every honest attestation made before it would then
fail the ordering check. Caught by the export test, and it is the reason that
test asserts on the function rather than on a bundle: the two timestamps land in
the same second on a fast test box, so a bundle-level assertion could pass
either way.

## 4. The independent audit, and what it broke

Everything above was written by the same person who wrote the code it describes,
which is the arrangement that misses its own mistakes. So before the section was
called done, a fresh agent was given the three files and one instruction: **try
to falsify this.** Not review it — break it. It was told the design claim was
that an attestation binds a reviewer to a row, and told to prove that false.

It found nine things. Eight were real defects and one was a documentation error
that misstated the trust model. Every one is now a test.

**4.1 The `reviewer` field in the exported block was decorative.** This is the
finding that justified the audit on its own. The HMAC covers
`axiom-attestation/v1:` plus the row's `record_hash` — one 64-character string,
nothing else. So the block's `reviewer` label was not covered by anything. A
holder of **any** registered reviewer key could take a row that names somebody
else, compute a perfectly valid attestation with their own key, write the other
reviewer's name into the block, re-sign the bundle with the export key (which
the attacker holds in this scenario, since the threat model for the structural
checks includes an insider holding it), and **both verifiers returned `ok:
true`**.

The fix is that the verifier must be *told* which reviewer each key belongs to.
`reviewer_keys` changed from `{key_id: key_bytes}` to
`{key_id: (key_bytes, reviewer_name)}` in both verifiers, and a block whose
label disagrees with the name bound to the supplied key is now an
`attribution_consistent` failure. The alternative — hashing the reviewer name
into the attestation message — was rejected because it makes the attestation
non-transferable: the recipient would have to be told the name to recompute it,
which is the same problem one step later. Supplying the name out of band is what
a key directory is for, and it belongs in the caller's hands.

**4.2 Deleting a field disabled the ordering checks.** Every time comparison was
guarded with truthiness — `if a.get("revoked_at") and ...`. Delete
`registered_at` from the block and the check silently does not run. A re-signed
bundle then verified clean for a recipient holding no reviewer keys, which is
the ordinary recipient. Fixed with `REQUIRED_ATTRIBUTION_FIELDS`: **absence is a
failure, not a skip.** The audit's point was sharp — the code was written to
tolerate the shape it produced, and never considered the shape an attacker
would.

**4.3 A fabricated attribution is indistinguishable to a keyless recipient.**
Not a bug; a limit I had not stated. With no reviewer key supplied, the
structural checks pass on any internally consistent block, because HMAC is
symmetric and there is nothing to verify without the secret. The honest position
is to say so, so a test now asserts the limit in both directions and §5 below
reads differently as a result.

**4.4 `attest()` had a check-then-write race.** It read the registry on one
connection and wrote the attestation on another. A `revoke()` landing in between
produced an attestation recorded *after* the revocation existed — precisely the
outcome the refusal exists to prevent, arrived at without the refusal firing.
Found by a two-thread repro, not by a test. Fixed by re-checking the revocation
and the registry entry under the write lock, with a test that monkeypatches
`_atomic` to fire `revoke()` exactly once mid-write.

**4.5 `attest` and `attribution_for_export` disagreed about which entry is
"the" registration.** After a certificate renewal a key had two non-revocation
entries; `attest` took the newest and the export took the first. An honest
attestation therefore exported under the *superseded* certificate and failed the
verifier's cert check at the recipient — green on the machine that made it,
red on the machine that received it. This is the same failure shape as §3.1,
which means §3.1's fix was local and the pattern was not. Both sides now take
the newest non-revocation entry, and a test renews a certificate and asserts the
export reports the new one.

**4.6 Malformed blocks raised `AttributeError` instead of a named failure.** A
block whose `attestation` was an integer, or whose key map lookup hit a
non-string, crashed the verifier rather than producing a `check` entry. A
verifier that raises is a verifier whose output a caller cannot parse, and
"crashed" is not a verdict. Fixed with type checks ahead of every comparison and
a `try/except TypeError` around the key-map lookup.

**4.7 The module docstring said the registry was "signed by the registry key".**
There is no registry key. The registry is hash-chained and append-only, which
makes entries *tamper-evident* to someone who recomputes the chain — it does not
make them *authentic* to someone who does not already trust the database. The
sentence was wrong in the direction of claiming more than exists, and was
corrected with the consequence stated.

**4.8 The standalone verifier's revocation branch was unguarded.** A mutation
that disabled only `tools/verify_ledger_export.py`'s revocation ordering check
left the suite **green**, because the tests for that branch exercised the backend
verifier only. The parity test exists precisely to catch divergence between the
two, and it did not cover this branch. Added to the parity table.

**4.9 A revocation could be undone by re-registering the same key bytes.** The
refusal was in `attest()`, which is the wrong layer — by the time you are
attesting, the damage is a bad registry, not a bad attestation. `register()` now
refuses a key with a revocation anywhere in its history. Note this was found a
different way: the mutation for the `attest()` check **survived**, and asking why
it survived showed the check was dead duplicate code, because the in-lock query
already scanned the full history. The guard that was doing the work was in a
different function from the one that read as the guard.

## 5. Verification performed

- **Suite 180 → 238, all green.** `tests/test_attribution.py` contributes 58.
- **40 mutations, 40 killed, 0 survived, 0 skipped.** The first pass left eight
  survivors; three were bad mutations of my own (renaming a trigger does not
  disable it), and five were genuine test gaps: the registry chain's `prev_hash`
  direction, the registration date's presence in the hash, the dead revocation
  branch, the exporter's unreported-key check, and the standalone verifier's
  structural checks. Each now has a test that goes red without its guard.
- **Every survivor was investigated, not just patched.** Two turned out to be
  code that was not doing what it read as doing (§4.9 above, and `active_key_for`
  reporting a revoked key as active, which had no caller and now has a test).
- **Two tests initially passed for the wrong reason and were fixed.** A tamper
  test was being caught by the bundle signature rather than by the structural
  check, so it proved nothing about attribution — it now re-signs after
  tampering, which models the attacker who holds the export key and is the only
  attacker the structural checks are for. And a test called `le.sign(b, KEY)`
  expecting it to mutate; `sign()` returns a copy.
- **A guard fired on my own comment.** `test_standalone_verifier_runs_without_the
  _database_present` scans the standalone verifier's source for `from backend`,
  and my new comment said `backend/ledger_export.py`. The guard is right — a
  substring scan is crude but the property it protects is real — so the comment
  was reworded rather than the guard relaxed.

## 6. What a recipient can and cannot conclude

A bundle carrying attribution, verified by `tools/verify_ledger_export.py` with
the reviewer's key supplied **and the reviewer's name bound to that key**,
establishes that the attestation recomputes under that key over that row's
`record_hash`, and that the row names the same reviewer and certificate the
attestation block does. Without the key it establishes the consistency half only,
and the verifier says so rather than claiming a check it did not run —
`attestations_verified` appears only when keys were supplied.

**The name binding is not optional in practice.** A verifier told the key
belongs to Hoffman will reject a block labelled Okafor. A verifier given the
key alone, with no name, checks the HMAC and reports that it could not check the
identity. Supplying a key with no name is a weaker check and the tool warns
rather than pretending otherwise.

It does not establish that a human being was at the keyboard. It does not
establish that the reviewer's key was not shared or stolen. It does not name the
export signer. It does not date anything. **A keyless recipient cannot tell an
honest attribution from a fabricated one** — that is the disclosure §4.3 forced,
and it is the reason the reviewer key directory is a real deliverable rather
than a convenience. **An unattested row is not a failure** — it is a decision
nobody has attested, and the manifest counts how many there are so the recipient
can see the difference between "all attested" and "one of forty".

## 7. The lessons this pass adds

**A control that records what its own checker rejects is worse than no control,
because the operator sees green.** §3.1 is the general shape: writer and checker
each had a guard, the guards disagreed about which field mattered, and the
disagreement was invisible until a bundle crossed machines. §4.5 is the same
shape a second time, which is the part worth remembering — fixing an instance of
a bug class does not fix the class. The parity test — structural tampers, each
asserted caught by both verifiers on the same check — exists to make that class
of disagreement fail loudly in CI instead of quietly at a regulator.

**A branch that reads as a control can be unreachable for a reason invisible in
the branch itself.** §3.3's `elif entry["revoked_at"] and ...` looks correct at
the point of writing and on every reading afterwards. Only driving it with data
found it. And §4.9 shows the mirror image: a check that reads as the control can
be redundant because a different one is doing the work, which is just as
misleading in the other direction.

**If the same person writes the artifact and its checker, the checker agrees
with the artifact.** §4.1 is what that costs: a design I had explained to myself
three times in three documents, where the central field was not covered by
anything, and every test I wrote passed because I wrote the tests around my own
reading. The audit did not read the design; it tried to break the claim. That is
a different activity and it found different things.

---

*Internal. Review when session-bound disposition entry is built (the remaining
AD-2 work), when the export key gains an identity, or when a bundle carrying
attribution first ships.*
