@echo off
REM Pushes the AxiomDynamics repo to GitHub.
REM Run by double-clicking. Window stays open so you can read the result.

cd /d "C:\Users\RGV\AxiomDynamics"

echo ============================================
echo  AxiomDynamics - push to GitHub
echo ============================================
echo.

echo Top commit before push:
git log --oneline -1
echo.
echo Commits waiting to go up:
git log --oneline origin/main..HEAD
echo.

git push origin main
set RESULT=%ERRORLEVEL%

echo.
if %RESULT%==0 (
  echo ============================================
  echo  PUSHED OK
  echo.
  echo  Top commit now on GitHub:
  git log --oneline -1
  echo.
  echo  Verify: https://github.com/kaanju19-lang/AxiomDynamics/commits/main
  echo ============================================
) else (
  echo ============================================
  echo  PUSH FAILED  ^(exit %RESULT%^)
  echo  Copy the red text above and send it back.
  echo ============================================
)

echo.
pause
