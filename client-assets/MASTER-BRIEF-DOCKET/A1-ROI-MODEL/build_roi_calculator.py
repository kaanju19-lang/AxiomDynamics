"""
Builds the AxiomDynamics customer-facing ROI calculator.

Two pricing axes, deliberately separate:

  AXLE VOLUME  -- drives the annual license. Value scales with assets monitored.
  SITE COUNT   -- drives the platform fee. Cost scales with geography, not axles.
                  One yard and a 13-division network with the same axle count are
                  very different things to deploy and support.

Rules that hold throughout:
  1. Every hardcoded number is either a public, citable figure (NTSB/DOJ/AP) or an
     explicitly-labeled modeling assumption, with the note in the cell beside it.
  2. No derived value is pre-computed in Python. Every one is a live formula.

Run:  python3 build_roi_calculator.py
Then: python3 <skill>/scripts/recalc.py AxiomDynamics-ROI-Calculator.xlsx
"""

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.comments import Comment

NAVY = "0A1628"
INPUT_FILL = PatternFill("solid", fgColor="FFF2CC")
HEAD_FILL = PatternFill("solid", fgColor="0A1628")
TOTAL_FILL = PatternFill("solid", fgColor="DCFCE7")

BLUE_INPUT = Font(name="Arial", size=10, color="0000FF")
BLACK_CALC = Font(name="Arial", size=10, color="000000")
GREEN_LINK = Font(name="Arial", size=10, color="008000")
WHITE_BOLD = Font(name="Arial", size=10, bold=True, color="FFFFFF")
BOLD = Font(name="Arial", size=10, bold=True, color="000000")
TITLE_FONT = Font(name="Arial", size=16, bold=True, color="0A1628")
NOTE_FONT = Font(name="Arial", size=9, italic=True, color="475569")

MONEY = '"$"#,##0;("$"#,##0);"-"'
PCT = '0.0%'
NUM = '#,##0'
DEC = '#,##0.0'

thin = Side(style="thin", color="CBD5E1")
BOX = Border(left=thin, right=thin, top=thin, bottom=thin)

wb = Workbook()


def header_row(sheet, row, labels, widths=None, height=30):
    for i, lab in enumerate(labels, start=1):
        c = sheet.cell(row=row, column=i, value=lab)
        c.font = WHITE_BOLD
        c.fill = HEAD_FILL
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = BOX
    sheet.row_dimensions[row].height = height
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


def label_cell(sheet, row, text, wrap=True):
    c = sheet.cell(row=row, column=1, value=text)
    c.font = BLACK_CALC
    c.alignment = Alignment(wrap_text=wrap, vertical="center")
    c.border = BOX
    return c


# ================================================================ SHEET 1
ws = wb.active
ws.title = "1. Your Fleet"
ws.sheet_view.showGridLines = False
ws["A1"] = "AxiomDynamics — Customer ROI Calculator"
ws["A1"].font = TITLE_FONT
ws["A2"] = "Enter your numbers in the yellow cells only. Everything else calculates."
ws["A2"].font = NOTE_FONT
ws["A3"] = "Ring any yellow cell for a note on where that number comes from."
ws["A3"].font = Font(name="Arial", size=9, italic=True, color="94A3B8")

ws["A5"] = "A.  YOUR DEPLOYMENT"
ws["A5"].font = Font(name="Arial", size=11, bold=True, color=NAVY)
header_row(ws, 6, ["Input", "Value", "Unit", "What it means"],
           widths=[46, 16, 14, 62])

