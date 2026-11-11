/**
 * Builds the AxiomDynamics Build History & Working Summary (.docx).
 *
 * Every figure, date, commit hash and document reference in the output was read
 * from the repository, not recalled. Sources, in order of authority:
 *   - git log (commit count read at build time, efb87ed..HEAD)
 *   - client-assets/MASTER-BRIEF-DOCKET/D00 Part VI (the gap register)
 *   - project-logs/{CURRENT-STATE.md, chat-1,chat-2,chat-3}
 *   - assets/* (internal analysis: Q6, IP strategy, library reconciliation,
 *     the arithmetic pass, the model decision paper, the export build record)
 *   - backend/*.py and tests/*.py, executed
 *
 * Run: node project-logs/build-history-summary.js
 * Out: project-logs/AxiomDynamics-Build-History-and-Working-Summary.docx
 */

const fs = require("fs");
const path = require("path");
const { execSync } = require("child_process");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle,
  PageBreak, Header, Footer, PageNumber, LevelFormat, TableOfContents,
  convertInchesToTwip,
} = require("docx");

// ---------------------------------------------------------------- live figures
// The commit count and the test count are read at build time. Writing them as
// literals is how every stale figure in this project happened: the number is
// correct when the sentence is drafted and wrong the moment the sentence is
// committed, because editing the file adds a commit.
function gitCount() {
  try {
    return execSync("git rev-list --count HEAD", {
      cwd: path.join(__dirname, ".."), encoding: "utf8",
    }).trim();
  } catch (e) {
    return "an unknown number of";
  }
}
function testCount() {
  try {
    const out = execSync("python3 -I tests/run_tests.py", {
      cwd: path.join(__dirname, ".."), encoding: "utf8",
    });
    const m = out.match(/(\d+) passed, (\d+) failed/);
    return m ? `${m[1]} passed, ${m[2]} failed` : "unknown";
  } catch (e) {
    return "not run at build time";
  }
}
const COMMITS = gitCount();
const TESTS = testCount();

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
/** Turn a string with **bold** and `mono` spans into TextRuns. */
function inlineRuns(text, size, color, forceBold, baseFont) {
  const font = baseFont || "Calibri";
  const runs = [];
  String(text).split("**").forEach((seg, si) => {
    const strong = si % 2 === 1 || forceBold;
    seg.split("`").forEach((t, ti) => {
      if (!t) return;
      runs.push(new TextRun({
        text: t, size, color,
        bold: strong || undefined,
        font: ti % 2 === 1 ? "Consolas" : font,
      }));
    });
  });
  return runs;
}

/** Paragraph that honours **bold** spans inside its text. */
function PB(text, opts = {}) {
  const {
    size = 21, italics = false, color = SLATE, font = "Calibri",
    spaceBefore = 0, spaceAfter = 120, align = AlignmentType.JUSTIFIED,
  } = opts;
  const runs = [];
  String(text).split("**").forEach((seg, si) => {
    const strong = si % 2 === 1;
    seg.split("`").forEach((t, ti) => {
      if (!t) return;
      runs.push(new TextRun({
        text: t, size, italics, color, font,
        bold: strong || undefined,
        font: ti % 2 === 1 ? "Consolas" : font,
      }));
    });
  });
  return new Paragraph({
    alignment: align,
    spacing: { before: spaceBefore, after: spaceAfter, line: 276 },
    children: runs,
  });
}

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
      children: inlineRuns(
        String(text), size,
        header ? "FFFFFF" : (color || SLATE),
        bold || header, mono ? "Consolas" : "Calibri",
      ),
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
              children: inlineRuns(text, 19, textColor),
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
    ["Prepared", "2026-11-09 at the opening of chat-3; revised 2026-11-11 after chat-5"],
    ["Scope", `Repository as it stands at HEAD — ${COMMITS} commits; Stages 0–9 covering chat-1 through chat-5`],
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
    ["II", "Stages 0–8: the build from first commit to the replicated ledger series, and every correction"],
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
doc.push(P("The original instruction, restated in the user's own words and never varied since, was to build the system on real physics: named physical laws, rolling per-axle z-scores, kinematics from Eₖ = ½mv², acoustics against the standard bearing defect-frequency equations (BPFO, BPFI, BSF, FTF) — explicitly not black-box ML and not fixed absolute alarm thresholds. The standing instruction that captured this is: \"We will keep this same concept throughout.\" It has been honoured across all " + COMMITS + " commits."));

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
doc.push(P("Every warrant carries a SHA-256 hash over a canonical JSON serialisation of its advisory ID, asset, timestamp, full evidence array and both model and reference-population versions. That is what makes the record tamper-evident at the individual-warrant level. The disposition ledger, which is a different record, is now append-only, hash-chained and signed (Stage 7), and the residual limits of that claim are in Part VII."));

// ================================================================ PART II
doc.push(H1("Part II — Stage-by-stage build chronology"));

