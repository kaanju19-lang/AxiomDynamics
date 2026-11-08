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

// --- Industry SVG Icons ---
function svgRailCar(size = 24) {
  const svg = `<svg viewBox="0 0 48 32" width="${size}" height="${size}" style="display:inline-block">
    <rect x="2" y="8" width="44" height="16" rx="2" fill="none" stroke="#0ea5e9" stroke-width="2"/>
    <circle cx="8" cy="28" r="3" fill="#0ea5e9"/>
    <circle cx="40" cy="28" r="3" fill="#0ea5e9"/>
    <line x1="6" y1="24" x2="42" y2="24" stroke="#0ea5e9" stroke-width="1" opacity="0.5"/>
  </svg>`;
  const div = document.createElement('div');
  div.innerHTML = svg;
  return div.firstElementChild;
}

function svgBearing(size = 20, temp = "normal") {
  const colors = { normal: "#10b981", warning: "#f59e0b", critical: "#ef4444" };
  const color = colors[temp] || colors.normal;
  const svg = `<svg viewBox="0 0 40 40" width="${size}" height="${size}" style="display:inline-block">
    <circle cx="20" cy="20" r="18" fill="none" stroke="#e2e8f0" stroke-width="2"/>
    <circle cx="20" cy="20" r="12" fill="none" stroke="${color}" stroke-width="2"/>
    <circle cx="20" cy="20" r="4" fill="${color}" opacity="0.6"/>
    <circle cx="20" cy="6" r="2.5" fill="${color}"/>
    <circle cx="34" cy="20" r="2.5" fill="${color}"/>
    <circle cx="20" cy="34" r="2.5" fill="${color}"/>
    <circle cx="6" cy="20" r="2.5" fill="${color}"/>
  </svg>`;
  const div = document.createElement('div');
  div.innerHTML = svg;
  return div.firstElementChild;
}

function svgTrack(size = 16) {
  const svg = `<svg viewBox="0 0 48 12" width="${size}" height="${size * 0.25}" style="display:inline-block">
    <line x1="4" y1="4" x2="44" y2="4" stroke="#64748b" stroke-width="1.5" stroke-dasharray="2,3"/>
    <line x1="4" y1="8" x2="44" y2="8" stroke="#64748b" stroke-width="1.5" stroke-dasharray="2,3"/>
    <circle cx="10" cy="6" r="0.8" fill="#0ea5e9"/>
    <circle cx="24" cy="6" r="0.8" fill="#0ea5e9"/>
    <circle cx="38" cy="6" r="0.8" fill="#0ea5e9"/>
  </svg>`;
  const div = document.createElement('div');
  div.innerHTML = svg;
  return div.firstElementChild;
}

