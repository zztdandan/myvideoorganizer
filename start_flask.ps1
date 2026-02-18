# Flask Application Startup Script
# Automatically handles port conflicts and permission issues

$ErrorActionPreference = "Continue"

# Change to script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Flask Video Organizer Startup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Check virtual environment
Write-Host "[1/4] Checking virtual environment..." -ForegroundColor Yellow
$venvPath = Join-Path $scriptDir ".venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "  Error: Virtual environment .venv not found" -ForegroundColor Red
    Write-Host "  Please run: python -m venv .venv" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# 2. Activate virtual environment
Write-Host "[2/4] Activating virtual environment..." -ForegroundColor Yellow
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    try {
        & $activateScript
        Write-Host "  OK Virtual environment activated" -ForegroundColor Green
    }
    catch {
        Write-Host "  Warning: Failed to activate virtual environment, continuing..." -ForegroundColor Yellow
    }
}
else {
    Write-Host "  Warning: Activation script not found" -ForegroundColor Yellow
}

# 3. Check Python
Write-Host "[3/4] Checking Python environment..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  OK $pythonVersion" -ForegroundColor Green
}
catch {
    Write-Host "  Error: Python not found" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# 4. Check and select available port
Write-Host "[4/4] Checking port availability..." -ForegroundColor Yellow

# Function: Test if port is available
function Test-PortAvailable {
    param([int]$Port)
    
    try {
        $listener = New-Object System.Net.Sockets.TcpListener([System.Net.IPAddress]::Any, $Port)
        $listener.Start()
        $listener.Stop()
        return $true
    }
    catch {
        return $false
    }
}

# Try default port 5050
$port = 5050
$portFound = $false
$startPort = 5050
$endPort = 9999

if (Test-PortAvailable -Port $port) {
    Write-Host "  OK Port $port is available" -ForegroundColor Green
    $portFound = $true
}
else {
    Write-Host "  X Port $port is in use, searching for alternative ($startPort-$endPort)..." -ForegroundColor Yellow
    
    # Try ports in wider range
    for ($p = $startPort; $p -le $endPort; $p++) {
        if (Test-PortAvailable -Port $p) {
            $port = $p
            $portFound = $true
            Write-Host "  OK Found available port: $port" -ForegroundColor Green
            break
        }
        # Show progress every 10 ports
        if (($p - $startPort) % 10 -eq 0 -and $p -gt $startPort) {
            Write-Host "  Checking port $p..." -ForegroundColor Gray
        }
    }
    
    if (-not $portFound) {
        Write-Host "  Error: Cannot find available port ($startPort-$endPort)" -ForegroundColor Red
        Write-Host "  Trying to find process using port $startPort..." -ForegroundColor Yellow
        
        # Try to find process using the port
        try {
            $netstat = netstat -ano | Select-String ":$startPort\s"
            if ($netstat) {
                $pid = ($netstat -split '\s+')[-1]
                if ($pid -match '^\d+$') {
                    $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
                    if ($proc) {
                        $procName = $proc.ProcessName
                        Write-Host "  Process using port ${startPort}: ${procName} (PID: ${pid})" -ForegroundColor Yellow
                        Write-Host "  You can terminate it with: Stop-Process -Id ${pid} -Force" -ForegroundColor Yellow
                    }
                }
            }
        } catch {
            # Ignore errors in process detection
        }
        
        Write-Host "  Please manually terminate the process or modify the script to use a different port range" -ForegroundColor Yellow
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# 5. Start application
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Starting Flask application..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Access URL: " -NoNewline -ForegroundColor White
Write-Host "http://127.0.0.1:$port" -ForegroundColor Green
Write-Host "  Stop server: " -NoNewline -ForegroundColor White
Write-Host "Press Ctrl+C" -ForegroundColor Yellow
Write-Host ""

# Start Flask application
try {
    python app.py --host 127.0.0.1 --port $port
}
catch {
    Write-Host ""
    Write-Host "Startup failed!" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