rows_a = [
    ("Freight car axles to be monitored", "B7", 500, NUM,
     "Count of axle-end bearings you want the platform watching. A 110-car train has 440 axles. "
     "BNSF's system runs roughly 1,300 trains/day, so the addressable axle population is in the "
     "hundreds of thousands -- this figure is your scope, not the network total.", "axles"),
    ("Average train speed through monitored territory", "B8", 45, NUM,
     "Converts detection lead time into track miles of early warning. Class I mainline averages "
     "run 40-50 mph; the Southern Transcon moves UPS 'Z' trains LA-Chicago in about 49 hours.", "mph"),
    ("Monitored locations (yards, corridors, divisions)", "B9", 1, NUM,
     "HOW MANY DISTINCT PLACES the platform is deployed. Second pricing axis, not driven by axle "
     "count. Each location needs its own edge server, detector integration, install trip, and "
     "support coverage. 1 = a single yard. A regional corridor = the subdivisions it spans. "
     "BNSF in full = 13 operating divisions across 3 regions.", "sites"),
]
for i, (label, ref, val, fmt, note, unit) in enumerate(rows_a):
    r = 7 + i
    label_cell(ws, r, label)
    input_cell(ws, ref, val, note, fmt)
    u = ws.cell(row=r, column=3, value=unit)
    u.font = NOTE_FONT
    u.border = BOX
    d = ws.cell(row=r, column=4, value="Ring the yellow cell for the source or reasoning.")
    d.font = NOTE_FONT
    d.alignment = Alignment(wrap_text=True, vertical="center")
    d.border = BOX
    ws.row_dimensions[r].height = 30

ws["A11"] = "B.  YOUR CURRENT EXPOSURE"
ws["A11"].font = Font(name="Arial", size=11, bold=True, color=NAVY)
header_row(ws, 12, ["Input", "Value", "Unit", "Where this number comes from"],
           widths=[46, 16, 14, 62])

rows_b = [
    ("Bearing-related derailments in the last 5 years", "B13", 3, NUM,
     "Pull from your own incident log. If you do not track this separately, use FRA accident data "
     "filtered to the cause code for bearing/journal failure.", "events"),
    ("Typical direct cost per bearing derailment", "B14", 500000, MONEY,
     "TYPICAL CASE, industry working figure: track repair, equipment damage, service disruption "
     "on a contained bearing set-out. Most bearing derailments are this, not the headline cases. "
     "Replace with your own claims average -- this is the single most important cell to correct.", "USD"),
    ("SEVERE bench — NTSB low (reference only)", "B15", 5000000, MONEY,
     "SOURCED, SEVERE-CASE ONLY: NTSB report RAB1712 documents a BNSF bearing-caused derailment at "
     "$5,000,000. An investigated, above-average event -- do NOT use as your typical cost. "
     "Sensitivity datum only.", "USD"),
    ("SEVERE bench — NTSB high (reference only)", "B16", 13500000, MONEY,
     "SOURCED, SEVERE-CASE ONLY: NTSB docket records a BNSF derailment at $13,500,000, excluding "
     "lading and environmental remediation. Above-average and investigated. Reference datum.", "USD"),
    ("Probability a missed defect escalates to catastrophic", "B17", 0.0005, '0.00%',
     "MODELING ASSUMPTION, NOT A CITATION. No published base rate exists. Even 2% per missed defect "
     "would imply dozens of billion-dollar events annually nationwide -- physically impossible. "
     "0.05% keeps the implied nationwide rate roughly consistent with observed East Palestine-scale "
     "frequency. Change deliberately and re-read the result.", "%"),
    ("Catastrophic event cost (hazmat release)", "B18", 1000000000, MONEY,
     "SOURCED: East Palestine, OH (Feb 2023, Norfolk Southern -- same wheel-bearing failure mode). "
     "DOJ/EPA settlement exceeded $310M, personal-injury class settlement $600M, cumulative reported "
     "cost passed $1B by mid-2024.", "USD"),
]
for i, (label, ref, val, fmt, note, unit) in enumerate(rows_b):
    r = 13 + i
    label_cell(ws, r, label)
    input_cell(ws, ref, val, note, fmt)
    u = ws.cell(row=r, column=3, value=unit)
    u.font = NOTE_FONT
    u.border = BOX
    d = ws.cell(row=r, column=4, value="Ring the yellow cell for the source.")
    d.font = NOTE_FONT
    d.alignment = Alignment(wrap_text=True, vertical="center")
    d.border = BOX
    ws.row_dimensions[r].height = 34

