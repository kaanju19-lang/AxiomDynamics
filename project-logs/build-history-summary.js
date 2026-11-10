/**
 * Builds the AxiomDynamics Build History & Working Summary (.docx).
 *
 * Every figure, date, commit hash and document reference in the output was read
 * from the repository, not recalled. Sources, in order of authority:
 *   - git log (37 commits, efb87ed..b946678)
 *   - client-assets/MASTER-BRIEF-DOCKET/D00 Part VI (the gap register)
 *   - project-logs/{CURRENT-STATE.md, chat-1,chat-2,chat-3}
 *   - assets/* (internal analysis: Q6, IP strategy, library reconciliation)
 *   - backend/*.py and tests/*.py, executed
 *
 * Run: node project-logs/build-history-summary.js
 * Out: project-logs/AxiomDynamics-Build-History-and-Working-Summary.docx
 */

const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle,
  PageBreak, Header, Footer, PageNumber, LevelFormat, TableOfContents,
  convertInchesToTwip,
} = require("docx");

// ---------------------------------------------------------------- palette
const NAVY = "0A1628";
const SLATE = "334155";
const RULE = "B8C0CC";
const BAND = "EEF2F7";
const RED = "9B1C1C";
const GREEN = "065F46";

// ---------------------------------------------------------------- metrics
const PW = 12240;          // US Letter portrait, DXA
const PH = 15840;
const MARGIN = 1080;       // 0.75"
const CONTENT = PW - 2 * MARGIN;   // 10080

// ---------------------------------------------------------------- helpers
const kids = (c) => (Array.isArray(c) ? c : [c]);

function P(text, opts = {}) {
  const {
    size = 21, bold = false, italics = false, color = SLATE, font = "Calibri",
    spaceBefore = 0, spaceAfter = 120, align = AlignmentType.JUSTIFIED,
    style = undefined, keepNext = false, indent = 0,
  } = opts;
  return new Paragraph({
    style,
    keepNext,
    alignment: align,
    spacing: { before: spaceBefore, after: spaceAfter, line: 276 },
    indent: indent ? { left: indent } : undefined,
    children: [new TextRun({ text, size, bold, italics, color, font })],
  });
}

/** Paragraph built from an array of {text, bold, italics, color, size} runs. */
function PR(runs, opts = {}) {
  const { spaceBefore = 0, spaceAfter = 120, align = AlignmentType.JUSTIFIED, indent = 0 } = opts;
  return new Paragraph({
    alignment: align,
    spacing: { before: spaceBefore, after: spaceAfter, line: 276 },
    indent: indent ? { left: indent } : undefined,
    children: runs.map((r) => new TextRun({
      text: r.text,
      bold: !!r.bold,
      italics: !!r.italics,
      color: r.color || SLATE,
      size: r.size || 21,
      font: r.font || "Calibri",
    })),
  });
}

function H1(text) {
  return new Paragraph({ text, heading: HeadingLevel.HEADING_1, pageBreakBefore: true });
}
function H2(text) {
  return new Paragraph({ text, heading: HeadingLevel.HEADING_2 });
}
function H3(text) {
  return new Paragraph({ text, heading: HeadingLevel.HEADING_3 });
}

function BULLET(text, level = 0) {
  return new Paragraph({
    numbering: { reference: "bullets", level },
    alignment: AlignmentType.LEFT,
    spacing: { after: 70, line: 270 },
    children: [new TextRun({ text, size: 21, color: SLATE, font: "Calibri" })],
  });
}

function numbered(ref, items, opts = {}) {
  const { size = 21, color = SLATE } = opts;
  return items.map((t) => new Paragraph({
    numbering: { reference: ref, level: 0 },
    alignment: AlignmentType.LEFT,
    spacing: { after: 70, line: 270 },
    children: [new TextRun({ text: t, size, color, font: "Calibri" })],
  }));
}

const cellBorder = { style: BorderStyle.SINGLE, size: 2, color: RULE };
const CELL_BORDERS = { top: cellBorder, bottom: cellBorder, left: cellBorder, right: cellBorder };

function cell(text, opts = {}) {
  const {
    bold = false, header = false, size = 18, color, width,
    align = AlignmentType.LEFT, mono = false,
  } = opts;
  return new TableCell({
    width: width ? { size: width, type: WidthType.DXA } : undefined,
    borders: CELL_BORDERS,
    shading: header
      ? { type: ShadingType.CLEAR, fill: NAVY, color: "auto" }
      : undefined,
    margins: { top: 70, bottom: 70, left: 90, right: 90 },
    children: [new Paragraph({
      alignment: align,
      spacing: { after: 0, line: 250 },
      children: [new TextRun({
        text: String(text),
        bold: bold || header,
        size,
        color: header ? "FFFFFF" : (color || SLATE),
        font: mono ? "Consolas" : "Calibri",
      })],
    })],
  });
}

/**
 * width: relative flex weights (e.g. [2,3,5]). Converted to DXA sums to CONTENT.
 */
function table(headers, rows, opts = {}) {
  const { width = null, mono = [], size = 18, zebra = true } = opts;
  const n = headers.length;
  const flex = width || Array(n).fill(1);
  const total = flex.reduce((a, b) => a + b, 0);
  const dxa = flex.map((w) => Math.round((w / total) * CONTENT));

  const headerRow = new TableRow({
    tableHeader: true,
    children: headers.map((h, i) => cell(h, { header: true, width: dxa[i], size: 17 })),
  });

  const body = rows.map((r, ri) => new TableRow({
    children: r.map((c, i) => {
      const isMono = mono.includes(i);
      const shaded = zebra && ri % 2 === 1;
      const c2 = cell(c, {
        width: dxa[i], size: isMono ? 16 : size, mono: isMono,
      });
      if (shaded) {
        c2.options = c2.options || {};
      }
      return c2;
    }),
  }));

  return new Table({
    width: { size: CONTENT, type: WidthType.DXA },
    columnWidths: dxa,
    borders: CELL_BORDERS,
    rows: [headerRow, ...body],
  });
}

/** A tinted callout box: a one-cell table with a label. */
function callout(label, text, opts = {}) {
  const { fill = BAND, labelColor = NAVY, textColor = SLATE } = opts;
  return new Table({
    width: { size: CONTENT, type: WidthType.DXA },
    columnWidths: [CONTENT],
    borders: {
      top: { style: BorderStyle.SINGLE, size: 2, color: RULE },
      bottom: { style: BorderStyle.SINGLE, size: 2, color: RULE },
      left: { style: BorderStyle.SINGLE, size: 18, color: NAVY },
      right: { style: BorderStyle.SINGLE, size: 2, color: RULE },
    },
    rows: [new TableRow({
      children: [new TableCell({
        width: { size: CONTENT, type: WidthType.DXA },
        shading: { type: ShadingType.CLEAR, fill, color: "auto" },
        margins: { top: 120, bottom: 120, left: 160, right: 140 },
        children: [
          new Paragraph({
            spacing: { after: 60 },
            children: [new TextRun({ text: label, bold: true, size: 18, color: labelColor, font: "Calibri" })],
          }),
          ...kids(typeof text === "string"
            ? [new Paragraph({
              alignment: AlignmentType.JUSTIFIED,
              spacing: { after: 0, line: 264 },
              children: [new TextRun({ text, size: 19, color: textColor, font: "Calibri" })],
            })]
            : text),
        ],
      })],
    })],
  });
}

function spacer(h = 120) {
  return new Paragraph({ spacing: { after: h }, children: [] });
}

// ================================================================ CONTENT
const doc = [];

// ---------------------------------------------------------------- cover
doc.push(
  new Paragraph({
    spacing: { before: 2400, after: 0 },
    alignment: AlignmentType.LEFT,
    children: [new TextRun({
      text: "AXIOMDYNAMICS", bold: true, size: 28, color: NAVY, font: "Calibri",
      characterSpacing: 120,
    })],
  }),
  new Paragraph({
    spacing: { before: 40, after: 200 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 12, color: NAVY, space: 8 } },
    children: [new TextRun({
      text: "Build History & Working Summary",
      bold: true, size: 56, color: NAVY, font: "Calibri",
    })],
  }),
  P("Physics-first predictive maintenance for freight rail", {
    size: 26, color: SLATE, spaceAfter: 120,
  }),
  P("A complete, stage-by-stage account of how this project was built — the code, the docket, the commercial model, the internal strategy, and the record of what was lost and rebuilt.", {
    size: 21, color: SLATE, spaceAfter: 400,
  }),
);

doc.push(table(
  ["Field", "Value"],
  [
    ["Document", "Build History & Working Summary"],
    ["Prepared", "2026-11-09, at the opening of chat-3"],
    ["Scope", "Repository as it stands at commit b946678 — 37 commits, 80 tracked files"],
    ["Purpose", "Standing reference before the next build phase; replaces the memory of a conversation that no longer exists"],
    ["Classification", "Internal. Contains commercial strategy and a candid record of failures. Not for customer distribution."],
    ["Companion", "project-logs/CURRENT-STATE.md (state), assets/ (analysis), client-assets/MASTER-BRIEF-DOCKET/ (deliverables)"],
  ],
  { width: [2, 8], size: 18 },
));

doc.push(spacer(300));
doc.push(callout(
  "How to read this document",
  "This is written to be read cold, without the conversation it describes. Every claim traces to a file in the repository. Where a figure is a modelling assumption rather than a sourced fact, it says so. Where the documents and the code disagree, this document says which one wins — and in three places it records disagreements that are still unresolved, because a summary that smoothed them over would recreate the exact failure this project keeps having to correct.",
));

