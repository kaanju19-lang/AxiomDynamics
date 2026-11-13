// AxiomDynamics dashboard. Vanilla JS, no CDN dependencies on purpose --
// this is meant to open on an air-gapped box with nothing installed.

const TIER_ORDER = { "INFORMATIONAL": 0, "REVIEW": 1, "URGENT REVIEW": 2 };
const SEVERITY_ORDER = { normal: 0, watch: 1, warning: 2, critical: 3 };

function tierClass(tier) {
  return tier.toLowerCase().replace(/\s+/g, "");
}

async function getJSON(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${url} -> ${r.status}`);
  return r.json();
}

function el(tag, attrs = {}, children = []) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "text") e.textContent = v;
    else e.setAttribute(k, v);
  }
  for (const c of children) e.appendChild(c);
  return e;
}

// ---------------------------------------------------------------------------
// Generic canvas line chart. series = [{label, points:[[x,y],...], color}]
// options: { yLabel, xLabel, hLines:[{y,label,color}], vLines:[{x,label,color}] }
// ---------------------------------------------------------------------------
function drawLineChart(canvas, series, options = {}) {
  const ctx = canvas.getContext("2d");
  const W = canvas.width, H = canvas.height;
  ctx.clearRect(0, 0, W, H);

  const padL = 56, padR = 20, padT = 16, padB = 36;
  const plotW = W - padL - padR, plotH = H - padT - padB;

  let allX = [], allY = [];
  for (const s of series) for (const [x, y] of s.points) { allX.push(x); allY.push(y); }
  for (const h of options.hLines || []) allY.push(h.y);
  for (const v of options.vLines || []) allX.push(v.x);
  if (allX.length === 0) return;

  const xMin = Math.min(...allX), xMax = Math.max(...allX);
  let yMin = Math.min(...allY), yMax = Math.max(...allY);
  if (yMax === yMin) { yMax += 1; yMin -= 1; }
  const yPad = (yMax - yMin) * 0.08;
  yMin -= yPad; yMax += yPad;

  const xToPx = (x) => padL + ((x - xMin) / (xMax - xMin || 1)) * plotW;
  const yToPx = (y) => padT + plotH - ((y - yMin) / (yMax - yMin || 1)) * plotH;

  // grid
  ctx.strokeStyle = "#e2e8f0";   // grid only: decorative, kept faint
  ctx.lineWidth = 1;
  ctx.font = "11px Segoe UI, Arial";
  ctx.fillStyle = "#475569";   // axis text
  const GRID_N = 5;
  for (let i = 0; i <= GRID_N; i++) {
    const y = yMin + (yMax - yMin) * (i / GRID_N);
    const py = yToPx(y);
    ctx.beginPath(); ctx.moveTo(padL, py); ctx.lineTo(W - padR, py); ctx.stroke();
    ctx.fillText(y.toFixed(1), 4, py + 3);
  }
  for (let i = 0; i <= GRID_N; i++) {
    const x = xMin + (xMax - xMin) * (i / GRID_N);
    const px = xToPx(x);
    ctx.fillText(x.toFixed(0), px - 10, H - padB + 14);
  }

  // horizontal reference lines (e.g. legacy fixed threshold)
  for (const h of options.hLines || []) {
    const py = yToPx(h.y);
    ctx.strokeStyle = h.color || "#b91c1c";
    ctx.setLineDash([6, 4]);
    ctx.beginPath(); ctx.moveTo(padL, py); ctx.lineTo(W - padR, py); ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = h.color || "#b91c1c";
    ctx.fillText(h.label || "", padL + 6, py - 4);
  }

  // vertical marker lines (e.g. defect frequencies)
  for (const v of options.vLines || []) {
    const px = xToPx(v.x);
    ctx.strokeStyle = v.color || "#1d4ed8";
    ctx.setLineDash([4, 3]);
    ctx.beginPath(); ctx.moveTo(px, padT); ctx.lineTo(px, H - padB); ctx.stroke();
    ctx.setLineDash([]);
    ctx.save();
    ctx.fillStyle = v.color || "#1d4ed8";
    ctx.translate(px + 3, padT + 10);
    ctx.fillText(v.label || "", 0, 0);
    ctx.restore();
  }

  // series lines
  for (const s of series) {
    ctx.strokeStyle = s.color || "#0369a1";
    ctx.lineWidth = 1.6;
    ctx.beginPath();
    s.points.forEach(([x, y], i) => {
      const px = xToPx(x), py = yToPx(y);
      if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
    });
    ctx.stroke();
  }

  // axis labels
  ctx.fillStyle = "#0d1520";
  ctx.font = "11px Segoe UI, Arial";
  if (options.yLabel) ctx.fillText(options.yLabel, 6, 12);
  if (options.xLabel) ctx.fillText(options.xLabel, W - padR - 60, H - 4);

  // legend
  let lx = padL;
  for (const s of series) {
    ctx.fillStyle = s.color || "#0369a1";
    ctx.fillRect(lx, 2, 10, 10);
    ctx.fillStyle = "#0d1520";
    ctx.fillText(s.label, lx + 14, 11);
    lx += 14 + ctx.measureText(s.label).width + 16;
  }
}

// ---------------------------------------------------------------------------
// Fleet table + alerts
// ---------------------------------------------------------------------------

async function loadFleet() {
  const fleet = await getJSON("/api/fleet");
  const tbody = document.getElementById("fleet-tbody");
  tbody.innerHTML = "";
  fleet.sort((a, b) => TIER_ORDER[b.severity_tier] - TIER_ORDER[a.severity_tier]);
  for (const u of fleet) {
    // Rows open the detail panel on click. A click-only affordance is unusable
    // without a mouse, so the row carries a tab stop, a button role and an
    // Enter/Space handler -- three attributes that must travel together or the
    // row announces itself as interactive and then does nothing.
    const tr = el("tr", {
      "data-unit": u.unit_id,
      tabindex: "0",
      role: "button",
      "aria-label": `Open detail for unit ${u.unit_id}, ${u.severity_tier}`,
    });

    // Unit + Rail Car icon
    const unitCell = el("td", {});
    unitCell.appendChild(AxiomIcons.icon("railcar", { size: 18, state: "normal" }));
    unitCell.appendChild(document.createTextNode(" " + u.unit_id));
    tr.appendChild(unitCell);

    tr.appendChild(el("td", { text: u.car }));
    tr.appendChild(el("td", { text: String(u.axle) }));
    tr.appendChild(el("td", { text: `${(u.speed_mps * 2.237).toFixed(0)} mph` }));

    // Temperature with bearing indicator
    const tempCell = el("td", {});
    const tempStatus = u.peak_temp_f > (u.ambient_temp_f + 170) ? "critical" :
                       u.peak_temp_f > (u.ambient_temp_f + 115) ? "warning" : "normal";
    tempCell.appendChild(AxiomIcons.icon("bearing", { size: 18, state: tempStatus }));
    tempCell.appendChild(document.createTextNode(` ${u.peak_temp_f.toFixed(1)}°F`));
    tr.appendChild(tempCell);

    const badgeCell = el("td", {});
    badgeCell.appendChild(el("span", { class: `badge ${tierClass(u.severity_tier)}`, text: u.severity_tier }));
    if (u.severity_tier !== "INFORMATIONAL") {
      badgeCell.appendChild(el("span", {
        class: "corroborated-tag",
        text: u.corroborated ? "✓ corroborated (2+ signals agree)"
                              : "⚠ single signal — capped at REVIEW",
      }));
    }
    tr.appendChild(badgeCell);
    const open = () => showDetail(u.unit_id);
    tr.addEventListener("click", open);
    tr.addEventListener("keydown", (ev) => {
      if (ev.key === "Enter" || ev.key === " ") {
        ev.preventDefault();   // Space would otherwise scroll the page
        open();
      }
    });
    tbody.appendChild(tr);
  }
}

async function loadAlerts() {
  const warrants = await getJSON("/api/alerts");
  const list = document.getElementById("alerts-list");
  list.innerHTML = "";
  if (warrants.length === 0) {
    list.appendChild(el("p", { class: "summary", text: "No Ghost Warrants open across the fleet right now." }));
    return;
  }
  for (const w of warrants) {
    const div = el("div", { class: "warrant" });
    const head = el("div", { class: "warrant-head" });
    head.appendChild(el("span", { class: "advisory-id", text: w.advisory_id }));
    head.appendChild(el("span", { text: `${w.asset_id} — ${w.train_consist}` }));
    head.appendChild(el("span", { class: `badge ${tierClass(w.severity_tier)}`, text: w.severity_tier }));
    head.appendChild(el("span", {
      class: "corroborated-tag",
      text: w.corroborated ? "corroborated" : "single signal — capped at REVIEW",
    }));
    div.appendChild(head);
    div.appendChild(el("p", { class: "summary", text: `Confidence: ${w.confidence}. Recommended response: ${w.recommended_response}` }));

    const ul = el("ul", { class: "evidence-list" });
    for (const e of w.evidence) {
      const flagged = e.severity !== "normal";
      ul.appendChild(el("li", {
        class: flagged ? "flagged" : "",
        text: `${flagged ? "⚠" : "·"} ${e.signal_type.replace(/_/g, " ")} [${e.severity}] — ${e.detail}`,
      }));
    }
    div.appendChild(ul);
    div.appendChild(buildDispositionForm(w));
    list.appendChild(div);
  }
}

const DISPOSITION_OPTIONS = [
  ["concur_dispatch", "Concur & Dispatch"],
  ["escalate", "Escalate to Engineering"],
  ["override_downgrade", "Override / Downgrade"],
  ["reject_sensor", "Reject Sensor Hardware"],
];

// --- Session state (AD-2) ---
// Held in a module variable and deliberately *not* in localStorage or
// sessionStorage. A bearer token in web storage survives a tab close and is
// readable by any script that ever runs on this origin; on an air-gapped box the
// reviewer will sign in once per shift, which is the correct cost.
let SESSION = null; // { token, reviewer_name, cert_id, expires_at }

const AUTH_MODE_NOTE =
  "Disposition entry requires a reviewer account. No account exists on this " +
  "deployment, so entry is closed. An administrator must enroll a reviewer " +
  "bound to a live certification (tools/seed_demo_account.py).";

function authHeaders() {
  return SESSION ? { "Authorization": "Bearer " + SESSION.token } : {};
}

function clearSession() {
  SESSION = null;
}

async function signIn(username, passphrase) {
  const r = await fetch("/api/session", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username: username, passphrase: passphrase }),
  });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.error || `HTTP ${r.status}`);
  SESSION = data;
  return data;
}

async function signOut() {
  if (!SESSION) return;
  try {
    await fetch("/api/session", { method: "DELETE", headers: authHeaders() });
  } catch (_) { /* signing out locally still must succeed */ }
  clearSession();
}

function buildDispositionForm(w) {
  const form = el("form", { class: "disposition-form" });
  const select = el("select", {});
  for (const [val, label] of DISPOSITION_OPTIONS) {
    select.appendChild(el("option", { value: val, text: label }));
  }
  const noteInput = el("input", {
    type: "text", placeholder: "Note (optional, 500 chars)", maxLength: "500",
  });
  const submit = el("button", { type: "submit", text: "Record Disposition" });
  const status = el("span", { class: "disposition-status" });
  const who = el("span", { class: "disposition-who" });

  // The reviewer name and certification ID are no longer inputs. They come from
  // the signed-in session, and the server refuses a body that tries to set them.
  // A text box here would be a lie about what the row will say.
  form.appendChild(who);
  form.appendChild(select);
  form.appendChild(noteInput);
  form.appendChild(submit);
  form.appendChild(status);

  function renderIdentity() {
    if (SESSION) {
      who.textContent = `${SESSION.reviewer_name} (${SESSION.cert_id})`;
      who.className = "disposition-who signed-in";
      submit.disabled = false;
    } else {
      who.textContent = "Not signed in — no decision can be recorded.";
      who.className = "disposition-who signed-out";
      submit.disabled = true;
    }
  }
  renderIdentity();

  // Existing decisions are shown, not hidden. A reviewer recording a second
  // disposition should be able to see what they are superseding.
  const history = el("div", { class: "disposition-history" });
  form.appendChild(history);

  async function loadHistory() {
    try {
      const r = await fetch(`/api/warrant/${w.advisory_id}/disposition`);
      if (!r.ok) return;
      const data = await r.json();
      history.textContent = "";
      if (!data.count) return;
      const head = el("div", { class: "disposition-history-head" }, [
        el("span", {
          text: `${data.count} recorded decision${data.count === 1 ? "" : "s"}`,
        }),
        el("span", {
          class: data.chain_ok ? "chain-ok" : "chain-bad",
          text: data.chain_ok ? "chain verified" : "CHAIN BROKEN",
        }),
      ]);
      history.appendChild(head);
      for (const rec of data.history) {
        const row = el("div", { class: "disposition-history-row" }, [
          el("span", { class: "dh-when", text: rec.recorded_at }),
          el("span", { class: "dh-who", text: `${rec.reviewer_name} (${rec.cert_id})` }),
          el("span", { class: "dh-what", text: rec.disposition_label }),
        ]);
        if (rec.note) row.appendChild(el("span", { class: "dh-note", text: rec.note }));
        history.appendChild(row);
      }
    } catch (_) { /* history is informative; failing to load it must not block a review */ }
  }

  form.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    if (!SESSION) {
      status.textContent = "Sign in before recording a decision.";
      return;
    }
    status.textContent = "Saving...";
    try {
      const r = await fetch(`/api/warrant/${w.advisory_id}/disposition`, {
        method: "POST",
        headers: Object.assign({ "Content-Type": "application/json" }, authHeaders()),
        // No reviewer_name, no cert_id: the server takes both from the token and
        // refuses the request if either key appears here.
        body: JSON.stringify({
          disposition: select.value,
          note: noteInput.value,
        }),
      });
      if (r.status === 401) {
        clearSession();
        renderIdentity();
        throw new Error((await r.json()).error || "session expired");
      }
      if (!r.ok) throw new Error((await r.json()).error || `HTTP ${r.status}`);
      const saved = await r.json();
      status.textContent = saved.supersedes_id
        ? `Appended (supersedes record #${saved.supersedes_id}).`
        : "Recorded.";
      noteInput.value = "";
      await loadHistory();
      await loadAlerts();
    } catch (e) {
      status.textContent = `Error: ${e.message}`;
    }
  });

  loadHistory();
  return form;
}

