"""
Builds the AxiomDynamics customer-facing ROI calculator.

Design intent: the railroad's procurement and safety teams type THEIR numbers
into yellow cells. Everything else is a formula. Two rules hold throughout:

  1. Every hardcoded number is either a public, citable figure (NTSB/DOJ/AP
     derailment costs) or an explicitly-labeled modeling assumption. The
     Assumptions sheet carries the source note in the cell beside each one.
  2. No formula is pre-computed in Python. Every derived cell is a live
     formula so the workbook recalculates when an input changes.

Run:  python3 build_roi_calculator.py
Then: python3 <skill>/scripts/recalc.py output.xlsx
"""

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.comments import Comment

# ---------------------------------------------------------------- palette ---
NAVY = "0A1628"
TEAL = "0EA5E9"
LIGHT = "F8FAFC"
BAND = "F1F5F9"
INPUT_FILL = PatternFill("solid", fgColor="FFF2CC")   # yellow = type here
HEAD_FILL = PatternFill("solid", fgColor="0A1628")
SUBHEAD_FILL = PatternFill("solid", fgColor="E2E8F0")
TOTAL_FILL = PatternFill("solid", fgColor="DCFCE7")
WARN_FILL = PatternFill("solid", fgColor="FEE2E2")

BLUE_INPUT = Font(name="Arial", size=10, color="0000FF")      # hardcoded input
BLACK_CALC = Font(name="Arial", size=10, color="000000")      # formula
GREEN_LINK = Font(name="Arial", size=10, color="008000")      # cross-sheet link
WHITE_BOLD = Font(name="Arial", size=10, bold=True, color="FFFFFF")
BOLD = Font(name="Arial", size=10, bold=True, color="000000")
TITLE_FONT = Font(name="Arial", size=16, bold=True, color="0A1628")
NOTE_FONT = Font(name="Arial", size=9, italic=True, color="475569")

MONEY = '"$"#,##0;("$"#,##0);"-"'
MONEY_MM = '"$"#,##0.0,,"M";("$"#,##0.0,,"M");"-"'
PCT = '0.0%'
NUM = '#,##0'
DEC = '#,##0.0'

thin = Side(style="thin", color="CBD5E1")
BOX = Border(left=thin, right=thin, top=thin, bottom=thin)

wb = Workbook()

# ============================================================ SHEET: INPUTS
ws = wb.active
ws.title = "1. Your Fleet"
ws.sheet_view.showGridLines = False

ws["A1"] = "AxiomDynamics — Customer ROI Calculator"
ws["A1"].font = TITLE_FONT
ws["A2"] = "Enter your numbers in the yellow cells only. Everything else calculates."
ws["A2"].font = NOTE_FONT
ws["A3"] = "Ring any yellow cell for a note on where that number comes from."
ws["A3"].font = Font(name="Arial", size=9, italic=True, color="94A3B8")

def header_row(sheet, row, labels, widths=None):
    for i, lab in enumerate(labels, start=1):
        c = sheet.cell(row=row, column=i, value=lab)
        c.font = WHITE_BOLD
        c.fill = HEAD_FILL
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = BOX
    sheet.row_dimensions[row].height = 30
    if widths:
        for i, w in enumerate(widths, start=1):
            sheet.column_dimensions[get_column_letter(i)].width = w

def input_cell(sheet, ref, value, note=None, fmt=None):
    c = sheet[ref]
    c.value = value
    c.font = BLUE_INPUT
    c.fill = INPUT_FILL
    c.border = BOX
    c.alignment = Alignment(horizontal="right")
    if fmt:
        c.number_format = fmt
    if note:
        c.comment = Comment(note, "AxiomDynamics")
    return c

def calc_cell(sheet, ref, formula, fmt=None, bold=False):
    c = sheet[ref]
    c.value = formula
    c.font = BOLD if bold else BLACK_CALC
    c.border = BOX
    c.alignment = Alignment(horizontal="right")
    if fmt:
        c.number_format = fmt
    return c

# --- Section A: fleet size ---
ws["A5"] = "A.  FLEET SIZE"
ws["A5"].font = Font(name="Arial", size=11, bold=True, color="0A1628")