// ---------------------------------------------------------------- TOC
doc.push(new Paragraph({ children: [new PageBreak()] }));
doc.push(new Paragraph({
  spacing: { after: 240 },
  children: [new TextRun({ text: "Contents", bold: true, size: 34, color: NAVY, font: "Calibri" })],
}));
doc.push(new TableOfContents("Contents", {
  hyperlink: true,
  headingStyleRange: "1-3",
}));
// A word-field TOC renders empty until Word updates fields. The static list
// below means the printed/PDF copy is still navigable without that step.
doc.push(spacer(240));
doc.push(P("Parts", { size: 17, bold: true, color: NAVY, spaceAfter: 100 }));
doc.push(table(
  ["Part", "Covers"],
  [
    ["I", "What the product is, why physics rather than ML, and the six models"],
    ["II", "Stage 0–5: the eight stages of the build, 37 commits, and every correction"],
    ["III", "The 38-artifact docket, document by document, and the precedence ladder"],
    ["IV", "The loss of chat-1's work — mechanism, cost, and the rules that came out of it"],
    ["V", "What chat-2 rebuilt, and how it verified the rebuild"],
    ["VI", "Internal strategy in assets/: entity, IP and exit, carrier dossiers"],
    ["VII", "Open items — including two unresolved commercial-modelling findings"],
    ["VIII", "How to resume: read order, state checks, push, and the decisions waiting"],
    ["A", "Appendix — repository map, commit chronology, status at a glance"],
  ],
  { width: [1, 9], size: 17 },
));

// ================================================================ PART I
doc.push(H1("Part I — What this project is"));

doc.push(P("AxiomDynamics is a predictive-maintenance product for freight rail, built on named physical models rather than machine learning. It monitors freight car axles, derives a condition estimate from wayside detector signals, and presents ranked advisories — called Ghost Warrants — to a certified human reviewer who records a decision. The platform does not decide anything. That boundary is the product's central commercial and legal fact, and it is stated identically in B01, B02, C02, D02, D07, D08 and D12."));

doc.push(H2("The governing idea"));
doc.push(P("The original instruction, restated in the user's own words and never varied since, was to build the system on real physics: named physical laws, rolling per-axle z-scores, kinematics from Eₖ = ½mv², acoustics against the standard bearing defect-frequency equations (BPFO, BPFI, BSF, FTF) — explicitly not black-box ML and not fixed absolute alarm thresholds. The standing instruction that captured this is: \"We will keep this same concept throughout.\" It has been honoured across all 37 commits."));

doc.push(H2("Why physics rather than ML — the argument, not the preference"));
doc.push(P("The argument is written into the documents themselves, most directly in B02 §3 and D08 §1, and it has four parts:"));
doc.push(...numbered("numA", [
  "A learned model cannot be explained to a regulator. A physics model can be audited line by line, and its output recomputed from its input by anyone holding the documentation.",
  "A learned model changes behaviour when retrained. A deterministic model gives the same answer today and in five years, which is what makes a disposition defensible two years after it was recorded.",
  "A learned model cannot be reproduced by the railroad's own engineer. The buyer here is a Class I carrier's engineering and safety organisation, which is professionally hostile to unexplained outputs.",
  "A learned model requires a data supply chain. A physics engine running on one dependency in an air-gapped box requires none — which is the platform's principal security argument (B04, B05).",
]));

doc.push(H2("The six models"));
doc.push(table(
  ["#", "Model", "Physical basis", "What it catches that legacy practice misses"],
  [
    ["1", "Thermodynamics (rate of change)", "Rolling dT/dt, z-scored against the axle's own trailing baseline. Thresholds: watch 2.5σ, warning 3.5σ, critical 5.0σ, floored by a 0.4 °F/min minimum to suppress noise on flat traces.", "A bearing heating rapidly that has not yet crossed a fixed absolute alarm. This is the East Palestine failure mode."],
    ["2", "Peer comparison", "Robust median/MAD z-score: Z = (x − median(P)) ÷ (1.4826 × MAD(P)). The 1.4826 constant makes MAD a consistent estimator of σ.", "A reading judged against what is normal for that axle and for its peers, rather than in isolation. Resistant to one or two extreme peer readings."],
    ["3", "Kinematics", "Eₖ = ½mv², plus grade (gravity), rolling resistance (Davis-style) and aerodynamic drag, integrated numerically at dt = 0.5 s.", "Whether a car will stop or run away on a given grade if it goes to idle — and, inverted, whether an unusual coasting profile indicates excessive rolling resistance."],
    ["4", "Acoustics", "FFT (Hann window, rFFT) against the four standard rolling-element defect frequencies, requiring the peak to stand 4σ above a broadband noise floor estimated excluding a guard band.", "A specific defect frequency standing out above noise, rather than a generic \"weird sound\" classifier. A loud but broadband-noisy spectrum does not false-positive."],
    ["5", "Same-axle differential", "Absolute left/right journal temperature difference, critical at 95 °F.", "A one-sided defect — one journal failing while both run at similar load and speed. Independent of absolute level, so heavy load or high ambient does not mask it."],
    ["6", "ROI panel", "Blended expected cost per missed defect from two sourced cost tiers plus an assumed escalation probability.", "Presents the economic case in the operator's own units, with sourced and assumed figures visibly separated."],
  ],
  { width: [0.4, 2, 4.2, 4.4], size: 16 },
));

doc.push(H3("The seventh element, which is not a model"));
doc.push(P("Evidence fusion into Ghost Warrants is the piece that turns six signals into something a safety department can act on. It lives in backend/warrants.py and has two design decisions worth stating plainly, because both are load-bearing:"));
doc.push(...numbered("numB", [
  "Severity tiers are named INFORMATIONAL, REVIEW and URGENT REVIEW — never watch/warning/critical. The rename exists so that no reader can mistake these for operational alarm levels. The platform never issues a stop-train or braking instruction.",
  "Escalation to URGENT REVIEW requires corroboration: at least two independent signal types must agree. A single signal, however severe, is capped at REVIEW. One noisy sensor cannot manufacture a false urgent case on its own.",
]));
doc.push(P("Every warrant carries a SHA-256 hash over a canonical JSON serialisation of its advisory ID, asset, timestamp, full evidence array and both model and reference-population versions. That is what makes the record tamper-evident at the individual-warrant level — and it is a different claim from the ledger being append-only, which it is not yet (see Part VII)."));

// ================================================================ PART II
doc.push(H1("Part II — Stage-by-stage build chronology"));

doc.push(P("The build ran in eight distinct stages across 37 commits, from 2026-11-08 00:53 to 2026-11-09 22:02. The stages below follow the git history. Commit hashes and dates are taken from the log, not recollected."));

doc.push(callout(
  "Reading the chronology",
  "Each stage states what triggered it, what was produced, what was corrected, and what it left open. The corrections matter more than the builds — nearly every defect in this project was found by checking a document against the code rather than by reading the document, and that pattern is the single most useful thing in this history.",
));

// ---- Stage 0
doc.push(H2("Stage 0 — The demonstration application (2026-11-08, 00:53–02:31)"));
doc.push(P("Commits: efb87ed (initial, 17 files, 2,806 lines), 3b25d86, ce64e0a, 0796015."));
doc.push(P("The project began as a working web application, not a document set. The initial commit contained the complete backend physics engine, a synthetic fleet generator, a stdlib HTTP server, a vanilla-JS dashboard and 21 physics tests — a running demonstration from the first commit, which is unusual and which set the tone for everything after."));
doc.push(H3("What was built"));
doc.push(BULLET("backend/physics.py — the three physics modules (thermodynamics, kinematics, acoustics) plus the two legacy-comparison checks (ambient-relative alarm, same-axle differential) and the robust MAD peer z-score. Every function names the textbook equation it implements in its docstring."));
doc.push(BULLET("backend/simulate.py — synthetic fleet and sensor-trace generator. Eight units across four scenarios (normal, thermal fault, acoustic fault, both). Unit U3 is deliberately modelled on the East Palestine conditions: 10 °F ambient, a slow thermal ramp, a descending grade."));
doc.push(BULLET("backend/main.py — stdlib http.server, no framework, serving both the API and the static frontend."));
doc.push(BULLET("frontend/ — vanilla JS canvas charts, no CDN, no build step, no npm."));
doc.push(BULLET("tests/test_physics.py — 21 tests covering every formula, including a test that the ambient-relative check reproduces the East Palestine reading."));
doc.push(H3("The visual iterations"));
doc.push(P("Three further commits refined the interface: an enterprise dispatch-centre aesthetic (3b25d86), a light professional redesign (ce64e0a), and a set of hand-drawn SVG rail assets — car icons, bearing indicators with temperature status, track diagrams (0796015). The third commit's message is worth recording because it names the intent: \"professional visual elements to create authentic railroad tool feel.\""));
doc.push(H3("Why the technical choices were made"));
doc.push(P("The README states the reasoning, and it is architectural rather than stylistic: no FastAPI, no Chart.js, no npm, no CDN. Python standard library plus numpy for FFT and array math. The reason given is the actual deployment story — an air-gapped wayside or dispatch environment where IT will not approve installing a dependency tree on a live network. That decision, taken at the first commit, is what later makes B04, B05 and D09's air-gap guarantee possible to state honestly: there is exactly one third-party runtime dependency, and no outbound network path anywhere in the code."));
doc.push(callout(
  "The honest limitation, stated from the start",
  "There is no freely downloadable public real-time rail wayside sensor dataset, and the build environment had no outbound internet to fetch one anyway. So simulate.py generates traces from the same equations in physics.py, with documented fault conditions injected. To point the platform at real data later, three generate_* functions are replaced with loaders returning the same shapes — physics.py and main.py do not care where the samples came from. This limitation later becomes the docket's largest disclosed gap: there is no detector ingest path at all.",
));

