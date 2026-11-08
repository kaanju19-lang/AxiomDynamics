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
└── MASTER-BRIEF-DOCKET/
    ├── D00-DOCKET-INDEX.md            docket map, precedence rules, gap analysis
    ├── A1-ROI-MODEL/                  Excel business case + build script
    └── D08-MASTER-LICENSING-AND-LIABILITY.md
```

Docket parts: commercial model (A), build blueprint for the Railroad's IT (B), deployment and certification (C), legal contract stack (D).

## `assets/` — internal only

| Path | Contents |
|---|---|
| `market-intel/carrier-dossiers/` | BNSF; UP/NS; CN/CPKC network dossiers |
| `external-pilot-cost-structure-and-licensing-model.md` | Internal copy of the commercial model |

## Current build state

**Built:** ROI model (A1), licensing model (D08, commercial grade — needs conversion to contract language), docket index (D00).

**Highest value next:** NDA (D11), tech stack disclosure (B04), master pilot agreement (D02).

**Deliberately not built:** the earlier `04-pilot-proposal` narrative — superseded by D02 as a legal instrument.

## Standing constraints

- Nothing in `assets/` may be forwarded. Nothing in `client-assets/` may contain internal assessment.
- Every legal document in the docket requires review by qualified counsel before execution.
- Carrier dossiers require re-verification before use — the UP/NS merger is live and the facts move.
