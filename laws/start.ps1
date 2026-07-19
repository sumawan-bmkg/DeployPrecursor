#!/usr/bin/env pwsh
<#
.SYNOPSIS
    BMKG LAWS — Hybrid V9.5+V8 Operational Server
.DESCRIPTION
    Starts the FastAPI production server for BMKG Geomagnetic lithosphere activity warning.
    Loads V9.5 PIMES (gatekeeper) and V8 SupCon (magnitude specialist) models.

    Environment variables (all optional):
        LAWS_HOST      — Bind address (default: 0.0.0.0)
        LAWS_PORT      — Bind port    (default: 8000)
        LAWS_DEVICE    — 'cuda' or 'cpu' (default: cuda)
        LAWS_H5_DIR    — Path to HDF5 scalogram directory
        LAWS_LOG_LEVEL — 'info', 'debug', 'warning' (default: info)

    Usage:
        .\start.ps1
        $env:LAWS_DEVICE='cpu'; .\start.ps1
        $env:LAWS_PORT=8080; .\start.ps1
#>

$ErrorActionPreference = 'Stop'
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$LogDir = Join-Path $ScriptDir 'logs'

# Ensure logs directory exists
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

$Timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$LogFile = Join-Path $LogDir "LAWS_$Timestamp.log"

Write-Host "╔═══════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   BMKG LAWS Operational Server              ║" -ForegroundColor Cyan
Write-Host "║   Hybrid V9.5 PIMES + V8 SupCon Pipeline    ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Activate virtual environment if present
$VenvActivate = Join-Path $ScriptDir '.venv' 'Scripts' 'Activate.ps1'
if (Test-Path $VenvActivate) {
    Write-Host "[*] Activating virtual environment..." -ForegroundColor Yellow
    . $VenvActivate
}

$HostVar = [System.Environment]::GetEnvironmentVariable('LAWS_HOST')
$PortVar = [System.Environment]::GetEnvironmentVariable('LAWS_PORT')
$DeviceVar = [System.Environment]::GetEnvironmentVariable('LAWS_DEVICE')

$HostAddr = if ($HostVar) { $HostVar } else { '0.0.0.0' }
$Port = if ($PortVar) { [int]$PortVar } else { 8000 }
$Device = if ($DeviceVar) { $DeviceVar } else { 'cuda' }

Write-Host "[HOST]  $HostAddr" -ForegroundColor Green
Write-Host "[PORT]  $Port" -ForegroundColor Green
Write-Host "[DEV]   $Device" -ForegroundColor Green
Write-Host "[LOG]   $LogFile" -ForegroundColor Green
Write-Host ""

# Validate checkpoint files
$V8Ckpt = Join-Path $ScriptDir 'checkpoints' 'v8_supcon_best.pth'
$V95Ckpt = Join-Path $ScriptDir 'checkpoints' 'v95_pimes_champion.pth'

if (-not (Test-Path $V8Ckpt)) {
    Write-Host "[!] WARNING: V8 checkpoint not found at $V8Ckpt" -ForegroundColor Yellow
}
if (-not (Test-Path $V95Ckpt)) {
    Write-Host "[!] WARNING: V9.5 checkpoint not found at $V95Ckpt" -ForegroundColor Yellow
}

Write-Host "[*] Starting uvicorn server..." -ForegroundColor Yellow
Write-Host ""

# Launch Uvicorn via Python module (more reliable than uvicorn command on Windows)
try {
    python -m uvicorn app.api.main:app `
        --host $HostAddr `
        --port $Port `
        --log-level info `
        --workers 1 `
        --no-reload 2>&1 | Tee-Object -FilePath $LogFile
}
catch {
    Write-Host "[!] Server exited with error: $_" -ForegroundColor Red
    Write-Host "[*] Trying fallback: direct python..." -ForegroundColor Yellow
    python -c "import uvicorn; uvicorn.run('app.api.main:app', host='$HostAddr', port=$Port, log_level='info')" 2>&1 | Tee-Object -FilePath $LogFile
}