// ---- Stage 1
doc.push(H2("Stage 1 — The commercial model (2026-11-08, 08:22–12:25)"));
doc.push(P("Commits: 2b7aa6c, f1f705e, dd3c1d5, c995c76, 549f36d, 668e5eb, 0dda8d3."));
doc.push(P("Once the demonstration existed, the next question was what to charge for it. This stage produced the entire commercial structure, and it did so through three corrections that are the most instructive part of the history."));
doc.push(H3("1a — The first cost model, and the weakness found inside it (2b7aa6c, f1f705e)"));
doc.push(P("The first commit added an external pilot cost structure document. The second built the client-assets tree with the Excel ROI calculator, and — critically — its commit message records a finding rather than a delivery: \"document tier-1 pricing weakness found in the model.\" The initial flat-tier structure returned only 1.5× at the entry tier."));
doc.push(H3("1b — Re-pricing to marginal bands (dd3c1d5)"));
doc.push(P("The correction. A flat tier structure charges one rate for the whole axle count, which produces a cliff: a customer with 501 axles pays the 500–2,000 rate on all 501, so doubling the fleet more than doubles the bill and the customer's return gets worse as they expand. That is the opposite of what a fleet-scale economics product should do."));
doc.push(P("The fix was marginal bands — each band charges only for the axles inside it — which makes the return improve monotonically with fleet size and rewards expansion rather than punishing it. The rates set were $600 for the first 500 axles, $500 for the next 1,500, and $375 above 2,000. The commit message names both defects it fixed: \"fixes tier-1 sub-2x return and a cliff that made ROI fall as fleets grew.\""));
doc.push(H3("1c — The second pricing axis (c995c76)"));
doc.push(P("A more important realisation: axle count prices assets, but a railroad's cost is also driven by geography. Two deployments with identical axle counts are not the same job if one is a single classification yard and the other spans eleven subdivisions. Every location needs its own edge compute, detector integration, commissioning trip, network path and support coverage."));
doc.push(P("So a second axis was added: $45,000 per monitored site per year beyond the first, with the first site included in the base licence. This produced the single most important commercial fact in the docket — that at fixed axle count, spreading across sites destroys the economics. Holding 500 axles constant and moving from one site to eleven raises cost 114% and more than doubles unit cost, from $2,360 to $5,060 per axle over three years."));
doc.push(H3("1d — Market intelligence (c995c76, 549f36d, 0dda8d3)"));
doc.push(P("The same stage produced three carrier dossiers — BNSF, UP/NS combined, and CN/CPKC — so that the sales conversation could be conducted in the customer's own units and geography. The UP/NS commit carries a strategy correction in its message: \"correct carrier strategy for $85B merger.\" The merger changes who the buyers are and which of them are competitors to each other, which matters for the eventual IP strategy (Part VI)."));
doc.push(P("These dossiers were originally placed in client-assets/ and were later moved to assets/ — see Stage 2."));

// ---- Stage 2
doc.push(H2("Stage 2 — The classification rule, and the restructuring it forced (2026-11-08, 15:30–15:45)"));
doc.push(P("Commits: ed10875 (restructure), 487c378 (stop tracking runtime state)."));
doc.push(P("This is a small stage with a large consequence, and it establishes the working rule the project still uses."));
doc.push(H3("The rule"));
doc.push(callout(
  "The classification rule, still in force",
  "If a customer could read it, it goes in client-assets/. If it is about us — our strategy, our weaknesses, our playbook, our research — it goes in assets/. This is not a filing preference. client-assets/ is presumed forwardable to a Class I railroad's legal and procurement teams: anything there may be attached to an email without a second thought. Anything in assets/ may not.",
));
doc.push(H3("Why it was needed"));
doc.push(P("The rule was violated with the first three carrier dossiers. They sat in client-assets/ despite containing the company's competitive strategy, its assessment of which carriers are buyable and which are not, and its judgement about a customer's negotiating position. ed10875 moved them out and split the tree. This became the standing instruction \"Strictly goes in our assets folder,\" which remains in force."));
doc.push(H3("The second fix: repository hygiene"));
doc.push(P("487c378 stopped tracking axiom.db and __pycache__, and added a .gitignore. A committed SQLite file and compiled bytecode are both runtime state and both leak; the correction is small but it is recorded in B01 §7 as item 9, marked corrected, because the docket tracks repository hygiene as a production concern rather than an incidental cleanup."));

// ---- Stage 3
doc.push(H2("Stage 3 — The technical annexes (2026-11-08, 16:00–16:22)"));
doc.push(P("Commits: 77d4cf5 (B01, B04, B05), 903f1ae (library reconciliation)."));
doc.push(H3("B01, B04, B05 — written against production, not the demo"));
doc.push(P("The three technical documents were written in one pass, and their most important property is stated in B01's own opening: \"Written against: the production architecture, not the demonstration build. §7 lists every point where the two currently differ. Nothing in this document should be treated as describing the demo.\""));
doc.push(P("That decision — to describe the intended production system and separately enumerate every gap to it — is what makes the rest of the docket honest. It produced B01 §7, a ten-item gap table that includes the project's largest known defect (item 5: no inbound sensor route exists), and it forced B04 and B05 to be written by inspecting the code rather than the marketing."));
doc.push(P("The three documents settled three architectural decisions, later recorded as AD-1 to AD-3 in B01:"));
doc.push(table(
  ["Decision", "Content", "Consequence"],
  [
    ["AD-1", "Fully on-premise edge, zero outbound network. No licence server, telemetry, update callback or third-party cloud. Ever.", "The air-gap claim becomes truthful. It costs the vendor remote diagnostics and all product telemetry."],
    ["AD-2", "Reviewer identity via local accounts plus a signed certification registry, administered by the Railroad.", "No dependency on railroad directory services; no path to pivot into their directory. Costs a second credential set."],
    ["AD-3", "The disposition ledger is append-only: superseded, never overwritten, never deleted.", "The regulatory argument rests on this. The shipped code does not implement it yet."],
  ],
  { width: [1, 5, 4], size: 16 },
));
doc.push(P("B05 states the air-gap claim as verified fact rather than assertion, by naming what was checked: no outbound HTTP client in any backend module, no telemetry, no licence callback, no crash reporting, and no external URL in the frontend. It also sets a rule rather than a caveat — if a future release requires any outbound call, it must be disclosed in B05, D06 and D09 before shipment."));
doc.push(H3("The library reconciliation (903f1ae)"));
doc.push(P("A 47-document reference library, Railroad_AirGapped_Governance_Master_Library, was analysed against the docket. The analysis is unusually clear-eyed and its central finding is a structural conflict rather than a gap list."));
doc.push(P("The library assumes a governance model that transfers asset ownership to the carrier at end of life. Adopting it wholesale would destroy the commercial position in D13, where AxiomDynamics retains all IP and escrow grants operability only. The recommendation was to adopt the library's evidence, integrity, authorisation and recovery spine while rejecting its ownership-and-closure spine — and to separate the concepts explicitly: asset documentation is transferable; source and model rights are not, absent an insolvency trigger."));
doc.push(P("The analysis also rejected outright what does not apply: the library's AI/ML governance artefacts (training data manifests, embeddings, prompt governance) would actively damage a deterministic physics platform's credibility with a technical buyer. Enterprise infrastructure assumptions — Kubernetes, VM templates, Terraform — were skipped for the same reason."));
doc.push(callout(
  "The deferred work this created",
  "The reconciliation identified six documents the docket lacks: a pilot authorisation gate (C03), rollback and recovery (C04), an evidence register and hash manifest (E01), air-gap media chain of custody (E02), DR with stated RTO/RPO (E03), and continuous compliance (E04), plus a records retention schedule and a governance RACI. D00 records these as deliberately deferred Phase 2 candidates — real gaps, identified, not needed for a BNSF pilot, and not pretended to be closed.",
));

// ---- Stage 4
doc.push(H2("Stage 4 — Contract drafting (2026-11-08, 16:50–20:38)"));
doc.push(P("Commits: a4d4fff (IP strategy), d05501f (D14), e8a08fc (D13), 7c47aa6 (D12, D11, D02), 96e058c (D07, C01, C02), b9aa4a8 (D05, D06, D09)."));
doc.push(P("This is the largest drafting stage: nine documents across six commits, in a deliberate order. The order itself is the design — the documents that constrain everything else were written first."));
doc.push(H3("The drafting sequence, and why"));
doc.push(table(
  ["Order", "Document", "Why it came at this point"],
  [
    ["1", "IP Strategy (internal)", "Settled the five-stage retain / brand / review / open / auction architecture before any licence language was written. The decision recorded: retain 100% of IP for the first five years; no sale in that window; licences only."],
    ["2", "D14 Operating Model & Liability Boundary", "Establishes who installs, operates, supports and staffs — before any contract is drafted that would assume an answer."],
    ["3", "D13 IP Ownership & Escrow", "Implements the strategy decision. Escrow releases the running version only, insolvency-triggered: operability, never ownership."],
    ["4", "D12, D11, D02", "D12 resolves the safety-critical disclaimer paradox before the pilot agreement can contradict it. D11 is needed before D02 because an NDA precedes a pilot."],
    ["5", "D07, C01, C02", "The master contract, plus the two documents that make its operating model real: C01 is why \"the Railroad installs it\" is not a fiction, and C02 defines what \"certified reviewer\" means."],
    ["6", "D05, D06, D09", "The mechanics that follow signature: conversion, support, and the security schedule. This commit also closed the twelve identified contractual loopholes."],
  ],
  { width: [0.7, 3.3, 6], size: 16 },
));
doc.push(H3("The twelve loopholes"));
doc.push(P("The docket's central organising device is a list of twelve ways rail technology contracts commonly fail, each with a named fix. They are recorded in D00 Part III, and all twelve are marked closed. The two most consequential:"));
doc.push(P("The safety-critical disclaimer paradox. The company's claim is that it prevents derailments; its inevitable limitation-of-liability clause will say it does not guarantee detection. Put together, those are a contradiction a plaintiff's lawyer would find in ten minutes. The resolution was not to weaken either statement but to define the product precisely — a decision-support system presenting a ranked, physics-derived risk assessment to a qualified human reviewer, with the railroad retaining the operating decision — and to require that framing to be identical in B01, C02, D02, D07 and D08. D12 is the annex that makes the disclaimer credible rather than self-serving, and D12 §9 makes it controlling over every other document."));
doc.push(P("The who-pays-for-a-false-positive gap. A false stop on a Class I main line costs train-hours, crew-hours and network knock-on. Nothing in early drafts said who bore that cost, and a railroad's counsel will ask in the first meeting. The fix was a defined, bounded regime: a quarterly service credit schedule tied to measured false-positive rate, capped at the platform fee, excluding detector-data causes and consequential damages. This converts an unbounded risk into a priced one."));
doc.push(callout(
  "The withdrawn claim",
  "Earlier internal drafts cited \"<0.1% false positives\" as a marketing figure. It was never measured and has been withdrawn from the client-facing docket. D06 §4 now sets a measurement regime with no target, and A2 states no target. The reasoning recorded in D00 is worth keeping: claiming a rate before measuring it, in the same docket that promises a credit when the rate is high, is the contradiction a plaintiff builds a case on.",
));

