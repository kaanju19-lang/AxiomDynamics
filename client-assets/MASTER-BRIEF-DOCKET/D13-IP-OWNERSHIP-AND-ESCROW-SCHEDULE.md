# D13 — IP Ownership & Escrow Schedule

**Docket position:** D13. The definitive statement of what AxiomDynamics owns, what the Railroad owns, what transfers and when. Referenced by D02, D03, D05, D07, D08 and D14.

> **Drafting status:** Commercial grade. Requires counsel review before execution — particularly §4 (Escrow Release) and §6 (Change of Control), which are the operative clauses for the exit strategy.

---

## 1. The principle

AxiomDynamics owns the platform. The Railroad owns its data and the right to operate the platform. On insolvency, the Railroad gains the right to keep operating the version it has — **not** ownership of the platform, and not the right to build from it commercially.

That distinction is the whole of this document. Escrow transfers *operability*, never *ownership*.

## 2. Ownership schedule

**Decision recorded 2026-11-08.** AxiomDynamics retains 100% of all IP for the first five years. No sale, assignment or transfer of IP rights to any party in that window.

| Stage | Window | IP ownership | Transfer to customer |
|---|---|---|---|
| I — Prove | Y1–Y5 | 100% AxiomDynamics | Licence only |
| II — Brand | Y5–Y8 | 100% AxiomDynamics | White-label brand licence |
| III — Review | Y8 | 100% AxiomDynamics | Joint strategic review |
| IV — Open | Y8+ | Majority retained, or equity stake | Possible joint structure |
| V — Auction | Trigger-based | Sold in full | Sole buy-out |

## 3. What each party owns

**AxiomDynamics owns, absolutely:**

- Source code, object code, build scripts and tooling
- The physics models, equations, constants and their derivation
- All algorithms, thresholds, ranking logic and rule sets
- The certification registry design and its schema
- Documentation, training materials and this docket
- All derivative works, improvements and future versions
- All trademarks, trade dress and product names
- **The right to build future versions and to license to any other party**

**The Railroad owns, absolutely:**

- All raw sensor data from its detectors
- All derived condition data and computed values on its system
- All advisories and warrants generated on its system
- All disposition records it creates
- All exports and reports it produces
- Configuration data and deployment documentation about its own environment

**Licence back to the Railroad:** perpetual, irrevocable, non-exclusive right to use, copy and retain its own data in usable export format, during the term and after termination. The Railroad is never hostage to us for its own operating records.

**Licence back to AxiomDynamics:** the Railroad grants a non-exclusive licence to use its data in aggregated, non-attributable form for model improvement — **only if the Railroad opts in**, and only where such use can be accomplished without transmitting data off its network (which under AD-1 means it generally cannot be, absent a Railroad-initiated export). Default position: **no cross-customer learning occurs.**

## 4. Escrow — scope and release

**Deposit.** AxiomDynamics deposits the source code, build instructions and configuration documentation for **each released version** with a mutually agreed escrow agent.

**Critical: escrow tracks the running version, not a frozen initial build.** Depositing only the day-one MVP would mean that on release the Railroad receives a version that no longer matches what it is operating — the escrow would be worthless precisely when it is needed. Every production release updates the deposit within thirty days. Verification of deposit receipt is performed annually by the agent.

**Release conditions — exhaustive and closed:**

1. AxiomDynamics becomes insolvent, enters administration, receivership, or liquidation;
2. AxiomDynamics ceases to conduct business;
3. AxiomDynamics permanently ceases to support the licensed product version, having failed to cure within ninety days of written notice;
4. AxiomDynamics fails to deliver a security patch for a known critical vulnerability within the period defined in D06, having failed to cure within thirty days of written notice.

**No other trigger.** In particular, release is **not** available for: commercial dispute, non-payment, disagreement over fees, change of control, or as a remedy for any breach other than those listed. A general breach does not open the vault.

Release requires the escrow agent to verify the condition independently, not merely accept the Railroad's assertion.

**What release grants.** On release the Railroad receives the deposited version and a **perpetual, non-exclusive, non-transferable, royalty-free licence to use, maintain, modify and repair that version for its own internal railway operations.** Explicitly including the right to engage a third party to maintain it, and the right to fix defects itself.

**What release does not grant.** The Railroad may not, under any circumstances:

- Sell, licence, sublicence, distribute or otherwise provide the software to any third party;
- Offer it as a service to any other organisation;
- Incorporate it into a product offered commercially;
- Use it outside its own railway operations;
- Claim ownership of the IP, the models, or any derivative of them;
- Prevent AxiomDynamics from continuing to develop, licence and sell the platform;
- Assert any right to versions developed after the release date.

**The distinction in one sentence:** the Railroad gets the ability to keep its own railway running, and nothing more. AxiomDynamics keeps the product.

