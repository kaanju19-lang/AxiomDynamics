# Supply Chain — Build Record, 2026-11-11 (chat-5)

**Docket position:** None. **Internal — not for customer distribution.**

**Companion documents:** D09 §4.4, §7.2, §7.3 (the promises), D10 Parts 2 and 5
(the register), C01 Part C2 (the sealed archive), `tools/sbom.py`,
`tools/pin_requirements.py`, `tools/sign_release.py`.

---

## 1. What was open, and what "open" meant

D09 §4.4 carried three rows with 2027 targets: no SBOM in releases, no hash
pinning of dependency downloads, no signed release artefacts. All three are now
built as tools. **Two are not yet applied, and this document is mostly about that
distinction**, because the project has already been burned once by reading
"built" as "done" — B01 §4.5a item 1 promised rewrite-detection that did not
exist, and the sentence survived three audits.

| Control | Tool | Applied? |
|---|---|---|
| SBOM | `tools/sbom.py` | **No** — no release has shipped carrying one |
| Hash pinning | `tools/pin_requirements.py` | **No** — `requirements.txt` is still a range; the build now fails rather than shipping unpinned |
| Signed releases | `tools/sign_release.py` | **No** — no key issued, nothing signed |

## 2. The finding that came out before the code

D10 Part 2 read: *"The complete inventory of third-party code that executes as
part of the Platform. **One component.**"* Then a table with numpy in it.

The numpy binary wheel is not one component. It bundles six more things that
execute inside our process: OpenBLAS, LAPACK, `libgfortran` (GPL-3.0 **with the
GCC Runtime Library Exception**), `libquadmath` (LGPL-2.1-or-later),
`lapack-lite`, `dragon4` and `libdivide`. Two of those carry licences that make a
procurement reviewer stop and read again.

The licences are fine — the GCC runtime exception exists precisely so proprietary
software can link the GCC runtime, and the LGPL is satisfied by dynamic linking,
which is how it ships. The warranty at D07 §3.4 stands. **What was wrong was the
completeness claim**, and it matters for a reason beyond accuracy: a register that
says "one component" and is off by seven is the exact understatement a security
reviewer finds first, and it retroactively casts doubt on every other count in the
document.

Corrected in D10 Part 2, with each bundled library, its licence and what it is.
`tools/sbom.py` now emits the same list from the installed tree, so the table can
be regenerated instead of trusted.

## 3. SBOM — `tools/sbom.py`

CycloneDX 1.5 JSON, written directly rather than with a library, for the same
reason `tools/verify_ledger_export.py` imports nothing from the Platform: a
recipient must be able to read the artefact with a text editor and a JSON parser.
Adding a dependency to generate the document about our dependencies is a joke that
writes itself.

**The digest is a tree hash, not a file hash.** Each component carries a SHA-256
over the sorted list of (relative path, file SHA-256) for every file it installed,
length-prefixed so path and content boundaries cannot be shifted. That is
recomputable on the Railroad's machine from their installed tree, which is what
makes it a verification tool rather than a claim — and it catches a substituted
wheel, because a substituted wheel installs different bytes under the same name
and version.

**Scoping is the design decision worth arguing about.** Run unscoped on this build
host, the tool found 153 distributions — `ufw` (a GPL-3 firewall tool), `Twisted`,
`odfpy`, and plenty else the Platform has never imported. A customer reading that
SBOM would reasonably conclude we ship them. So `generate --requirements` scopes to
the requirement file and its transitive closure; this project's comes out at **one
component**. The unscoped mode still exists because it is useful on a real
deployment host, and it warns by existing without a scope.

**Verification is six checks**: format, spec version, no declared component
missing, no installed component undeclared, tree hash, interpreter version. The
undeclared direction is the dangerous one — an unaccounted dependency is a
dependency nobody reviewed, sitting in the process.

## 4. Hash pinning — `tools/pin_requirements.py`, and a mistake I made

**I wrote two invented SHA-256 strings into `requirements.txt` and committed
nothing.** They looked like digests. They were not digests of anything. Had they
survived, `pip install --require-hashes` would have rejected every real numpy
download, and the failure would have arrived at release time on the Railroad's
machine — the exact outcome the control exists to prevent, caused by the control.

Caught before commit, reverted, and the tool was written so that it cannot happen
again:

