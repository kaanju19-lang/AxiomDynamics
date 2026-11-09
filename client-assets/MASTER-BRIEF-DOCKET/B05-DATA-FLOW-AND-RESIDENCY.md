# B05 — Data Flow & Data Residency Statement

**Docket position:** B05. The document the Railroad's CISO will read first. Pairs with B04 and D09 (Data Processing & Security Addendum).

**The short answer, stated before the detail:** AxiomDynamics does not receive, transmit, store, or process any Railroad data outside the Railroad's own network. There is no cloud component, no telemetry, no analytics, no licence callback, and no remote access path. Nothing. This is architectural, not a policy we promise to follow.

---

## 1. Data categories

| Category | Description | Origin | Where it lives |
|---|---|---|---|
| **Sensor readings** | Bearing temperature, wheel impact load, acoustic signatures per axle pass | Wayside detectors | Railroad edge box, in memory and local files |
| **Derived condition data** | Computed defect frequencies, rate-of-change, z-scores, peer comparisons | Physics engine | Railroad edge box |
| **Advisory warrants** | Ranked findings presented to a reviewer | Warrant builder | Railroad edge box |
| **Dispositions** | Reviewer identity, certification ID, decision, timestamp | Certified reviewer | Railroad edge box, append-only ledger |
| **Audit exports** | Signed bundles of the above for regulatory evidence | Admin action | Railroad-controlled storage |
| **ROI reports** | Cost-avoidance summaries | ROI model | Railroad edge box |

**Every row above terminates inside the Railroad's perimeter.** No category has an external destination.

## 2. What leaves the network

**Nothing.**

Verified against code, not asserted:

- No outbound HTTP client in any backend module — no `requests`, no `urllib.request`, no `http.client`, no `socket` usage for egress.
- No telemetry or analytics calls.
- No licence-validation callback. Licence enforcement is **contractual and cryptographic** (offline-signed licence files), not online.
- No crash reporting or diagnostic upload.
- Frontend references no external URL — no CDN, no font service, no tracking pixel, no third-party script.

The only network connections the software makes are **inbound**, on the port it serves, and the healthcheck's localhost call to itself.

**If a future release requires any outbound call, it must be disclosed here, in D06, and in D09 before shipment — and the air-gap claim in B04 §5 would require revision.** That is a rule, not a caveat.

## 3. What AxiomDynamics receives

**During normal operation: nothing.**

Under support (D06), the Railroad may **choose** to export logs or data and send them to us by a channel the Railroad controls. That is:
- Railroad-initiated, never automatic;
- Railroad-reviewed before sending;
- subject to D09's handling obligations once received;
- refinable — we can work from redacted logs in most cases.

**There is no standing remote access. We cannot connect to the edge box.** Support is remote-observation-free by design (B01 §8), and that is a cost to us and a benefit to the Railroad's security posture.

## 4. Residency

All data is resident on Railroad premises, on Railroad-owned or Railroad-leased hardware, within Railroad-controlled physical and network security. There is no processing outside the jurisdiction(s) in which the box sits.

**Cross-border note — for a carrier operating in more than one country:** a single deployment sits in one country. A tri-country CPKC deployment is three or more independent boxes, each resident in its own jurisdiction, with no data crossing between them. Any cross-border aggregation would be a separate, disclosed feature requiring its own schedule — it is not present in this architecture.

## 5. Data ownership

Per **D07 §11** (which incorporates **D13 §3**) and **D09 §2**:

- **Railroad owns** all sensor data, derived condition data, warrants, dispositions, and exports.
- **AxiomDynamics owns** the models, source code, rules, and weights — including improvements derived from Railroad data.
- The Railroad has a **licence back** to its own data in a usable export format on termination.
- No cross-customer learning is performed under this architecture, because no data leaves the box. **The question does not arise** — which is a materially easier answer than the aggregation agreement most vendors require.

## 6. Retention and deletion

- **Dispositions**: retained per the Railroad's records policy; specified in D09. Regulatory evidence retention is typically multi-year — the Railroad sets it, not us.
- **Raw sensor data**: retention is Railroad policy. Volumetric pressure is real — a high-density corridor generates a lot of it — so a rolling retention window is expected, with derived and disposition records kept longer.
- **On termination**: Railroad exports what it wants, then deletes the rest. We never held a copy, so there is nothing for us to delete.

## 7. Security controls in the architecture

| Control | Status |
|---|---|
| No external attack surface beyond the serving port | Present |
| Non-root container execution | Present |
| No third-party code beyond numpy | Present (see B04) |
| No outbound egress | Present — the strongest control in the set |
| Authenticated reviewer identity | **Required, not yet built** (B01 §7 item 1) |
| Append-only audit ledger | **Required, not yet built** (B01 §7 item 2) |
| TLS on the serving port | **Railroad-standard dependent** (B01 §7 item 10) |
| Signed update packages | **Required, not yet built** (D06) |

This table is deliberately uncomfortable. **Four controls are architectural and present; three are commitments we have not yet built; one depends on the Railroad.** Presenting the four as if they covered the other four is exactly the misrepresentation this docket exists to prevent.

---

*Descriptive annex. Creates no warranty. Verified against the repository at time of writing. Any change to network behavior, data handling, or dependency inventory requires revision of this document before release.*