header_row(ws, 6, ["Input", "Value", "Unit", "What it means"],
           widths=[46, 16, 14, 62])

rows_a = [
    ("Freight car axles to be monitored", "B7", 500, NUM,
     "Count of axle-end bearings you want the platform watching. A 110-car train has 440 axles; a single yard's active fleet is typically several thousand.",
     "axles"),
    ("Average train speed through monitored territory", "B8", 45, NUM,
     "Used to convert detection lead time into distance-ahead-of-failure. Class I mainline averages run 40-50 mph.",
     "mph"),
]

r = 7
for label, ref, val, fmt, note, unit in rows_a:
    ws.cell(row=r, column=1, value=label).font = BLACK_CALC
    ws.cell(row=r, column=1).border = BOX
    input_cell(ws, ref, val, note, fmt)
    ws.cell(row=r, column=3, value=unit).font = NOTE_FONT
    ws.cell(row=r, column=3).border = BOX
    ws.cell(row=r, column=4, value=note[:20] + "..." if len(note) > 20 else note).font = NOTE_FONT
    ws.cell(row=r, column=4).alignment = Alignment(wrap_text=True, vertical="center")
    ws.cell(row=r, column=4).border = BOX
    r += 1

# --- Section B: current exposure ---
ws["A10"] = "B.  YOUR CURRENT EXPOSURE"
ws["A10"].font = Font(name="Arial", size=11, bold=True, color="0A1628")

header_row(ws, 11, ["Input", "Value", "Unit", "Where this number comes from"],
           widths=[46, 16, 14, 62])

rows_b = [
    ("Bearing-related derailments in the last 5 years", "B12", 3, NUM,
     "Pull from your own incident log. If you do not track this separately, use FRA accident data filtered to cause code for bearing/journal failure.",
     "events"),
    ("Typical direct cost per bearing derailment", "B13", 500000, MONEY,
     "TYPICAL CASE. Industry working figure for a low-speed contained bearing set-out: track repair, equipment damage, service disruption. Most bearing derailments are this, not the headline cases. Replace with your own claims average.",
     "USD"),
    ("SEVERE case bench — NTSB low (reference only)", "B14", 5000000, MONEY,
     "SOURCED, SEVERE-CASE ONLY: NTSB report RAB1712 documents a BNSF bearing-caused derailment at $5,000,000. This is an investigated, above-average event — do NOT use it as your typical cost. It is here as a sensitivity datum.",
     "USD"),
    ("SEVERE case bench — NTSB high (reference only)", "B15", 13500000, MONEY,
     "SOURCED, SEVERE-CASE ONLY: NTSB docket records a BNSF derailment at $13,500,000, excluding lading and environmental remediation. Again above-average and investigated. Reference datum, not a default.",
     "USD"),
    ("Probability a missed defect escalates to catastrophic", "B16", 0.0005, '0.00%',
     "MODELING ASSUMPTION, NOT A CITATION. No published base rate exists. NOTE: even 2% per missed defect would imply dozens of billion-dollar events annually nationwide — physically impossible. 0.05% keeps the nationwide rate roughly consistent with observed East Palestine-scale frequency. Adjust deliberately and re-read the result.",
     "%"),
    ("Catastrophic event cost (hazmat release)", "B17", 1000000000, MONEY,
     "SOURCED: East Palestine, OH (Feb 2023, Norfolk Southern, same wheel-bearing failure mode). DOJ/EPA settlement exceeded $310M, personal-injury class settlement $600M, cumulative reported cost passed $1B by mid-2024.",
     "USD"),
]

r = 12
for label, ref, val, fmt, note, unit in rows_b:
    c = ws.cell(row=r, column=1, value=label)
    c.font = BLACK_CALC
    c.alignment = Alignment(wrap_text=True, vertical="center")
    c.border = BOX
    input_cell(ws, ref, val, note, fmt)
    ws.cell(row=r, column=3, value=unit).font = NOTE_FONT
    ws.cell(row=r, column=3).border = BOX
    d = ws.cell(row=r, column=4, value="Ring the yellow cell for the source.")
    d.font = NOTE_FONT
    d.alignment = Alignment(wrap_text=True, vertical="center")
    d.border = BOX
    ws.row_dimensions[r].height = 34
    r += 1