ws["A20"] = "C.  DERIVED — EXPECTED COST PER MISSED DEFECT"
ws["A20"].font = Font(name="Arial", size=11, bold=True, color=NAVY)
header_row(ws, 21, ["Derived metric", "Value", "Unit", "Formula"],
           widths=[46, 16, 14, 62])

c = ws.cell(row=22, column=1, value="Blended expected cost per missed defect")
c.font = BOLD
c.fill = TOTAL_FILL
c.border = BOX
v = ws.cell(row=22, column=2, value="=(1-B17)*B14+B17*B18")
v.font = BOLD
v.number_format = MONEY
v.fill = TOTAL_FILL
v.border = BOX
v.alignment = Alignment(horizontal="right")
ws.cell(row=22, column=3, value="USD").font = NOTE_FONT
ws.cell(row=22, column=3).border = BOX
f = ws.cell(row=22, column=4,
            value="(1 - p_catastrophic) x typical_cost + p_catastrophic x catastrophic_cost")
f.font = NOTE_FONT
f.alignment = Alignment(wrap_text=True, vertical="center")
f.border = BOX
ws.row_dimensions[22].height = 30

ws.cell(row=24, column=1,
        value="Sensitivity: set B14 to the NTSB severe figure (B15) and the model jumps to the "
              "headline number -- useful for a worst-case slide, misleading as a base case.").font = \
    Font(name="Arial", size=9, italic=True, color="B91C1C")
ws.cell(row=24, column=1).alignment = Alignment(wrap_text=True)

# ================================================================ SHEET 2
d = wb.create_sheet("2. Detection")
d.sheet_view.showGridLines = False
d["A1"] = "Detection Performance — Legacy vs. AxiomDynamics"
d["A1"].font = TITLE_FONT
d["A2"] = "Lead time converts directly into train miles of early warning."
d["A2"].font = NOTE_FONT

header_row(d, 4, ["Metric", "Legacy Detector Network", "AxiomDynamics", "Unit", "Source / basis"],
           widths=[40, 22, 22, 12, 58])


def det_row(sheet, r, label, legacy, axiom, unit, basis, fmt_l=DEC, fmt_a=DEC):
    c = sheet.cell(row=r, column=1, value=label)
    c.font = BLACK_CALC
    c.alignment = Alignment(wrap_text=True, vertical="center")
    c.border = BOX
    for col, val, fmt in ((2, legacy, fmt_l), (3, axiom, fmt_a)):
        cc = sheet.cell(row=r, column=col, value=val)
        cc.font = BLUE_INPUT
        cc.fill = INPUT_FILL
        cc.border = BOX
        cc.alignment = Alignment(horizontal="center", vertical="center")
        cc.number_format = fmt
    u = sheet.cell(row=r, column=4, value=unit)
    u.font = NOTE_FONT
    u.border = BOX
    b = sheet.cell(row=r, column=5, value=basis)
    b.font = NOTE_FONT
    b.alignment = Alignment(wrap_text=True, vertical="center")
    b.border = BOX
    sheet.row_dimensions[r].height = 32


det_row(d, 5, "Mean time from defect onset to alarm", 4.8, 1.5, "hours",
        "MODELING ASSUMPTION. 4.8 h is the illustrative legacy figure used in the platform's ROI "
        "module; 1.5 h is a defensible AxiomDynamics latency. Replace both with your own detector logs.")

det_row(d, 6, "False-positive rate (would stop a train)", 0.035, 0.001, "of detections",
        "MODELING ASSUMPTION. Legacy 3.5% reflects reported hot-bearing-detector stop rates. "
        "AxiomDynamics reflects the two-signal corroboration gate plus human reviewer disposition.",
        fmt_l=PCT, fmt_a=PCT)

