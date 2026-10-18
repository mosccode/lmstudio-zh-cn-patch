@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
where py >nul 2>&1
if errorlevel 1 (
  echo Python 3 is required for this patcher.
  echo Install Python 3, then run this file again.
  pause
  exit /b 1
)
set "MCPDIR=%~1"
if "%MCPDIR%"=="" set "MCPDIR=W:\Comfy-Desktop\mcp\comfyui-mcp-server"
if not exist "%MCPDIR%\server.py" (
  echo ComfyUI MCP server not found: %MCPDIR%
  echo Drag the server folder onto this file, or edit MCPDIR in this file.
  pause
  exit /b 2
)
py -3 "%~dp0patch_comfyui_mcp_cn.py" --dir "%MCPDIR%" --restore
set RC=%ERRORLEVEL%
echo.
pause
exit /b %RC%
