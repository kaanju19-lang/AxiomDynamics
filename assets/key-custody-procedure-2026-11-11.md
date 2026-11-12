# AD-2 key custody and joiner/mover/leaver — 2026-11-11

Internal build record. Chat-8, phase two. The docket document is **D09 §8.4**;
this is why it says what it says and what writing it turned up.

## What was asked

B01 §7 item 1 has been open on "key custody and joiner/mover/leaver — a written
procedure, not code" since chat-6. Chat-7 narrowed it further with the signed
key directory. The instruction was to write the procedure.

## Where it went, and why not a new document

D09 is the security addendum and already had §4.5 for the **export** key's
custody. It also had §8.1–8.3 on access control, which were thin: 8.2 said
"the Railroad revokes their Platform access" and stopped. A reviewer credential
is the same class of problem as an export key, so the procedure belongs beside
the one the docket already carries. **§8.4, eight subsections.** No new document
and no new docket ID — adding an artifact for a procedure the security addendum
is the natural home for would have meant a new ID for content that belongs to an
existing one.

## What the section says

**8.4.1** separates the three credentials, because conflating them is how this
fails in practice: an account (passphrase, PBKDF2 verifier), a session token
(32 bytes, digest stored, transient), and a reviewer attestation key (32 raw
bytes, `key_id` published, key held). It says plainly that the attestation key
is not a password — losing it stops attesting, not signing in.

**8.4.2–8.4.5** are joiner, mover, leaver and rotation, each fixed in order
because each step depends on the one before. The joiner begins at a signed F08
and cannot begin anywhere else, since an account is bound to a certificate that
must already be live.

**8.4.4** is the load-bearing one. It splits the leaver path into what the
software does and what a person must do: revoking the certificate **immediately
stops every live session bound to it**, because `resolve_session` re-checks
liveness at each call; revoking the account and handling the key are manual.

**8.4.6** adds the custody log — the Railroad's human register, recording
`key_id` and never the key, which is the only record that ties a key to a person
rather than to a certificate.

**8.4.7** forbids using the export key as a reviewer key or the reverse.

**8.4.8** states the limits: a credential holder is not a person; the scheme is
symmetric; a demo cannot attest; and nothing but revocation is enforced by
software.

## What writing it turned up

**Two real defects, both found by trying to make the procedure's own sentences
true.** This is the part worth carrying: neither was found by a test, and one
had been in the code since chat-6 and survived a suite of 346 tests plus two
adversarial audits.

### 1. A key could be registered to a second reviewer, and the second one won

I wrote "`attribution.register` refuses a key already registered under a
different reviewer". Before publishing the sentence I ran it. It did not.

`register` refused only a key revoked *anywhere* in its history. A *live* key
presented under a different reviewer was accepted. Because `attest` resolves the
**newest** registry entry for a `key_id` — deliberately, so a certificate
renewal works — the second reviewer took the key over: they could attest rows
naming themselves, and the original reviewer was locked out of their own key.

The registry is append-only, so the bad binding **could never be removed**. The
key directory caught the conflict at publish time (`entries_consistent`), which
is far too late to be useful: the register is already poisoned.

Fixed in `register`, at the write. Verified against both sides:

| Case | Before | After |
|---|---|---|
| Same key, different reviewer | accepted, key hijacked | **refused** |
| Same key, same reviewer, same cert | accepted | accepted |
| Same key, same reviewer, **renewed** cert | accepted | accepted |

The second and third matter: renewal is the documented path in §8.4.5 and
`test_a_renewal_under_a_new_certificate_exports_the_new_certificate` depends on
it. My first attempt refused the renewal too, which would have broken rotation
to fix a sharing bug. The rule is about the **reviewer** changing, not the
certificate.

### 2. A refused key directory still handed back bindings

`key_directory.verify` returned `{"ok": False, "bindings": {"<key>": "Hoffman"}}`
for a directory it had just refused for naming one key two reviewers. The
refusal was true and the conflicted name was still on offer — anything that
checks `ok` late, or logs the bindings and carries on, took a name from a
document that had failed.

Fixed: a refused directory returns `{}`. Tested from both directions, so the fix
cannot empty the happy path.

### 3. The procedure named a tool that did not exist

§8.4.2 initially said to call `attribution.register(...)`. There was no way for
an operator to do that: the only code that created a reviewer key was
`tools/seed_demo_account.py`, and it **generates a key and discards it** — so on
a demo nobody holds a key and attestation can never happen (now disclosed in
§8.4.8 rather than left as a silent absence).

`tools/issue_reviewer_key.py` is the missing piece: generate, register, print
the `key_id`, never the key. It refuses to overwrite an existing key file,
because a key file is the only copy of a credential and the registry cannot be
repaired after the fact. **4 tests**, including that a refused registration
leaves no key file behind — bytes on disk that no registry entry names are how a
later run silently issues a second credential.

## Verification

Every mechanism claim in §8.4 was executed rather than reasoned about:

- A session issued, then its certificate revoked → the next resolve fails with
  *"the certification behind this session has been revoked"*.
- A revoked account cannot be re-enrolled under the same username, which is why
  §8.4.3 says a mover's account is **not** revoked.
- `attribution.revoke` and `accounts.revoke_account` both exist with those names.
- `ledger_export.py keygen` runs, writes mode 0600, and prints the `key_id` §4.5.1
  says it prints.
- The C01 command as written in the docket runs and issues a key.

Both new guards are mutation-tested: removing the reviewer guard fails exactly
`test_one_key_cannot_be_registered_to_a_second_reviewer`; restoring the leaked
bindings fails exactly `test_a_refused_directory_returns_no_bindings`.

Suite **351 → 359**: 2 attribution, 2 key-directory, 4 for the tool.

## Docket corrected in the same pass

B01 §10 (AD-2 bullet), §2 item 2, §7 item 1 (status cell and its closing
paragraph), B02 §2, C01 (new reviewer-credential block), C02 §5, D00 Part IV and
the AD-2 line, D09 §4.4 rows, and F08's preamble. Grep confirms no document
still claims the procedure is unwritten.

## Not closed, and the section says so

A credential holder is not a person; the HMAC scheme is symmetric; a demo cannot
attest; and every step except certificate revocation is performed by a human.
Writing the procedure makes the item **auditable** under D09 §10.1, which is a
real change — but it is not the same as closing it, and B01 §7 item 1 now says
exactly that rather than implying a document settles the matter.