det_row(d, 7, "Defects caught per 500 axles per year", 1.4, 2.1, "defects",
        "MODELING ASSUMPTION. Legacy counts only what its thresholds trip. AxiomDynamics adds "
        "rate-of-change and peer-outlier catches that never reach a fixed threshold. A 1.5x uplift "
        "is a deliberately modest claim.")

d["A9"] = "DERIVED — EARLY-WARNING DISTANCE"
d["A9"].font = Font(name="Arial", size=11, bold=True, color=NAVY)
header_row(d, 10, ["Derived metric", "", "Value", "Unit", "Formula"], widths=[40, 22, 22, 12, 58])


def det_derived(sheet, r, label, formula, unit, note, is_total=False, fmt=NUM):
    c = sheet.cell(row=r, column=1, value=label)
    c.font = BOLD if is_total else BLACK_CALC
    c.border = BOX
    if is_total:
        c.fill = TOTAL_FILL
    sheet.cell(row=r, column=2).border = BOX
    v = sheet.cell(row=r, column=3, value=formula)
    v.font = BOLD if is_total else GREEN_LINK
    v.number_format = fmt
    v.border = BOX
    v.alignment = Alignment(horizontal="center")
    if is_total:
        v.fill = TOTAL_FILL
    u = sheet.cell(row=r, column=4, value=unit)
    u.font = NOTE_FONT
    u.border = BOX
    n = sheet.cell(row=r, column=5, value=note)
    n.font = NOTE_FONT
    n.alignment = Alignment(wrap_text=True, vertical="center")
    n.border = BOX


det_derived(d, 11, "Speed of the monitored train", "='1. Your Fleet'!B8", "mph",
            "Linked from sheet 1", fmt=NUM)
det_derived(d, 12, "Lead-time advantage over legacy", "=B5-C5", "hours",
            "legacy_hours - axiom_hours")
det_derived(d, 13, "Additional track miles of early warning", "=C12*C11", "miles",
            "lead_time_advantage_hours x speed_mph", is_total=True)

d["A15"] = ("Read this as: at your stated line speed, the earlier alarm arrives while the car is "
            "still this many track miles from failure -- enough distance to plan a set-out at the "
            "next siding rather than react to a failure in the block. For context, hot-bearing "
            "detectors are typically spaced 40-64 miles apart, so on some subdivisions the legacy "
            "network gets one look before failure.")
d["A15"].font = NOTE_FONT
d["A15"].alignment = Alignment(wrap_text=True, vertical="top")
d.merge_cells("A15:E17")

# ================================================================ SHEET 3
b = wb.create_sheet("3. Benefit")
b.sheet_view.showGridLines = False
b["A1"] = "Annual Benefit — Three-Year View"
b["A1"].font = TITLE_FONT
b["A2"] = "All values pulled from sheets 1 and 2. No new inputs here."
b["A2"].font = NOTE_FONT
header_row(b, 4, ["Line", "Year 1", "Year 2", "Year 3", "Basis"], widths=[44, 18, 18, 18, 56])


def ben_row(sheet, r, label, formula_by_col, basis, fmt=DEC, is_total=False):
    c = sheet.cell(row=r, column=1, value=label)
    c.font = BOLD if is_total else BLACK_CALC
    c.border = BOX
    if is_total:
        c.fill = TOTAL_FILL
    for col in (2, 3, 4):
        L = get_column_letter(col)
        cc = sheet.cell(row=r, column=col, value=formula_by_col(L))
        cc.font = BOLD if is_total else BLACK_CALC
        cc.number_format = fmt
        cc.border = BOX
        cc.alignment = Alignment(horizontal="right")
        if is_total:
            cc.fill = TOTAL_FILL
    n = sheet.cell(row=r, column=5, value=basis)
    n.font = NOTE_FONT
    n.alignment = Alignment(wrap_text=True, vertical="center")
    n.border = BOX
    sheet.row_dimensions[r].height = 26