# --- derived: blended expected cost ---
ws["A19"] = "C.  DERIVED — EXPECTED COST PER MISSED DEFECT"
ws["A19"].font = Font(name="Arial", size=11, bold=True, color="0A1628")

header_row(ws, 20, ["Derived metric", "Value", "Unit", "Formula"],
           widths=[46, 16, 14, 62])

ws.cell(row=21, column=1, value="Blended expected cost per missed defect").font = BOLD
ws.cell(row=21, column=1).fill = TOTAL_FILL
ws.cell(row=21, column=1).border = BOX
calc_cell(ws, "B21", "=(1-B16)*B13+B16*B17", MONEY, bold=True)
ws.cell(row=21, column=2).fill = TOTAL_FILL
ws.cell(row=21, column=3, value="USD").font = NOTE_FONT
ws.cell(row=21, column=3).border = BOX
ws.cell(row=21, column=4, value="(1 - p_catastrophic) x typical_cost + p_catastrophic x catastrophic_cost").font = NOTE_FONT
ws.cell(row=21, column=4).alignment = Alignment(wrap_text=True, vertical="center")
ws.cell(row=21, column=4).border = BOX
ws.row_dimensions[21].height = 30

ws.cell(row=23, column=1,
        value="Every cell above right of column B is a live formula. Change a yellow cell and this recalculates.").font = NOTE_FONT
ws.cell(row=24, column=1,
        value="Sensitivity check: set B13 to the NTSB severe-case figure (B14) and the model moves to the headline number — useful for a worst-case slide, misleading as a base case.").font = Font(name="Arial", size=9, italic=True, color="B91C1C")
ws.cell(row=24, column=1).alignment = Alignment(wrap_text=True)

# ======================================================== SHEET: DETECTION
d = wb.create_sheet("2. Detection")
d.sheet_view.showGridLines = False

d["A1"] = "Detection Performance — Legacy vs. AxiomDynamics"
d["A1"].font = TITLE_FONT
d["A2"] = "Lead time converts directly into train miles of early warning."
d["A2"].font = NOTE_FONT

header_row(d, 4, ["Metric", "Legacy Detector Network", "AxiomDynamics", "Unit", "Source / basis"],
           widths=[40, 22, 22, 12, 58])

def row(sheet, r, label, legacy, axiom, unit, basis, legacy_is_formula=False, axiom_is_formula=False,
        legacy_fmt=None, axiom_fmt=None):
    c = sheet.cell(row=r, column=1, value=label)
    c.font = BLACK_CALC
    c.alignment = Alignment(wrap_text=True, vertical="center")
    c.border = BOX
    for col, val, isf, fmt in ((2, legacy, legacy_is_formula, legacy_fmt),
                               (3, axiom, axiom_is_formula, axiom_fmt)):
        cc = sheet.cell(row=r, column=col)
        cc.value = val
        cc.font = BLACK_CALC if isf else BLUE_INPUT
        if not isf:
            cc.fill = INPUT_FILL
        cc.border = BOX
        cc.alignment = Alignment(horizontal="center", vertical="center")
        if fmt:
            cc.number_format = fmt
    u = sheet.cell(row=r, column=4, value=unit)
    u.font = NOTE_FONT
    u.border = BOX
    b = sheet.cell(row=r, column=5, value=basis)
    b.font = NOTE_FONT
    b.alignment = Alignment(wrap_text=True, vertical="center")
    b.border = BOX
    sheet.row_dimensions[r].height = 30

row(d, 5, "Mean time from defect onset to alarm", 4.8, 1.5, "hours",
    "MODELING ASSUMPTION. 4.8 h is the illustrative legacy figure used in the platform's ROI module; 1.5 h is a more defensible AxiomDynamics alarm latency than the 0.57 h the ROI module cites. Replace both with your own detector logs before quoting.", legacy_fmt=DEC, axiom_fmt=DEC)