// ---- Stage 5
doc.push(H2("Stage 5 — Closing the docket (2026-11-09, 16:09–16:32)"));
doc.push(P("Commits: cf2e6ba (Q7 — the largest single commit), 33ccc7e, de9b245."));
doc.push(H3("Q7 — the forms register and the remaining instruments"));
doc.push(P("cf2e6ba is the largest commit in the project: 35 files, 3,900 insertions. It built F00–F13 (the fourteen executable forms), A2 (the rate card), D03 (the MSA), D04 (the five SOW templates), D01 (the preface and checklist), and D10 (the component register) — then ran a two-pass consistency audit across the whole set."));
doc.push(P("Two things from that commit deserve permanent record. The first is A2's role: it became the single authority on price, governing every other document. The second is F00 Rule 7, which is a documentation principle rather than a form:"));
doc.push(callout(
  "F00 Rule 7 — a blank and a decision are different things",
  "Every unfilled field is one of exactly two kinds. A fill-in blank is a value that exists and will be entered at execution — a party name, a date, an agreed amount. It is written as underscores and is safe to leave because the process that fills it is defined. An unmade decision is a question the docket has not answered — which law governs, which entity form. It is never written as a blank, because a blank implies we know it will be filled in. It is written as an explicit open item stating what must be decided, who decides it, and what happens meanwhile. The difference is the difference between a document that is quietly incomplete and one that is honestly incomplete.",
));
doc.push(P("Rule 7 also names the prohibited pattern: never write a clause that points to a field no document actually contains. That rule was written because D07 §14.3 had done exactly that — it sent dispute venue to \"[the courts / arbitration seat] stated in the Order signature block\", and no Order template has such a field. The clause read as complete to anyone who did not go and check, and there was nothing to check. This defect is fixed in chat-2 (Part IV)."));
doc.push(H3("B02 and B03, and the correction that followed"));
doc.push(P("33ccc7e added the flow map and the one-page executive infographic, and reconciled build status. de9b245 followed eleven minutes later with a correction that is the most important single commit in the project's quality history: \"Correct B02/B03: disclose that no detector ingest path exists.\""));
doc.push(P("The diagram had drawn a flow from wayside detector to edge inference. No endpoint accepted a Railroad payload. The signals came from the physics equations on synthetic traces. The docket's largest known gap had been drawn as a built capability — and it was found by checking the diagram against the code, not by reading the diagram."));
doc.push(P("That correction is now the standing discipline of the project: verify against the file, then write. Every later stage cites it, and the transcript of chat-2 records the assistant's own summary of why it matters — \"it looked right, so nobody checked whether it was true.\""));

// ================================================================ PART III
doc.push(H1("Part III — The docket, document by document"));

doc.push(P("The Master Brief Docket is 38 artifacts in client-assets/MASTER-BRIEF-DOCKET/ — 36 Markdown documents, one Excel model (A1, with its build script beside it) and one HTML infographic. The docket index is D00, and D00 Part IV is the authority on precedence: where two documents conflict, the ladder below decides which wins."));

doc.push(H3("The precedence ladder (D00 Part IV)"));
doc.push(table(
  ["Rank", "Instrument", "Governs"],
  [
    ["1", "D07 Comprehensive Master Contract", "Generally, everything"],
    ["2", "D02 Master Pilot Agreement", "During the pilot term, where it conflicts with D07"],
    ["3", "D09 Data Processing & Security Addendum", "Data protection and security matters"],
    ["4", "D03 MSA", "Structure, ordering, change control across all orders"],
    ["5", "D04 SOW", "Scope and deliverables for that specific order"],
    ["6", "A2 Rate Card", "Price — where any document's fee differs from A2, A2 wins"],
    ["7", "B-series technical annexes", "Descriptive only; create no warranty unless D07 incorporates them"],
    ["8", "F-series forms", "Administrative; a form records an event and never varies a term"],
    ["9", "Rule of construction", "Where a B-series document describes a capability D07 disclaims, the disclaimer governs and the annex must be corrected"],
  ],
  { width: [0.6, 3.6, 5.8], size: 16 },
));
doc.push(P("Rules 6 and 9 are the two that keep the docket honest over time. Rule 6 keeps the numbers honest. Rule 9 keeps the capability claims honest: it converts a contradiction between annex and contract into a drafting error that must be fixed, rather than a gap to be argued about after an incident."));

function docBlock(id, title, status, purpose, detail) {
  doc.push(H3(`${id} — ${title}`));
  doc.push(PR([
    { text: "Status: ", bold: true },
    { text: status },
  ], { spaceAfter: 60 }));
  doc.push(PR([{ text: "Purpose: ", bold: true }, { text: purpose }], { spaceAfter: 60 }));
  if (detail) doc.push(P(detail, { spaceAfter: 160 }));
}

doc.push(H2("A — Commercial model"));
docBlock("A1", "ROI Model", "Built (.xlsx, five sheets, plus build script)",
  "A five-sheet Excel business case where the yellow cells are the only inputs, so every derived figure is auditable from the customer's own data.",
  "Sheet 1 (Fleet) takes axles, speed, site count and the customer's exposure, then derives a blended expected cost per missed defect. Sheet 2 (Detection) compares legacy and AxiomDynamics detection times and converts lead time into track miles of early warning. Sheet 3 (Benefit) computes prevented-failure cost minus false-alarm disruption. Sheet 4 (Licensing Cost) applies the two pricing axes. Sheet 5 (Summary) produces the three-year business case, ROI multiple and payback period. Every sourced figure is cited and every assumption is labelled in the cell beside it. Note: the committed workbook's cost basis does not match A2 — see the arithmetic finding in Part VII.");
docBlock("A2", "Rate Card & Band Definitions", "Built, and authoritative on price across the whole docket",
  "The single place every contract cites for price, so pilot agreement, rollover and licence cannot quote three different numbers.",
  "Marginal bands: first 500 axles at $600, next 1,500 at $500, above 2,000 at $375. Site axis: $45,000 per additional site per year, first site included. Three worked examples (500/1 site = $300,000; 1,000/3 sites = $640,000; 5,000/20 sites = $3,030,000), the corridor arithmetic showing geography can be roughly half the annual cost of a corridor deployment, and the rollover arithmetic ending at $810,000 net over three production years. Also carries the optional performance component (§4A): 3% of a corroborated prevented-failure cost, capped at 33% of base, offered only by election and never during a pilot.");

doc.push(H2("B — Build blueprint, for the Railroad's IT"));
docBlock("B01", "System Blueprint & Architecture", "Built",
  "The component inventory, data flow, failure modes and scale envelope — written against production architecture, not the demo.",
  "Holds AD-1 to AD-3, the ten-item production gap table (§7), and the costs of the architectural choices (§8) stated plainly because the railroad's IT team will find them anyway. Its opening sentence is a warning to every later reader: nothing in it describes the demo.");
docBlock("B02", "Flow Map", "Built (.md) — corrected at de9b245",
  "The visual companion to B01: what enters, what is computed, where a human intervenes, what is recorded, what leaves.",
  "Solid lines mean shipped; dotted mean designed and not built. §2's ingest path is the one that was drawn wrong and corrected. §9 closes with the most useful sentence in the document: the ledger needs rebuilding, but the front door does not yet exist.");
docBlock("B03", "Executive Infographic", "Built (.html)",
  "One page for executives who will not read B01.",
  "Encodes the platform/human boundary as a deliberate break in the drawn line, and carries a status block disclosing the absent ingest path.");
docBlock("B04", "Technology Stack Disclosure", "Built, verified against the repository",
  "The dependency register for IT security review and open-source licence compliance.",
  "Names exactly one non-stdlib runtime dependency (numpy, BSD-3-Clause) and explains why no web framework exists: to demonstrate that a predictive-maintenance platform does not require a software supply chain to operate. §7 names four supply-chain gaps — no pinning, no hash verification, no SBOM, no signed artefacts — and states that none blocks a demo and all four block production.");
docBlock("B05", "Data Flow & Data Residency", "Built, verified against code",
  "The document a railroad's CISO reads first.",
  "Answers the air-gap question with what was actually checked rather than what is promised, and sets a rule: any future outbound call must be disclosed in B05, D06 and D09 before shipment. §7 is deliberately uncomfortable — four controls architecturally present, three not yet built, one dependent on the railroad.");

doc.push(H2("C — Deployment and people"));
docBlock("C01", "DIY Self-Deployment SOP", "Built",
  "The self-deployment manual for the railroad's own IT team. D00 states plainly that this document is why D14's operating model works — without it, \"the Railroad installs it\" is a fiction.",
  "Granular numbered steps with expected outputs, three installation paths (standard pip, air-gapped sealed archive, containerised), pre-installation checks, and a verification stage. Assumes a competent Linux administrator with no prior rail-domain knowledge.");
docBlock("C02", "Certification & Role-Based Assessment", "Built",
  "Defines what \"certified\" means, which D02 §5 requires.",
  "Four roles — Operator, Reviewer, Administrator, Safety Officer — with a competency matrix, assessment methods, passing thresholds (reviewer: 80% combined across a knowledge test and a hands-on scenario; administrator: lab completed with no critical error), certification validity, and revocation. Defines the three-year recertification cycle referenced in A2.");

doc.push(H2("D — The contract stack"));
docBlock("D01", "Preface & Master Deliverables Checklist", "Built",
  "Front matter: what the docket is, what it is not, who reads which document, and the pre-execution checklist.",
  "Maps each audience to its documents — Chief Engineer, IT/security, procurement/finance, legal — then sets the pre-execution gate across entity and authority, commercial terms, contract integrity and technical honesty.");
docBlock("D02", "Master Pilot Agreement", "Built",
  "The entry contract: scoped, time-boxed, reversible.",
  "Twelve-month term from the Commissioning Date, $370,000 total, evaluation criteria that are explicitly not performance guarantees, and fees confirmed against A2 §5.1. D02 contains no precedence clause of its own — D00's ladder governs, because an index pointing at a clause that does not exist is the same dangling-reference failure the docket exists to prevent.");
docBlock("D03", "Master Services Agreement", "Built",
  "The umbrella signed once per customer; survives individual orders and governs ordering and change control.",
  "Lists every incorporated document by number, sets the conflict rule, the change-control mechanism, insurance, liability and IP, and the order of precedence within the agreement.");