ben_row(b, 5, "Axles monitored", lambda L: "='1. Your Fleet'!B7", "From sheet 1", fmt=NUM)
ben_row(b, 6, "Defects detected (AxiomDynamics rate)",
        lambda L: f"=({{L}}5/500)*'2. Detection'!C7".replace("{L}", L),
        "(axles / 500) x defects_per_500_axles")
ben_row(b, 7, "Defects a legacy network would have missed",
        lambda L: f"=({L}5/500)*MAX(0,'2. Detection'!C7-'2. Detection'!B7)",
        "(axles/500) x max(0, axiom_catch - legacy_catch)")
ben_row(b, 8, "Expected cost per missed defect", lambda L: "='1. Your Fleet'!B22",
        "From sheet 1, section C", fmt=MONEY)
ben_row(b, 9, "Prevented failure cost", lambda L: f"={L}7*{L}8",
        "missed_defects x expected_cost_per_defect", fmt=MONEY, is_total=True)
ben_row(b, 10, "False-alarm / disruption cost", lambda L: f"={L}6*1500",
        "detected x $1,500 per unnecessary inspection (modeling assumption)", fmt=MONEY)
ben_row(b, 11, "Net annual benefit", lambda L: f"={L}9-{L}10",
        "prevented cost - false alarm cost", fmt=MONEY, is_total=True)

# ================================================================ SHEET 4
ct = wb.create_sheet("4. Licensing Cost")
ct.sheet_view.showGridLines = False
ct["A1"] = "AxiomDynamics Cost — Two Axes"
ct["A1"].font = TITLE_FONT
ct["A2"] = ("License scales with axle volume. Platform fee scales with site count. "
            "They are separate because they price different costs.")
ct["A2"].font = NOTE_FONT

header_row(ct, 4, ["Item", "Year 1 (Pilot)", "Year 2", "Year 3", "Notes"],
           widths=[44, 18, 18, 18, 56])

ct_rows = [
    (5, "Axles monitored", NUM, "From sheet 1"),
    (6, "Monitored locations", NUM, "From sheet 1 -- the second pricing axis"),
    (7, "Volume band", None, "Band where most of the volume sits. Pricing is marginal across bands."),
]
for r, label, fmt, note in ct_rows:
    label_cell(ct, r, label)
    for col in (2, 3, 4):
        ct.cell(row=r, column=col).border = BOX
        ct.cell(row=r, column=col).alignment = Alignment(horizontal="right")
    n = ct.cell(row=r, column=5, value=note)
    n.font = NOTE_FONT
    n.border = BOX
    n.alignment = Alignment(wrap_text=True, vertical="center")

for col in (2, 3, 4):
    L = get_column_letter(col)
    v = ct.cell(row=5, column=col, value="='1. Your Fleet'!B7")
    v.font = GREEN_LINK
    v.number_format = NUM
    s2 = ct.cell(row=6, column=col, value="='1. Your Fleet'!B9")
    s2.font = GREEN_LINK
    s2.number_format = NUM
    bd = ct.cell(row=7, column=col,
                 value=f'=IF({L}5<=500,"Band 1 — Core",IF({L}5<=2000,"Band 2 — Enterprise","Band 3 — Network"))')
    bd.font = BLACK_CALC
    bd.alignment = Alignment(horizontal="center")

label_cell(ct, 9, "Annual base license (per-axle, marginal)")
label_cell(ct, 10, "Platform fee (per-site, beyond the first)")
label_cell(ct, 11, "One-time hardware integration")
label_cell(ct, 12, "Training & change management")
label_cell(ct, 13, "Performance component")
for r in range(9, 14):
    for col in (2, 3, 4):
        ct.cell(row=r, column=col).border = BOX
        ct.cell(row=r, column=col).alignment = Alignment(horizontal="right")