// ---------------------------------------------------------------------------
// Detail panel: thermo / acoustics / kinematics for one unit
// ---------------------------------------------------------------------------

async function showDetail(unitId) {
  const panel = document.getElementById("detail-panel");
  panel.hidden = false;
  document.getElementById("detail-title").textContent = `Unit ${unitId}`;
  panel.scrollIntoView({ behavior: "smooth" });

  const [thermo, fft, kin] = await Promise.all([
    getJSON(`/api/unit/${unitId}/thermo`),
    getJSON(`/api/unit/${unitId}/acoustics`),
    getJSON(`/api/unit/${unitId}/kinematics`),
  ]);

  renderThermo(thermo);
  renderFFT(fft);
  renderKinematics(kin);
}

function renderThermo(d) {
  const points = d.times_s.map((t, i) => [t / 60.0, d.temps_f[i]]);
  const rightPoints = d.times_s.map((t, i) => [t / 60.0, d.temps_right_f[i]]);
  const ambientDeltaLine = d.ambient_temp_f + 170.0; // legacy critical: 170F ABOVE ambient, not a flat number
  drawLineChart(document.getElementById("chart-thermo"),
    [
      { label: "Left journal (F)", points, color: "#0369a1" },
      { label: "Right journal (F)", points: rightPoints, color: "#047857" },
    ],
    {
      yLabel: "deg F", xLabel: "minutes",
      hLines: [
        { y: ambientDeltaLine, label: `legacy critical (170F above ${d.ambient_temp_f.toFixed(0)}F ambient)`, color: "#b91c1c" },
        { y: d.ambient_temp_f, label: "ambient", color: "#475569" },
      ],
    });

  const peakF = Math.max(...d.temps_f);
  const worst = d.alerts[d.alerts.length - 1];
  const lines = [];
  lines.push(`Peak ${peakF.toFixed(1)}F, ambient ${d.ambient_temp_f.toFixed(0)}F ` +
    `(legacy point-in-time check: ${d.legacy.legacy_status}, ${d.legacy.delta_f.toFixed(1)}F above ambient).`);
  lines.push(worst
    ? `Rate-of-change z-score flagged ${d.alerts.length} point(s); most recent: ${worst.severity} ` +
      `(${worst.rate_f_per_min.toFixed(2)} F/min, z=${worst.zscore.toFixed(1)}).`
    : `Rate-of-change z-score: no abnormal heating rate detected.`);
  lines.push(`Vs. this axle's own history (${20} passes): ${d.peer_historical.severity} ` +
    `(robust z=${d.peer_historical.robust_z.toFixed(1)}). Vs. cross-fleet peers: ${d.peer_cross_fleet.severity} ` +
    `(robust z=${d.peer_cross_fleet.robust_z.toFixed(1)}).`);
  const diff = d.differential;
  lines.push(`Same-axle L/R differential: |${diff.temp_left_f.toFixed(1)}F - ${diff.temp_right_f.toFixed(1)}F| = ` +
    `${diff.diff_f.toFixed(1)}F (limit ${diff.critical_diff_f.toFixed(0)}F) — ${diff.status}.`);
  document.getElementById("thermo-summary").textContent = lines.join(" ");
}