docBlock("D04", "Statement of Work templates", "Built (SOW-1 to SOW-5)",
  "The executable per-deployment orders.",
  "SOW-1 Pilot Implementation ($370,000) · SOW-2 Additional Site ($45,000/yr plus licence) · SOW-3 Feasibility & Physics Assessment ($45,000–$75,000) · SOW-4 Prototype Development ($150,000–$400,000) · SOW-5 Professional Services (per A2 §5.5). SOW-3's structure is deliberate: its deliverable permits \"no, and here is why,\" which is what makes a discovery engagement honest rather than a sales call with an invoice.");
docBlock("D05", "Pilot to YoY Licensing Rollover", "Built",
  "The conversion mechanics — what happens on day 366.",
  "90-day election window, 50% pilot licence credit ($90,000), three-year price lock at 0% with Year 4+ capped at 5%, and a defined exit if the railroad declines — including what data it keeps. Exists because a pilot converting at full production price with no credit changes the internal ROI shape at exactly the moment the CFO reviews it.");
docBlock("D06", "Technical Support, SLA & Update Governance", "Built",
  "Response times, severity tiers, patching cadence, EOL policy, and the false-positive cost regime.",
  "Four severity tiers with 4-business-hour to 5-business-day response, business-hours scope with no uptime guarantee, a patch cadence by category (security as discovered, defect monthly, minor quarterly, major annually), and §4's quarterly service credit schedule tied to measured false-positive rate and capped at the platform fee.");
docBlock("D07", "Comprehensive Master Contract", "Built — §14.5 deliberately open",
  "The full terms: federal guidelines, data security, indemnities, liability, insurance, export control, audit rights, dispute resolution.",
  "§6 allocates the detector-data warranty in three parts — railroad warrants its hardware, supplier warrants its processing, neither warrants the other's domain. §15.6 gives 90 days of free transition assistance on termination. §14.5 now states governing law, seat and forum as an explicit open counsel decision, with what must be decided, who decides and by when, the Texas default stated as expectation not term, and a defined fallback. That rebuild happened in chat-2 — see Part IV.");
docBlock("D08", "Master Licensing & Liability", "Built — a commercial annex, not an instrument to sign",
  "Explains the money: licensing structure, tier bands, corridor economics, the performance component.",
  "D08 explains; D07 and D02 are what a customer executes, and where they differ they govern and D08 is corrected. Its most valuable content is the honesty about pricing history: it records that earlier flat tiers ($450K / $950K / $1.8M) failed on both counts — the entry tier returned only 1.5×, and scaling from 500 to 1,000 axles dropped ROI from 1.9× to 1.8× — and it flags the current rates as a pricing hypothesis validated only against modelled return, not against a real procurement conversation.");
docBlock("D09", "Data Processing & Security Addendum", "Built",
  "The security schedule: residency, controls, incident notification, retention, subprocessor register, audit rights.",
  "72-hour supplier-to-railroad notification and 24-hour railroad-to-supplier for discovered vulnerabilities, with a 30-day root-cause analysis. §4.4 lists the five known gaps with remediation targets. §7.2 and §7.3 were added because a control disclosed only in a remediation table is not disclosed — see Part IV.");
docBlock("D10", "Subprocessor & Third-Party Component Register", "Built",
  "Zero subprocessors; one runtime dependency. The artefact the railroad can rely on today in the absence of an SBOM.",
  "Incorporated by reference in D02 §11, D07 §3.4, D13 §8 and B04 §7 — it now exists, which was previously a dangling reference.");
docBlock("D11", "Mutual NDA", "Built",
  "Needed before D02, and always needed first.",
  "Mutual confidentiality with compelled-disclosure handling, residual-knowledge clause, and term and survival.");
docBlock("D12", "Regulatory Status & Safety-Critical Function Statement", "Built — controlling over every other document",
  "Single annex stating the platform is not a certified safety appliance, is not a substitute for required inspection, and relieves the railroad of no regulatory obligation.",
  "Resolves the docket's largest paradox. §3 is the WDBD exclusion, stated carefully. §5 makes human authority absolute. §8 sets advertising and representational discipline. §9 makes this document controlling, which is what makes the product's disclaimers credible rather than self-serving.");
docBlock("D13", "IP Ownership & Escrow Schedule", "Built",
  "Definitive statement of what transfers and when.",
  "Records the five-year retention decision, separates railroad data from supplier models explicitly, and confines escrow to the running version on insolvency — operability, never ownership. §5 states the honest limitation of escrow rather than overselling it. §9 requires contributor assignment, which is what makes the ownership claim survive a contractor.");
docBlock("D14", "Operating Model & Liability Boundary", "Built",
  "Who installs, operates, supports and staffs — and what the supplier does not do.",
  "Separates operational liability, largely removed by responsible self-install, from product liability, which is retained regardless. §8, representational discipline, is the most important section: it governs what the company may say about outcomes, and it is the section a support engineer's language is measured against.");

doc.push(H2("F — The executable forms"));
doc.push(P("Contracts say what the rules are; forms are how the rules are applied one event at a time. Every form has exactly one purpose, one signatory, and a stated consequence for silence. The fourteen, with their trigger and default:"));
doc.push(table(
  ["ID", "Form", "Used when", "Signatory", "Default if unsigned"],
  [
    ["F01", "Site Readiness & Survey", "Before any site deployment", "Customer technical contact", "No deployment scheduled"],
    ["F02", "Configuration Attestation", "On commissioning at every site", "Customer IT Director", "No Commissioning Date; pilot term does not start"],
    ["F03", "Change Order", "Any change to scope, price or schedule", "Both authorised reps", "Change does not take effect"],
    ["F04", "Travel Pre-Approval", "Before booking billable travel", "Customer authorised rep", "Travel is not billable"],
    ["F05", "Payment Terms Schedule", "With every Order", "Both parties", "A2 §10 default terms apply"],
    ["F06", "Deliverable Acceptance", "On delivery of a deliverable", "Customer authorised rep", "Deemed accepted after 10 Business Days"],
    ["F07", "Travel & Expense Claim", "Within 14 days of travel", "Supplier, countersigned", "Not reimbursed"],
    ["F08", "Reviewer Certification Application", "Before a reviewer is certified", "Candidate + sponsor", "No certification issued"],
    ["F09", "Advisory Disposition Record", "Every advisory, without exception", "Certified Reviewer", "Disposition missing — D02 §5 obligation 5 breach"],
    ["F10", "Security Incident Notification", "On a reportable incident", "Supplier or Customer", "Breach of D09 §6"],
    ["F11", "Site Visit Report", "After every on-site attendance", "Supplier engineer", "Visit undocumented; not billable"],
    ["F12", "Formal Notice", "Contractual notices, termination, breach", "Authorised signatory", "Notice not effective"],
    ["F13", "Data Export & Transition Certificate", "On termination or migration", "Both parties", "Export not certified complete"],
  ],
  { width: [0.6, 2.8, 3.4, 2.1, 3.6], size: 15 },
));
doc.push(P("F00 sits above these as the register and policy, and carries the seven documentation rules. Three records carry evidentiary weight: F02 establishes the Commissioning Date and the configuration the customer certified; F09 records what a human decided and when, and is what answers \"did someone look at this?\" after an incident; F03 proves scope moved deliberately rather than by drift. F11 and F09 together are what hold the liability boundary — F11 records what was observed and what was declined, F09 records that a qualified human made the operating call."));
doc.push(callout(
  "The gap that sat inside F09, and how it closed",
  "This document was first written on 2026-11-09 while F09 described an append-only record that the code did not yet produce \u2014 the write path was an upsert keyed on advisory_id, so a second decision silently destroyed the first. That was disclosed in six places rather than hidden, which was right, but it meant the docket's most legally significant record claimed more than the code did. Later the same day the ledger was rebuilt: insert-only, corrections by reference, database triggers refusing UPDATE and DELETE, and a SHA-256 chain across rows. F09's Part 7 now states what the chain proves and what it does not. The gap did not vanish; it narrowed to signed, off-box export.",
));

// ================================================================ PART IV
doc.push(H1("Part IV — The loss, and the rebuild"));

doc.push(P("This part exists because the record of it is scattered across four files, and because the failure it describes is the reason the working rules are what they are. It should not be softened, and it is not softened here."));

doc.push(H2("What happened"));
doc.push(P("Chat-1 built the repository inside a temporary sandbox container, not on the owner's disk. To get anything out, it bundled the repo into a .bundle file, embedded it in a .bat, and the owner ran it once — which is how de9b245 reached GitHub. Everything chat-1 did after that push stayed inside the container: the F00 Rule 7 work, the D07 §14 rewrite, Q6, and commits 0b66d21 and cb4f74d. Then it extracted 2,527 turns of conversation into readable transcripts — into the same container — and committed those too."));
doc.push(P("When the session ended, the container was destroyed and took all of it. Not a deletion. The work was never on the owner's machine."));
doc.push(callout(
  "The precise failure",
  "The bundle was made once, mid-session, and never remade. From de9b245 onward there was no export step. Chat-1 kept treating \"committed\" as if it meant \"safe\", when inside that container it only meant saved in a place that was about to be emptied. When chat-1 reported \"committed as cb4f74d\" and \"the transcripts are here now\", that was true in its own frame and misleading in the owner's — and the owner reasonably read it as my files are saved.",
  { fill: "FBEAEA", labelColor: RED },
));

doc.push(H2("What was lost, and what it cost"));
doc.push(table(
  ["Lost", "Recoverable?", "How"],
  [
    ["F00 Rule 7 (blank vs decision)", "Yes, as a reconstruction of the decision", "Rebuilt in f58b07c. The decision is identical; the prose is not guaranteed to be."],
    ["D07 §14 venue rewrite", "Yes, as a reconstruction", "Rebuilt in f58b07c as §14.5, with the open-item structure."],
    ["Q6 entity formation analysis", "Yes, as a reconstruction", "Rebuilt in f58b07c into assets/legal-architecture/."],
    ["project-logs structure", "Yes", "Rebuilt, and extended with the transcript rule."],
    ["0b66d21, cb4f74d", "No", "Bookkeeping commits; their content was rebuilt under new hashes."],
    ["Chat-1 conversation — 2,527 turns", "No. Permanently.", "No copy anywhere: no archive, mirror or cache. chat-1/SUMMARY.md is a distillation — a judgement about what mattered, not the conversation."],
  ],
  { width: [3.4, 2.4, 4.2], size: 16 },
));
doc.push(P("The distinction matters for anyone reading the rebuilt documents: because the rebuild is a reconstruction rather than a recovery, the wording may differ from what chat-1 wrote. The decisions are identical. The prose is not. Do not treat the current text as a restoration of an earlier draft."));

