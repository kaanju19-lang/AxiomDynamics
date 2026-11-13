# Asymmetric signatures: the decision, and the dependency it rests on

**Chat-11, 2026-11-13.** D10 / D09 §4.4. Decision paper, not a build.

**Status:** decided in principle, **not approved, not implemented.** Nothing in this paper changes code.

**Audited.** This paper was handed to a separate agent instructed to falsify it. It
found eight defects, four of them material: a misattributed quotation, an
overstated scope claim, wrong package arithmetic, and an overclaim about which
docket item closes. All four are corrected below and the corrections are marked,
because a decision paper that quietly reads as if it were right first time is
worth less than one that shows what it got wrong.

---

## The question

Three open items in the docket are the same defect wearing three hats:

- **B01 §7 item 1** — a credential holder is not a person. An HMAC proves *a key was used*, and anyone holding that key can produce the same proof.
- **B01 §7 item 11** — "export signing key **provenance**". The key has no trusted issuer behind it.
- **D09 §4.4 / D10 Part 5** — the signed key directory proves *the export-key holder authored these bindings*, not that they were entitled to.

The first two are usually run together, and this paper's first draft did exactly
that. **They are not the same question**, and separating them is most of the work
here.

A symmetric signature cannot name an author: everyone who can verify can also
produce. That is a fact about HMAC and an asymmetric signature fixes it. But
**provenance** — item 11's actual word — is a different property: it asks whether
the public key that verifies a signature reached the Railroad by a route they
trust. No signature scheme supplies that. It is supplied by key distribution and
custody, which is organisational work.

**So an asymmetric signature closes the "cannot name a signer" gaps. It does not
close item 11 as item 11 is worded.** It reduces item 11 to a distribution
problem, which is progress and is not closure. A reader who takes only one
sentence from this paper should take that one.

---

## What already exists — a code precedent, not an adoption

`tools/sign_release.py` signs a release archive with a **detached GPG
signature**, and verifies against a supplied public key rather than a local
trustdb: it imports the key into a throwaway `GNUPGHOME`, so verification does not
depend on the verifier's keyring state. That is a sound design and the right
precedent.

Its docstring states the principle, in these words:

> the Railroad's own security team already knows how to check `gpg --verify`, and a bespoke scheme would ask them to learn ours.

**A correction to this paper's first draft**, which quoted a different and more
polished sentence and attributed it to this file. That sentence is in
**D09 §7.3**, not in `sign_release.py`. The tool's own wording is the plainer one
above, and it is the one quoted here.

**What this is and is not.** It is a **code precedent**: a tested implementation
of the mechanism, 10 tests, and a verification story built around a tool the
customer already uses. It is **not an adoption**. B04 §7 says the control is
"Tool built, not applied … No GPG key exists and none is under custody, so
nothing has been signed", and D09 §7.3 repeats it. A tool that has never run and
has no key behind it has not adopted anything. Calling that "we already did
asymmetric crypto" would be the three-state collapse B04 §7 exists to prevent.

---

## The argument for scope: cost per signature

This is the number that decides how far to go, and it is **the weakest evidence in
the paper**. It is also load-bearing, so it is labelled as an estimate rather than
derived, and a reader should treat it as the thing to check first.

**Estimated, not measured:** an asymmetric operation via `gpg` is a
`subprocess.run` that starts a process, unlocks a secret key, computes and exits.
Something in the tens to low hundreds of milliseconds is plausible on a small edge
box. **This figure was invented for this paper.** It has not been benchmarked on
the target hardware, and the recommendation below should be re-checked against a
real measurement before any code is written.

What *is* derived from the repository:

| Where | Volume | Source | Verdict if the estimate holds |
|---|---|---|---|
| **Releases** | a handful per year | obvious | `gpg` — already built |
| **Export bundles** | **64 per year** per series: 12 monthly full + 52 weekly incremental | `ledger_replication.due_exports` | affordable; seconds per year |
| **Per-disposition attestations** | *assumed* low hundreds per day | **assumption — see below** | likely unaffordable in the write path |

**The disposition rate is an assumption, not a derivation.** No file in this
repository states one; the demo fleet generates synthetic signals and the demo
ledger is small. The paper's first draft called both volumes "derivable from what
is already built", which is true of the bundle count and false of this one. If the
real rate is tens per day rather than hundreds, the per-row verdict may flip, and
that is worth knowing before it is decided.

That said, the structural point does not depend on the number. `store.save_disposition`
calls `attest(conn, rec)` **after the INSERT and before COMMIT** — the attestation
is inside the SQLite transaction. **Any signing done there holds a write lock for
its duration**, whatever that duration is. A design that puts an external process
launch inside a database transaction is the thing to avoid on principle, not only
on measurement.

**So the scope splits:**

- **Per bundle** — once per export, outside any transaction, and the bundle is the artefact a recipient holds. Asymmetric signing here makes the export **name a signer**.
- **Per row** — inside a write transaction, on the hot path. **Stays HMAC.**

**What that does to item 1, stated plainly because the first draft overclaimed
it:** nothing. The bundle would be signed by a **bundle-signing key**, which is
neither the release key nor any reviewer's key. No reviewer key is involved in
signing a bundle. Row-level attestations inside it remain HMAC, and a holder of
reviewer A's key can still attest as A. **B01 §7 item 1 stays open**, because it
is a question about humans, which no signature scheme settles.

