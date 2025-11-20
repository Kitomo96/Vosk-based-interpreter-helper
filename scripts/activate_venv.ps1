#!/usr/bin/env powershell
# Activate Virtual Environment Helper
# Quick script to activate the venv

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VenvPath = Join-Path $ProjectRoot "venv"
$ActivateScript = Join-Path $VenvPath "Scripts\Activate.ps1"

if (Test-Path $ActivateScript) {
    Write-Host "Activating virtual environment..." -ForegroundColor Cyan
    & $ActivateScript
    Write-Host "✓ Virtual environment activated" -ForegroundColor Green
    Write-Host ""
    Write-Host "Python location:" -ForegroundColor Yellow
    python -c "import sys; print(sys.executable)"
    Write-Host ""
} else {
    Write-Host "✗ Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run setup_venv.ps1 first:" -ForegroundColor Yellow
    Write-Host "  .\scripts\setup_venv.ps1" -ForegroundColor White
    Write-Host ""
}
