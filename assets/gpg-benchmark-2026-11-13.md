# The two invented numbers, measured

**Chat-12, 2026-11-13.** Rung 3 of chat-11's ladder. Benchmark, not a build.

`assets/asymmetric-signature-decision-2026-11-13.md` labels two figures as
invented and says both must be established before any code is written. This file
establishes the first and **derives the second from the repository, where it turns
out to have been stated all along.**

---

## Finding 1 — the signature cost was estimated an order of magnitude too high

The paper estimated "tens to low hundreds of milliseconds" for one `gpg` signature
and called it the weakest evidence in the paper. Measured on this host
(`gpg (GnuPG) 2.2.27`, Linux, 25 iterations, median):

**Read the payload column as a size, not an artefact.** The tool signs
`os.urandom(size)`, not a real export bundle or a real release archive. That is
sound for timing — gpg hashes the byte stream and does not care what it holds —
but the earlier table called these "export bundle" and "release archive" as though
they had been built, and an audit was right to flag the difference.

| Operation | ed25519 | RSA-3072 |
|---|---|---|
| process start only (`gpg --version`) | 3.85 ms | 4.45 ms |
| sign 256 B detached | **8.71 ms** | 21.78 ms |
| sign 512 KB export bundle | **10.21 ms** | 23.35 ms |
| sign 4 MB release archive | 16.14 ms | 34.01 ms |
| **sign with a passphrase (loopback)** | **299.27 ms** | 322.18 ms |

**The estimate was right for a passphrase-protected key and wrong for an
unprotected one, and nothing in the paper distinguished them.** That distinction
is the whole result, so it is worth being precise about it.

An unprotected signing key costs **~10 ms**, not hundreds. Payload size barely
matters — 4 MB costs 16 ms — because the work is the process launch and the
crypto, not the file. The 64 bundles a year that `ledger_replication.due_exports`
produces therefore cost **0.65 s per year** at ed25519, not the "seconds per year"
the paper guessed. The guess was conservative and in the right direction.

**The passphrase path is 30x the unprotected path and does not go away.** It is
the realistic path for an unattended edge box, because a signing key with no
passphrase is a key that anyone with disk access can use.

**What the 300 ms is, corrected after an independent audit.** The first version of
this file said the cost was "gpg-agent plus pinentry startup on each invocation,
not key derivation". **That was wrong, and it was stated with more confidence than
the benchmark supported.** The auditor isolated it three ways: stubbing
`pinentry` with a no-I/O responder moved the time only 454.8 → 436.3 ms; symmetric
encryption with no key and no agent showed `--s2k-mode 0` at 4.5 ms and
`--s2k-mode 3` at 326 ms; and the agent's own CPU per signing call was 420–456 ms
while `gpg` itself burned 0.00 s user and system time.

**So the cost is iterated S2K key derivation**, at the maximal iteration count
`gpg` uses by default, paid again on every signing call because gpg-agent does not
retain a passphrase-unlocked key across process invocations. It is CPU, not
process startup and not pinentry.

**A second correction: this file claimed to have tested the warm-agent case and
the tool never did.** The sentence removed above said the cost was measured
"whether the key was already unlocked in a warm agent, whether the agent was
killed first". Those variants are not in `tools/bench_gpg_signature.py` — an audit
pointed out that the artifact a reader would re-run cannot reproduce the claim. I
ran them by hand at the time and the conclusion held (≈443 ms with
`--passphrase`, ≈349 ms warm-and-cached, so the cost is not avoided by warming),
but **a claim of evidence must live in the tool, not in the author's memory of a
terminal.** The measurement here is the single protected-key number; the warm-agent
question is answered above as an observation, and labelled as one.

So the honest figure for "what a signature costs" is a **choice of two numbers**,
and which one applies is a security decision the paper never asked:

- **unprotected key: ~10 ms** — cheap enough that per-row signing would survive on
  latency grounds, which destroys the paper's premise that per-row is unaffordable