row(d, 6, "False-positive rate (signals that would stop a train)", 0.035, 0.001, "of detections",
    "MODELING ASSUMPTION. Legacy 3.5% reflects reported hot-bearing-detector stop rates. AxiomDynamics figure reflects the two-signal corroboration gate in backend/warrants.py plus human reviewer disposition.", legacy_fmt=PCT, axiom_fmt=PCT)

row(d, 7, "Defects caught per 500 axles per year", 1.4, 2.1, "defects",
    "MODELING ASSUMPTION. Legacy counts only what its detector thresholds trip. AxiomDynamics adds rate-of-change and peer-outlier catches that never reach a fixed threshold — a 1.5x uplift is a deliberately modest claim, not the 2.3x an earlier draft used.", legacy_fmt=DEC, axiom_fmt=DEC)

# derived
d["A9"] = "DERIVED — EARLY-WARNING DISTANCE"
d["A9"].font = Font(name="Arial", size=11, bold=True, color="0A1628")

header_row(d, 10, ["Derived metric", "", "Value", "Unit", "Formula"], widths=[40, 22, 22, 12, 58])

d.cell(row=11, column=1, value="Speed of the monitored train").font = BLACK_CALC
d.cell(row=11, column=1).border = BOX
d.cell(row=11, column=2).border = BOX
d.cell(row=11, column=3, value="='1. Your Fleet'!B8").font = GREEN_LINK
d.cell(row=11, column=3).number_format = NUM
d.cell(row=11, column=3).border = BOX
d.cell(row=11, column=3).alignment = Alignment(horizontal="center")
d.cell(row=11, column=4, value="mph").font = NOTE_FONT
d.cell(row=11, column=4).border = BOX
d.cell(row=11, column=5, value="='1. Your Fleet'!B8").font = NOTE_FONT
d.cell(row=11, column=5).border = BOX

d.cell(row=12, column=1, value="Lead-time advantage over legacy").font = BLACK_CALC
d.cell(row=12, column=1).border = BOX
d.cell(row=12, column=2).border = BOX
d.cell(row=12, column=3, value="=B5-C5").font = BLACK_CALC
d.cell(row=12, column=3).number_format = DEC
d.cell(row=12, column=3).border = BOX
d.cell(row=12, column=3).alignment = Alignment(horizontal="center")
d.cell(row=12, column=4, value="hours").font = NOTE_FONT
d.cell(row=12, column=4).border = BOX
d.cell(row=12, column=5, value="legacy_hours - axiom_hours").font = NOTE_FONT
d.cell(row=12, column=5).border = BOX

d.cell(row=13, column=1, value="Additional track miles of early warning").font = BOLD
d.cell(row=13, column=1).fill = TOTAL_FILL
d.cell(row=13, column=1).border = BOX
d.cell(row=13, column=2).border = BOX
d.cell(row=13, column=3, value="=C12*C11").font = BOLD
d.cell(row=13, column=3).number_format = NUM
d.cell(row=13, column=3).fill = TOTAL_FILL
d.cell(row=13, column=3).border = BOX
d.cell(row=13, column=3).alignment = Alignment(horizontal="center")
d.cell(row=13, column=4, value="miles").font = NOTE_FONT
d.cell(row=13, column=4).border = BOX
d.cell(row=13, column=5, value="lead_time_advantage_hours x speed_mph").font = NOTE_FONT
d.cell(row=13, column=5).border = BOX

d["A15"] = ("Read this as: at your stated line speed, the earlier alarm arrives while the car is still "
            "this many track miles from failure — enough distance to plan a set-out at the next siding "
            "rather than react to a failure in the block.")
d["A15"].font = NOTE_FONT
d["A15"].alignment = Alignment(wrap_text=True, vertical="top")
d.merge_cells("A15:E17")

# ========================================================== SHEET: BENEFIT
b = wb.create_sheet("3. Benefit")
b.sheet_view.showGridLines = False

b["A1"] = "Annual Benefit — Three-Year View"
b["A1"].font = TITLE_FONT
b["A2"] = "All values pulled from sheets 1 and 2. No new inputs here."
b["A2"].font = NOTE_FONT

header_row(b, 4, ["Line", "Year 1", "Year 2", "Year 3", "Basis"],
           widths=[44, 18, 18, 18, 56])

