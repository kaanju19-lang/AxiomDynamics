# AxiomDynamics — Working Tree

Two folders, one rule.

## The classification rule

> **If a customer could read it, it goes in `client-assets/`. If it is about us — our strategy, our weaknesses, our playbook, our research — it goes in `assets/`.**

This is not a filing preference. `client-assets/` is presumed forwardable to a Class I railroad's legal and procurement teams. Anything sitting there may be attached to an email without a second thought. Anything in `assets/` may not.

That rule was violated with the first three carrier dossiers, which contained our competitive strategy, our assessment of which carriers are buyable and which are not, and our judgement about a customer's negotiating position. Moved to `assets/market-intel/carrier-dossiers/`.

## `client-assets/` — forwardable

One deliverable: the **Master Brief Docket**. A uniform contract-and-architecture set reviewed by both parties' counsel. Index and document register in `MASTER-BRIEF-DOCKET/D00-DOCKET-INDEX.md`.

```
client-assets/
└── MASTER-BRIEF-DOCKET/          38 artifacts: A1–A2, B01–B05, C01–C02,
                                  D00–D14, F00–F13, plus the index
```

Docket parts: commercial model (A), build blueprint for the Railroad's IT (B), deployment and certification (C), legal contract stack (D).

## `assets/` — internal only

| Path | Contents |
|---|---|
| `market-intel/carrier-dossiers/` | BNSF; UP/NS; CN/CPKC network dossiers |
| `external-pilot-cost-structure-and-licensing-model.md` | **Superseded 2026-11-10** — the original commercial-model draft, kept as a record of how the structure was first conceived. Do not quote its figures; it carries the withdrawn 2.0x/4.1x anchors and the retracted 16x/12x–50x claims. Use A2 for price and D08 for terms. |

## Current build state

**The docket is complete — 38 artifacts, 37 docket IDs** (A–D and F series). `MASTER-BRIEF-DOCKET/D00-DOCKET-INDEX.md` Part IV is the authority on status; this file is not, and has been out of date before.

**What is not complete is the build behind it.** The known gaps between the docket and the code are tracked in D00 Part VI. The largest is that there is no detector ingest path: every demonstration signal is generated from the physics equations on synthetic traces.

## Standing constraints

- Nothing in `assets/` may be forwarded. Nothing in `client-assets/` may contain internal assessment.
- Every legal document in the docket requires review by qualified counsel before execution.
- Carrier dossiers require re-verification before use — the UP/NS merger is live and the facts move.