function renderFFT(d) {
  const points = d.spectrum_freqs_hz.map((f, i) => [f, d.spectrum_magnitude[i]]);
  const vLines = Object.entries(d.defect_frequencies_hz).map(([label, hz]) => ({
    x: hz, label, color: d.peaks[label].found ? "#b91c1c" : "#475569",
  }));
  drawLineChart(document.getElementById("chart-fft"),
    [{ label: "FFT magnitude", points, color: "#b45309" }],
    { yLabel: "amplitude", xLabel: "Hz", vLines });

  const hits = Object.entries(d.peaks).filter(([, p]) => p.found);
  document.getElementById("fft-summary").textContent = hits.length
    ? `Shaft rotation ${d.shaft_hz.toFixed(2)} Hz. Defect match: ` +
      hits.map(([label, p]) => `${label} at ${p.peak_hz.toFixed(1)}Hz (${p.sigma_above_noise.toFixed(1)}σ above noise floor)`).join("; ")
    : `Shaft rotation ${d.shaft_hz.toFixed(2)} Hz. No bearing defect frequency stands out above the noise floor.`;
}

function renderKinematics(d) {
  const points = d.profile.distances_m.map((dist, i) => [dist, d.profile.velocities_mps[i] * 2.237]);
  drawLineChart(document.getElementById("chart-coast"),
    [{ label: "Speed (mph)", points, color: "#047857" }],
    { yLabel: "mph", xLabel: "meters coasted" });

  const mph = (v) => (v * 2.237).toFixed(1);
  let summary;
  if (d.profile.will_accelerate_on_grade) {
    summary = `On this ${d.grade_percent.toFixed(1)}% descending grade, gravity alone exceeds rolling ` +
      `resistance: with throttle at idle and NO brake applied, this axle's car would accelerate from ` +
      `${mph(d.initial_speed_mps)} mph toward a terminal velocity near ` +
      `${mph(d.profile.velocities_mps[d.profile.velocities_mps.length - 1])} mph as drag catches up -- ` +
      `braking input is required here, coasting alone will not control speed.`;
  } else {
    summary = `On this ${d.grade_percent.toFixed(1)}% grade, coasting from ${mph(d.initial_speed_mps)} mph ` +
      `(KE=${(d.initial_kinetic_energy_j / 1e6).toFixed(2)} MJ) comes to a stop after ` +
      `${d.profile.stop_distance_m.toFixed(0)} m / ${d.profile.stop_time_s.toFixed(0)} s.`;
  }
  document.getElementById("coast-summary").textContent = summary;
}