## 5. The honest limitation of escrow

Worth stating plainly, because it is true and because a buyer's counsel may raise it:

**Once source code is in the Railroad's hands, the practical ownership distinction becomes difficult to enforce.** A determined organisation with the source can derive the models and rebuild the system, whatever the licence says. Escrow is a commercial and legal protection, not a technical one.

Three things mitigate it: the non-commercialisation and non-sublicence terms above, the confidentiality obligation surviving release, and the fact that the released version is a snapshot that does not include future development.

**What genuinely protects the IP is not escrow terms — it is the evidence base.** Rebuilding the code takes eighteen months; reconstructing years of corroborated outcomes is impossible. That is the same conclusion reached in the IP strategy analysis, and it is the reason the disposition ledger is treated as the core asset rather than a compliance artifact.

## 6. Change of control and assignment

**AxiomDynamics may assign** this agreement, and all licences granted under it, to a purchaser of the IP or of the company, without customer consent — **provided** the assignee assumes all obligations and the customer's licence rights survive unchanged.

*Why this must be granted now:* without it, a buyer inherits contracts it may be unable to assume, and the value of the eventual transaction falls. This clause is worth money at exit and costs nothing today.

**The Railroad may not assign** its licence without AxiomDynamics' written consent, save to a successor by merger or reorganisation **of that Railroad's own corporate structure**, subject to the successor assuming all obligations and the licensed site count not increasing without a corresponding fee.

*Why both directions matter:* the Railroad's licence must not travel with a merger we never priced. If BNSF's licence can be assigned to a merged entity covering three networks, we have sold a network licence for a yard price.

**On AxiomDynamics' change of control:** the licence terms, pricing protection and escrow arrangements in force at the date of change survive, and may not be unilaterally varied by the acquirer.

## 7. Protection of the platform

From the date of installation, the Railroad shall not, and shall ensure its personnel and contractors do not:

- Reverse engineer, decompile or disassemble the software, save as permitted by escrow release under §4 or by non-waivable law;
- Create derivative works for any purpose other than internal maintenance of a released version;
- Remove or obscure proprietary notices;
- Use the platform to develop, train or benchmark a competing product;
- Permit any third party to do any of the above.

**Note the asymmetry and be honest about it:** these clauses are enforceable against a cooperating customer and largely unenforceable against a determined one. They exist to establish intent and to support a remedy if a breach is discovered, not to prevent it technically. Any feature claiming to prevent reverse engineering should not be represented as a security control.

## 8. Third-party components

Per B04, the only third-party runtime dependency is numpy (BSD-3-Clause), which imposes no copyleft obligation. All third-party components are compatible with proprietary licensing and with escrow deposit.

**Warranty:** the platform contains no component whose licence would require disclosure of AxiomDynamics' source code, or would restrict the licensing model in §1, on any basis. Any change to the dependency inventory that would affect this must be disclosed before release — see B04 §7 and D10.

## 9. Contractor and contributor assignments

**Every individual who contributes code, models, equations or documentation to the platform shall execute an IP assignment in favour of AxiomDynamics before their first contribution**, whether employee or contractor, and whether or not compensated.

Database rights, moral rights (to the extent waivable) and all future rights are assigned.

**This is the most commonly discovered defect in any diligence process and it is fatal at the worst moment.** A single unassigned contractor contribution can cloud title to the entire product and stall an acquisition at signing. There is no cure available after the fact except a negotiated agreement with a party who then knows their leverage.

**Verification:** a register of all contributors and the status of their assignment is maintained and available to a buyer's counsel under NDA.

## 10. Trade secrets

The physics models, constants and thresholds constitute trade secrets within the meaning of applicable law. Protection relies on: the confidentiality obligations in D07 and D11, access restriction on a need-to-know basis, the licence restrictions in §7, and the escrow release being conditional rather than routine.

**Marks:** source code, model derivation documents and constant tables are marked Confidential — Trade Secret. This marking is not decorative; in a trade secret claim the absence of marking is used to argue the information was not treated as secret.

## 11. What this document changes elsewhere

| Document | Interaction |
|---|---|
| D02 Pilot | Incorporates §2, §6, §9 by reference |
| D03 MSA | §6 assignment governs all orders |
| D05 Rollover | Stage II white-label in §2 must be offered as a priced option |
| D07 Master Contract | Confidentiality, reverse engineering, third-party warranty |
| D08 Licensing | Licence scope; §4 escrow is the only relaxation of the licence |
| D10 Component Register | §8 disclosure obligation |
| D14 Operating Model | Division of responsibility is unaffected by IP ownership |

---

*Commercial terms. Not legal advice. Escrow release conditions, assignment and change-of-control provisions must be reviewed by counsel in the relevant jurisdiction. Contributor assignment (§9) requires a separate instrument and should be executed before any further development.*
