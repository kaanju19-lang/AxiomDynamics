@echo off
REM Swap in the rebuilt A1 workbook.
REM
REM The old AxiomDynamics-ROI-Calculator.xlsx is locked by Windows while it is
REM open in Excel, so it cannot be replaced from the build environment. Close
REM Excel first, then double-click this file.
REM
REM The rebuilt file corrects two things against the old one:
REM   * the pilot year now totals $370,000 (A2 §5.1), not $285,000 -- the old
REM     workbook omitted the $35,000 validation and $50,000 support lines
REM   * the "one-time hardware integration" label is corrected, because we sell
REM     no hardware (D08 §6, D14 §3)
REM
REM Rebuild from source at any time with:
REM     cd client-assets\MASTER-BRIEF-DOCKET\A1-ROI-MODEL
REM     python3 build_roi_calculator.py

cd /d "%~dp0"

if not exist "AxiomDynamics-ROI-Calculator.rebuilt.xlsx" (
    echo ERROR: AxiomDynamics-ROI-Calculator.rebuilt.xlsx not found.
    echo Rebuild it with: python3 build_roi_calculator.py
    pause
    exit /b 1
)

if exist "~$AxiomDynamics-ROI-Calculator.xlsx" (
    echo ERROR: the workbook still looks open in Excel.
    echo Close Excel completely, then run this again.
    pause
    exit /b 1
)

del "AxiomDynamics-ROI-Calculator.xlsx"
move "AxiomDynamics-ROI-Calculator.rebuilt.xlsx" "AxiomDynamics-ROI-Calculator.xlsx"

echo Done. AxiomDynamics-ROI-Calculator.xlsx is now the rebuilt workbook.
echo Verify: pilot year should total $370,000 on sheet 4.
pause