doc.push(H2("The rules that came out of it"));
doc.push(P("Three standing instructions now govern every session, and each is a direct consequence of something that went wrong:"));
doc.push(...numbered("numC", [
  "\"Drop all the entire project work directly in AxiomDynamics folder so we don't lose any data from sandbox.\" Every document, script and log is written into C:\\Users\\RGV\\AxiomDynamics on the first pass, and committed in the same pass that produces it. No drafts in sandbox scratch space.",
  "Verify against the file, then write. Never cite from memory and check afterwards. That habit produced every bad citation in the project, and the worst defect — the ingest path drawn as built — came from the same habit applied to a diagram.",
  "Extract and commit the session transcript at close, raw .jsonl included. From chat-2 onward this holds, and the files are in project-logs/transcripts/.",
]));
doc.push(P("One further operational fact, because it is not obvious: the sandbox cannot reach GitHub. git push and git fetch both fail with HTTP 403 from the proxy. Commits land locally in the real repository; the owner pushes with PUSH-TO-GITHUB.bat in the repo root. This means \"committed\" and \"on GitHub\" are different states, and the local origin/main ref is not evidence of remote state."));

// ================================================================ PART V
doc.push(H1("Part V — What chat-2 did"));

doc.push(P("Chat-2 opened on 2026-11-09 as a fresh thread. Its first act was to verify it knew what chat-1 was about rather than assume it — and in doing so it found that none of chat-1's final work was in the repository."));
doc.push(H2("What it found"));
doc.push(BULLET("F00 still read \"six rules\", not seven."));
doc.push(BULLET("D07 §14.3 still pointed at a non-existent Order field."));
doc.push(BULLET("assets/legal-architecture/ was empty."));
doc.push(BULLET("project-logs/ did not exist at all."));
doc.push(H2("What it rebuilt — commit f58b07c"));
doc.push(P("F00 Rule 7, including the amendment to Rule 4 so square brackets mean definitions only, and the correction of D00's rule count from five to seven."));
doc.push(P("D07 §14, with §14.3 now deferring to an explicit §14.5 that states governing law and seat as an open counsel decision carrying four parts: what must be decided, who decides and by when, the Texas default stated as expectation not term, and a defined fallback if an Order is executed while it is open. §14.3 no longer points at a field that does not exist. D03 points at §14.5 rather than holding a second blank."));
doc.push(P("Q6 in assets/legal-architecture/, covering entity formation, the support boundary and corridor strategy. Its formation figures were re-verified against official sources: Texas Certificate of Formation $300, no franchise tax below the $2.65M 2026 no-tax-due threshold, foreign-entity registration $750. The Delaware annual tax was left explicitly unresolved because sources conflict for 2026 ($300 versus $400) — and the document says so rather than picking a number to make the table tidy."));
doc.push(P("Q6's most transferable content is not the entity analysis but §7: a substitution table of sentences an engineer can actually say at 17:55 when a customer asks \"should I pull this car?\" The argument for building it that way is that a policy is read at induction, but a substitution table is used in the moment — and the failure mode is not malice, it is a tired engineer giving a helpful answer."));
doc.push(H2("What else it closed"));
doc.push(P("The D09 signed-release gap. Signing previously appeared only as a §4.4 row; §7.3 now states plainly that artefacts are unsigned today, what the SHA-256 manifest does and does not prove, and what changes at Q2 2027. The reasoning is recorded in the document itself: a control disclosed only in a remediation table is not disclosed, it is noted. The rule that followed is that every control in §4.4's gap table has a corresponding negative statement in the section a reader would look in."));
doc.push(H2("Verification performed in chat-2"));
doc.push(P("Citational: every D-reference in Q6 and every section reference in the rebuilt sections was resolved to a real heading. Two errors were found this way and corrected — D06 §2.4 corrected to §7.4, and D03 §12 corrected to §9. Count consistency: no document still said \"six rules\". Duplicate-heading scan across all 36 docket documents: clean. Scope: Q6 confirmed absent from client-assets/. Diff inspected with --ignore-cr-at-eol: 536 real insertions against 7 real deletions, the larger raw numbers being CRLF conversion rather than content."));
doc.push(H2("The transcript rule, and its limit"));
doc.push(P("Chat-2 found its own session log still on disk at .claude/projects/session/ — 780 events, 1.6 MB — extracted 256 readable turns and committed both the readable version and the raw .jsonl as ee9800c. That is now the standing rule, recorded in project-logs/transcripts/README.md and in persistent memory."));
doc.push(P("The honest limit, stated in the same README: this protects chat-2 onward. Chat-1 is a real loss and no amount of procedure brings it back."));

// ================================================================ PART VI
doc.push(H1("Part VI — Internal strategy in assets/"));

doc.push(P("Five internal documents sit in assets/. None may be forwarded to a customer, and the classification rule in Part II is what keeps them there. Each is summarised here because the strategy they contain is not in the docket and is needed to discuss the next phase."));

doc.push(H2("Q6 — Entity formation, support boundary, corridor strategy"));
doc.push(table(
  ["Question", "Answer recorded", "Confidence"],
  [
    ["Entity form", "Texas LLC now; convert to Delaware C-corp only on a specific trigger", "High"],
    ["State of formation", "Texas — Delaware's advantage is shareholder litigation the company does not have", "High"],
    ["Conversion triggers", "Institutional round, stock option pool, or acquisition approach — decided by event, not feeling", "High"],
    ["Largest threat to the shield", "A personal guarantee, not formation mechanics. No amount of correct formation survives one", "High, and under-weighted in earlier analysis"],
    ["Support boundary", "A substitution table of sentences, a written record, and staffing discipline", "High"],
    ["First corridor", "Choose by failure mode and data availability, not carrier size", "Medium — depends on live relationships"],
  ],
  { width: [2.6, 6.2, 2.2], size: 16 },
));
doc.push(P("The document is candid about what it cannot decide: which carrier to approach first, and the correct venue and governing law, which is D07 §14.5 and an open counsel decision rather than a formation question."));

doc.push(H2("IP Strategy & Exit Architecture"));
doc.push(P("Records a decision taken 2026-11-08: AxiomDynamics retains all IP for the first five years, sells no IP rights in that window, and grants only licences. The architecture is five stages — Prove (Y1–5, licence only, BNSF first), Brand (Y5–8, exclusive white-label), Review (Y8, joint assessment), Open (Y8+, joint options with majority retained), Auction (when triggered, sole buy-out with an open bid floor)."));
doc.push(P("Two defects in the original staged plan were identified and resolved. First, Stage II grants exclusive white-label while Stage III assumes UP and NS are operating the build — a contradiction. The fix separates brand exclusivity from use exclusivity: exclusive branding, non-exclusive right to operate, with the exclusivity priced separately rather than bundled into a licence rate. Second, \"quietly\" is not available: there are six Class I carriers whose procurement, safety and mechanical officers sit on the same AAR committees, and BNSF is a Berkshire Hathaway subsidiary subject to public-company disclosure. Contract confidentiality is achievable; secrecy is not."));
doc.push(P("The legal trap the document catches is worth carrying forward: under US law, joint owners of a copyright or patent can each exploit the asset independently and license it to third parties without consent or accounting to the other owner. \"Joint ownership with majority retained\" is not a recognised legal structure — there is no shareholding to be a majority of. The recommendation is never to co-own: use equity or field-of-use licensing instead."));
doc.push(P("The valuation arithmetic sets a floor rather than a target: three carriers at a blended $6M/year is $18M of recurring revenue; at 75% contribution margin and a 12× multiple the standalone business is roughly $160M, and a 2–3× strategic premium puts a credible auction range at $300M–$500M. The rule recorded is not to entertain a sole buy-out below the NPV of the annuity plus a strategic premium."));

doc.push(H2("Governance library reconciliation"));
doc.push(P("Already covered in Stage 3. The carry-forward point is the deferred Phase 2 document set — C03 authorisation gate, C04 rollback, E01 evidence register, E02 media chain of custody, E03 DR with RTO/RPO, E04 continuous compliance, plus records retention and a RACI — and the structural conclusion that the library's ownership-and-closure spine must be rejected while its evidence and integrity spine is adopted."));

doc.push(H2("Carrier dossiers — BNSF, UP/NS, CN/CPKC"));
doc.push(P("Three operating dossiers, each written to allow a conversation in the customer's own units and geography. Every figure is cited and anything unsourced is labelled. Each ends with a section titled \"What we do not know\" — which is the part that makes the rest usable."));
doc.push(P("The BNSF dossier carries the detector network as the actual \"site\" unit, which is where the second pricing axis came from. The UP/NS dossier records the strategic fact that a merger makes BNSF an opposing litigant rather than a neutral prospect. The CN/CPKC dossier frames Canadian regulatory requirements as the actual sales argument for that market."));
doc.push(callout(
  "Re-verification requirement",
  "The carrier dossiers require re-verification before use. The UP/NS merger is live and the facts move. Two of the figures in the commercial material were already found to reference a stale site-count range and were corrected in 668e5eb.",
));

doc.push(H2("External pilot cost structure and licensing model"));
doc.push(P("The internal counterpart to A2 and D08: the same commercial model from the vendor's side, with margin reasoning that does not belong in a client-facing annex."));

// ================================================================ PART VII
doc.push(H1("Part VII — Open items and unresolved findings"));

doc.push(P("The docket index asks to be corrected when a gap closes and refuses to claim a gap is closed when it is not. This part applies the same standard to the project as a whole. Six items are open. Two of them were found in chat-3 and are the most consequential things in this document."));