- **protected key: ~300 ms** — per-row is hopeless at hundreds a day, and per-bundle
  is free

**The cost argument does not settle the scope question, and the measurement
proves it.** At 10 ms, hundreds of rows a day is 1–5 s of CPU spread over a day.
The paper's verdict that per-row is "likely unaffordable" rests on the 300 ms
figure, which only applies if the key is protected, which the paper never
considered. What *does* settle it is the structural point the paper made
independently and correctly: **`save_disposition` calls `attest()` after the
INSERT and before COMMIT, so any signing there holds the SQLite write lock for
its duration.** At 300 ms a per-row signature serialises the whole ledger; at
10 ms it still serialises it, just faster. **The write-lock argument is the real
one and it survives the measurement. The latency argument was never the real one
and it does not.**

---

## Finding 2 — the disposition rate was not an assumption, it was in B01 §6

The paper says:

> **The disposition rate is an assumption, not a derivation.** No file in this
> repository states one.

**That is false.** `B01 §6 Scale envelope` states it:

> "Per edge box, designed for: one to six detector feeds, up to ~5,000 monitored
> axles, sub-second inference per unit, **disposition volume in the low hundreds
> per day**."

The paper's assumed figure and B01's stated figure agree — "low hundreds per day"
in both. So the number was not invented; it was recalled without a citation and
then labelled as an assumption, which is a milder error than inventing it but the
same error in kind as the two chat-11 caught. **The right correction is to cite
B01 §6, not to keep calling it an assumption.**

**But B01 §6's figure is itself unsourced.** It states a design envelope without
saying where the volume came from, and nothing in the repository derives it —
there is no real fleet, no Railroad volume data, and the demo fleet is synthetic.
So the chain is: this paper assumed a number, B01 asserted the same number, and
neither can point at evidence. **Two documents agreeing is not a source.**

What is derivable, and what the real open question is: at low hundreds per day the
per-row question is moot (a few hundred rows cannot saturate anything at 10 ms
each); it becomes live at tens of thousands per day, which is a fleet far beyond
one edge box and therefore beyond this product's stated scale envelope. **The
scope question B01's envelope creates is answered by the envelope itself.**

---

## What this changes in the decision paper

1. **The latency estimate is retired and replaced by two measured figures**, with
   the passphrase distinction made explicit. The paper's own warning — "the
   recommendation below should be re-checked against a real measurement before any
   code is written" — is now discharged.
2. **The per-row verdict is re-grounded.** It stays "stays HMAC", but the reason
   is the write-lock, not the latency. A reader who rejected the write-lock could
   have argued the latency point away; they cannot argue the lock away.
3. **The disposition-rate claim is corrected** from "no file states one" to
   "B01 §6 states one, unsourced, and it agrees with the assumed figure."
4. **The recommendation itself does not change.** Option A, detached GPG over
   export bundles, per-row stays HMAC. Measured cost strengthens it: 0.65 s/year is
   not a cost at all.

**The owner's decision is unchanged and still the blocker:** accepting `gnupg` and
`dirmngr` into an image whose proposition is zero outbound network. This benchmark
does not touch that, and should not be read as making the decision easier — the
cheap numbers make *per-bundle signing* cheap, which was never in doubt, while the
`dirmngr` question is about the air-gap story, not about milliseconds.

---

## How to reproduce

```
python3 tools/bench_gpg_signature.py --iters 25 --key-type ed25519
python3 tools/bench_gpg_signature.py --iters 25 --key-type rsa
```

Raw output committed at `assets/benchmarks/gpg-sign-ed25519.json` and
`assets/benchmarks/gpg-sign-rsa3072.json`. The tool creates a throwaway
`GNUPGHOME` and removes it; it touches no real keyring and performs no network
operation.

**Caveat on the host:** this is a container, not the target edge box. Absolute
numbers will differ on Railroad hardware. The **ratio** between protected and
unprotected signing is the finding, and that ratio will not invert — it is
pinentry process startup, which is slower on weaker hardware, not faster.
