#!/usr/bin/env powershell
# Setup Virtual Environment for Vosk-based Interpreter Helper
# Run this script to create and configure the Python virtual environment

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Vosk Interpreter Helper - venv Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get project root (parent of scripts directory)
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VenvPath = Join-Path $ProjectRoot "venv"

Write-Host "Project root: $ProjectRoot" -ForegroundColor Yellow
Write-Host "Virtual environment will be created at: $VenvPath" -ForegroundColor Yellow
Write-Host ""

# Check if Python is available
try {
    $PythonVersion = python --version 2>&1
    Write-Host "✓ Found Python: $PythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found in PATH!" -ForegroundColor Red
    Write-Host "  Please install Python 3.8+ from python.org" -ForegroundColor Red
    exit 1
}

# Check if venv already exists
if (Test-Path $VenvPath) {
    Write-Host "" 
    Write-Host "⚠ Virtual environment already exists at: $VenvPath" -ForegroundColor Yellow
    $Response = Read-Host "Do you want to delete and recreate it? (y/N)"
    if ($Response -eq "y" -or $Response -eq "Y") {
        Write-Host "Removing existing venv..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force $VenvPath
    } else {
        Write-Host "Setup cancelled." -ForegroundColor Yellow
        exit 0
    }
}

# Create virtual environment
Write-Host ""
Write-Host "Creating virtual environment..." -ForegroundColor Cyan
try {
    python -m venv $VenvPath
    Write-Host "✓ Virtual environment created" -ForegroundColor Green
} catch {
    Write-Host "✗ Failed to create virtual environment" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}

# Install dependencies using venv's pip directly
Write-Host ""
Write-Host "Installing dependencies..." -ForegroundColor Cyan

$VenvPython = Join-Path $VenvPath "Scripts\python.exe"
$RequirementsFile = Join-Path $ProjectRoot "requirements.txt"

if (-not (Test-Path $RequirementsFile)) {
    Write-Host "✗ requirements.txt not found at: $RequirementsFile" -ForegroundColor Red
    exit 1
}

try {
    Write-Host "Upgrading pip..." -ForegroundColor Yellow
    & $VenvPython -m pip install --upgrade pip 2>&1 | Out-Null
    
    Write-Host "Installing requirements from requirements.txt..." -ForegroundColor Yellow
    & $VenvPython -m pip install -r $RequirementsFile
    
    Write-Host "✓ Dependencies installed successfully" -ForegroundColor Green
} catch {
    Write-Host "✗ Failed to install dependencies" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}

# Success message
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✓ Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Virtual environment created at:" -ForegroundColor Cyan
Write-Host "  $VenvPath" -ForegroundColor White
Write-Host ""
Write-Host "To activate the virtual environment, run:" -ForegroundColor Cyan
Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host ""
Write-Host "Or use the helper script:" -ForegroundColor Cyan
Write-Host "  .\scripts\activate_venv.ps1" -ForegroundColor White
Write-Host ""
Write-Host "The Electron app will automatically use the venv when available." -ForegroundColor Yellow
Write-Host ""