doc.push(H2("1. Finding 1 — the modelled-return anchors do not reproduce"));
doc.push(P("A2 §3.2 states that the customer's modelled return improves \"approximately 2.0× at 500 axles, rising to about 4.1× at 10,000.\" D08 §3 repeats both figures verbatim. Recomputed with A1's own default assumptions, on the only two cost bases that exist in the repository:"));
doc.push(table(
  ["Axles", "3-yr benefit", "On A2/D08 cost basis", "On A1 workbook basis"],
  [
    ["500", "$2,090,025", "1.77×", "2.36×"],
    ["1,000", "$4,180,050", "2.17×", "3.02×"],
    ["2,000", "$8,360,100", "2.44×", "3.51×"],
    ["5,000", "$20,900,250", "3.07×", "4.51×"],
    ["10,000", "$41,800,500", "3.36×", "4.99×"],
  ],
  { width: [2, 3, 2.5, 2.5], size: 17 },
));
doc.push(P("Neither basis produces 2.0× at 500 and 4.1× at 10,000, and a sweep across plausible per-defect valuations found no parameter set in the repository that reproduces both endpoints. The direction of the claim is correct — return does improve monotonically with fleet size on either basis — but the two anchor values are not derivable from the model the docket ships."));
doc.push(P("This was left open deliberately. The sentences carrying these numbers are also the document's defence against a flat-tier cliff objection, and D08 already labels them a pricing hypothesis validated only against modelled return. Replacing them with 1.77/3.36 is defensible; so is restating the claim without anchor values. That is a commercial decision about what the first real conversation opens with, and it changes a client-facing sentence in two documents — so it should be decided, not quietly edited."));

doc.push(H2("2. Finding 2 — D08's modelled benefits exceed what A1 produces, and the cause is now identified"));
doc.push(P("D08 §5 says a 500-axle customer sees $6–8M of avoided damage in the pilot year and $14–20M over four years; §6 says $40–60M over six years with a 20×–30× return. A1 at 500 axles with its default assumptions produces $696,675 net annual benefit. The ratio is between 5× and 14× across the three periods."));
doc.push(P("The cause is a modelling fork, not an arithmetic error, and it is now traced. Two different figures for the probability that a missed defect escalates to a catastrophic event exist in the repository:"));
doc.push(table(
  ["Location", "Probability", "Expected cost per missed defect"],
  [
    ["backend/roi.py — P_CATASTROPHIC_GIVEN_MISSED_DEFECT", "2%", "$29,065,000"],
    ["A1 workbook, sheet 1 cell B17", "0.05%", "$1,224,625 on the $500k typical-cost base, $9,745,375 on the $9.25M contained base"],
  ],
  { width: [3.4, 1.6, 5], size: 16 },
));
doc.push(P("The two probabilities differ by a factor of 40. The A1 note explains why it was lowered: \"Even 2% per missed defect would imply dozens of billion-dollar events annually nationwide — physically impossible. 0.05% keeps the implied nationwide rate roughly consistent with observed East Palestine-scale frequency.\""));
doc.push(P("D08's benefit figures, meanwhile, are reproducible if a prevented defect is valued at the contained-tier midpoint of $9.25M and nothing else: 0.65 × $9.25M ≈ $6.0M and 0.86 × $9.25M ≈ $8.0M, which is exactly D08's $6–8M pilot-year band at 0.7 defects missed. So D08 was built on the contained-tier value without the probability blend, and A1 applies the blend — a factor of roughly 9.25."));
doc.push(callout(
  "Why this one matters most",
  "These are the headline numbers in the document a CFO reads. D08 §5 states that A1 is the instrument of record and that \"this document must never be used to present one\" of these figures. The two disagree by nearly an order of magnitude at identical inputs. One of two things must happen: either D08 §5–§6 is restated from A1's output, or A1's evaluation assumptions are judged too conservative and the workbook is changed. Deciding that changes what the pilot pitch asks a customer to believe — which is why it is an owner decision and not an editorial one.",
  { fill: "FBEAEA", labelColor: RED },
));

doc.push(H2("3. D07 §14.5 — governing law, seat and forum"));
doc.push(P("An open counsel decision, correctly labelled as open. The section now says what must be decided, who decides and by when, that Texas is an expectation rather than a term, and what happens if an Order is executed while it is open. It must still be closed by signed addendum before first execution. Q6 is explicit that this is not a formation question and that entity choice does not answer it."));

doc.push(H2("4. The four unbuilt code controls"));
doc.push(P("D00 Part VI is the authority on these, and it refuses to let them migrate to \"closed\" on the strength of a document. The largest is the absent detector ingest path: no endpoint accepts a Railroad payload, so every demonstration number demonstrates the method, not the Railroad's data. The validation chain — schema, timestamp, plausibility — is designed and not built. The other three are the append-only ledger, the signed certification registry, and the signed audit export, each with a disclosed workaround and a remediation target in D09 §4.4."));
doc.push(table(
  ["Gap", "Disclosed in", "Consequence while open"],
  [
    ["No detector ingest path at all", "B01 §7 #5 · B02 §2 · B03 status", "Every demonstration number demonstrates the method, not the customer's data. The largest gap in the docket."],
    ["Signed, off-box export of the ledger", "B01 §4.5 · B01 §7 #8 · D09 §4.4 · F09 Part 7", "Append-only and hash-chained, but not signed and not replicated: someone with write access to the database file could rewrite and rehash, and a lost disk loses the ledger."],
    ["Certification registry is local accounts, no cryptographic verification", "B01 §7 #1 · D09 §4.4 · F08 Part 1", "A reviewer can self-assert a cert ID. Manual control via F08 is the substitute."],
    ["No SBOM artefact in releases", "D09 §4.4 · §7.2", "Customer cannot independently verify the dependency chain. Target Q1 2027."],
    ["No hash pinning of dependencies", "D09 §4.4", "A compromised package index could serve malware. Target Q1 2027."],
    ["No signed release artefacts", "D09 §4.4 · §7.3", "A release archive could be substituted. Target Q2 2027."],
    ["Licence scope enforced by contract only", "D02 §6 · D05 §5.2", "Nothing technically prevents a second site. Scope is an obligation, not a control."],
    ["Insurance limit is $2M, not $5M", "D07 §10.1 · D03 §9", "Stated honestly with a step-up commitment. Certificates must match the clause."],
  ],
  { width: [3.4, 2.4, 4.2], size: 15 },
));

doc.push(H2("5. The Phase 0 pre-signature items"));
doc.push(P("Nothing can be executed until the company exists. D01's pre-execution checklist requires entity, authority, EIN, insurance, bank and USPTO items before signature. Q6 recommends a Texas LLC with a $300 Certificate of Formation and a proper operating agreement reviewed by counsel. The filing fee is the cheapest part of forming a company and the least important; the operating agreement is the item worth paying for."));

doc.push(H2("6. Deferred by decision"));
doc.push(P("The six governance documents identified in the library reconciliation are deferred Phase 2 candidates, not omissions. The E-series assurance set is genuinely not needed for a BNSF pilot. The distinction D00 insists on is that a deferred decision is a decision, and it is not the same thing as a delivered control."));

// ================================================================ PART VIII
doc.push(H1("Part VIII — How to resume"));

doc.push(P("This part is written for whoever opens the next session, including the case where it is a fresh thread with no memory of this one."));

doc.push(H2("Read in this order"));
doc.push(...numbered("numD", [
  "project-logs/CURRENT-STATE.md — the authoritative state: what is built, what is pushed, what is open.",
  "project-logs/chat-3/SUMMARY.md — where the last session actually stopped.",
  "This document — the long-form history and the reasoning behind the structure.",
  "client-assets/MASTER-BRIEF-DOCKET/D00-DOCKET-INDEX.md, Part VI — the gap register, which is the authority on what is closed.",
]));

doc.push(H2("Confirm state rather than trusting any document"));
doc.push(P("Every written push list in this project has gone stale at least once. Confirm with the repository:"));
doc.push(table(
  ["Command", "What it answers"],
  [
    ["git log --oneline -8", "Where the last session stopped"],
    ["git status --short --branch", "Branch and how far ahead of the remote ref"],
    ["git log --oneline origin/main..HEAD", "What is actually unpushed — never trust a written list"],
    ["git diff --ignore-cr-at-eol --stat", "Real changes. Without the flag, nearly every file reads as modified"],
    ["python3 -I assets/a2-d08-arithmetic-pass.py", "Whether the A2/D08 figures still hold. Exits non-zero on any mismatch"],
    ["python3 tests/run_tests.py", "The 21 physics and warrant tests. Currently 21 passed, 0 failed"],
  ],
  { width: [4.6, 5.4], size: 16, mono: [0] },
));
doc.push(callout(
  "The line-ending trap",
  "git status in this repository lists nearly every tracked file as modified on a fresh Windows checkout. It is CRLF working-tree content against LF blobs, not a content change: git diff --ignore-cr-at-eol returns empty. There is no .gitattributes and core.autocrlf is unset. Always check with --ignore-cr-at-eol before believing a diff stat, stage only the files actually changed, and never git add -A. During chat-3 an editor round-trip converted the A1 builder to CRLF and turned a two-line fix into 1,248 changed lines; that commit had to be reset and recommitted so it showed 420 insertions and 2 deletions.",
));

doc.push(H2("Push"));
doc.push(P("The sandbox cannot reach GitHub — git push and fetch fail with HTTP 403 from the proxy. Commits land locally in C:\\Users\\RGV\\AxiomDynamics and the owner pushes with PUSH-TO-GITHUB.bat. At the moment this document was written the six earlier commits had been pushed and the local ref for origin/main stood at b946678, so what remains ahead of it is this document\u2019s own commit. Confirm with git log --oneline origin/main..HEAD rather than with this sentence, because a local remote-tracking ref is not evidence of what the remote holds."));

doc.push(H2("The decisions waiting, in order of consequence"));
doc.push(...numbered("numE", [
  "Which model governs the commercial numbers — A1's probability-blended evaluation or D08 §5–§6's contained-tier basis. Everything quoted to a customer depends on this.",
  "Whether to strike or restate the 2.0×/4.1× return anchors in A2 §3.2 and D08 §3.",
  "Which of those two answered, regenerate the A1 workbook from the corrected builder and re-run the arithmetic check.",
  "D07 §14.5 — approve a governing law, seat and mediation provider with counsel, and record it in a signed addendum.",
  "Phase 0 formation, if a real customer conversation is closer than a code milestone.",
]));

// ================================================================ APPENDIX
doc.push(H1("Appendix A — Repository map"));