# Year 1 pilot: fixed package, site count flows into hardware
for ref, val in (("B11", 65000), ("B12", 40000)):
    c = ct[ref]
    c.value = val
    c.font = BLUE_INPUT
    c.fill = INPUT_FILL
    c.number_format = MONEY
# pilot hardware scales with sites: first site 65k, each extra 45k
ct["B11"] = "=65000+MAX(0,'1. Your Fleet'!B9-1)*45000"
ct["B11"].font = BLACK_CALC
ct["B11"].number_format = MONEY
ct["B13"].value = 0
ct["B13"].font = BLUE_INPUT
ct["B13"].fill = INPUT_FILL
ct["B13"].number_format = MONEY

for col in (2, 3, 4):
    L = get_column_letter(col)
    lic = ct.cell(row=9, column=col,
                  value=f'=MIN({L}5,500)*$C$23+MAX(0,MIN({L}5,2000)-500)*$C$24+MAX(0,{L}5-2000)*$C$25')
    lic.font = BLACK_CALC
    lic.number_format = MONEY
    pf = ct.cell(row=10, column=col, value=f"=MAX(0,{L}6-1)*$C$26")
    pf.font = BLACK_CALC
    pf.number_format = MONEY
    if col != 2:
        for r in (11, 12):
            c = ct.cell(row=r, column=col, value=0)
            c.font = BLACK_CALC
            c.number_format = MONEY
        pc = ct.cell(row=13, column=col, value=f"=MIN('3. Benefit'!{L}9*0.03,{L}9*0.33)")
        pc.font = BLACK_CALC
        pc.number_format = MONEY
    else:
        pc = ct.cell(row=13, column=col, value=0)
        pc.number_format = MONEY
        pc.font = BLUE_INPUT
        pc.fill = INPUT_FILL

# Year-1 license is the pilot rate, not the production formula
ct["B9"].value = 180000
ct["B9"].font = BLUE_INPUT
ct["B9"].fill = INPUT_FILL
ct["B9"].number_format = MONEY
ct["B10"].value = 0
ct["B10"].font = BLUE_INPUT
ct["B10"].fill = INPUT_FILL
ct["B10"].number_format = MONEY

notes = {
    9: "$180,000 pilot-year license; production is per-axle marginal (see rate card)",
    10: "Per monitored location beyond the first -- see rate card",
    11: "$65,000 first site + $45,000 each additional (install, edge server, detector harness)",
    12: "$40,000 operator certification + reviewer workflow",
    13: "3% of prevented cost, capped at 33% of base license",
}
for r, txt in notes.items():
    n = ct.cell(row=r, column=5, value=txt)
    n.font = NOTE_FONT
    n.border = BOX
    n.alignment = Alignment(wrap_text=True, vertical="center")
    ct.row_dimensions[r].height = 28

c = ct.cell(row=15, column=1, value="TOTAL ANNUAL COST")
c.font = Font(name="Arial", size=11, bold=True, color=NAVY)
c.fill = TOTAL_FILL
c.border = BOX
for col in (2, 3, 4):
    L = get_column_letter(col)
    t = ct.cell(row=15, column=col, value=f"=SUM({L}9:{L}13)")
    t.font = Font(name="Arial", size=11, bold=True)
    t.number_format = MONEY
    t.fill = TOTAL_FILL
    t.border = BOX
    t.alignment = Alignment(horizontal="right")

# rate card
ct.cell(row=18, column=1, value="RATE CARD — EDIT THESE TO RE-PRICE THE DEAL")
ct.cell(row=18, column=1).font = Font(name="Arial", size=11, bold=True, color=NAVY)
ct.cell(row=19, column=1,
        value="Per-axle rates are marginal: each band charges only for the axles inside it, so "
              "return improves as the fleet grows. A flat tier would charge more than double for a "
              "doubling of axles and make the customer's ROI fall as they expand.").font = NOTE_FONT