doc.push(P(`The build ran in nine distinct stages across ${COMMITS} commits, from 2026-11-08 00:53 to the present. The stages below follow the git history. Commit hashes and dates are taken from the log, not recollected.`));

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
doc.push(H2("Stage 1 — The commercial model (2026-11-08, 08:22–15:03)"));
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
doc.push(P("That decision — to describe the intended production system and separately enumerate every gap to it — is what makes the rest of the docket honest. It produced B01 §7, a gap table that began at ten items and has since grown to twelve as new gaps were disclosed, including the project's largest known defect (item 5: no inbound sensor route exists), and it forced B04 and B05 to be written by inspecting the code rather than the marketing."));
doc.push(P("The three documents settled three architectural decisions, later recorded as AD-1 to AD-3 in B01:"));
doc.push(table(
  ["Decision", "Content", "Consequence"],
  [
    ["AD-1", "Fully on-premise edge, zero outbound network. No licence server, telemetry, update callback or third-party cloud. Ever.", "The air-gap claim becomes truthful. It costs the vendor remote diagnostics and all product telemetry."],
    ["AD-2", "Reviewer identity via local accounts plus a signed certification registry, administered by the Railroad.", "No dependency on railroad directory services; no path to pivot into their directory. Costs a second credential set."],
    ["AD-3", "The disposition ledger is append-only: superseded, never overwritten, never deleted.", "The regulatory argument rests on this. The code did not implement it when this table was written; it has since 2026-11-09. See Stage 7.3."],
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
doc.push(P("This is the largest drafting stage: eleven client-facing documents plus the internal IP strategy, across six commits, in a deliberate order. The order itself is the design — the documents that constrain everything else were written first."));
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
doc.push(P("cf2e6ba is the largest commit in the project: 35 files, 3,900 insertions. It built F00–F13 (the register and policy, plus thirteen executable forms), A2 (the rate card), D03 (the MSA), D04 (the five SOW templates), D01 (the preface and checklist), and D10 (the component register) — then ran a two-pass consistency audit across the whole set."));
doc.push(P("Two things from that commit deserve permanent record. The first is A2's role: it became the single authority on price, governing every other document. The second is F00 Rule 7, which is a documentation principle rather than a form:"));
doc.push(callout(
  "F00 Rule 7 — a blank and a decision are different things",
  "Every unfilled field is one of exactly two kinds. A fill-in blank is a value that exists and will be entered at execution — a party name, a date, an agreed amount. It is written as underscores and is safe to leave because the process that fills it is defined. An unmade decision is a question the docket has not answered — which law governs, which entity form. It is never written as a blank, because a blank implies we know it will be filled in. It is written as an explicit open item stating what must be decided, who decides it, and what happens meanwhile. The difference is the difference between a document that is quietly incomplete and one that is honestly incomplete.",
));
doc.push(P("Rule 7 also names the prohibited pattern: never write a clause that points to a field no document actually contains. That rule was written because D07 §14.3 had done exactly that — it sent dispute venue to \"[the courts / arbitration seat] stated in the Order signature block\", and no Order template has such a field. The clause read as complete to anyone who did not go and check, and there was nothing to check. This defect is fixed in chat-2 (Part IV)."));
doc.push(H3("B02 and B03, and the correction that followed"));
doc.push(P("33ccc7e added the flow map and the one-page executive infographic, and reconciled build status. de9b245 followed twelve minutes later with a correction that is the most important single commit in the project's quality history: \"Correct B02/B03: disclose that no detector ingest path exists.\""));
doc.push(P("The diagram had drawn a flow from wayside detector to edge inference. No endpoint accepted a Railroad payload. The signals came from the physics equations on synthetic traces. The docket's largest known gap had been drawn as a built capability — and it was found by checking the diagram against the code, not by reading the diagram."));
doc.push(P("That correction is now the standing discipline of the project: verify against the file, then write. Every later stage cites it, and the transcript of chat-2 records the assistant's own summary of why it matters — \"it looked right, so nobody checked whether it was true.\""));

// ---- Stage 6
doc.push(H2("Stage 6 — Recovering the loss, and the rules that came out of it (2026-11-09, 21:16–21:49)"));
doc.push(P("Stage 6 is process rather than product, and it is the stage that makes every later stage recoverable. It is covered in Part IV and Part V; what belongs here is the chronology. Commits f58b07c through 05b161d rebuilt chat-1's lost work (F00 Rule 7, D07 §14, Q6), installed the write-in-repo standing instruction, built the push helper, and committed the chat-2 transcript and its raw log — which is why the conversation now survives its session. It ends where chat-2 did."));

// ---- Stage 7
doc.push(H2("Stage 7 — chat-3: three builds, two analysis passes, and two audits (2026-11-09 22:01 – 2026-11-10 06:58)"));
doc.push(P("Chat-3 opened by verifying the handoff against the repository rather than trusting it, and found that four commits the carry-forward named as unpushed were already in origin/main, while the work actually waiting was different. That is the Stage 5 discipline applied one layer up, and it is the right way to read the rest of this stage: every conclusion below was reached by opening a file, not by recollection."));
doc.push(P("Then came three builds — the build history document itself, the append-only disposition ledger and the signed ledger export — and two analysis passes, the A2/D08 arithmetic check and the decision paper that prices its findings. The session closed by extracting its own transcript. The decision paper and the export were both materially changed by an independent audit after they were written, and in both cases the audit found something I had not thought of — including one case where the checker agreed with the mistake because I had written the checker too. The arithmetic pass was not audited and did not need repair; it is the one phase here that survived unamended."));

doc.push(H3("7.1 — The A2/D08 arithmetic pass (commits ed78962, b946678)"));
doc.push(P("The highest-value item in the handoff and untouched since cf2e6ba. assets/a2-d08-arithmetic-pass.py recomputes every figure in A2 and D08 from its stated source equation and exits non-zero on any mismatch. 78 of 78 computed figures agreed, so no arithmetic error exists in either document. Two claims did not reproduce — the two carried into Part VII as Findings 1 and 2 — and both were left open because fixing them means choosing which model governs, which is an owner decision rather than an editorial one."));
doc.push(P("The pass also fixed two real defects in the A1 workbook builder: a sheet-5 note attributed a 2% escalation rate to a cell that has held 0.05% since the correction, and the script saved to a path inside the destroyed chat-1 sandbox, so running it raised FileNotFoundError. The committed workbook was deliberately not regenerated — doing so would have baked both open findings into a new file before the model question was settled."));

doc.push(H3("7.2 — The build history document (commit a3ba43f)"));
doc.push(P("Requested by the owner because chat-1's conversation no longer exists and the build needed a readable record of itself. 29 pages when written, 32 after the Stage 6–7 revision, and revised again at chat-4's close to carry Stage 8 and to mark Findings 1 and 2 closed; eight parts plus an appendix, generated from the repository by project-logs/build-history-summary.js so it can be rebuilt after a change. Layout was verified by rendering to PDF and reading the pages, which found two defects: every numbered list shared one continuous sequence, and the Word TOC field rendered empty in a converter that does not update fields."));

doc.push(H3("7.3 — The append-only disposition ledger (commit 209efe6)"));
doc.push(P("Chosen next because it was the one open code control needing no commercial decision from the owner, and because the docket's most legally significant record was overstating what the code did. backend/store.py used advisory_id as PRIMARY KEY with INSERT ... ON CONFLICT DO UPDATE, so a second disposition on the same advisory overwrote the first — its reviewer, its note and its recorded_at all gone. F09 described an append-only record; the code produced one row that could be rewritten. Six documents disclosed the gap."));
doc.push(P("The rebuild: insert-only writes, with a correction expressed as a new row carrying supersedes_id; BEFORE UPDATE and BEFORE DELETE triggers that RAISE(ABORT), so the guarantee lives in the schema rather than in application convention; a per-row SHA-256 chain (prev_hash plus record_hash) and verify_chain() naming the first row that fails; and BEGIN IMMEDIATE on writes so two concurrent appends cannot both read the same prev_hash and fork the chain. Migration from the v1 table runs inside init_db(), preserving the surviving decision and its original timestamp without fabricating lost history."));
doc.push(P("Two defects were found while closing it. tests/run_tests.py was loading only test_physics.py, so the new 17-test module would never have run in CI — it now discovers every test_ file. And the root README opened \"three named physical models\" then listed seven, had two items numbered 7., and described the 2% catastrophic-escalation placeholder as current."));

doc.push(H3("7.4 — The A2/D08 decision paper (commit b23d0c7)"));
doc.push(P("No product code changed. assets/a2-d08-model-decision-2026-11-09.md plus its checker price both answers so the owner's decision is a comparison rather than more research. Three findings the arithmetic pass did not have: the 2.0×/4.1× anchors are recoverable on a third cost basis (pilot plus three full years at list, no conversion credit) at p ≈ 0.0412%, which makes Finding 1 a disclosure defect rather than a fabrication — but p is not unique, so it stays open; D08 contradicts itself, pricing a prevented failure at ~$993,000 in §4 and $8.6M–$11.4M in §5, with §4's figure within 0.7% of A1's; and backend/roi.py is 29× from A1 per missed defect, of which probability accounts for 20.5×."));
doc.push(P("The audit found four errors in the paper, including one where I had labelled a figure as roi.py's output when roi.py takes warrants rather than axles and the number was never computable. The corrected comparison is per defect, and it is a larger gap than the one I had written."));

doc.push(H3("7.5 — The signed ledger export (commit d9c83d4)"));
doc.push(P("backend/ledger_export.py writes an HMAC-SHA256-signed bundle — manifest, records, signature — and tools/verify_ledger_export.py verifies it without importing anything from backend/, from an empty directory under -I. A recipient needs the bundle, the key and a Python standard library. Bundles chain through previous_export_hash; keygen refuses to clobber a key and forces mode 0600."));
doc.push(P("HMAC rather than Ed25519, and the reason is a constraint rather than a preference: the standard library has no asymmetric primitive, requirements.txt is numpy-only by design for air-gapped installs, and hand-rolling a curve in a product that tells CISOs it does not hand-roll crypto would be worse than the gap. The two limits — a symmetric signature cannot name the signer, and cannot prove when it was made — are given their own section in B01 §4.5a rather than a footnote."));
doc.push(callout(
  "The audit found a total wipe that verified green",
  "Delete every row with file access, run the honest exporter, and a recipient holding the previous bundle was told every check passed — five records gone, no warning. Each check was individually correct: hashes valid, ids ordered, count matching, signature good. None compared the bundle against one the recipient already held, and an empty bundle is trivially self-consistent. My own 33 tests passed because I had not thought of the attack, so had not written it. Fixed by recording the ledger's own head in every manifest and failing when a later bundle reports a shorter ledger (no_truncation), plus genesis_anchor for rows deleted from the front and empty_bundle_justified for a zero-record export. The fix then broke the zero-record incremental export — a quiet week failed range_from — and D09 requires a weekly export, so the documented procedure would have failed on any quiet week. Both are covered by tests now.",
  { fill: "FBEAEA", labelColor: RED },
));
doc.push(P("Verification: 42 export tests, full suite 80. The erasure attack re-run against the fixed standalone tool exits 1 with no_truncation. Live end-to-end: real server, three dispositions including a genuine supersede, exported, verified from a different directory under -I."));

doc.push(H3("7.6 — The transcript"));
doc.push(PB("Re-snapshotted at 5,032 events (17.1 MB) and rebuilt the readable extract at 641 turns, of which ten are the owner's. The mid-session snapshot was byte-for-byte a prefix of the new one, verified line by line, so it was deleted rather than kept as 13 MB of duplicate. The extractor is now committed at project-logs/extract_transcript.py instead of a shell heredoc, with the trap written into it: the role is the top-level `type` field, not message[\"role\"], and reading the wrong one yields zero turns and no error."));

// ---- Stage 8
doc.push(H2("Stage 8 — chat-4: the replication series, the model decision, and ten defects three passes found (2026-11-10)"));
doc.push(P("Chat-4 opened by verifying the handoff against the repository, which is now the established first move and which again found the written push list stale: the carry-forward named a remote ref of bb99cdd while the local ref stood at 4eafe58 with one commit waiting on top of it. The build that followed closed the half of B01 §7 item 12 that needed no commercial decision and no new dependency — nothing produced export bundles on a cadence, so a week nobody remembered to export was a week with no evidence."));
doc.push(P("The phase's most important output is not the module. It is that two independent audits found nine material defects, and the second found four in code the first had already approved."));

doc.push(H3("8.1 — The design constraint the docket imposed"));
doc.push(P("D09 §3.2 promises the Platform has no mechanism to send data to Supplier or any external service, and B02 repeats that the supplier cannot reach the box. So off-box replication cannot mean the box pushes bundles over a network without contradicting a customer-facing promise in order to close a control gap. The owner chose on-box scheduling with physical carriage: the Platform produces the series and verifies it, and moving it to backup media remains the Railroad's step under D09 §3.3. The module therefore contains no network code at all, and both docket rows now say carriage remains open rather than claiming replication is finished — which is the honest reading, and a smaller claim than the one the item previously implied was pending."));

doc.push(H3("8.2 — What was built"));
doc.push(PB("backend/ledger_replication.py executes the cadence D09 §4.5.4 already specified: a monthly full export, a weekly incremental (`after_id`, chained by `previous_export_hash`), every bundle citing the previous one's signature_of(), a zero-record week kept rather than skipped, and no file ever overwritten. A series.json beside the bundles records the last digest and the last id carried; it is written via mkstemp, fsync and an atomic rename with the directory entry fsynced, and the whole read-decide-write sequence runs under an advisory lock. inspect opens every bundle, recomputes its digest, verifies it against its predecessor, and walks month and week keys to report a missing period. 32 tests; the full suite went from 80 to 112."));

doc.push(callout(
  "Two audits and nine material defects, with a green suite of 108 in between",
  "The first audit found five. The no_regression fix had landed in backend/ledger_export.py but not in tools/verify_ledger_export.py — the very tool D09 §4.5.4 names for the quarterly check — so the contract's own verifier rejected every legitimate chained full export while the in-repo one passed. inspect() never opened a bundle, so a record edited inside a signed bundle came back 'series is continuous'. It could not see a missing period at all. A lost series.json silently restarted the series under a docstring promising refusal, and the test asserting it did so was named as though it tested the opposite. Concurrent runs stranded signed bundles the state never recorded. The second audit then found four more. The period walker HUNG FOREVER on a 53-week ISO year — 2026 is one — so the quarterly tool would simply never return. The same walker could not see a deleted latest month. due_exports read the state outside the lock, so concurrent run_due calls produced duplicate bundles the cadence says must not exist. And the test written to guard the verifier fix asserted that a string was absent in a way that passed when the check was deleted entirely — a test that could not fail. That last one is the most instructive: it was written immediately after an audit about checks that pass for the wrong reason, and it repeated the error in miniature.",
  { fill: "FBEAEA", labelColor: RED },
));
doc.push(P("The pattern across both audits is the one this document has recorded at every stage: the work was internally consistent and externally wrong. A test suite written by the author of a mechanism tests the author's model of the threat. What corrected it each time was a reader with no stake in the conclusion, told to falsify rather than confirm."));

doc.push(H3("8.2a — A tenth defect, found by trying it rather than reading the code"));
doc.push(PB("At chat-4's close, validating the completed work rather than assuming it, I attacked a written bundle by adding a top-level key. **Both verifiers reported ok=True.** The signature covers a selected tuple — `format`, `manifest`, `records` — and the digest names four fields; neither covers \"everything else\", so any added key rode along unsigned. It could then be changed after signing with nothing noticing, and a recipient reading it would reasonably take it as attested by the bundle it sat in."));
doc.push(PB("The fix is small: verification now requires the bundle to be exactly the four signed parts and rejects anything else with the check `bundle_no_extras`. The signing construction was left alone, because selecting named fields is the right way to sign — it makes the covered set explicit in code rather than implicit in whatever the document happens to contain. **The defect was that verification never checked for anything outside that set.** One test was added and mutation-tested: neuter the check in both files and it goes red, restore it and it passes."));
doc.push(PB("This one is worth recording because of how it was found. Nine defects in this stage came from two adversarial audits; this one came from the owner's instruction to *validate the completed tasks*, which meant attacking the artifact instead of re-reading it. The lesson is the same one at a different angle: a green suite says the tests you thought of pass."));

doc.push(H3("8.3 — The model decision, and the numeric defect under it"));
doc.push(PB("The second phase of chat-4 closed both findings carried in Part VII. The owner delegated the question (\"you decide\"); the answer was **A1**, expressed as Option D in the decision paper. D08 was restated from A1 rather than the reverse, on the reasoning that A1 is the instrument the customer operates from their own inputs while D08 is a narrative built on top of it."));
doc.push(PB("Restating D08 §5 surfaced a defect in it that the old headline had hidden. D08 §2 scopes the pilot at **100–200 axles**; the old §5 computed a pilot-year benefit at 500. At 200 axles A1 produces $278,670 against a $370,000 fee — **0.75×. The pilot does not pay for itself at its own scoped fleet size**, and D08 now says so in those words instead of quoting a millions figure. That is an uncomfortable sentence in a licensing document and it stayed in, because the alternative is a customer discovering it during the pilot."));
doc.push(PB("The numeric defect underneath was worse than either document. **`backend/roi.py` valued a missed defect 29× too high** — it carried a 2% catastrophic-escalation probability where A1's cell B17 has held 0.05% since the first correction, and blended the $9.25M midpoint of two severe-tier benchmarks as though it were the typical cost. Expected cost per missed defect is now **$999,750**, arithmetically identical to A1's B22. The two NTSB benchmarks survive as `SEVERE_FAILURE_COST_*`, explicitly reference-only, and the dataclass field was renamed `severe_cost_range_usd` so no later reader mistakes them for the typical case."));
doc.push(callout(
  "The guard that could not fail",
  "The ROI test rebuilt its expected value from the same constants it then compared against — `expected = (1 - roi.P_CAT) * roi.TYPICAL + roi.P_CAT * roi.CATASTROPHIC`, asserted equal to `roi.EXPECTED_COST_PER_MISSED_DEFECT_USD`, which is that same expression. It passes for any values of the constants. Restoring the 2% defect deliberately produced **112 passed, 0 failed**. The fix was to assert literals, then break the thing on purpose and confirm red — after which the same defect gives 111 passed, 1 failed. This is the third session running in which an audit found a test passing for the wrong reason, and the second in which the failing test was one I had just written.",
  { fill: "FBEAEA", labelColor: RED },
));
doc.push(P("Nine more findings from the adversarial audit of the restatement were fixed before commit, and they are worth listing because most were questions of citation rather than arithmetic: A2 §3.2 claimed its rules needed \"no conversion credit\" when 1.77× requires one (no-credit is 1.65×/3.34×); the \"CLOSED\" block printed pre-restatement totals while checking nothing; two internal assets still carried the withdrawn model; A2 §9 ran the pilot at 500 axles; D08 §4's $1,390,000 was a rounded figure $289.50 light and was replaced with the derived $1,399,650; a \"five years\" heading sat over a six-year table; and the A1 builder's own prose said \"~2.0×\" while its cell computed 2.2546×."));

// ---- Stage 9
doc.push(H2("Stage 9 — chat-5: an audited ledger, an ingest path, three supply-chain tools, and attribution (2026-11-11)"));
doc.push(P("Chat-5 opened with an instruction that set its shape: work the open items from low priority to high, one at a time, then wrap everything and hand off. The numbered list in CURRENT-STATE is priority-ordered rather than effort-ordered — a point the owner raised at chat-4's close — and this session is the demonstration, because the second item on the list was the largest piece of work in it. Five tasks closed."));
doc.push(P("The first was not code at all. D07 §14.5 has carried an open venue question since the docket was drafted, and the first deliverable was a counsel brief and a Phase 0 formation checklist written so that a lawyer answers a specific question rather than being handed the problem. The venue answer stays open and labelled open, because it is a counsel decision and guessing at it in a customer document is the exact failure this project keeps finding elsewhere."));

doc.push(H3("9.1 — The ledger audit, and a false claim in a customer document"));
doc.push(PB("A fresh agent was given the disposition ledger, the export bundle and the replication series, with the instruction to falsify rather than review. It found four defects, one critical: a rewritten chain verified against a bundle already held, because the previous-bundle comparison checked the slice it was handed rather than the slice it should have been. Two more were structural — a mid-chain deletion the whole-series walk never saw, and `INSERT OR REPLACE` defeating the append-only triggers on the disposition table, because SQLite does not fire a `BEFORE DELETE` trigger for it unless recursive triggers are on. The fourth was duplicate JSON keys, which two parsers can read as two different records."));
doc.push(callout(
  "One of the four was a customer-facing claim the code did not back",
  "B01 §7 item 8 asserted a property the export did not have. That is the category of defect that matters most here, and not because it is technically the worst: a customer could check it against us and be right to complain. Code is verifiable by running it. Prose is not, and prose that overstates a control is worse than prose that undersells one, because the overstatement is what a regulator reads.",
  { fill: "FBEAEA", labelColor: RED },
));

doc.push(H3("9.2 — The ingest path: narrowing the largest gap, not closing it"));
doc.push(PB("`POST /api/ingest` now applies the three-gate chain B02 §2 has specified since the flow map was drawn — schema, then timestamp, then plausibility, in that order and for stated reasons — accepting for scoring, retaining as suspect without scoring, or refusing with a named reason and logging the refusal. Twenty-four tests. This is the item D00 calls the largest gap in the register, and the record is careful about the size of the claim: the schema is a demonstration schema, the endpoint has no authentication, and no accepted reading is scored. **Building the validator did not put a Railroad reading behind any number**, and both the build record and the gap register say that in those words rather than letting \"ingest path built\" imply otherwise."));

doc.push(H3("9.3 — The supply chain, and a distinction that had been collapsing"));
doc.push(PB("D09 §4.4 disclosed three supply-chain gaps: SBOM, hash verification of dependency downloads, and GPG-signed releases. Three tools were built for them — `tools/sbom.py`, `tools/pin_requirements.py`, `tools/sign_release.py` — and none of them is applied. That distinction is the point of the stage. The project had been using one word for two states, and \"implemented\" had drifted to mean \"a tool exists\". The three-state discipline this pass adopted — **absent, built, applied** — is now carried per control in D09 §4.4, because a disclosed gap that is built-but-not-applied is still a gap and a reader has to be able to see which one they are looking at."));
doc.push(P("A mistake worth recording sat in the middle of it: the pinning tool's first version pinned the hashes it had just downloaded, which records whatever the server served rather than what was verified. A pinning mechanism that trusts its own fetch is not a pinning mechanism. It was found by asking what the tool would do against a compromised mirror, not by a test."));

doc.push(H3("9.4 — Attribution: what it closed, and the defect the audit was for"));
doc.push(PB("The owner delegated the design question — asked which attribution claim the Platform should be able to make, they answered that they were unsure and trusted the judgement. The answer built here is per-reviewer HMAC keys, an append-only hash-chained registry, and attestations that travel **inside each exported record**. The placement is a decision worth recording: a top-level attribution block would have failed the `bundle_no_extras` check added at chat-4's close, and loosening that check would have traded a security property for layout. Inside `records`, the block is covered by the bundle signature automatically, and `row_hash()` ignores it because it selects a named field list, so no existing `record_hash` changed."));
doc.push(PB("The scheme is symmetric, and that was deliberate rather than lazy. There is no vetted curve implementation in this deployment's dependency set, and hand-rolling one in a product whose pitch includes not hand-rolling crypto would be a worse gap than a symmetric attestation whose limits are written down. Those limits are stated in the module, in D09 §4.5.5 and in the build record: the claim is *a registered key was used*, not *a person signed*, and custody is what binds one to the other. The registry itself is **hash-chained, not signed** — tamper-evident to a reader who recomputes the chain, which is weaker than authentication, and several documents had been calling it signed until this pass corrected them."));
doc.push(callout(
  "The finding that justified the audit on its own",
  "The `reviewer` label inside an exported attestation was not covered by the HMAC. The signed message is a fixed prefix plus the row's `record_hash` — the reviewer name is not in it, so the label was decorative. A holder of **any** registered reviewer key could take a row naming somebody else, compute a perfectly valid attestation with their own key, write the other reviewer's name into the block, re-sign the bundle with the export key, and **both verifiers returned a pass**. Every test in a suite of forty-five passed anyway, because the suite was written by the person who believed the label was covered. The fix requires the verifier be told which reviewer each key belongs to; hashing the name into the message was rejected because it makes the attestation non-transferable and moves the same problem one step later.",
  { fill: "FBEAEA", labelColor: RED },
));
doc.push(PB("Eight more findings came with it: ordering checks guarded by truthiness, so deleting a field disabled the check; a check-then-write race in `attest()` between reading the registry and writing the attestation; `attest` and the export disagreeing about which registry entry is the registration after a certificate renewal, so an honest bundle failed at the recipient; malformed blocks raising `AttributeError` instead of a named failure; a docstring claiming a registry signature that does not exist; a standalone-verifier branch no test reached; and a revocation that could be undone by re-registering the same key bytes, which the mutation run exposed as dead duplicate code sitting in the wrong function. All nine are §4 of the build record and each is now a test."));
doc.push(P("Verification for the stage: forty mutations against the three modules, forty killed, zero survived — ten of them added specifically to cover what the audit found. The suite went from 180 to 238."));

doc.push(H3("9.5 — The lesson this stage adds"));
doc.push(P("Three of the five tasks in this session ended with an audit finding something the author's own tests could not, and every session in this project has now had that happen. The pattern is not carelessness. It is that the person who writes the claim also writes the test that agrees with it, and no amount of care inside that loop breaks the loop. The standing rule — a fresh agent told to falsify — is what has been doing the work, and Stage 9's head-line finding is the clearest case yet, because it survived a green suite that had been built specifically to attack the thing it was hiding in."));
doc.push(P("The second lesson is a document one, and it accumulated rather than arrived: most of this session's corrections were to prose, not code. The registry was repeatedly described as \"signed\" when it is hash-chained; a customer document claimed a property the export did not have; the rate card priced a registry as unbuilt that is now partly built. None of those would fail a test."));

// ---- Stage 10
doc.push(H2("Stage 10 — chat-6: authenticated disposition entry, and a guard the audit found inert (2026-11-11)"));
doc.push(PB("Chat-6 opened with the owner restating a standing rule as a permanent one: every chat capped at 125,000 tokens, and every build phase laid out as a priority ladder from low complexity through high, worked one item at a time. The ladder for this phase had six rungs, and the chosen track was the item chat-5's handoff named as the largest remaining code item: **session-bound disposition entry**, the blocking half of B01 §7 item 1."));

doc.push(H3("10.1 — What the gap was, stated precisely"));
doc.push(PB("Chat-5 built the reviewer registry and HMAC attestations. A disposition could be *bound* to a registered reviewer and the binding *verified* by a recipient of an export. But the write route read `reviewer_name` and `cert_id` out of the JSON body, so the name on a decision was whatever the caller typed. The claim that a reviewer made a decision was verifiable but not **enforced at the point of entry** — and a registry nobody is required to present is a registry that documents intent rather than gating action."));

doc.push(H3("10.2 — What was built"));
doc.push(PB("`backend/accounts.py` binds an account at enrollment to a certification record already in the reviewer registry, and refuses enrollment for a certificate the registry does not have or has revoked. The account stores a PBKDF2-HMAC-SHA256 verifier — 600,000 iterations, a 16-byte per-account salt — rather than a passphrase. The platform's own dependency set contains no KDF, and hashlib's is used rather than writing one, for the reason the attribution scheme also gave: a product that tells CISOs it does not hand-roll crypto does not get to make an exception for the thing protecting the login."));
doc.push(PB("A session is a 32-byte bearer token of which only the SHA-256 digest is stored, so a copy of the database yields nothing usable. `resolve_session` checks five things, and the fifth is the one that is expensive to omit: the token was issued here, the session is not revoked, it has not expired, the account is still live, and **the certificate behind it is still live**. A certificate revoked at 09:00 would otherwise keep authorising writes until the token's TTL ran out, and every one of them would be attributed to a certificate that no longer existed."));
doc.push(PB("The account register is append-only and hash-chained with the same trigger set as the reviewer registry, and its hash **covers salt, iteration count and verifier**. That last part is not decoration: a host owner who could swap a verifier would own the account and every session it ever issued, so a value the hash does not cover would be a value somebody can change. The same reasoning as the registry's decision to hash `registered_at`."));
doc.push(PB("The route takes identity from the session and **nowhere else**, and a body carrying `reviewer_name` or `cert_id` is **refused rather than ignored**. That choice is the one integrators will notice: an ignored field lets a caller believe they named the reviewer, and the resulting code names the wrong person for as long as nobody re-reads the response. Refusing it turns a silent wrong answer into a 400 with a reason. With **no account enrolled the path closes (503)** instead of falling back to the old free-text behaviour — the fallback would make the gate only as strong as somebody remembering to enrol an account. `tools/seed_demo_account.py` is the deliberate act that opens it."));
doc.push(PB("`store.save_disposition` grew a `guard` callable run inside its write transaction, because the ledger's write lock is the only instant at which \"still live\" and \"still unwritten\" are both true. The same race that made `attest()` re-read under its lock in chat-5."));

doc.push(H3("10.3 — The guard that could not fail, found by the audit that was told to falsify"));
doc.push(PB("An independent agent was given the claim — *a disposition cannot be written unless the caller presents a live session token, and the identity on the row comes from the session* — and told to falsify it rather than review the code. It falsified the first half in one line. **The revocation guard did nothing.** `save_disposition` called `guard()` and discarded the return value, while the route installed `lambda: accounts.cert_is_live(...)` — which *returns a boolean*. So the guard ran, computed `False`, and the row was written anyway. A certificate revoked between resolve and INSERT produced HTTP 200, a row, and a reviewer name under a certificate that no longer existed."));
doc.push(callout(
  "Why 310 green tests said nothing",
  "The test simulated the race with a guard that **raised**. That is not the guard the route installs. A guard whose only tested failure mode is one the caller does not use is not a guard; it is a guard-shaped object that the suite and the route agree about and the attacker does not. This is the fourth session running where an audit found something the author's tests could not, and the third in which the failing thing was newly built rather than old.",
  { fill: "FBEAEA", labelColor: RED },
));
doc.push(PB("The fix aborts on a falsy return, and the route turns that abort into a 401 rather than a 500. The new test revokes the certificate **inside** `resolve_session` — the real race, through the real route, not a synthetic guard — and reverting the fix reproduces the exploit verbatim: HTTP 200, row written, certificate already revoked. That reproduction is the evidence; a test that only passes is not."));

doc.push(H3("10.4 — The hostile-input sweep"));
doc.push(PB("Two more defects came from asking what a malformed body does rather than what a valid one does. `{\"note\": {…}}` raised `AttributeError` on `.strip()`, and `{\"disposition\": [\"x\"]}` raised `TypeError` because `list in dict` hashes the key — both surfaced as a 500, both now 400 with a reason. The second is the same class as a defect another module in this repository already had, which is the argument for a sweep over body shapes rather than a fix per reported bug."));

doc.push(H3("10.5 — What held, and what the stage deliberately does not claim"));
doc.push(PB("No credential path produced a write: absent header, bare token, `Basic`, the token replaced by its own digest, expired, signed out, account revoked. A token for reviewer A could not record a decision as B, and nine alternative body field names changed nothing. Duplicate JSON keys could not smuggle identity. Exactly one call path reaches `store.save_disposition`; the ingest, export and replication modules only read the ledger. A host owner with database write access can hand-insert a session row or rewrite an expiry, and the module says so instead of implying otherwise."));
doc.push(PB("Four limits are stated rather than implied. It does not prove a **human** was at the keyboard — it proves a credential was presented, and custody and joiner/mover/leaver are a procedure, not a function. It does not protect the **token in transit**: the demo host is plain HTTP, and a bearer token there is a shared secret on the wire (B01 §7 item 10). It does not make **attestation** stronger: passing the reviewer's HMAC key as the login credential was rejected precisely because it would put the attestation secret on the server for the life of every session. And entry now requires a live **session**, not an **attestation** — an unattested row is still an honest state the manifest counts."));

doc.push(H3("10.6 — Documents this stage corrected"));
doc.push(P("Most of the prose corrections were the same overstatement in four places: that entry is not gated. B01 §7 item 1, B01's AD-2 architecture row, its \"what this does not claim\" item 2, D09 §4.4, D00 Parts IV and VI, and F08's purpose note all said a reviewer can self-assert a certification ID. Each was rewritten in the same pass as the code change, per a rule this docket repeats: a gap moves to closed only when the code changes and every document that discloses it is amended in the same commit. F08 changed character rather than status — it is no longer a substitute for a missing technical control, it is now the record of *who the person behind the credential is*, which software still cannot establish."));
doc.push(P("Verification for the stage: suite 238 to 315. Six guard mutations and five credential mutations attempted; all killed, one only as a pair, which is recorded in the code because a source-level guard is what closes it. The audit that was run last found the defect that the tests did not, which is the order this project has learned to run them in."));

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
  "Holds AD-1 to AD-3, the production gap table (§7, twelve items), and the costs of the architectural choices (§8) stated plainly because the railroad's IT team will find them anyway. Its opening sentence is a warning to every later reader: nothing in it describes the demo.");
docBlock("B02", "Flow Map", "Built (.md) — corrected at de9b245",
  "The visual companion to B01: what enters, what is computed, where a human intervenes, what is recorded, what leaves.",
  "Solid lines mean shipped; dotted mean designed and not built. §2's ingest path is the one that was drawn wrong and corrected. §9 closed with the most useful sentence in the document — that the ledger needed rebuilding and the front door did not yet exist. Both clauses have since been rewritten there: the ledger was built on 2026-11-09, and the front door is still absent.");
docBlock("B03", "Executive Infographic", "Built (.html)",
  "One page for executives who will not read B01.",
  "Encodes the platform/human boundary as a deliberate break in the drawn line, and carries a status block disclosing the absent ingest path.");
docBlock("B04", "Technology Stack Disclosure", "Built, verified against the repository",
  "The dependency register for IT security review and open-source licence compliance.",
  "Names exactly one non-stdlib runtime dependency (numpy, BSD-3-Clause) and explains why no web framework exists: to demonstrate that a predictive-maintenance platform does not require a software supply chain to operate. §7 names four supply-chain gaps — no pinning, no hash verification, no SBOM, no signed artefacts — and states that none blocks a demo and all four block production.");
docBlock("B05", "Data Flow & Data Residency", "Built, verified against code",
  "The document a railroad's CISO reads first.",
  "Answers the air-gap question with what was actually checked rather than what is promised, and sets a rule: any future outbound call must be disclosed in B05, D06 and D09 before shipment. §7 is deliberately uncomfortable — five controls present, two not yet built, one dependent on the railroad. The ledger moved from commitment to present on 2026-11-09.");

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
  "72-hour supplier-to-railroad notification and 24-hour railroad-to-supplier for discovered vulnerabilities, with a 30-day root-cause analysis. §4.4 lists six known gaps with remediation targets. §7.2 and §7.3 were added because a control disclosed only in a remediation table is not disclosed — see Part IV.");
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
doc.push(P("Contracts say what the rules are; forms are how the rules are applied one event at a time. Every form has exactly one purpose, one signatory, and a stated consequence for silence. The thirteen executable forms, with their trigger and default — F00 is the register and policy above them, not a form:"));
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
doc.push(P("Chat-3's own record of its opening is worth adding because it is the same lesson applied one layer up. The handoff document named specific commits as unpushed; four of them were already in origin/main, and the work actually waiting was different. A written state list is a hypothesis. The repository is the fact."));

doc.push(H2("The rules that came out of it"));
doc.push(P("Three standing instructions now govern every session, and each is a direct consequence of something that went wrong:"));
doc.push(...numbered("numC", [
  "\"Drop all the entire project work directly in AxiomDynamics folder so we don't lose any data from sandbox.\" Every document, script and log is written into C:\\Users\\RGV\\AxiomDynamics on the first pass, and committed in the same pass that produces it. No drafts in sandbox scratch space.",
  "Verify against the file, then write. Never cite from memory and check afterwards. That habit produced every bad citation in the project, and the worst defect — the ingest path drawn as built — came from the same habit applied to a diagram.",
  "Extract and commit the session transcript at close, raw .jsonl included. From chat-2 onward this holds, and the files are in project-logs/transcripts/.",
]));
doc.push(P("One further operational fact, because it is not obvious: the command environment cannot reach GitHub. git push and git fetch both fail with HTTP 403 from the proxy. Commits land locally in the real repository; the owner pushes with PUSH-TO-GITHUB.bat in the repo root. This means \"committed\" and \"on GitHub\" are different states, and the local origin/main ref is not evidence of remote state."));

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
doc.push(P("Chat-2 found its own session log still on disk at .claude/projects/session/ — 791 events, 1.6 MB — extracted 302 readable turns and committed both the readable version and the raw .jsonl as ee9800c. That is now the standing rule, recorded in project-logs/transcripts/README.md and in persistent memory. Chat-3 repeated it at close: 5,032 events, 641 extracted turns, raw log committed (53ad93a), with the extractor itself committed so the procedure is reproducible rather than remembered."));
doc.push(P("The honest limit, stated in the same README: this protects chat-2 onward. Chat-1 is a real loss and no amount of procedure brings it back."));

// ================================================================ PART VI
doc.push(H1("Part VI — Internal strategy in assets/"));

doc.push(P("Five internal documents sit in assets/ from chat-1 and chat-2, and three working papers were added in chat-3. None may be forwarded to a customer, and the classification rule in Part II is what keeps them there. Each is summarised here because the strategy they contain is not in the docket and is needed to discuss the next phase."));

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

doc.push(H2("Three documents added in chat-3, and what each is for"));
doc.push(P("These are working papers, not strategy. Each exists so that a claim made elsewhere can be checked by running a script rather than by re-reading a document."));
doc.push(table(
  ["Document", "What it does", "Checks"],
  [
    ["a2-d08-arithmetic-pass-2026-11-09.md", "Recomputes every figure in A2 and D08 from its stated source equation. Establishes that neither document contains an arithmetic error, and isolates the two claims that do not reproduce.", "78 figures, a2-d08-arithmetic-pass.py"],
    ["a2-d08-model-decision-2026-11-09.md", "Prices both answers to Findings 1 and 2 so the owner's decision is a comparison rather than more research. Adds three findings the arithmetic pass did not have, including that D08 contradicts itself.", "65 figures, a2-d08-model-decision.py"],
    ["ledger-export-build-2026-11-09.md", "Records the signed export: the HMAC decision and its three bounds, the erasure hole the audit found and the attack that demonstrated it, the fix, and the quiet-week regression the fix caused.", "the export suite, tests/test_export.py"],
  ],
  { width: [3.4, 5.2, 1.4], size: 15 },
));
doc.push(P("The export build record §5.1 is the most useful page in the set. It walks the erasure attack step by step and shows that every individual check was correct — which is why the first version's own test suite passed — 33 tests at that point, none of which attempted the attack, because I had not thought of it. The lesson recorded there and in persistent memory is that a suite written by the author of a mechanism tests the author's model of the threat, not the threat."));

// ================================================================ PART VII
doc.push(H1("Part VII — Open items and unresolved findings"));

doc.push(PB("The docket index asks to be corrected when a gap closes and refuses to claim a gap is closed when it is not. This part applies the same standard to the project as a whole. Five items were open when this part was written in chat-3. **Two of them — Findings 1 and 2 — closed on 2026-11-10 in chat-4**, when the owner delegated the model question and it was decided in favour of A1. They are kept here in full with their resolution rather than deleted, because the misstatements they describe are exactly what a first draft of a commercial document does, and the reader who writes the next one should see how they were caught. Items 3 to 5 below are the three that remain open, and item 6 records work deliberately deferred."));

doc.push(H2("1. Finding 1 — the modelled-return anchors did not reproduce (CLOSED 2026-11-10)"));
doc.push(P("A2 §3.2 stated that the customer's modelled return improves \"approximately 2.0× at 500 axles, rising to about 4.1× at 10,000.\" D08 §3 repeated both figures verbatim. Recomputed with A1's own default assumptions, on the only two cost bases that then existed in the repository:"));
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
doc.push(P("Neither basis produces 2.0× at 500 and 4.1× at 10,000. On the two cost bases that already exist in the repository, the shipped model does not reproduce the anchors. The direction of the claim is correct — return does improve monotonically with fleet size on either basis — but the two anchor values are not derivable from the model as presented."));
doc.push(P("The decision paper then found a third basis that does reproduce them, and this is the correction worth carrying. On pilot cost plus three full years at list price with no conversion credit, the cost ratio the anchors demand — cost at 10,000 axles over cost at 500 = 9.756 — is a property of the pricing, not of the benefit model, so a single value of the catastrophic-escalation probability fits both endpoints. Against three years of benefit that value is p = 0.0714%, producing 2.00× and 4.06×; against four years of benefit it is 0.0412%, which also fits. Finding 1 was therefore a disclosure defect — an unstated frame, not an invention — but the parameter was not uniquely determined, because the benefit horizon was stated nowhere."));
doc.push(PB("**How it closed.** The owner delegated the choice in chat-4 (\"you decide\") and A1 was chosen, expressed as Option D in `assets/a2-d08-model-decision-2026-11-09.md`. A2 §3.2 and D08 §3 now state **1.77× at 500 axles and 3.36× at 10,000**, with the cost basis written into the sentence rather than left to inference: A1 at its own defaults, three years of benefit against the four-year fee commitment at list price net of the §9 conversion credit. The text also states the fallback a reader needs — **1.65× and 3.34×** on a basis that additionally disallows the conversion credit — and warns against mixing the two in one table. The withdrawn pair is not reproducible on any basis in the repository, and that sentence is now in the arithmetic pass as a checked statement rather than a claim."));
doc.push(PB("One consequence is worth a reader's attention because it looks like a contradiction and is not: **A2 §3.2 says 1.77× at 500 axles and D08 §5 says 2.01× on the same inputs.** A2 charges the pilot year in full and credits it with no benefit — the conservative frame appropriate to a rate card. D08 credits the 200-axle pilot year with the modest benefit it actually produces. Both documents now say which question they are answering, which is the fix that mattered."));

doc.push(H2("2. Finding 2 — D08's modelled benefits exceeded what A1 produces (CLOSED 2026-11-10)"));
doc.push(P("D08 §5 said a 500-axle customer sees $6–8M of avoided damage in the pilot year and $14–20M over four years; §6 said $40–60M over six years with a 20×–30× return. A1 at 500 axles with its default assumptions produces $696,675 net annual benefit. The ratio was between 5× and 14× across the three periods."));
doc.push(PB("The cause was a modelling fork, not an arithmetic error. Two different figures for the probability that a missed defect escalates to a catastrophic event existed in the repository — and the table below is written in the past tense deliberately, because **the fork itself is now gone**:"));
doc.push(table(
  ["Location", "Then", "Now"],
  [
    ["backend/roi.py — P_CATASTROPHIC_GIVEN_MISSED_DEFECT", "2% → $29,065,000", "0.05% → $999,750, identical to A1's B22"],
    ["A1 workbook, sheet 1 cell B17", "0.05% → $999,750 typical / $9,745,375 on the $9.25M severe base", "unchanged — this was already the governing figure"],
  ],
  { width: [3.4, 3.1, 3.1], size: 16 },
));
doc.push(PB("The two probabilities differed by a factor of 40. The A1 note explains why it holds 0.05%: \"Even 2% per missed defect would imply dozens of billion-dollar events annually nationwide — physically impossible. 0.05% keeps the implied nationwide rate roughly consistent with observed East Palestine-scale frequency.\" A1 was right and `roi.py` was wrong by 29×."));
doc.push(P("D08's benefit figures were reproducible if a prevented defect was valued at the contained-tier midpoint of $9.25M and nothing else: 0.65 × $9.25M ≈ $6.0M and 0.86 × $9.25M ≈ $8.0M, which is exactly the old $6–8M pilot-year band at 0.7 defects missed. D08 was built on the contained-tier value without the probability blend; A1 applies the blend, a factor of roughly 9.25."));
doc.push(PB("**How it closed.** D08 §5–§6 were restated from A1 rather than the reverse — the decision was that A1 governs — and the restatement surfaced something the old headline hid. D08 §2 scopes the pilot at **100–200 axles**, and at 200 axles A1's modelled benefit is $278,670 against a $370,000 fee: **0.75×. The pilot does not pay for itself at its own scoped fleet size, and the document now says so in those words** rather than quoting a pilot-year millions figure that assumed 500 axles. Production years at 500 axles model $696,675/yr. Four-year return **2.01×**; six-year **2.06×** — close to flat, because fee escalation from Year 4 nearly cancels the dilution of one weak pilot year across more production years. It does not fall, which is the opposite of what I first assumed and asserted; the check caught it."));
doc.push(callout(
  "What this finding was actually about",
  "Not arithmetic — every individual computation on both sides was correct. It was two documents quietly using different models for the same words. D08 §5 already stated that A1 is the instrument of record and that the document must never be used to present these figures; the document then presented different ones. That is the failure mode this project keeps meeting: internally consistent, externally wrong. The correction that matters is not the new number, it is that the basis is now written beside every figure, so the next reader can tell which question is being answered.",
  { fill: "EAF3EA", labelColor: "2E6B32" },
));

doc.push(H2("3. D07 §14.5 — governing law, seat and forum"));
doc.push(P("An open counsel decision, correctly labelled as open. The section now says what must be decided, who decides and by when, that Texas is an expectation rather than a term, and what happens if an Order is executed while it is open. It must still be closed by signed addendum before first execution. Q6 is explicit that this is not a formation question and that entity choice does not answer it."));

doc.push(H2("4. The unbuilt code controls"));
doc.push(PB("D00 Part VI is the authority on these, and it refuses to let them migrate to \"closed\" on the strength of a document. **Chat-6 closed the session-bound entry gap** and added the two rows below that closing it revealed. The largest was the absent detector ingest path. **As of chat-5 an endpoint exists and validates**, which narrows it without closing it: the schema is a demonstration schema, the endpoint has no authentication, and no accepted reading is scored, so every demonstration number still demonstrates the method rather than the Railroad's data. Of the others, the ledger closed in chat-3 (append-only, hash-chained, signed), chat-5 built the reviewer registry and per-disposition attribution, and chat-6 gated entry on an authenticated session — which retires \"attribution is an AD-2 dependency\" and \"entry is not gated\" together, and leaves the export-key identity, key custody and the key directory open. The three supply-chain tools were built in chat-5 and **none is applied**, which is a gap with a tool beside it rather than a closed item."));
doc.push(table(
  ["Gap", "Disclosed in", "Consequence while open"],
  [
    ["No Railroad payload has ever been ingested", "B01 §7 #5 · B02 §2 · B03 status", "The endpoint exists and validates (chat-5), but the schema is a demonstration schema and nothing accepted is scored. Every demonstration number demonstrates the method, not the customer's data. Still the largest gap in the docket."],
    ["Key custody and joiner/mover/leaver", "B01 §7 #1 · D09 §4.4 · F08 Part 1", "**Entry closed in chat-6**: a disposition requires a live session token, identity comes from the session and not the body, and a certificate revoked mid-session stops writing. What remains is the human half — who holds which credential, and its withdrawal on a mover or leaver — plus a signed key directory. Software can authenticate a credential; it cannot authenticate a person."],
    ["Export signature cannot name the export signer", "B01 §4.5a · B01 §7 #11 · D09 §4.4", "Attribution is per-disposition and closed (chat-5), but the *export* HMAC is still symmetric and unnamed: the bundle cannot say who exported it. Needs AD-2 account binding plus a key per export."],
    ["A key holder can attest as the key holder, not as a person", "B01 §4.5a · D09 §4.5.5", "The attestation proves a registered key was used. Binding it to a person is credential issuance and custody. A recipient given no reviewer key cannot tell an honest attestation from a fabricated one."],
    ["No reviewer key directory", "D09 §4.5.5", "A recipient must be told out of band which key belongs to which reviewer — today that is a name typed on the command line. Attribution is only as strong as the directory."],
    ["Ledger cannot date itself; a wipe before the first bundle is invisible", "B01 §4.5a · D09 §4.4–4.5", "No timestamping authority and no pre-series anchor. Bundle retention plus a written key-custody procedure are the controls that carry that weight."],
    ["Nothing carries the replicated series off-box", "B01 §7 #12 · D09 §4.4–4.5 · D09 §3.2", "The Platform produces the D09 §4.5.4 cadence itself and verifies it (chat-4). Carriage stays open **by design**: D09 §3.2 promises no outbound network, so moving the series to backup media is the Railroad's physical step under §3.3. A lost disk before carriage loses everything since the last copy."],
    ["Supply chain: three tools built, none applied", "D09 §4.4 · §7.2 · §7.3", "SBOM generation, hash pinning and GPG-signed releases all have tooling as of chat-5 and **none of it runs in a release**. A disclosed gap with a tool beside it is still a gap. Target Q1–Q2 2027."],
    ["Entry requires a session, not an attestation", "B01 §7 #1 · D09 §4.4", "A signed-in reviewer can record a decision without attesting it. That is deliberate — the server does not hold an attestation key and must not — but it means an unattested row is honest rather than impossible, and the manifest counts it."],
    ["No unauthenticated-reachability control on ingest", "B01 §7 #5 · B02 §2", "`POST /api/ingest` has no authentication. **An unauthenticated ingest route is a data-poisoning route**, which is why it belongs on a trusted segment until AD-2 lands."],
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
  "project-logs/chat-4/CARRY-FORWARD.md — where chat-4 actually stopped and what it left waiting.",
  "project-logs/chat-4/SUMMARY.md — the reasoning behind each phase of chat-4.",
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
    ["python3 -I assets/a2-d08-arithmetic-pass.py", "Whether the A2/D08 figures still hold. Currently 97 checks, all passing; Findings 1 and 2 are checked as closed"],
    ["python3 -I assets/a2-d08-model-decision.py", "The decision paper's 65 figures. Exits non-zero on any mismatch"],
    ["python3 -I tests/run_tests.py", "The full suite: physics, ledger, export and replication. Currently 114 passed, 0 failed"],
    ["python3 tools/verify_ledger_export.py --bundle B --key-file K", "Checks an exported ledger bundle without the application or the database"],
  ],
  { width: [4.6, 5.4], size: 16, mono: [0] },
));
doc.push(callout(
  "The line-ending trap",
  "git status in this repository lists nearly every tracked file as modified on a fresh Windows checkout. It is CRLF working-tree content against LF blobs, not a content change: git diff --ignore-cr-at-eol returns empty. There is no .gitattributes and core.autocrlf is unset. Always check with --ignore-cr-at-eol before believing a diff stat, stage only the files actually changed, and never git add -A. During chat-3 an editor round-trip converted the A1 builder to CRLF and turned a two-line fix into 1,248 changed lines; that commit had to be reset and recommitted so it showed 420 insertions and 2 deletions.",
));

doc.push(H2("Push"));
doc.push(P("The command environment cannot reach GitHub — git push and fetch fail with HTTP 403 from the proxy. Commits land locally in C:\\Users\\RGV\\AxiomDynamics and the owner pushes with PUSH-TO-GITHUB.bat. At the moment this revision was written the local ref for origin/main stood at bb99cdd, and the first commit after it was 893096e. The number of commits ahead is not written here on purpose: this document's own commit changes it, which is exactly why the instruction is to run the command rather than read a figure. Confirm with git log --oneline origin/main..HEAD rather than with this sentence, because a local remote-tracking ref is not evidence of what the remote holds."));

doc.push(H2("The decisions waiting, in order of consequence"));
doc.push(PB("Three of the five items this list carried in chat-3 closed on 2026-11-10. Recorded here so the next reader does not reopen them: the **model question was decided in favour of A1** (Option D in the decision paper), the **2.0×/4.1× anchors were restated** at 1.77×/3.36× with the basis in the text and the 1.65×/3.34× fallback stated, and **the A1 workbook was rebuilt** from the corrected builder and, once Excel released its lock, **installed** — the docket `.xlsx` now charges the $370,000 pilot year and returns 2.0653×, agreeing with A2 §5.1, and the intermediate `REPLACE-WORKBOOK.bat` pair was deleted. Chat-5 then built the reviewer registry and per-disposition attribution, which retires the attribution item as an AD-2 *dependency* and replaces it with the sharper question of account binding. What remains:"));
doc.push(...numbered("numE", [
  "D07 §14.5 — approve a governing law, seat and mediation provider with counsel, and record it in a signed addendum. Blocks first execution. Not a formation question, and entity choice does not answer it.",
  "Session-bound disposition entry — bind local accounts to registry entries and require an authenticated session to record a disposition. This is now the blocking half of B01 §7 item 1, and it is a larger job than attribution was.",
  "Phase 0 formation, if a real customer conversation is closer than a code milestone. Texas LLC, $300 filing, operating agreement worth paying for.",
]));

// ================================================================ APPENDIX
doc.push(H1("Appendix A — Repository map"));

doc.push(table(
  ["Path", "Contents", "Class"],
  [
    ["backend/", "physics.py (models 1–5), simulate.py (synthetic fleet), warrants.py (fusion and hashing), roi.py (model 6, the ROI panel), store.py (append-only SQLite ledger), ledger_export.py (signed export), main.py (stdlib HTTP server and routes)", "Code"],
    ["tools/", "verify_ledger_export.py — standalone export verifier, imports nothing from backend/", "Code"],
    ["frontend/", "index.html, style.css, app.js — vanilla JS canvas dashboard, zero dependencies", "Code"],
    ["tests/", "test_physics.py (physics formulas plus the A1 constants guard), test_store.py (ledger), test_export.py (signed export), test_ledger_replication.py (cadence, chaining, inspection), run_tests.py (stdlib runner, discovers test_*.py) — 114 tests", "Code"],
    ["client-assets/MASTER-BRIEF-DOCKET/", "The 38-artifact docket: A1–A2, B01–B05, C01–C02, D00–D14, F00–F13 (36 Markdown + xlsx + html)", "Client-facing"],
    ["assets/", "Q6 entity analysis, IP strategy, library reconciliation, carrier dossiers, cost model, arithmetic pass, model decision paper, export and replication build records, each with its check script", "Internal — never forwardable"],
    ["project-logs/", "CURRENT-STATE, README, chat-1/2/3/4 summaries and carry-forwards, transcripts with raw jsonl, extract_transcript.py, build-history-summary.js", "Internal"],
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
    ["11-09 22:18", "a3ba43f", "7", "Build history and working summary (29 pp) plus generator"],
    ["11-09 22:19", "b3dcda4", "7", "CURRENT-STATE: document, push state, artifact counts"],
    ["11-09 22:19", "8716b6c", "7", "chat-3 summary: record the build history document"],
    ["11-09 22:20", "bd2e67b", "7", "project-logs README: list the build history document"],
    ["11-09 22:35", "209efe6", "7", "Rebuild disposition ledger as append-only (AD-3)"],
    ["11-09 22:37", "07f567c", "7", "chat-3 log: record the append-only ledger phase"],
    ["11-09 22:38", "57f7c23", "7", "CURRENT-STATE: date the ledger phase"],
    ["11-09 23:08", "b23d0c7", "7", "Cost the A2/D08 model decision so it can be made"],
    ["11-09 23:09", "44e2cac", "7", "CURRENT-STATE: point open item 1 at the decision paper"],
    ["11-09 23:09", "bb99cdd", "7", "chat-3 log: record the decision phase and its audit"],
    ["11-09 23:16", "893096e", "7", "chat-3 transcript: extract and commit, raw log included"],
    ["11-10 06:52", "d9c83d4", "7", "Signed, verifiable ledger export (AD-3 part two)"],
    ["11-10 06:58", "53ad93a", "7", "Transcript: snapshot chat-3 at close, raw log included"],
    ["11-10 09:30", "5ce18cd", "8", "Ledger replication series: scheduled cadence, chained bundles, inspection"],
    ["11-10 09:30", "7116f64", "8", "chat-4 carry-forward: record the replication phase and de-stale the push section"],
    ["11-10 10:10", "58bfaef", "8", "Restate A2/D08 and roi.py on A1; fix the ROI test that could not fail"],
    ["11-10 10:11", "827261f", "8", "chat-4 carry-forward: record the model decision and the one unfinished workbook step"],
  ],
  { width: [1.5, 1.3, 0.8, 6.4], size: 14, mono: [1] },
));
doc.push(P("Stage 6 is the rebuild-and-process stage: it recovered the lost chat-1 work, installed the write-in-repo rule, and built the transcript-preservation machinery that makes this document possible. Stage 7 is chat-3, and it is the stage that changed the most after it was written — two of its four phases were materially repaired because an independent audit found what the author had not. Stage 8 is chat-4, which ran two phases: the replication series, and the model decision that closed both findings Part VII had carried since chat-3. Its most transferable lesson is in §8.3 — a numeric defect valued a missed defect 29× too high, and the test guarding it could not fail. Stage 9 is chat-5: the ledger audit, the ingest path, three supply-chain tools built but not applied, and per-disposition attribution, where an audit found a relabelling attack a green suite had been built to catch and did not. Stage 10 is chat-6, and it is the shortest demonstration of the pattern: a revocation guard written to close a race, called by a route that passed it a boolean, and tested only with a guard that raised — so the guard was inert and 310 tests were green.", { spaceBefore: 120 }));

doc.push(H2("Current status at a glance"));
doc.push(table(
  ["Area", "State", "Note"],
  [
    ["Physics engine and tests", "Complete, 114/114 passing", "Physics formula tests, ledger, signed export, replication; deterministic, no learned parameters"],
    ["Demonstration application", "Runs", "Synthetic data only"],
    ["Client docket", "38 artifacts built, 0 outstanding in the index", "Not yet counsel-reviewed"],
    ["Detector ingest", "Validator built 2026-11-11", "Three gates, named refusals. Demonstration schema, no authentication, nothing accepted is scored — the largest gap, narrowed and not closed"],
    ["Append-only ledger", "Built 2026-11-09", "Insert-only, triggers, SHA-256 chain"],
    ["Signed ledger export", "Built 2026-11-10, hardened / audited 2026-11-11", "HMAC-SHA256 bundle, standalone verifier, chaining, and a body that must be exactly the signed parts. Symmetric: cannot name the export signer or date itself"],
    ["Ledger replication series", "Built 2026-11-10", "Monthly full + weekly incremental, chained, inspection reports gaps. Carries nothing off the box by design (D09 §3.2)"],
    ["Off-box carriage", "By design the Railroad's step", "The Platform produces and verifies the series; physically moving it to backup media is the customer's action under D09 §3.3"],
    ["Reviewer registry and attribution", "Built 2026-11-11", "Hash-chained (not signed) append-only registry, per-reviewer HMAC keys, attestations carried inside exported records and checked by both verifiers. Entry is not yet gated on it"],
    ["Session-bound disposition entry", "Not built", "The blocking half of B01 §7 item 1: bind accounts to registry entries and require an authenticated session to record a disposition"],
    ["SBOM, hash pinning, signed releases", "Built 2026-11-11, none applied", "Three tools exist; none runs in a release. Q1–Q2 2027 targets; disclosed"],
    ["Company formation", "Not done", "Texas LLC recommended, $300 filing"],
    ["Commercial numbers", "Decided 2026-11-10 — A1 governs", "A2 §3.2 / D08 §3 restate at 1.77×–3.36×; D08 §5–§6 restated from A1. Findings 1 and 2 closed"],
    ["A1 workbook", "Rebuilt and installed 2026-11-10", "$370,000 pilot year, 2.0653x three-year ROI, agreeing with A2 §5.1"],
    ["D07 §14.5 venue", "Open counsel decision", "Blocks first execution"],
    ["Push state", "Commits ahead of the local remote ref", "Not counted here — the count changes with every commit. Verify with git log origin/main..HEAD; the command environment cannot reach GitHub"],
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
  description: "Stage-by-stage account of the AxiomDynamics build, 2026-11-08 to 2026-11-10.",
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