// ---------------------------------------------------------------------------

// State carried three ways, so it survives a monochrome print, a colour-blind
// reader and a screen reader: the top-edge bar (state-*), the number's colour
// (good/bad/accent), and the icon's own state colour. All three come from `cls`
// so they cannot drift apart.
const KPI_STATE = { good: "state-ok", bad: "state-bad", accent: "state-warn" };
const KPI_ICON_STATE = { good: "normal", bad: "critical", accent: "warning" };

function kpiCard(label, value, cls, sub, iconName) {
  const state = KPI_STATE[cls] || "";
  const card = el("div", { class: `kpi-card ${state}` });

  const head = el("div", { class: "kpi-head" });
  if (iconName) {
    head.appendChild(AxiomIcons.icon(iconName, {
      size: 15, state: KPI_ICON_STATE[cls] || "normal",
    }));
  }
  head.appendChild(el("div", { class: "kpi-label", text: label }));
  card.appendChild(head);

  card.appendChild(el("div", { class: `kpi-value ${cls || ""}`, text: value }));
  if (sub) card.appendChild(el("div", { class: "kpi-sub", text: sub }));
  return card;
}

async function loadROI() {
  const roi = await getJSON("/api/roi");
  const strip = document.getElementById("kpi-strip");
  strip.innerHTML = "";

  const fmtUsd = (n) => `$${(n / 1000).toFixed(0)}k`;

  strip.appendChild(kpiCard(
    "Fleet Mission-Ready", `${roi.mission_ready_pct.toFixed(1)}%`,
    roi.mission_ready_pct >= 90 ? "good" : "accent",
    `${roi.fleet_size} axles monitored`,
    "gauge",
  ));
  strip.appendChild(kpiCard(
    "Net Estimated Benefit", fmtUsd(roi.net_estimated_benefit_usd), "good",
    `${roi.estimated_failures_avoided} corroborated defect(s) × $${(roi.expected_cost_per_missed_defect_usd / 1e6).toFixed(1)}M expected cost/miss`,
    "currency",
  ));
  strip.appendChild(kpiCard(
    "Mean Time To Detect", `${roi.axiom_mttd_hours.toFixed(2)} hrs`, "accent",
    `vs. ${roi.legacy_mttd_hours.toFixed(1)} hrs legacy (${roi.mttd_improvement_pct.toFixed(0)}% faster)`,
    "clock",
  ));
  strip.appendChild(kpiCard(
    "Open Reviews", `${roi.urgent_review_count + roi.review_count}`,
    roi.urgent_review_count > 0 ? "bad" : "good",
    `${roi.urgent_review_count} urgent · ${roi.review_count} single-signal`,
    "warrant",
  ));

  const noteEl = document.getElementById("kpi-note");
  noteEl.innerHTML = "";
  noteEl.appendChild(el("div", { text: `Sourced: ${roi.sourced_note}` }));
  noteEl.appendChild(el("div", { text: `Assumptions: ${roi.assumptions_note}`, style: "margin-top:4px" }));
}

