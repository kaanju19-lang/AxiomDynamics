# Chat-11 — three documentation defects, a decision paper, and a guard for the class

**2026-11-13.** Suite **390 → 398**. Four commits.

---

## The shape of this chat

The ladder opened with the two low rungs and the decision paper, because the
buildable queue inside the repository is near-empty and three of six remaining
items are blocked outside it. That forecast held: **no control moved from "built,
not applied" to "applied"**, so the Master % Tracker did not move. The work was
correcting documents that had drifted and making the drift mechanical to catch.

**The recurring defect this chat is about:** a capability gets built, the code and
its tests move, and the documents that described the old state do not. Chat-9 and
chat-10 both hit it and both fixed instances by hand. Chat-11 found two more
instances *in different documents* and wrote a test so the next one is caught by
the suite rather than by a reader.

---

## What was found

### B04's inventory was four chats stale

The component table listed nine files and 2,695 lines. The repository held
**8,200**. Seven backend modules were missing — `ledger_export`, `attribution`,
`accounts`, `ingest`, `ingest_auth`, `ledger_replication`, `key_directory` — which
are exactly the cryptographic and authentication surface a security reviewer reads
B04 for. `frontend/icons.js` was missing too.

The same document called the SBOM "**Not produced**" and release signing "Not
currently signed" while `tools/sbom.py` and `tools/sign_release.py` both existed,
were tested, and had been listed as built in D09 and D10 since chat-5.

**Corrected to the three-state distinction** D09 §4.4 already uses: not built /
built, not applied / applied. All five supply-chain controls sit in the middle
state. **A tool that exists is not a control that operates** — and a document
saying "not produced" when a generator exists is now as wrong as one saying
"signed" when nothing is.

### B02 §9 contradicted its own §2

The paragraph said "**The ingest path (§2) is not built at all**" and "the front
door does not yet exist". Ingest was built in chat-5, authenticated in chat-6, and
B02's own §2 twelve lines earlier says "the chain now runs as drawn". The same
paragraph described item 1 as open at the entry point, which chat-6 closed.

Corrected to state what is true: the front door exists and is authenticated, the
schema is a demonstration one, and **an accepted payload is validated and logged,
not scored** — so no demonstration number moves because of ingested data.

### D10 told clients a GPG key exists

> D10 Part 5: "**The key is issued and published by Supplier**…"
> D09 §7.3: "no key is issued and no release has been signed."
> B04 §7: "No GPG key exists and none is under custody, so nothing has been signed."

D10 is the register the security reviewer reads. It was the one that was wrong.
Found by an adversarial audit of the decision paper, not by the sweep — the sweep
had been looking for *absence* claims, and this was a false *presence* claim. Both
directions go stale.

---

## The decision paper, and what the audit did to it

`assets/asymmetric-signature-decision-2026-11-13.md`. Recommendation: detached GPG
signatures over **export bundles** only; per-row attestations stay HMAC.

**The substantive result is a refusal to overclaim.** The ladder described items 1
and 11 as one defect. They are not:

- An asymmetric signature closes "**cannot name a signer**".
- Item 11 says "**provenance**" — whether the public key reached the Railroad by a
  route they trust. **No signature scheme supplies that.** It is key distribution.

So the paper says plainly that it narrows item 11 from a cryptography problem to a
logistics one, and does **not** close it. Item 1 is untouched: the bundle-signing
key is neither a release key nor a reviewer key.

**Why the scope splits per-bundle versus per-row** — and this is the part that does
not depend on any invented number: `store.save_disposition` calls `attest(conn, rec)`
**after the INSERT and before COMMIT**. Any signing there holds a write lock.
Putting an external process launch inside a database transaction is wrong on
principle, not just on measurement.

**The decision this paper asks for is the owner's**: `gnupg` in the shipped image,
and `dirmngr` with it — a daemon that performs network fetches, in an image whose
entire proposition is zero outbound network. One line of Dockerfile, one paragraph
to a CISO.

**The adversarial audit found eight defects in the first draft. Four were
material:**

1. A quotation attributed to `sign_release.py` that is actually in D09 §7.3 — the
   tool's own wording is plainer, and it is now the one quoted.
2. "Costs one OS package" — `gnupg` pulls about twelve, `dirmngr` among them.
3. "Not a code change you can make in one file" — it is one line. The draft
   overstated the cost to argue a case it had already made.
4. "This closes item 11" — contradicted the paper's own next paragraph.

Plus two figures that were **invented and presented as derived**: the gpg timing
estimate and the disposition rate. Both are now labelled as estimates, with a note
that they should be measured before any code is written.

---

## The guard

Two files were added, and the second is the one that matters beyond this chat.

`tests/test_b04_inventory.py` (5 checks) parses B04's table and compares it against
disk in both directions: every named file exists with the quoted line count,
**nothing in `backend/` or `frontend/` is missing from it**, and the quoted total
equals the row sum. The omission direction is the defect that actually happened.

`tests/test_docket_currency.py` (3 checks) holds six capabilities the code
demonstrably has, and fails if any docket document asserts one is absent. It skips
a line containing "no longer", because that is how a retraction is written.

**Both were mutation-tested and both went red.** Five mutations total: restore an
old line count, add an unlisted module, restore "Not produced", reinsert the ingest
claim, and a cross-section contradiction in B02. All killed; documents restored to
green afterwards.

**One trap hit while writing the guard, worth carrying:** the first version of the
B02 check failed on my own correction, because the retraction *quotes* the phrase it
retracts. A guard that cannot tell a claim from a quotation of it will fail on every
well-written fix. The rule is now narrower — an unretracted assertion only.

---

## A correction to this chat's own opening

At the open I reported the gap-row bucket at **16.4** and the total at **78.8**.
Neither was derived; I adjusted chat-10's 16.7 by impression. Scoring the rows
properly gave **16.0** and **78.4**.

Then, while correcting B02, I wrote "49 tests across the two ingest suites" into
the document. The files say **25 + 18 = 43**. Caught before commit, corrected.

**Two invented numbers in one chat, in the same chat that wrote a paper about
invented numbers.** That is the finding worth carrying: the habit is not cured by
having named it once. The only reliable rule is the mechanical one — derive, then
write, and prefer a test over a memory.

---

## Master % Tracker at chat-11's close

Basis and rubric: `assets/master-tracker-rubric-2026-11-13.md`. Re-derive, do not
quote.

| Bucket | Weight | Open | Close | Δ |
|---|---|---|---|---|
| Docket documents (37) | 40 | 40.0 | 40.0 | — |
| B01 §7 gap rows (12) | 30 | 16.0 | 16.0 | — |
| Core software (8) | 20 | 20.0 | 20.0 | — |
| Release readiness (5) | 10 | 2.4 | 2.4 | — |
| **Total** | **100** | **78.4** | **78.4** | **—** |

**Zero movement, and that is the correct reading.** Three of four rungs were
documentation and decision work. The suite rose 390 → 398, which is a better test
suite, not a better product. A tracker that moved here would be measuring effort.