b.cell(row=5, column=1, value="Axles monitored").font = BLACK_CALC
b.cell(row=5, column=1).border = BOX
for col in (2, 3, 4):
    c = b.cell(row=5, column=col, value="='1. Your Fleet'!B7")
    c.font = GREEN_LINK
    c.number_format = NUM
    c.border = BOX
    c.alignment = Alignment(horizontal="right")
b.cell(row=5, column=5, value="From sheet 1").font = NOTE_FONT
b.cell(row=5, column=5).border = BOX

b.cell(row=6, column=1, value="Defects detected (AxiomDynamics rate)").font = BLACK_CALC
b.cell(row=6, column=1).border = BOX
for col in (2, 3, 4):
    c = b.cell(row=6, column=col, value="=(B5/500)*'2. Detection'!C7")
    c.font = BLACK_CALC
    c.number_format = DEC
    c.border = BOX
    c.alignment = Alignment(horizontal="right")
b.cell(row=6, column=5, value="(axles / 500) x defects_per_500_axles").font = NOTE_FONT
b.cell(row=6, column=5).border = BOX

b.cell(row=7, column=1, value="Defects a legacy network would have missed").font = BLACK_CALC
b.cell(row=7, column=1).border = BOX
for col in (2, 3, 4):
    c = b.cell(row=7, column=col, value="=(B5/500)*MAX(0,'2. Detection'!C7-'2. Detection'!B7)")
    c.font = BLACK_CALC
    c.number_format = DEC
    c.border = BOX
    c.alignment = Alignment(horizontal="right")
b.cell(row=7, column=5, value="(axles/500) x max(0, axiom_catch - legacy_catch)").font = NOTE_FONT
b.cell(row=7, column=5).border = BOX

b.cell(row=8, column=1, value="Expected cost per missed defect").font = BLACK_CALC
b.cell(row=8, column=1).border = BOX
for col in (2, 3, 4):
    c = b.cell(row=8, column=col, value="='1. Your Fleet'!B21")
    c.font = GREEN_LINK
    c.number_format = MONEY
    c.border = BOX
    c.alignment = Alignment(horizontal="right")
b.cell(row=8, column=5, value="From sheet 1, section C").font = NOTE_FONT
b.cell(row=8, column=5).border = BOX

b.cell(row=9, column=1, value="Prevented failure cost").font = BOLD
b.cell(row=9, column=1).fill = TOTAL_FILL
b.cell(row=9, column=1).border = BOX
for col in (2, 3, 4):
    c = b.cell(row=9, column=col, value=f"={get_column_letter(col)}7*{get_column_letter(col)}8")
    c.font = BOLD
    c.number_format = MONEY
    c.fill = TOTAL_FILL
    c.border = BOX
    c.alignment = Alignment(horizontal="right")
b.cell(row=9, column=5, value="missed_defects x expected_cost_per_defect").font = NOTE_FONT
b.cell(row=9, column=5).border = BOX

b.cell(row=10, column=1, value="False-alarm / disruption cost").font = BLACK_CALC
b.cell(row=10, column=1).border = BOX
for col in (2, 3, 4):
    c = b.cell(row=10, column=col, value=f"={get_column_letter(col)}6*1500")
    c.font = BLACK_CALC
    c.number_format = MONEY
    c.border = BOX
    c.alignment = Alignment(horizontal="right")
b.cell(row=10, column=5, value="detected x $1,500 per unnecessary inspection (modeling assumption)").font = NOTE_FONT
b.cell(row=10, column=5).border = BOX
b.cell(row=10, column=5).alignment = Alignment(wrap_text=True, vertical="center")

b.cell(row=11, column=1, value="Net annual benefit").font = BOLD
b.cell(row=11, column=1).fill = TOTAL_FILL
b.cell(row=11, column=1).border = BOX
for col in (2, 3, 4):
    c = b.cell(row=11, column=col, value=f"={get_column_letter(col)}9-{get_column_letter(col)}10")
    c.font = BOLD
    c.number_format = MONEY
    c.fill = TOTAL_FILL
    c.border = BOX
    c.alignment = Alignment(horizontal="right")