doc.push(table(
  ["Path", "Contents", "Class"],
  [
    ["backend/", "physics.py (the six models), simulate.py (synthetic fleet), warrants.py (fusion and hashing), roi.py (cost model), store.py (SQLite dispositions), main.py (stdlib HTTP server and routes)", "Code"],
    ["frontend/", "index.html, style.css, app.js — vanilla JS canvas dashboard, zero dependencies", "Code"],
    ["tests/", "test_physics.py (21 formula tests), test_store.py (17 ledger tests), run_tests.py (stdlib runner, discovers test_*.py)", "Code"],
    ["client-assets/MASTER-BRIEF-DOCKET/", "The 38-artifact docket: A1–A2, B01–B05, C01–C02, D00–D14, F00–F13 (36 Markdown + xlsx + html)", "Client-facing"],
    ["assets/", "Q6 entity analysis, IP strategy, library reconciliation, carrier dossiers, cost model, arithmetic pass and its check script", "Internal — never forwardable"],
    ["project-logs/", "CURRENT-STATE, README, chat-1/2/3 summaries and carry-forwards, transcripts with raw jsonl", "Internal"],
    ["Dockerfile, render.yaml, requirements.txt, PUSH-TO-GITHUB.bat", "Deployment and the owner's push helper", "Operational"],
  ],
  { width: [3.2, 5.4, 1.4], size: 15 },
));

doc.push(H2("Commit chronology"));
doc.push(table(
  ["Date", "Commit", "Stage", "What it did"],
  [
    ["11-08 00:53", "efb87ed", "0", "Initial commit — full app, 17 files, 2,806 lines"],
    ["11-08 01:55", "3b25d86", "0", "Dispatch-centre visual overhaul"],
    ["11-08 02:06", "ce64e0a", "0", "Light professional redesign"],
    ["11-08 02:31", "0796015", "0", "SVG rail assets and bearing indicators"],
    ["11-08 08:22", "2b7aa6c", "1", "External pilot cost structure"],
    ["11-08 08:49", "f1f705e", "1", "Client-assets tree, ROI calculator; tier-1 weakness documented"],
    ["11-08 09:11", "dd3c1d5", "1", "Re-price to marginal bands — fixes sub-2× entry and the ROI cliff"],
    ["11-08 11:29", "c995c76", "1", "Second pricing axis (sites); BNSF dossier"],
    ["11-08 12:23", "549f36d", "1", "UP/NS dossier; strategy corrected for the merger"],
    ["11-08 12:25", "668e5eb", "1", "Site-count reference corrected to 34–55"],
    ["11-08 15:03", "0dda8d3", "1", "CN/CPKC dossier"],
    ["11-08 15:30", "ed10875", "2", "Split client deliverables from internal material"],
    ["11-08 15:45", "487c378", "2", "Stop tracking axiom.db and __pycache__"],
    ["11-08 16:00", "77d4cf5", "3", "B01, B04, B05 against production architecture"],
    ["11-08 16:22", "903f1ae", "3", "Governance library reconciliation"],
    ["11-08 16:50", "a4d4fff", "4", "IP strategy: five-stage architecture"],
    ["11-08 17:15", "d05501f", "4", "D14 operating model"],
    ["11-08 17:29", "e8a08fc", "4", "D13 IP and escrow"],
    ["11-08 19:53", "7c47aa6", "4", "D12, D11, D02"],
    ["11-08 20:09", "96e058c", "4", "D07, C01, C02"],
    ["11-08 20:38", "b9aa4a8", "4", "D05, D06, D09; all twelve loopholes closed"],
    ["11-09 16:09", "cf2e6ba", "5", "Q7 — F00–F13, A2, D03, D04, D01, D10; 35 files"],
    ["11-09 16:20", "33ccc7e", "5", "B02, B03; build status reconciled"],
    ["11-09 16:32", "de9b245", "5", "Correct B02/B03 — disclose the absent ingest path"],
    ["11-09 21:16", "f58b07c", "6", "Rebuild lost chat-1 work: Rule 7, §14.5, Q6, logs"],
    ["11-09 21:17", "c9b32bd", "6", "Push helper for the owner"],
    ["11-09 21:17", "146b8e4", "6", "Chat-2 summary: the rebuild and unpushed state"],
    ["11-09 21:22", "ebbeee6", "6", "Standing instruction: write directly into the repo"],
    ["11-09 21:23", "2ec168b", "6", "Push helper reports the actual top commit"],
    ["11-09 21:28", "785f335", "6", "CURRENT-STATE: confirmed push; stale-ref trap"],
    ["11-09 21:35", "ee9800c", "6", "Preserve chat-2 transcript; extraction as standing rule"],
    ["11-09 21:44", "3d773ac", "6", "Chat-3 carry-forward and the mechanism of the loss"],
    ["11-09 21:44", "36b43bd", "6", "Chat-2 transcript to close"],
    ["11-09 21:44", "d6f25ac", "6", "Chat-2 raw log, final"],
    ["11-09 21:49", "05b161d", "6", "Final transcript and raw log at close"],
    ["11-09 22:01", "ed78962", "7", "A2/D08 arithmetic pass — 78 figures, two findings"],
    ["11-09 22:02", "b946678", "7", "Project logs record the pass; chat-2 summary finalized"],
  ],
  { width: [1.5, 1.3, 0.8, 6.4], size: 14, mono: [1] },
));
doc.push(P("Stage 6 is the rebuild-and-process stage: it recovered the lost chat-1 work, installed the write-in-repo rule, and built the transcript-preservation machinery that makes this document possible. Stage 7 is chat-3.", { spaceBefore: 120 }));

doc.push(H2("Current status at a glance"));
doc.push(table(
  ["Area", "State", "Note"],
  [
    ["Physics engine and tests", "Complete, 38/38 passing", "21 formula tests + 17 ledger tests; deterministic, no learned parameters"],
    ["Demonstration application", "Runs", "Synthetic data only"],
    ["Client docket", "38 artifacts built, 0 outstanding in the index", "Not yet counsel-reviewed"],
    ["Detector ingest", "Not built", "The largest gap; disclosed in three places"],
    ["Append-only ledger", "Built 2026-11-09", "Insert-only, triggers, SHA-256 chain, 17 tests"],
    ["Signed certification registry", "Not built", "F08 is the manual substitute"],
    ["SBOM, hash pinning, signed releases", "Not built", "Q1–Q2 2027 targets; disclosed"],
    ["Company formation", "Not done", "Texas LLC recommended, $300 filing"],
    ["Commercial numbers", "Two open findings", "A1 and D08 disagree; an owner decision"],
    ["D07 §14.5 venue", "Open counsel decision", "Blocks first execution"],
    ["Push state", "1 commit ahead of the local remote ref", "Verify with git log origin/main..HEAD; sandbox cannot reach GitHub"],
  ],
  { width: [3.2, 3.2, 3.6], size: 16 },
));

doc.push(spacer(240));
doc.push(new Paragraph({
  border: { top: { style: BorderStyle.SINGLE, size: 6, color: RULE, space: 8 } },
  spacing: { before: 120, after: 120 },
  children: [new TextRun({
    text: "Internal working document. Contains commercial strategy and a candid record of project failures. Not for customer distribution. Nothing here is legal or financial advice; every document in the docket under D requires review by qualified counsel in the relevant jurisdiction before execution.",
    size: 17, italics: true, color: "64748B", font: "Calibri",
  })],
}));

// ================================================================ assemble
const document = new Document({
  creator: "AxiomDynamics",
  title: "AxiomDynamics — Build History & Working Summary",
  description: "Stage-by-stage account of the AxiomDynamics build, 2026-11-08 to 2026-11-09.",
  styles: {
    default: {
      document: {
        run: { font: "Calibri", size: 21, color: SLATE },
        paragraph: { spacing: { line: 276 } },
      },
      heading1: {
        run: { font: "Calibri", size: 36, bold: true, color: NAVY },
        paragraph: { spacing: { before: 360, after: 200 }, keepNext: true },
      },
      heading2: {
        run: { font: "Calibri", size: 28, bold: true, color: NAVY },
        paragraph: { spacing: { before: 300, after: 140 }, keepNext: true },
      },
      heading3: {
        run: { font: "Calibri", size: 23, bold: true, color: SLATE },
        paragraph: { spacing: { before: 220, after: 100 }, keepNext: true },
      },
    },
  },
  numbering: {
    config: [
      {
        reference: "bullets",
        levels: [
          {
            level: 0,
            format: LevelFormat.BULLET,
            text: "\u2022",
            alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 400, hanging: 240 } } },
          },
          {
            level: 1,
            format: LevelFormat.BULLET,
            text: "\u2013",
            alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 800, hanging: 240 } } },
          },
        ],
      },
      ...["numA", "numB", "numC", "numD", "numE"].map((reference) => ({
        reference,
        levels: [
          {
            level: 0,
            format: LevelFormat.DECIMAL,
            text: "%1.",
            alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 400, hanging: 260 } } },
          },
        ],
      })),
      {
        reference: "numbers",
        levels: [
          {
            level: 0,
            format: LevelFormat.DECIMAL,
            text: "%1.",
            alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 400, hanging: 260 } } },
          },
        ],
      },
    ],
  },
  sections: [{
    properties: {
      page: {
        size: { width: PW, height: PH },
        margin: {
          top: MARGIN, bottom: MARGIN, left: MARGIN, right: MARGIN,
          header: 500, footer: 500,
        },
      },
    },
    headers: {
      default: new Header({
        children: [new Paragraph({
          alignment: AlignmentType.RIGHT,
          border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: RULE, space: 6 } },
          children: [new TextRun({
            text: "AxiomDynamics · Build History & Working Summary · Internal",
            size: 15, color: "64748B", font: "Calibri",
          })],
        })],
      }),
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [
            new TextRun({ text: "Page ", size: 15, color: "64748B", font: "Calibri" }),
            new TextRun({ children: [PageNumber.CURRENT], size: 15, color: "64748B", font: "Calibri" }),
            new TextRun({ text: " of ", size: 15, color: "64748B", font: "Calibri" }),
            new TextRun({ children: [PageNumber.TOTAL_PAGES], size: 15, color: "64748B", font: "Calibri" }),
          ],
        })],
      }),
    },
    children: doc,
  }],
});

const outPath = path.join(__dirname, "AxiomDynamics-Build-History-and-Working-Summary.docx");
Packer.toBuffer(document).then((buf) => {
  fs.writeFileSync(outPath, buf);
  console.log("written:", outPath, `(${(buf.length / 1024).toFixed(1)} KB)`);
});