// --- Session UI ---
// Wires the sign-in bar in index.html. Kept out of buildDispositionForm because
// there is one session per page and one sign-in bar, not one per warrant.
function renderSessionBar() {
  const outBox = document.getElementById("session-signed-out");
  const inBox = document.getElementById("session-signed-in");
  if (!outBox || !inBox) return;
  if (SESSION) {
    outBox.hidden = true;
    inBox.hidden = false;
    document.getElementById("session-who").textContent =
      `${SESSION.reviewer_name} (${SESSION.cert_id})`;
    document.getElementById("session-expiry").textContent =
      `session expires ${SESSION.expires_at}`;
  } else {
    outBox.hidden = false;
    inBox.hidden = true;
  }
}

function wireSessionBar() {
  const form = document.getElementById("signin-form");
  const status = document.getElementById("signin-status");
  const btn = document.getElementById("signout-btn");

  if (form) {
    form.addEventListener("submit", async (ev) => {
      ev.preventDefault();
      const u = document.getElementById("signin-username").value;
      const p = document.getElementById("signin-passphrase").value;
      status.textContent = "Signing in...";
      try {
        await signIn(u, p);
        document.getElementById("signin-passphrase").value = "";
        status.textContent = "";
        renderSessionBar();
        await loadAlerts(); // the per-warrant forms read SESSION when they render
      } catch (e) {
        status.textContent = e.message;
      }
    });
  }

  if (btn) {
    btn.addEventListener("click", async () => {
      await signOut();
      renderSessionBar();
      await loadAlerts();
    });
  }

  renderSessionBar();
}

async function init() {
  wireSessionBar();
  await Promise.all([loadROI(), loadFleet(), loadAlerts()]);
}

init();