b.cell(row=11, column=5, value="prevented cost - false alarm cost").font = NOTE_FONT
b.cell(row=11, column=5).border = BOX

# ============================================================ SHEET: COST
ct = wb.create_sheet("4. Licensing Cost")
ct.sheet_view.showGridLines = False

ct["A1"] = "AxiomDynamics Licensing Cost"
ct["A2"] = "Tier is selected automatically from monitored axle count. Pricing is a hypothesis, not a published rate card."
ct["A2"].font = NOTE_FONT

header_row(ct, 4, ["Item", "Year 1 (Pilot)", "Year 2", "Year 3", "Notes"],
           widths=[44, 18, 18, 18, 56])

ct.cell(row=5, column=1, value="Axles monitored").font = BLACK_CALC
ct.cell(row=5, column=1).border = BOX
for col in (2, 3, 4):
    c = ct.cell(row=5, column=col, value="='1. Your Fleet'!B7")
    c.font = GREEN_LINK
    c.number_format = NUM
    c.border = BOX
ct.cell(row=5, column=5, value="From sheet 1").font = NOTE_FONT
ct.cell(row=5, column=5).border = BOX

ct.cell(row=6, column=1, value="Applicable tier").font = BLACK_CALC
ct.cell(row=6, column=1).border = BOX
for col in (2, 3, 4):
    L = get_column_letter(col)
    c = ct.cell(row=6, column=col,
                value=f'=IF({L}5<=500,"Tier 1 — Core",IF({L}5<=2000,"Tier 2 — Enterprise","Tier 3 — Network"))')
    c.font = BLACK_CALC
    c.border = BOX
    c.alignment = Alignment(horizontal="center")
ct.cell(row=6, column=5, value="<=500 axles: Tier 1 · <=2000: Tier 2 · above: Tier 3").font = NOTE_FONT
ct.cell(row=6, column=5).border = BOX

ct.cell(row=7, column=1, value="Annual base license").font = BLACK_CALC
ct.cell(row=7, column=1).border = BOX
ct.cell(row=8, column=1, value="One-time hardware integration").font = BLACK_CALC
ct.cell(row=8, column=1).border = BOX
ct.cell(row=9, column=1, value="Training & change management").font = BLACK_CALC
ct.cell(row=9, column=1).border = BOX
ct.cell(row=10, column=1, value="Support & monitoring").font = BLACK_CALC
ct.cell(row=10, column=1).border = BOX
ct.cell(row=11, column=1, value="Performance component (3% of prevented cost)").font = BLACK_CALC
ct.cell(row=11, column=1).border = BOX

for r_ in (7, 8, 9, 10, 11):
    for col in (2, 3, 4):
        ct.cell(row=r_, column=col).border = BOX
        ct.cell(row=r_, column=col).alignment = Alignment(horizontal="right")

# Year 1 pilot = fixed $370,000 package
ct.cell(row=7, column=2, value=180000).font = BLUE_INPUT
ct.cell(row=7, column=2).fill = INPUT_FILL
ct.cell(row=7, column=2).number_format = MONEY
ct.cell(row=8, column=2, value=65000).font = BLUE_INPUT
ct.cell(row=8, column=2).fill = INPUT_FILL
ct.cell(row=8, column=2).number_format = MONEY
ct.cell(row=9, column=2, value=40000).font = BLUE_INPUT
ct.cell(row=9, column=2).fill = INPUT_FILL
ct.cell(row=9, column=2).number_format = MONEY
ct.cell(row=10, column=2, value=50000).font = BLUE_INPUT
ct.cell(row=10, column=2).fill = INPUT_FILL
ct.cell(row=10, column=2).number_format = MONEY
ct.cell(row=11, column=2, value=0).font = BLUE_INPUT
ct.cell(row=11, column=2).fill = INPUT_FILL
ct.cell(row=11, column=2).number_format = MONEY

