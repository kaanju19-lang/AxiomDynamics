# Carry-Forward — chat-2 → chat-3

Paste this as the first message of a new thread. Written to be read cold.

---

You are resuming **AxiomDynamics** — physics-first predictive maintenance for
freight rail — from a previous conversation (chat-2).

**Read these first, in this order:**

1. `C:\Users\RGV\AxiomDynamics\project-logs\CURRENT-STATE.md`
2. `C:\Users\RGV\AxiomDynamics\project-logs\chat-2\SUMMARY.md`
3. `C:\Users\RGV\AxiomDynamics\project-logs\README.md`

The repo is at `C:\Users\RGV\AxiomDynamics`, remote
`github.com/kaanju19-lang/AxiomDynamics` (private).

**Standing instructions, all three in force:**

- *"We will keep this same concept throughout."* Physics-first framing and
  document structure do not vary between documents.
- *"Strictly goes in our assets folder."* Internal analysis in `assets/`, never
  `client-assets/`.
- *"Drop all the entire project work directly in AxiomDynamics folder."* Write
  into the real repo on the first pass and commit in the same pass. Never build
  in sandbox scratch space.
- **Verify against the file, then write.** Never cite from memory and check
  afterwards. That habit produced every bad citation in this project.

**Start the new thread by confirming state, not by trusting this file:** run
`git log --oneline -5` and `git status` in the repo, read
`project-logs/CURRENT-STATE.md`, then say what you found.

**Push state — corrected in chat-3.** This file originally named `785f335` and
`ee9800c` as unpushed. **Both reached GitHub;** `ee9800c` became the top of
`origin/main`. What was actually unpushed at the chat-2 → chat-3 boundary was the
later transcript and handoff work: `3d773ac`, `36b43bd`, `d6f25ac`, `05b161d`.
Run `PUSH-TO-GITHUB.bat` in the repo root. The sandbox cannot reach GitHub — 403
from the proxy — so pushing is always the owner's job. **Always confirm push state
with `git log --oneline origin/main..HEAD` rather than trusting a written list.**


**The work waiting:**

1. **Two A2/D08 model findings — an owner decision.** The arithmetic pass was
   completed in chat-3: all 78 figures recompute correctly, no arithmetic error.
   But two claims do not reproduce from the shipped model — the 2.0x/4.1x return
   anchors in A2 §3.2 and D08 §3, and D08 §5–§6's modelled benefits, which run
   5x–14x above what A1 computes at identical inputs. Details in
   `assets/a2-d08-arithmetic-pass-2026-11-09.md`. Deciding which model governs
   changes client-facing sentences, so it needs the owner.
2. **D07 §14.5** — governing law and venue. Honestly labelled as an open counsel
   decision; still needs a decision and a signed addendum before first execution.

**What was lost, so nobody hunts for it:** chat-1's entire conversation (2,527
turns) and its final phase of work. The sandbox container was destroyed and the
bundle-and-push step was never repeated after `de9b245`. Chat-2 rebuilt the work;
the transcripts are unrecoverable. `project-logs/transcripts/README.md` explains
it. From chat-2 onward every session's transcript is committed before close.
