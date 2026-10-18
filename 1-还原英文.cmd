@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>&1
if errorlevel 1 (
  echo Python 3 is required for this patcher.
  echo Install Python 3, then run this file again.
  pause
  exit /b 1
)
py -3 "%~dp0cn_localize.py" restore
exit /b %ERRORLEVEL%