# Years 2-3 = tier-driven formulas
for col in (3, 4):
    L = get_column_letter(col)
    c = ct.cell(row=7, column=col,
                value=f'=IF({L}5<=500,450000,IF({L}5<=2000,950000,1800000))')
    c.font = BLACK_CALC
    c.number_format = MONEY
    ct.cell(row=8, column=col, value=0).number_format = MONEY
    ct.cell(row=8, column=col).font = BLACK_CALC
    ct.cell(row=9, column=col, value=0).number_format = MONEY
    ct.cell(row=9, column=col).font = BLACK_CALC
    c10 = ct.cell(row=10, column=col, value=f"={L}7*0.12")
    c10.font = BLACK_CALC
    c10.number_format = MONEY
    # Performance component: 3% of prevented cost, CAPPED at 33% of the base
    # license. Uncapped, 3% of gross prevented cost ($52M) would exceed the
    # base license several times over and make the deal unserious. The cap is
    # what the cost-structure document actually describes: ~$150K on a $450K
    # base.
    c11 = ct.cell(row=11, column=col, value=f"=MIN('3. Benefit'!{L}9*0.03,{L}7*0.33)")
    c11.font = BLACK_CALC
    c11.number_format = MONEY

ct.cell(row=7, column=5, value="$180,000 pilot-year license").font = NOTE_FONT
ct.cell(row=7, column=5).border = BOX
ct.cell(row=8, column=5, value="$65,000 edge server + detector harness").font = NOTE_FONT
ct.cell(row=8, column=5).border = BOX
ct.cell(row=9, column=5, value="$40,000 operator certification + workflow").font = NOTE_FONT
ct.cell(row=9, column=5).border = BOX
ct.cell(row=10, column=5, value="12% of annual base license (modeling assumption)").font = NOTE_FONT
ct.cell(row=10, column=5).border = BOX
ct.cell(row=11, column=5, value="3% of prevented failure cost — only when corroborated").font = NOTE_FONT
ct.cell(row=11, column=5).border = BOX
ct.cell(row=11, column=5).alignment = Alignment(wrap_text=True, vertical="center")

ct.cell(row=13, column=1, value="TOTAL ANNUAL COST").font = Font(name="Arial", size=11, bold=True, color="0A1628")
ct.cell(row=13, column=1).fill = TOTAL_FILL
ct.cell(row=13, column=1).border = BOX
for col in (2, 3, 4):
    L = get_column_letter(col)
    c = ct.cell(row=13, column=col, value=f"=SUM({L}7:{L}11)")
    c.font = Font(name="Arial", size=11, bold=True)
    c.number_format = MONEY
    c.fill = TOTAL_FILL
    c.border = BOX
    c.alignment = Alignment(horizontal="right")
ct.cell(row=13, column=5, value="SUM of the five lines above").font = NOTE_FONT
ct.cell(row=13, column=5).border = BOX

# ========================================================== SHEET: SUMMARY
s = wb.create_sheet("5. Summary")
s.sheet_view.showGridLines = False

s["A1"] = "Three-Year Business Case"
s["A1"].font = TITLE_FONT
s["A2"] = "The number that matters is at the bottom. Everything above it is auditable."
s["A2"].font = NOTE_FONT

header_row(s, 4, ["", "Year 1 (Pilot)", "Year 2", "Year 3", "Three-Year Total"],
           widths=[46, 20, 20, 20, 22])

def sumrow(label, formula_maker, fmt=MONEY, is_total=False):
    global srow
    c = s.cell(row=srow, column=1, value=label)
    c.font = BOLD if is_total else BLACK_CALC
    c.border = BOX
    if is_total:
        c.fill = TOTAL_FILL
    for col in (2, 3, 4):
        L = get_column_letter(col)
        cc = s.cell(row=srow, column=col, value=formula_maker(L))
        cc.font = BOLD if is_total else BLACK_CALC
        cc.number_format = fmt
        cc.border = BOX
        cc.alignment = Alignment(horizontal="right")
        if is_total:
            cc.fill = TOTAL_FILL
    # total column
    tc = s.cell(row=srow, column=5, value=f"=SUM(B{srow}:D{srow})")
    tc.font = BOLD if is_total else BLACK_CALC
    tc.number_format = fmt
    tc.border = BOX
    tc.alignment = Alignment(horizontal="right")
    if is_total:
        tc.fill = TOTAL_FILL
    srow += 1

