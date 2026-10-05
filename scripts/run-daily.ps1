param(
    [string]$ProjectRoot = (Split-Path -Parent $PSScriptRoot)
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Set-Location $ProjectRoot

if (-not (Test-Path '.venv\Scripts\python.exe')) {
    python -m venv .venv
    .\.venv\Scripts\python.exe -m pip install .
}

& .\.venv\Scripts\python.exe -m legislative_monitor daily