- **No `--hash` flag exists.** There is no way to paste a digest in.
- **Every hash comes from `_sha256()` of a file `pip download` just produced**, in
  the same process.
- **`test_no_hash_anywhere_in_this_tool_was_typed_by_a_human`** asserts the tool
  contains no 64-hex-character literal, and the test file asserts the same about
  itself. A future session cannot reintroduce the mistake quietly.
- **A range is refused.** `numpy>=1.26` cannot be hash-pinned, because the index
  may serve any matching file; the tool says so instead of emitting a range with
  no hashes and calling it pinned.

**Why the file is not pinned right now.** The pin step needs index access; this
sandbox's proxy returns 403 to PyPI. So pinning is a release-host step, alongside
C01 Part C2's archive preparation. What changed in the repository is the
enforcement: the **Dockerfile and the release path now pass `--require-hashes`**,
so an unpinned `requirements.txt` **fails the build** instead of installing
whatever the index serves while a comment claims a control.

`render.yaml` deliberately does **not** get the flag. It deploys the public demo
from the public repo over the public internet; nothing it serves is a release
artefact. Breaking the demo would buy no security and cost a working site.

## 5. Signed releases — `tools/sign_release.py`

D09 §7.3 names GPG, so the tool wraps GPG rather than inventing a scheme. The
Railroad's security team already knows `gpg --verify`; asking them to learn ours
would be the same mistake the ledger export avoided by importing nothing.

**Reproducibility is a security property here, not tidiness.** If two builds of
the same content differ, the signature covers the difference — the build machine's
clock and user id become part of what was attested. The tool pins the gzip header
mtime (which `tarfile.open(..., "w:gz")` sets to `time.time()` independently of
the tar contents), normalises uid/gid to root, and sets one fixed mtime on every
entry.

That fix was found by mutation testing, not by reading: **removing both the gzip
mtime and the tar mtime still left the reproducibility test green**, because both
builds happened inside the same second. The test now sleeps 1.2 s between builds,
and the mutation goes red. This is the fourth session running that a green test
turned out not to be guarding anything.

The archive also writes the `MANIFEST.sha256` C01 Part C2 already describes, so
the sealed-archive path gains a signature without gaining a new procedure.

**What a signature does not prove** is in D09 §7.3: it proves the artefact was
signed by the key and has not changed; it does not prove the key was ours unless
the public key arrived by a route the Railroad trusts, and it does not prove the
build has no defect. Key custody carries that weight — exactly as with the export
key under §4.5.

## 6. Verification performed

- Suite **143 → 180, all green**, across three new files: 15 SBOM tests, 12
  pinning tests, 10 release tests.
- **Every guard mutation-tested individually.** Disabling the tree-hash check,
  the undeclared-component check, the declared-component check, the scoping, the
  range refusal, the empty-download guard, the verify mismatch path, the
  signature-failure path, the exclusion filter and the reproducibility fix each
  turned exactly the intended test red.
- **Two tests passed for the wrong reason and were rewritten**, both recorded
  above: the duplicate-key test (caught by the version check, not the loader) and
  the release-contents test (`axiom.db` was never in scope, so excluding it proved
  nothing).
- End-to-end against real GPG 2.2: key generation, build, export public key,
  sign, verify `ok`, append one byte to the archive, verify `FAILED`.
- End-to-end against a real numpy installation: SBOM generated, verified, then
  three attacks — changed tree hash, changed version, ghost component — each
  caught by a distinct named check.

## 7. The lesson this pass adds

**A control has three states, not two: absent, built, and applied. Collapsing the
middle one into either neighbour is how documents start lying.** D09 §7.3 already
had the rule that every gap in §4.4 needs a corresponding statement in §7 — this
pass extends it: the statement must say which of the three states the control is
in. "Implemented" is not a state.

The second, narrower lesson is the one about my own error. Two invented hashes
looked exactly like a pinned file. Nothing in the repository would have caught it
— the tests would have run, the build would have failed much later, on someone
else's machine. What caught it was reading back what I had written before
committing. That is not a process; it is luck with a habit attached, and the
regression test in §4 is the process that replaces it.

---

*Internal. Review when the pin step runs on the release host, when a GPG key is
issued, or when an SBOM ships with a release.*