srow = 5
sumrow("Prevented failure cost", lambda L: f"='3. Benefit'!{L}9")
sumrow("Less: false-alarm disruption", lambda L: f"=-'3. Benefit'!{L}10")
sumrow("Net benefit", lambda L: f"='3. Benefit'!{L}11", is_total=True)
# srow is now 8

srow = 9
sumrow("Total licensing & deployment cost", lambda L: f"='4. Licensing Cost'!{L}13")
# srow is now 10; net benefit total is E7, cost total is E9

c = s.cell(row=11, column=1, value="NET THREE-YEAR VALUE")
c.font = Font(name="Arial", size=12, bold=True, color="065F46")
c.fill = TOTAL_FILL
c.border = BOX
nc = s.cell(row=11, column=5, value="=E7-E9")
nc.font = Font(name="Arial", size=12, bold=True, color="065F46")
nc.number_format = MONEY
nc.fill = TOTAL_FILL
nc.border = BOX
nc.alignment = Alignment(horizontal="right")

c = s.cell(row=12, column=1, value="RETURN ON INVESTMENT")
c.font = Font(name="Arial", size=12, bold=True, color="065F46")
c.fill = TOTAL_FILL
c.border = BOX
rc = s.cell(row=12, column=5, value='=IF(E9=0,"n/a",E7/E9)')
rc.font = Font(name="Arial", size=12, bold=True, color="065F46")
rc.number_format = '0.0"x"'
rc.fill = TOTAL_FILL
rc.border = BOX
rc.alignment = Alignment(horizontal="right")

c = s.cell(row=13, column=1, value="PAYBACK ON YEAR-1 PILOT")
c.font = BOLD
c.border = BOX
pc = s.cell(row=13, column=5, value='=IF(B7=0,"n/a",B9/B7*12)')
pc.font = BOLD
pc.number_format = '0.0" months"'
pc.border = BOX
pc.alignment = Alignment(horizontal="right")

c = s.cell(row=14, column=1, value="Additional track miles of early warning")
c.font = BLACK_CALC
c.border = BOX
mc = s.cell(row=14, column=5, value="='2. Detection'!C13")
mc.font = BLACK_CALC
mc.number_format = NUM
mc.border = BOX
mc.alignment = Alignment(horizontal="right")

s["A16"] = ("Sensitivity: change the catastrophic-probability cell on sheet 1 (B15) and watch "
            "the expected cost per defect — and therefore the net value — move. At 0% the model "
            "counts only contained derailments; at 5% it leans heavily on the East Palestine figure.")
s["A16"].font = NOTE_FONT
s["A16"].alignment = Alignment(wrap_text=True, vertical="top")
s.merge_cells("A16:E18")

s["A20"] = "Verified vs. assumed"
s["A20"].font = Font(name="Arial", size=11, bold=True, color="0A1628")
s["A21"] = ("SOURCED: $5.0M and $13.5M contained derailment costs (NTSB RAB1712 and NTSB docket); "
            "$1.0B+ catastrophic tier (DOJ/EPA settlement $310M+, AP-reported $600M personal-injury "
            "settlement, cumulative cost past $1B).")
s["A21"].font = NOTE_FONT
s["A21"].alignment = Alignment(wrap_text=True, vertical="top")
s.merge_cells("A21:E22")
s["A23"] = ("ASSUMED — replace before quoting: the 2% catastrophic escalation rate, the 4.8-hour legacy "
            "and 0.57-hour AxiomDynamics detection times, defects caught per 500 axles, the 3.5% and 0.1% "
            "false-positive rates, the $1,500 per-false-alarm cost, and every dollar figure on the "
            "Licensing Cost sheet.")
s["A23"].font = Font(name="Arial", size=9, color="B91C1C")
s["A23"].alignment = Alignment(wrap_text=True, vertical="top")
s.merge_cells("A23:E25")

# freeze panes on data sheets
for sheet, cell in ((ws, "A7"), (d, "A5"), (b, "A5"), (ct, "A5"), (s, "A5")):
    sheet.freeze_panes = cell

wb.save("/sessions/ecstatic-gifted-bell/mnt/outputs/axiomdynamics-app/client-assets/02-roi-calculator/AxiomDynamics-ROI-Calculator.xlsx")
print("written")
