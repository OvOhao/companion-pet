# companion-pet installer for Windows (PowerShell). Safe to re-run.
$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ROOT
Write-Host "==> companion-pet @ $ROOT"

function Find-Py {
  foreach ($c in @("py -3", "python", "python3")) {
    $exe = $c.Split(" ")[0]
    if (Get-Command $exe -ErrorAction SilentlyContinue) { return $c }
  }
  throw "No Python found. Install Python 3 from python.org and re-run."
}
$PY = Find-Py
Write-Host "==> using python: $PY"

# 1. built-in art
if (-not (Test-Path "assets\builtin\characters.json")) {
  Write-Host "==> generating built-in mascots"
  iex "$PY assets\builtin\make_art.py"
}

# 2. venv + PySide6 (true-transparency GUI backend)
if (-not (Test-Path ".venv\Scripts\python.exe")) {
  Write-Host "==> creating venv"
  iex "$PY -m venv .venv"
}
Write-Host "==> installing PySide6 (~100MB, please wait)"
& ".venv\Scripts\python.exe" -m pip install --upgrade pip -q
& ".venv\Scripts\python.exe" -m pip install PySide6 -q

# 3. user character folder
$chars = Join-Path $env:USERPROFILE ".companion\characters"
New-Item -ItemType Directory -Force -Path $chars | Out-Null
Write-Host "==> drop your own PNG/GIF characters into: $chars"

# 4. register hooks in the user's Claude Code settings.json (plugin hooks.json
#    uses a /bin/sh launcher that does not run on Windows, so we wire the .cmd
#    launcher into user settings instead).
$cmd = (Join-Path $ROOT "bin\companion.cmd").Replace("\", "\\")
$settingsDir = Join-Path $env:USERPROFILE ".claude"
$settings = Join-Path $settingsDir "settings.json"
New-Item -ItemType Directory -Force -Path $settingsDir | Out-Null
if (Test-Path $settings) { $cfg = Get-Content $settings -Raw | ConvertFrom-Json }
else { $cfg = [pscustomobject]@{} }
if (-not $cfg.hooks) { $cfg | Add-Member hooks ([pscustomobject]@{}) -Force }
foreach ($ev in @("SessionStart","Stop","Notification","SessionEnd")) {
  $entry = [pscustomobject]@{ hooks = @([pscustomobject]@{ type="command"; command="`"$cmd`" hook" }) }
  $cfg.hooks | Add-Member $ev @($entry) -Force
}
$ptu = [pscustomobject]@{ matcher="Bash"; hooks=@([pscustomobject]@{ type="command"; command="`"$cmd`" hook" }) }
$cfg.hooks | Add-Member PostToolUse @($ptu) -Force
$cfg | ConvertTo-Json -Depth 12 | Set-Content $settings -Encoding UTF8
Write-Host "==> wired companion hooks into $settings"

Write-Host ""
Write-Host "==> Done. Try it now:"
Write-Host "      bin\companion.cmd start"
Write-Host "      bin\companion.cmd demo"
Write-Host "      bin\companion.cmd stop"
Write-Host "    Restart Claude Code to pick up the hooks."
