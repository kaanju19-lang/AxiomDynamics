# Signed reviewer key directory (2026-11-11, chat-7)

**The gap.** Chat-5 and chat-6 built per-reviewer HMAC attestations that travel
inside exported records, and an independent audit established that the
`reviewer` label in an attestation is **not covered by the HMAC** — the signed
message is the row's `record_hash`, not the name. What catches a key holder
relabelling their own attestation with somebody else's name is that the
verifier is told which reviewer each key belongs to and compares. Until now
that knowledge was a command-line argument: `--reviewer-key KEYID=NAME:path`.
A recipient who was not told the name could not check the label at all; a
recipient told the wrong name would either pass a forgery or fail an honest
bundle with no way to tell which had happened.

**What was built.**

- `backend/key_directory.py` — builds the binding list from the reviewer
  registry (reviewer, cert_id, key_id, registered_at, revoked_at per entry,
  including revocation history), signs it with the export key over a canonical
  JSON body, and verifies it: exact top-level field set, format, signature,
  per-entry field completeness, one-key-one-reviewer consistency, and whether
  any live binding remains.
- `tools/publish_key_directory.py` — the Platform-side builder. It refuses to
  publish if the registry chain does not verify.
- `tools/verify_key_directory.py` — the recipient-side verifier, importing
  nothing from `backend/`, same rule as the release verifier. It emits
  `KEY_ID=REVIEWER:` fragments ready for `verify_ledger_export.py`, so the
  recipient never types a name.
- `tests/test_key_directory.py` — 14 tests.

**It deliberately carries no key material.** A `key_id` is the first 16 hex of
the key's SHA-256; publishing it lets a recipient match a key they hold to a
name without revealing anything that would let anyone forge an attestation.

**The consistency check is the load-bearing one and it is not the signature.**
The directory's signature is symmetric — whoever can verify it can also sign
one. So the test that matters most forges a directory the attacker signs
themselves: one `key_id` attached to a second reviewer name, then re-signs it
so the signature passes. It is still refused, by `entries_consistent`, because
one key cannot name two reviewers. **A signature proves who wrote the file; the
consistency check constrains what the file is allowed to say.** The first is
weaker than it looks here, which is why the second exists.

**What it does and does not establish, stated flatly.** It establishes that the
holder of the export key authored this list of bindings. It does **not**
establish that they were entitled to — that is B01 §7 item 11, the asymmetric
signature with a published public key, still open. It says nothing about
whether a reviewer was at a keyboard. Because the scheme is symmetric, a
recipient holding the export key could produce their own directory; the
protection is meaningful for the normal case of a recipient who does not hold
it. The improvement over a name typed on a command line is real and bounded.

**Tests that carried the weight.** A relabelled binding breaks the signature;
an added top-level field is refused (`directory_no_extras`, the same lesson as
`bundle_no_extras`); a missing field is refused; a revoked binding drops out of
the live set and a directory with no live binding refuses to report a pass; the
registry's own UPDATE trigger stopped the first attempt to tamper the chain in
a test and forced the test to attack by forged append instead — the control
catching the test is worth recording; and the standalone verifier agrees with
the in-repo one on both an honest and a tampered directory.

Suite 326 → 340.

## Files

- `backend/key_directory.py` (new)
- `tools/publish_key_directory.py` (new)
- `tools/verify_key_directory.py` (new)
- `tests/test_key_directory.py` (new, 14 tests)
- `client-assets/MASTER-BRIEF-DOCKET/B01-SYSTEM-BLUEPRINT-AND-ARCHITECTURE.md`
  §7 item 1, and `D09` §4.5.5.