ct.cell(row=19, column=1).alignment = Alignment(wrap_text=True)
ct.merge_cells("A19:E19")

header_row(ct, 21, ["Pricing lever", "Applies to", "Rate", "At band limit", "Notes"],
           widths=[44, 18, 18, 18, 56])

rates = [
    (23, "Axle band 1 — Core", "First 500 axles", 600, "=500*C23",
     "At $600/axle a 500-axle single-site deployment returns ~2.0x over three years."),
    (24, "Axle band 2 — Enterprise", "Next 1,500 axles", 500, "=1500*C24",
     "Declining marginal rate keeps ROI rising as the fleet grows."),
    (25, "Axle band 3 — Network", "Above 2,000 axles", 375, "=3000*C25",
     "Steepest discount at the largest volume; performance component carries the upside."),
    (26, "Platform fee", "Each site beyond the first", 45000, "=1*C26",
     "MODELING ASSUMPTION for edge infrastructure, install, and support coverage per location."),
]
for r, name, applies, rate, at_limit, note in rates:
    label_cell(ct, r, name)
    a = ct.cell(row=r, column=2, value=applies)
    a.font = NOTE_FONT
    a.border = BOX
    a.alignment = Alignment(horizontal="center")
    p = ct.cell(row=r, column=3, value=rate)
    p.font = BLUE_INPUT
    p.fill = INPUT_FILL
    p.number_format = MONEY
    p.border = BOX
    p.alignment = Alignment(horizontal="right")
    p.comment = Comment("Pricing hypothesis, not a published rate card. Retuned so return improves "
                        "monotonically with fleet size.", "AxiomDynamics")
    l = ct.cell(row=r, column=4, value=at_limit)
    l.font = BLACK_CALC
    l.number_format = MONEY
    l.border = BOX
    l.alignment = Alignment(horizontal="right")
    n = ct.cell(row=r, column=5, value=note)
    n.font = NOTE_FONT
    n.alignment = Alignment(wrap_text=True, vertical="center")
    n.border = BOX
    ct.row_dimensions[r].height = 32

ct.cell(row=27, column=1,
        value="These cells drive rows 9, 10 and 13 above. Change a rate and years 2-3 recalculate.").font = NOTE_FONT

# ================================================================ SHEET 5
s = wb.create_sheet("5. Summary")
s.sheet_view.showGridLines = False
s["A1"] = "Three-Year Business Case"
s["A1"].font = TITLE_FONT
s["A2"] = "The number that matters is at the bottom. Everything above it is auditable."
s["A2"].font = NOTE_FONT
header_row(s, 4, ["", "Year 1 (Pilot)", "Year 2", "Year 3", "Three-Year Total"],
           widths=[46, 20, 20, 20, 22])


def sumrow(sheet, r, label, formula_maker, is_total=False):
    c = sheet.cell(row=r, column=1, value=label)
    c.font = BOLD if is_total else BLACK_CALC
    c.border = BOX
    if is_total:
        c.fill = TOTAL_FILL
    for col in (2, 3, 4):
        L = get_column_letter(col)
        cc = sheet.cell(row=r, column=col, value=formula_maker(L))
        cc.font = BOLD if is_total else BLACK_CALC
        cc.number_format = MONEY
        cc.border = BOX
        cc.alignment = Alignment(horizontal="right")
        if is_total:
            cc.fill = TOTAL_FILL
    tc = sheet.cell(row=r, column=5, value=f"=SUM(B{r}:D{r})")
    tc.font = BOLD if is_total else BLACK_CALC
    tc.number_format = MONEY
    tc.border = BOX
    tc.alignment = Alignment(horizontal="right")
    if is_total:
        tc.fill = TOTAL_FILL


