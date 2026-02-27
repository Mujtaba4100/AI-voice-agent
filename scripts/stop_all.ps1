# ============================================================================
# Stop All Services - AI Voice Agent
# ============================================================================
# This script stops all running services for the AI Voice Agent
#
# Usage: .\stop_all.ps1
# ============================================================================

Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "🛑 Stopping AI Voice Agent System" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# CONFIGURATION
# ============================================================================

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$PidsFile = Join-Path $ProjectRoot "scripts\.running_pids.json"
$NginxPath = "C:\nginx\nginx.exe"

# ============================================================================
# STOP PROCESSES
# ============================================================================

# Stop Nginx
Write-Host "🔄 Stopping Nginx..." -ForegroundColor Yellow
$nginxProcesses = Get-Process nginx -ErrorAction SilentlyContinue

if ($nginxProcesses) {
    try {
        # Try graceful shutdown first
        if (Test-Path $NginxPath) {
            Set-Location (Split-Path $NginxPath)
            & $NginxPath -s stop
            Start-Sleep -Seconds 2
        }
        
        # Force kill if still running
        $nginxProcesses = Get-Process nginx -ErrorAction SilentlyContinue
        if ($nginxProcesses) {
            $nginxProcesses | Stop-Process -Force
        }
        
        Write-Host "   ✓ Nginx stopped" -ForegroundColor Green
    }
    catch {
        Write-Host "   ⚠️  Error stopping Nginx: $_" -ForegroundColor Yellow
    }
}
else {
    Write-Host "   • Nginx not running" -ForegroundColor Gray
}

# Stop Uvicorn backend workers
Write-Host "🔄 Stopping backend workers..." -ForegroundColor Yellow
$uvicornProcesses = Get-Process -Name "python*" -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*uvicorn*backend*" -or $_.MainWindowTitle -like "*backend*"
}

if ($uvicornProcesses) {
    $uvicornProcesses | Stop-Process -Force
    Write-Host "   ✓ Stopped $($uvicornProcesses.Count) backend worker(s)" -ForegroundColor Green
}
else {
    Write-Host "   • No backend workers found" -ForegroundColor Gray
}

# Stop Streamlit
Write-Host "🔄 Stopping Streamlit..." -ForegroundColor Yellow
$streamlitProcesses = Get-Process -Name "python*" -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*streamlit*" -or $_.MainWindowTitle -like "*streamlit*"
}

if ($streamlitProcesses) {
    $streamlitProcesses | Stop-Process -Force
    Write-Host "   ✓ Streamlit stopped" -ForegroundColor Green
}
else {
    Write-Host "   • Streamlit not running" -ForegroundColor Gray
}

# Alternative: Stop by saved PIDs
if (Test-Path $PidsFile) {
    Write-Host "🔄 Stopping processes from saved PIDs..." -ForegroundColor Yellow
    
    try {
        $pids = Get-Content $PidsFile | ConvertFrom-Json
        
        $allPids = @()
        if ($pids.Backend) { $allPids += $pids.Backend }
        if ($pids.Streamlit) { $allPids += $pids.Streamlit }
        
        foreach ($pid in $allPids) {
            try {
                $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
                if ($process) {
                    Stop-Process -Id $pid -Force
                    Write-Host "   ✓ Stopped process: $pid" -ForegroundColor Green
                }
            }
            catch {
                # Process might already be stopped
            }
        }
        
        # Remove PID file
        Remove-Item $PidsFile -Force
    }
    catch {
        Write-Host "   ⚠️  Could not read PIDs file" -ForegroundColor Yellow
    }
}

# ============================================================================
# CLEANUP
# ============================================================================

Write-Host "🔄 Cleaning up..." -ForegroundColor Yellow

# Kill any remaining Python processes running our scripts
$remainingProcesses = Get-Process python* -ErrorAction SilentlyContinue | Where-Object {
    $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($_.Id)" -ErrorAction SilentlyContinue).CommandLine
    $cmdLine -like "*backend.py*" -or $cmdLine -like "*ui.py*" -or $cmdLine -like "*uvicorn*" -or $cmdLine -like "*streamlit*"
}

if ($remainingProcesses) {
    Write-Host "   ⚠️  Found $($remainingProcesses.Count) remaining Python process(es)" -ForegroundColor Yellow
    $answer = Read-Host "   Stop these processes? (Y/n)"
    
    if ($answer -ne "n" -and $answer -ne "N") {
        $remainingProcesses | Stop-Process -Force
        Write-Host "   ✓ Stopped remaining processes" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "✅ All services stopped" -ForegroundColor Green
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# VERIFY
# ============================================================================

Write-Host "🔍 Verification:" -ForegroundColor Cyan

# Check if ports are now free
$ports = @(80, 8000, 8001, 8002, 8501)
$stillInUse = @()

foreach ($port in $ports) {
    $connection = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($connection) {
        $stillInUse += $port
    }
}

if ($stillInUse.Count -gt 0) {
    Write-Host "   ⚠️  Ports still in use: $($stillInUse -join ', ')" -ForegroundColor Yellow
    Write-Host "   Run: Get-NetTCPConnection -LocalPort PORT | Format-List" -ForegroundColor Gray
}
else {
    Write-Host "   ✓ All ports are now free" -ForegroundColor Green
}

# Check for remaining processes
$nginx = Get-Process nginx -ErrorAction SilentlyContinue
$python = Get-Process python* -ErrorAction SilentlyContinue | Where-Object {
    $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($_.Id)" -ErrorAction SilentlyContinue).CommandLine
    $cmdLine -like "*backend*" -or $cmdLine -like "*ui.py*" -or $cmdLine -like "*streamlit*"
}

if ($nginx) {
    Write-Host "   ⚠️  Nginx still running" -ForegroundColor Yellow
}
if ($python) {
    Write-Host "   ⚠️  Python processes still running" -ForegroundColor Yellow
}

if (-not $nginx -and -not $python) {
    Write-Host "   ✓ No AI Voice Agent processes running" -ForegroundColor Green
}

Write-Host ""
Write-Host "To start services again, run: .\start_all.ps1" -ForegroundColor Cyan
Write-Host ""
