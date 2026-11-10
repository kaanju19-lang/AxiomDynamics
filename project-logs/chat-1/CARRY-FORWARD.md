# Carry-Forward — chat-1 → chat-2

Paste this as the first message of a new thread. It is written to be read cold.

---

You are resuming **AxiomDynamics** — physics-first predictive maintenance for
freight rail — from a previous conversation (chat-1).

**Read these first, in this order:**

1. `C:\Users\RGV\AxiomDynamics\project-logs\CURRENT-STATE.md`
2. `C:\Users\RGV\AxiomDynamics\project-logs\chat-1\SUMMARY.md`
3. `C:\Users\RGV\AxiomDynamics\project-logs\README.md` — especially "A gap in the
   record"

The repository is at `C:\Users\RGV\AxiomDynamics`, remote
`github.com/kaanju19-lang/AxiomDynamics`, private. Top commit on `origin/main` at
handoff: **`de9b245`**.

**Standing instructions, in force:**

- *"We will keep this same concept throughout."* The physics-first framing and
  document structure do not vary between documents.
- *"Strictly goes in our assets folder."* Internal analysis goes in `assets/`,
  never `client-assets/`. Client-facing is
  `client-assets/MASTER-BRIEF-DOCKET/` only.
- **Verify against the file, then write.** Never write a claim from memory and
  check afterwards. That habit produced every bad citation in chat-1, and it
  produced the worst defect in the project — the detector ingest path drawn as
  built when no inbound route exists.

**Three things were lost when chat-1's sandbox was destroyed.** They existed only
there and never reached GitHub: the F00 Rule 7 fix, the D07 §14 venue rewrite,
and Q6 (entity formation). Chat-2 rebuilt them — check `CURRENT-STATE.md` for
whether that is done. The transcripts of chat-1 are gone permanently and cannot
be rebuilt; the summary is all there is.

**What to work on next, highest value first:**

1. **The A2/D08 arithmetic pass** — neither has been re-derived figure by figure
   since `cf2e6ba`. A wrong number in a rate card is found by the customer's AP
   clerk rather than by us.
2. **Close D07 §14.5** — governing law and venue. It is honestly labelled as an
   open counsel decision now; it still needs a decision and a signed addendum
   before any Order is executed.

**Two traps:**

- The sandbox's `origin/main` ref is stale. `git log origin/main..HEAD` *inside
  the sandbox* overstates what is unpushed. The host repo is authoritative.
- `de9b245` is the last commit chat-2 can be sure GitHub has. Confirm before
  assuming anything newer is pushed.