sumrow(s, 5, "Prevented failure cost", lambda L: f"='3. Benefit'!{L}9")
sumrow(s, 6, "Less: false-alarm disruption", lambda L: f"=-'3. Benefit'!{L}10")
sumrow(s, 7, "Net benefit", lambda L: f"='3. Benefit'!{L}11", is_total=True)
sumrow(s, 9, "Total licensing, platform & deployment cost",
       lambda L: f"='4. Licensing Cost'!{L}15")


def bigstat(r, label, formula, fmt, color="065F46"):
    c = s.cell(row=r, column=1, value=label)
    c.font = Font(name="Arial", size=12, bold=True, color=color)
    c.fill = TOTAL_FILL
    c.border = BOX
    v = s.cell(row=r, column=5, value=formula)
    v.font = Font(name="Arial", size=12, bold=True, color=color)
    v.number_format = fmt
    v.fill = TOTAL_FILL
    v.border = BOX
    v.alignment = Alignment(horizontal="right")


bigstat(11, "NET THREE-YEAR VALUE", "=E7-E9", MONEY)
bigstat(12, "RETURN ON INVESTMENT", '=IF(E9=0,"n/a",E7/E9)', '0.0"x"')
bigstat(13, "PAYBACK ON YEAR-1 PILOT", '=IF(B7=0,"n/a",B9/B7*12)', '0.0" months"', color="0A1628")

c = s.cell(row=14, column=1, value="Additional track miles of early warning")
c.font = BLACK_CALC
c.border = BOX
m = s.cell(row=14, column=5, value="='2. Detection'!C13")
m.font = BLACK_CALC
m.number_format = NUM
m.border = BOX
m.alignment = Alignment(horizontal="right")

c = s.cell(row=15, column=1, value="Cost per monitored axle per year (Year 2)")
c.font = BLACK_CALC
c.border = BOX
pa = s.cell(row=15, column=5, value="='4. Licensing Cost'!C15/'1. Your Fleet'!B7")
pa.font = BLACK_CALC
pa.number_format = MONEY
pa.border = BOX
pa.alignment = Alignment(horizontal="right")

s["A17"] = ("Sensitivity: the two levers that move this most are B14 on sheet 1 (your typical "
            "derailment cost) and B17 (catastrophic escalation probability). Site count changes the "
            "cost side without changing benefit -- which is exactly why a distributed deployment "
            "must be sold on the exposure it covers, not on axle count alone.")
s["A17"].font = NOTE_FONT
s["A17"].alignment = Alignment(wrap_text=True, vertical="top")
s.merge_cells("A17:E19")

s["A21"] = "Verified vs. assumed"
s["A21"].font = Font(name="Arial", size=11, bold=True, color=NAVY)
s["A22"] = ("SOURCED: $5.0M and $13.5M contained derailment costs (NTSB RAB1712 and NTSB docket); "
            "$1.0B+ catastrophic tier (DOJ/EPA settlement $310M+, AP-reported $600M personal-injury "
            "settlement, cumulative cost past $1B).")
s["A22"].font = NOTE_FONT
s["A22"].alignment = Alignment(wrap_text=True, vertical="top")
s.merge_cells("A22:E23")
s["A24"] = ("ASSUMED — replace before quoting: the 0.05% catastrophic escalation rate (cell B17), the 4.8-hour "
            "legacy and 1.5-hour AxiomDynamics detection times, defects caught per 500 axles, the "
            "3.5% and 0.1% false-positive rates, the $1,500 per-false-alarm cost, the $45,000 "
            "per-site platform fee, and every rate on the rate card.")
s["A24"].font = Font(name="Arial", size=9, color="B91C1C")
s["A24"].alignment = Alignment(wrap_text=True, vertical="top")
s.merge_cells("A24:E26")

for sheet, cell in ((ws, "A7"), (d, "A5"), (b, "A5"), (ct, "A5"), (s, "A5")):
    sheet.freeze_panes = cell

import os
wb.save(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "AxiomDynamics-ROI-Calculator.xlsx"))
print("written")
