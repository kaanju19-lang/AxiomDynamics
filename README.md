# AxiomDynamics — Physics-First Predictive Maintenance (Demo)

A small web app for freight-rail predictive maintenance built on named
physical models instead of black-box ML or fixed alarm thresholds:

1. **Thermodynamics** — wheel-bearing temperature rate-of-change, flagged
   with a rolling z-score against each axle's own recent baseline, instead
   of a fixed absolute alarm. Also computes the legacy check correctly:
   real hot-bearing detectors alarm on temperature **above ambient**, not
   a flat number (see "East Palestine" note below).
2. **Peer comparison** — a robust median/MAD z-score against (a) this
   axle's own detector-pass history and (b) every other axle in the fleet
   right now, so a reading is judged against what's normal for it and for
   its peers, not in isolation.
3. **Kinematics** — coasting distance/energy from `E_k = 1/2 m v^2` plus
   grade and resistance terms, integrated numerically, to predict whether
   a car will stop or run away on a given grade.
4. **Acoustics** — FFT vibration analysis against the standard
   rolling-element bearing defect-frequency equations (BPFO, BPFI, BSF,
   FTF), to flag a specific defect frequency standing out above the noise
   floor, rather than a generic "weird sound" classifier.
5. **Same-axle left/right differential** — standard hot-bearing practice
   alongside the ambient-relative check: the two journals on one axle
   share load path and speed, so a large gap between them (independent of
   either journal's absolute level) points at a one-sided defect.
6. **Executive ROI panel** (`backend/roi.py`, `GET /api/roi`) — fleet
   mission-ready %, net estimated benefit, mean-time-to-detect vs. legacy,
   and open review counts, shown as a KPI strip at the top of the
   dashboard, built on real cited derailment cost data (see "ROI research"
   below) blended with clearly-labeled modeling assumptions where no
   public figure exists.

On top of those, two mechanisms:

7. **Evidence fusion → Predictive Ghost Warrants** — no single signal can
   trigger the top severity tier by itself. `backend/warrants.py` only
   escalates to **URGENT REVIEW** when at least two independent signal
   types agree; a lone signal (even a critical one) is capped at
   **REVIEW**. Every warrant carries a SHA-256 hash of its evidence, and
   severity tiers are named INFORMATIONAL / REVIEW / URGENT REVIEW
   specifically so they can't be mistaken for an operational alarm level —
   this system never issues a stop-train or braking instruction.
8. **Human reviewer disposition** — each Ghost Warrant has a real
   disposition workflow (`POST /api/warrant/{advisory_id}/disposition`):
   a named reviewer with a certification ID records Concur & Dispatch,
   Escalate, Override/Downgrade, or Reject Sensor Hardware, with an
   optional note. This is not decorative — it's what makes "a human is in
   the loop" an actual recorded action instead of a claim in a README.

   The ledger is **append-only**. A second decision on the same advisory
   does not overwrite the first: it is inserted as a new record whose
   `supersedes_id` points at the record it corrects, and both survive
   with their own timestamps. `UPDATE` and `DELETE` are refused by
   database triggers, and every record carries a SHA-256 over its content
   and its predecessor's hash, so `store.verify_chain()` can prove the
   history is intact and name the first record that is not. This is a
   deliberate constraint, not an accident of implementation: the whole
   regulatory argument rests on a record that cannot be quietly rewritten.
   Read `backend/store.py`'s module docstring for exactly what the chain
   does and does not prove.

Every number in the dashboard traces back to an equation in
`backend/physics.py` — read that file's docstrings for the exact formulas
and their sources. Nothing here is a trained model or a mystery black box.

## Why this design, not just "AI predicts failures"

This isn't arbitrary. [NTSB testimony on the Feb 3, 2023 East Palestine,
OH derailment](https://www.ntsb.gov/investigations/Documents/East%20Palestine%20Ohio%20Board%20Meeting%20Summary%20with%20Amendments.pdf)
found the failed bearing read 253°F above a 10°F ambient at the final
detector before critical alarm — by then it was in its final stage of
mechanical failure. [FRA Safety Advisory 2023-01](https://railroads.dot.gov/sites/fra.dot.gov/files/2023-02/(Safety%20Advisory%202023-01%20%20Posting%20on-line%20022823).pdf)
and its supplements, issued because of that derailment, call out the
specific gaps this design targets: single-point checks with no trend
history, inconsistent thresholds across detectors, and no standard
practice for comparing a reading against a bearing's own history or its
peers. The demo fleet includes a unit (U3) deliberately modeled on that
night's cold-ambient conditions, specifically to show the gap between a
legacy point-in-time check and a trend/peer-aware one on the same data.

## Why no FastAPI / Chart.js / npm install

This was deliberately built on nothing but the Python standard library
(`http.server`) plus `numpy` for FFT/array math, and plain Canvas/JS on the
frontend with zero CDN dependencies. That's not a style preference — it's
the actual deployment story for an air-gapped wayside/dispatch environment,
where IT will not approve installing a dependency tree on a live network.
Run it with:

```bash
pip install numpy   # only dependency; skip if numpy is already present (sqlite3 is in the Python stdlib)
cd axiomdynamics-app
python3 -m backend.main
```

Then open **http://127.0.0.1:8420/** in a browser. Click any row in the
Fleet table to see that axle's thermodynamics, acoustics, and kinematics
detail charts.

## What's real and what's simulated

There is no freely downloadable, public, real-time rail wayside sensor
dataset (the datasets that exist, like CWRU's bearing set, are generic
motor-test-rig data behind a university host, not rail axle data — and
this build environment had no outbound internet access to fetch anything
anyway). So `backend/simulate.py` generates synthetic sensor traces **from
the same physics equations in `physics.py`**, with documented fault
conditions injected (a bearing-wear friction ramp for the thermal fault, an
injected BPFO-frequency harmonic for the acoustic fault). Every constant
used (bearing geometry, thermal mass, radial load, etc.) is called out in
that file as "representative," not pulled from a specific OEM spec.

To point this at real sensor data later, replace the three `generate_*`
functions in `simulate.py` with loaders that return the same shapes
(`times, temps_f` / `t, signal, defect_freqs, shaft_hz`) — `physics.py` and
`main.py` don't care where the samples came from.

## ROI research: real bearing-failure derailment costs

The ROI panel's cost figures come from two real, cited cost tiers rather
than an invented "average cost per derailment" (no such standardized
public figure exists — FRA tracks accident counts and causes, not a
normalized dollar average).

**Tier 1 — contained bearing/wheelset failure, no hazmat release:**
a BNSF bearing-related derailment with $5,000,000 in reported damage
([NTSB](https://www.ntsb.gov/investigations/accidentreports/reports/rab1712.pdf)),
and a separate BNSF derailment with $13,500,000 in reported damage,
explicitly excluding lading and environmental remediation costs
([NTSB docket](https://data.ntsb.gov/Docket/Document/docBLOB?FileExtension=.PDF&FileName=BNSF%20Equipment%20Incident%20Report-Redacted.PDF&ID=40457595)).
These two figures bracket the $5.0M–$13.5M range used as the "contained"
tier.

**Tier 2 — catastrophic failure with hazmat release:** the Feb 3, 2023
East Palestine, OH derailment (Norfolk Southern, not BNSF, but the same
wheel-bearing failure mode this product targets) cost over $310 million
in a federal EPA/DOJ settlement
([DOJ](https://www.justice.gov/opa/pr/united-states-reaches-over-310-million-settlement-norfolk-southern-address-harms-caused-east)),
a separate $600 million personal-injury class settlement paid fully by
Norfolk Southern
([AP](https://apnews.com/article/east-palestine-derailment-norfolk-southern-gatx-oxyvinyls-2d5110bf096ec3524f3092999bee3060)),
and a cumulative cost reported to have exceeded $1 billion by mid-2024
([KTEN](https://www.kten.com/story/49275631/east-palestine-train-derailment-has-now-cost-norfolk-southern-1-billion)).

**What's an assumption, not a citation:** there is no published base rate
for what fraction of missed bearing defects progress to a catastrophic
event versus stay contained. `backend/roi.py` uses 2% and the A1 Excel
model uses 0.05% (`P_CATASTROPHIC_GIVEN_MISSED_DEFECT` in the code;
sheet 1 cell B17 in the workbook), and that 40× disagreement is an open
item — it is the reason the workbook and the licensing annex do not
produce the same benefit figures. Do not quote either number without
reading `assets/a2-d08-arithmetic-pass-2026-11-09.md` first. Both blend
the two sourced tiers into one expected-cost figure. The inspection-cost
and detection-time constants are also unsourced placeholders. Replace
them with your own numbers, or a pilot customer's real safety/cost data,
before this supports an actual business case.

## One important caveat on the kinematics module

The coasting model assumes **no brake or throttle input at all** for as
long as you let it run. On a steep enough descending grade it will show
the car accelerating toward a terminal velocity that a real train would
never actually reach, because crews brake well before that. Read a
"will accelerate on this grade" result as *"this axle needs braking input
to control speed here,"* not as a forecast of what a train will actually
do — it's a decision-support signal, not a crystal ball.

## Project layout

```
backend/
  physics.py    the three physics modules (thermo / kinematics / acoustics)
  simulate.py   synthetic fleet + sensor trace generator
  main.py       stdlib HTTP server, routes, static file serving
  ledger_export.py  signed, verifiable export of the disposition ledger
tools/
  verify_ledger_export.py   standalone bundle verifier; imports nothing from backend/
frontend/
  index.html, style.css, app.js   dashboard UI, vanilla JS canvas charts
tests/
  test_physics.py   correctness tests for every formula
  test_store.py     append-only and hash-chain tests for the ledger
  test_export.py    tamper, truncation, re-sign and re-key tests for the export
  run_tests.py      stdlib-only test runner; discovers test_*.py
```

## Running the tests

```bash
python3 tests/run_tests.py     # no pytest needed; discovers every test_*.py
# or, if you have pytest:
pytest tests/
```

80 tests currently: 21 for the physics formulas, 17 for the disposition
ledger, 42 for the signed export. The ledger and export tests are adversarial
by design — each one tries to destroy an earlier decision or forge a bundle, and
asserts that the attempt fails or is detected. Three of the export tests assert
a *failure to detect*, because the design has stated limits and a test that
records a limit is worth more than a comment that mentions it.

## API routes

- `GET /api/fleet` — summary status for every axle
- `GET /api/alerts` — combined predictive alerts, most severe first
- `GET /api/unit/{id}/thermo` — temperature series + z-score sweep + alerts
- `GET /api/unit/{id}/acoustics` — FFT spectrum + defect frequency matches
- `GET /api/unit/{id}/kinematics` — coasting profile for that axle's car
- `GET /api/roi` — fleet-wide executive KPI summary (mission-ready %, net
  estimated benefit, mean-time-to-detect, open reviews)
- `POST /api/warrant/{advisory_id}/disposition` — append a reviewer's
  disposition (`{"reviewer_name", "cert_id", "disposition", "note"?}`,
  where disposition is one of `concur_dispatch`, `escalate`,
  `override_downgrade`, `reject_sensor`). Returns the new `record_id`,
  the `supersedes_id` it corrects (or null), and the record's hash.
  Persisted in `axiom.db` (SQLite, stdlib `sqlite3`, survives a restart).
- `GET /api/warrant/{advisory_id}/disposition` — the full decision trail
  for one advisory, oldest first, with `chain_ok` reporting whether the
  hash chain verifies.
- `GET /api/ledger/verify` — recompute the whole disposition chain and
  report `{ok, rows, broken_at_id, reason}`.

## Deploying to Render (free tier)

This gets you a real `https://your-app-name.onrender.com` URL anyone can
open without installing anything. Render needs your code in a git repo it
can pull from (GitHub, GitLab, or Bitbucket) — if this folder isn't a git
repo yet:

```bash
cd axiomdynamics-app
git init
git add .
git commit -m "Initial commit"
```

Then push it to a new GitHub repo (create one at github.com/new, then
follow the push instructions it gives you).

**Option A — Blueprint (uses the included `render.yaml`):**
1. Go to [render.com](https://render.com) and sign up / log in.
2. Dashboard → **New** → **Blueprint**.
3. Connect your GitHub account and select this repo.
4. Render reads `render.yaml` and fills everything in automatically —
   review and click **Apply**.

**Option B — Manual web service (if you skip the Blueprint):**
1. Dashboard → **New** → **Web Service** → connect this repo.
2. Runtime: **Python 3**.
3. Build command: `pip install -r requirements.txt`
4. Start command: `python -m backend.main`
5. Add an environment variable: `AXIOM_HOST` = `0.0.0.0`
6. Instance type: **Free**.
7. Click **Create Web Service**.

Either way, Render builds and deploys automatically, then gives you a
public URL (first load on the free tier can take ~30-60s if the instance
had spun down from inactivity — that's normal, not a bug).

**Important caveat — reviewer dispositions won't persist on Render's free
tier.** Free-tier instances have an ephemeral filesystem: it spins down
after inactivity and loses any local file changes, including `axiom.db`.
Dispositions you record will survive until the instance sleeps, then
reset. Note that this is a *durability* limit, not an append-only one: the
schema still refuses in-place edits while it exists, but losing the file
loses the whole ledger. For a real pilot, upgrade to a paid Render plan
with a persistent disk, or point `AXIOM_DB_PATH` at a managed database —
and replicate off-box, because a single copy is a single point of loss
(D09 §4.4).

## Running it in Docker (air-gapped edge box story)

```bash
docker build -t axiomdynamics-demo .
docker run --rm -p 8420:8420 axiomdynamics-demo
```

Then open `http://127.0.0.1:8420/` same as the non-Docker run. The image is
`python:3.11-slim` + numpy only, runs as a non-root user, and has a basic
`HEALTHCHECK` hitting `/api/fleet`.

For a genuinely air-gapped box: build the image somewhere with internet,
`docker save axiomdynamics-demo -o axiomdynamics-demo.tar`, carry that tar
over on the encrypted USB, then `docker load -i axiomdynamics-demo.tar` on
the offline edge server and `docker run` as above. No pip, no npm, no
outbound connection needed on the edge box itself.

**Not build-tested here** — this sandbox has no internet access, so there
was no way to actually pull `python:3.11-slim` and run `docker build` to
verify it. The Dockerfile is straightforward and should work as-is, but
please run the build yourself and let me know if anything needs fixing.

## Extending this

Good next steps, roughly in order of how much new ground they cover:
- Swap `simulate.py` for a real data loader (CSV/serial/MQTT from an actual
  wayside detector or onboard sensor). **This is the largest known gap** —
  there is no inbound ingest route at all, so every demo number
  demonstrates the method rather than a customer's data.
- Replicate the signed ledger export off-box on a schedule. The export itself
  is built (`backend/ledger_export.py`, verified independently by
  `tools/verify_ledger_export.py`); what is missing is a second host that
  receives bundles automatically and acknowledges them (D09 §4.4–4.5).
- Add authentication if this ever leaves a single trusted machine — and
  the signed certification registry (AD-2) behind it, which is what turns
  a recorded reviewer name into a verified identity, and what would let the
  export's HMAC key be bound to a named signer instead of a custody procedure.