---

## The dependency decision — why this is a paper first

`gpg` is a system binary, not a Python package, and **it is not in the image**:
the `Dockerfile` contains no `apt-get` and no `gnupg`, and B04 §6 states "No
OS-level packages installed beyond the base image and numpy."

**A correction to the first draft on cost.** It said adding `gnupg` "costs one OS
package". That was wrong. On Debian slim, `gnupg` pulls roughly a dozen packages
— `dirmngr`, `gnupg-l10n`, `libassuan0`, `libgcrypt20`, `libksba8`, `libnpth0`,
`pinentry`, `gpgv` and their dependencies. And **`dirmngr` is a daemon that
performs network fetches on behalf of GPG.** Shipping it in an image whose entire
commercial proposition is "zero outbound network, verified against code" (B04 §5,
B05) is not a one-line change to a package list. It is a change to the air-gap
story.

**The code change is genuinely one line.** `python:3.11-slim` keeps `apt-get` and
`dpkg`; the Dockerfile simply never calls them. The first draft said "not a code
change you can make in one file", which was false and overstated the cost to argue
a case it had already made. The honest version: **one line of code, and a
paragraph of explanation to a CISO about why the box that fetches nothing now
contains a daemon that fetches things.**

**That is the product decision this paper is really asking for**, and it is the
owner's, not an engineer's.

| Option | Verifier needs | Image needs | Verdict |
|---|---|---|---|
| **A. `gpg` on both ends** | `gpg`, which a security team has | `gnupg` incl. `dirmngr` | **Preferred, conditional on accepting the above.** Keeps the verifier's story and reuses the tooling path already trusted |
| B. `cryptography` | `cryptography` installed | `cryptography` in the image | Rejected. Breaks the verifier's stdlib-only property and adds a second non-stdlib dependency to a product that advertises one |
| C. `PyNaCl` | `pynacl` installed | `pynacl` in the image | Rejected for the same reason |
| D. Hand-rolled Ed25519 | nothing | nothing | **Rejected outright.** In a product whose CISO-facing documents say it does not hand-roll crypto, this cannot be defended on any merits |

*(For the record, `cryptography` 50.0.2 is importable in this build environment.
Rejecting it is a decision about the shipped product's dependency story, not about
availability.)*

---

## A real contradiction found while checking this, which is more urgent than the paper

Checking whether `gpg` was available turned up something that needs fixing
independently of any decision here:

> **D10 Part 5, signed releases row:** "**The key is issued and published by Supplier**, and the signature proves authorship only to the extent the Railroad trusts the path the public key arrived by."
>
> **D09 §7.3:** "no key is issued and no release has been signed."
>
> **B04 §7:** "No GPG key exists and none is under custody, so nothing has been signed."

**D10 tells a client-facing reader, in the present tense, that a key exists. D09
and B04 say none does.** D10 is the register the security reviewer reads alongside
them, and it is the document that is wrong.

The first draft of this paper reported a *different and weaker* defect — that
D10's row does not say where the tool runs. That is also true, but it is
housekeeping. **The contradiction above is the one that would mislead**, and it is
the same failure shape chat-10 spent a day on: a document stating a state that the
code and the other documents deny. It should be corrected whether or not the
asymmetric build is ever approved.

---

## What a build would look like, if approved

Stated so the decision can be costed, not so it is pre-committed.

1. `backend/ledger_export.py` gains an optional detached signature over the canonical bundle bytes, written beside the bundle as `<bundle>.sig` plus the signer's public key. **The HMAC stays**, so an existing verifier does not break and a new one gains the signer's name.
2. `tools/verify_ledger_export.py` gains `--signature`, still importing nothing from `backend/`.
3. `Dockerfile` gains `gnupg`; B04 §6, D10 Part 2 and C01's prerequisites are corrected in the same commit, including an explanation of `dirmngr`.
4. A custody procedure for the bundle-signing key, as §8.4 already does for reviewer keys.

**It does not:** re-sign historical bundles, timestamp anything, or touch per-row attestations.

---

## Decision record

**Decided:** prefer Option A — detached GPG signatures over export bundles, verified with `gpg` — to close the *"cannot name a signer"* half of the export gap. Per-disposition attestations remain HMAC.

**Explicitly not claimed:** that this closes B01 §7 item 11. It reduces item 11 from a cryptography problem to a key-distribution problem. Item 1 is untouched.

**Requires the owner's decision:** accepting `gnupg`, and `dirmngr` with it, into an image whose selling point is that it talks to nothing. That is a commercial and architectural question.

**Before any code:** benchmark a `gpg` signature on target-class hardware, and establish the real disposition rate. Two numbers in this paper are invented and are labelled as such.

---

## What changes in the docket when this is accepted

Nothing yet. Docket edits follow the build, not the decision — a document that
says a thing is closed before it is would be the defect chat-10 spent a day
correcting.

**One exception, which should be done now regardless:** D10 Part 5's claim that
the key "is issued and published" contradicts D09 §7.3 and B04 §7 and must be
corrected on its own merits.
