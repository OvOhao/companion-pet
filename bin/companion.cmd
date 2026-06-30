@echo off
setlocal enabledelayedexpansion
rem Windows launcher for the companion CLI (the GUI daemon is auto-spawned
rem under the bundled venv's pythonw.exe). Runs under any python (stdlib only).
set "ROOT=%~dp0.."
set "COMPANION_ROOT=%ROOT%"
set "PYTHONPATH=%ROOT%;%PYTHONPATH%"

set "PY="
if defined COMPANION_PYTHON set "PY=%COMPANION_PYTHON%"
if not defined PY (
  where py >nul 2>nul && set "PY=py -3"
)
if not defined PY (
  where python >nul 2>nul && set "PY=python"
)
if not defined PY (
  where python3 >nul 2>nul && set "PY=python3"
)
%PY% -m companion %*
endlocal