function svgThermometer(size = 20, temp = "normal") {
  const colors = { normal: "#10b981", warning: "#f59e0b", critical: "#ef4444" };
  const color = colors[temp] || colors.normal;
  const svg = `<svg viewBox="0 0 24 40" width="${size}" height="${size}" style="display:inline-block">
    <rect x="8" y="2" width="8" height="22" rx="4" fill="none" stroke="${color}" stroke-width="2"/>
    <circle cx="12" cy="32" r="6" fill="${color}" opacity="0.7"/>
    <line x1="12" y1="8" x2="12" y2="20" stroke="${color}" stroke-width="2"/>
  </svg>`;
  const div = document.createElement('div');
  div.innerHTML = svg;
  return div.firstElementChild;
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
  ctx.strokeStyle = "#223041";
  ctx.lineWidth = 1;
  ctx.font = "11px Segoe UI, Arial";
  ctx.fillStyle = "#7f93a8";
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
    ctx.strokeStyle = h.color || "#e0624f";
    ctx.setLineDash([6, 4]);
    ctx.beginPath(); ctx.moveTo(padL, py); ctx.lineTo(W - padR, py); ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = h.color || "#e0624f";
    ctx.fillText(h.label || "", padL + 6, py - 4);
  }

  // vertical marker lines (e.g. defect frequencies)
  for (const v of options.vLines || []) {
    const px = xToPx(v.x);
    ctx.strokeStyle = v.color || "#4fd6e0";
    ctx.setLineDash([4, 3]);
    ctx.beginPath(); ctx.moveTo(px, padT); ctx.lineTo(px, H - padB); ctx.stroke();
    ctx.setLineDash([]);
    ctx.save();
    ctx.fillStyle = v.color || "#4fd6e0";
    ctx.translate(px + 3, padT + 10);
    ctx.fillText(v.label || "", 0, 0);
    ctx.restore();
  }

  // series lines
  for (const s of series) {
    ctx.strokeStyle = s.color || "#4fd6e0";
    ctx.lineWidth = 1.6;
    ctx.beginPath();
    s.points.forEach(([x, y], i) => {
      const px = xToPx(x), py = yToPx(y);
      if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
    });
    ctx.stroke();
  }

  // axis labels
  ctx.fillStyle = "#dbe6f0";
  ctx.font = "11px Segoe UI, Arial";
  if (options.yLabel) ctx.fillText(options.yLabel, 6, 12);
  if (options.xLabel) ctx.fillText(options.xLabel, W - padR - 60, H - 4);

  // legend
  let lx = padL;
  for (const s of series) {
    ctx.fillStyle = s.color || "#4fd6e0";
    ctx.fillRect(lx, 2, 10, 10);
    ctx.fillStyle = "#dbe6f0";
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
    const tr = el("tr", { "data-unit": u.unit_id });

    // Unit + Rail Car icon
    const unitCell = el("td", {});
    unitCell.appendChild(svgRailCar(18));
    unitCell.appendChild(document.createTextNode(" " + u.unit_id));
    tr.appendChild(unitCell);

    tr.appendChild(el("td", { text: u.car }));
    tr.appendChild(el("td", { text: String(u.axle) }));
    tr.appendChild(el("td", { text: `${(u.speed_mps * 2.237).toFixed(0)} mph` }));

    // Temperature with bearing indicator
    const tempCell = el("td", {});
    const tempStatus = u.peak_temp_f > (u.ambient_temp_f + 170) ? "critical" :
                       u.peak_temp_f > (u.ambient_temp_f + 115) ? "warning" : "normal";
    tempCell.appendChild(svgBearing(18, tempStatus));
    tempCell.appendChild(document.createTextNode(` ${u.peak_temp_f.toFixed(1)}°F`));
    tr.appendChild(tempCell);

    const badgeCell = el("td", {});
    badgeCell.appendChild(el("span", { class: `badge ${tierClass(u.severity_tier)}`, text: u.severity_tier }));
    if (u.severity_tier !== "INFORMATIONAL") {
      badgeCell.appendChild(el("span", {
        class: "corroborated-tag",
        text: u.corroborated ? "✓ corroborated" : "⚠ single signal",
      }));
    }
    tr.appendChild(badgeCell);
    tr.addEventListener("click", () => showDetail(u.unit_id));
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

function buildDispositionForm(w) {
  const form = el("form", { class: "disposition-form" });
  const nameInput = el("input", { type: "text", placeholder: "Reviewer name", required: "required" });
  const certInput = el("input", { type: "text", placeholder: "Certification ID", required: "required" });
  const select = el("select", {});
  for (const [val, label] of DISPOSITION_OPTIONS) {
    select.appendChild(el("option", { value: val, text: label }));
  }
  const submit = el("button", { type: "submit", text: "Record Disposition" });
  const status = el("span", { class: "disposition-status" });

  form.appendChild(nameInput);
  form.appendChild(certInput);
  form.appendChild(select);
  form.appendChild(submit);
  form.appendChild(status);

  form.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    status.textContent = "Saving...";
    try {
      const r = await fetch(`/api/warrant/${w.advisory_id}/disposition`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          reviewer_name: nameInput.value, cert_id: certInput.value, disposition: select.value,
        }),
      });
      if (!r.ok) throw new Error((await r.json()).error || `HTTP ${r.status}`);
      status.textContent = "Saved.";
      await loadAlerts();
    } catch (e) {
      status.textContent = `Error: ${e.message}`;
    }
  });

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
      { label: "Left journal (F)", points, color: "#4fd6e0" },
      { label: "Right journal (F)", points: rightPoints, color: "#4fe0a0" },
    ],
    {
      yLabel: "deg F", xLabel: "minutes",
      hLines: [
        { y: ambientDeltaLine, label: `legacy critical (170F above ${d.ambient_temp_f.toFixed(0)}F ambient)`, color: "#e0624f" },
        { y: d.ambient_temp_f, label: "ambient", color: "#7f93a8" },
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
    x: hz, label, color: d.peaks[label].found ? "#e0624f" : "#7f93a8",
  }));
  drawLineChart(document.getElementById("chart-fft"),
    [{ label: "FFT magnitude", points, color: "#e0a94f" }],
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
    [{ label: "Speed (mph)", points, color: "#4fe0a0" }],
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

function kpiCard(label, value, cls, sub) {
  const card = el("div", { class: "kpi-card" });
  card.appendChild(el("div", { class: "kpi-label", text: label }));
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
  ));
  strip.appendChild(kpiCard(
    "Net Estimated Benefit", fmtUsd(roi.net_estimated_benefit_usd), "good",
    `${roi.estimated_failures_avoided} corroborated defect(s) × $${(roi.expected_cost_per_missed_defect_usd / 1e6).toFixed(1)}M expected cost/miss`,
  ));
  strip.appendChild(kpiCard(
    "Mean Time To Detect", `${roi.axiom_mttd_hours.toFixed(2)} hrs`, "accent",
    `vs. ${roi.legacy_mttd_hours.toFixed(1)} hrs legacy (${roi.mttd_improvement_pct.toFixed(0)}% faster)`,
  ));
  strip.appendChild(kpiCard(
    "Open Reviews", `${roi.urgent_review_count + roi.review_count}`,
    roi.urgent_review_count > 0 ? "bad" : "good",
    `${roi.urgent_review_count} urgent · ${roi.review_count} single-signal`,
  ));

  const noteEl = document.getElementById("kpi-note");
  noteEl.innerHTML = "";
  noteEl.appendChild(el("div", { text: `Sourced: ${roi.sourced_note}` }));
  noteEl.appendChild(el("div", { text: `Assumptions: ${roi.assumptions_note}`, style: "margin-top:4px" }));
}

async function init() {
  await Promise.all([loadROI(), loadFleet(), loadAlerts()]);
}

init();

