# ============================================================================
# Start All Services - AI Voice Agent
# ============================================================================
# This script starts all required services for the AI Voice Agent:
# - 3 Backend API workers (ports 8000-8002)
# - Streamlit UI (port 8501)
# - Nginx reverse proxy (port 80)
#
# Usage: .\start_all.ps1
# ============================================================================

param(
    [string]$GeminiApiKey = $env:GEMINI_API_KEY,
    [switch]$SkipNginx = $false
)

Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "🚀 Starting AI Voice Agent System" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# CONFIGURATION
# ============================================================================

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VenvPath = Join-Path $ProjectRoot "venv\Scripts\Activate.ps1"
$BackendScript = Join-Path $ProjectRoot "backend.py"
$UIScript = Join-Path $ProjectRoot "ui.py"
$NginxPath = "C:\nginx\nginx.exe"

# Backend ports
$BackendPorts = @(8000, 8001, 8002)
$StreamlitPort = 8501

# ============================================================================
# PRE-FLIGHT CHECKS
# ============================================================================

Write-Host "🔍 Running pre-flight checks..." -ForegroundColor Yellow

# Check if virtual environment exists
if (-not (Test-Path $VenvPath)) {
    Write-Host "❌ Virtual environment not found at: $VenvPath" -ForegroundColor Red
    Write-Host "   Please run: python -m venv venv" -ForegroundColor Yellow
    exit 1
}
Write-Host "   ✓ Virtual environment found" -ForegroundColor Green

# Check if backend script exists
if (-not (Test-Path $BackendScript)) {
    Write-Host "❌ Backend script not found at: $BackendScript" -ForegroundColor Red
    exit 1
}
Write-Host "   ✓ Backend script found" -ForegroundColor Green

# Check if UI script exists
if (-not (Test-Path $UIScript)) {
    Write-Host "❌ UI script not found at: $UIScript" -ForegroundColor Red
    exit 1
}
Write-Host "   ✓ UI script found" -ForegroundColor Green

# Check Gemini API key
if (-not $GeminiApiKey) {
    Write-Host "⚠️  Warning: GEMINI_API_KEY not set" -ForegroundColor Yellow
    $GeminiApiKey = Read-Host "   Enter your Gemini API key (or press Enter to skip)"
}

if ($GeminiApiKey) {
    Write-Host "   ✓ Gemini API key configured" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  No Gemini API key - LLM will not function" -ForegroundColor Yellow
}

# Check if ports are available
Write-Host ""
Write-Host "🔍 Checking port availability..." -ForegroundColor Yellow

$portsInUse = @()
foreach ($port in ($BackendPorts + $StreamlitPort + 80)) {
    $connection = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($connection) {
        $portsInUse += $port
        Write-Host "   ⚠️  Port $port is already in use" -ForegroundColor Yellow
    } else {
        Write-Host "   ✓ Port $port is available" -ForegroundColor Green
    }
}

if ($portsInUse.Count -gt 0) {
    $answer = Read-Host "Some ports are in use. Continue anyway? (y/N)"
    if ($answer -ne "y" -and $answer -ne "Y") {
        Write-Host "❌ Aborted by user" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "✅ Pre-flight checks complete" -ForegroundColor Green
Write-Host ""

# ============================================================================
# START BACKEND WORKERS
# ============================================================================

Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "Starting Backend Workers"
Write-Host "========================================================================" -ForegroundColor Cyan

$BackendJobs = @()

foreach ($port in $BackendPorts) {
    Write-Host "🔄 Starting backend worker on port $port..." -ForegroundColor Yellow
    
    # Create startup script for this worker
    $startupScript = @"
Set-Location '$ProjectRoot'
& '$VenvPath'
`$env:GEMINI_API_KEY = '$GeminiApiKey'
uvicorn backend:app --host 0.0.0.0 --port $port --workers 1
"@
    
    # Start backend worker in new PowerShell window
    $job = Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", $startupScript -PassThru
    $BackendJobs += $job
    
    Write-Host "   ✓ Backend worker $port started (PID: $($job.Id))" -ForegroundColor Green
    Start-Sleep -Seconds 2
}

Write-Host ""
Write-Host "✅ All backend workers started" -ForegroundColor Green

# ============================================================================
# START STREAMLIT UI
# ============================================================================

Write-Host ""
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "Starting Streamlit UI"
Write-Host "========================================================================" -ForegroundColor Cyan

Write-Host "🔄 Starting Streamlit on port $StreamlitPort..." -ForegroundColor Yellow

$streamlitScript = @"
Set-Location '$ProjectRoot'
& '$VenvPath'
`$env:API_BASE_URL = 'http://localhost/api'
streamlit run ui.py --server.port $StreamlitPort --server.headless true
"@

$StreamlitJob = Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", $streamlitScript -PassThru

Write-Host "   ✓ Streamlit started (PID: $($StreamlitJob.Id))" -ForegroundColor Green

# ============================================================================
# START NGINX
# ============================================================================

if (-not $SkipNginx) {
    Write-Host ""
    Write-Host "========================================================================" -ForegroundColor Cyan
    Write-Host "Starting Nginx"
    Write-Host "========================================================================" -ForegroundColor Cyan
    
    if (Test-Path $NginxPath) {
        Write-Host "🔄 Starting Nginx..." -ForegroundColor Yellow
        
        # Check if nginx is already running
        $nginxProcess = Get-Process nginx -ErrorAction SilentlyContinue
        
        if ($nginxProcess) {
            Write-Host "   ⚠️  Nginx is already running" -ForegroundColor Yellow
        } else {
            Set-Location (Split-Path $NginxPath)
            Start-Process $NginxPath -WindowStyle Hidden
            Start-Sleep -Seconds 2
            
            $nginxProcess = Get-Process nginx -ErrorAction SilentlyContinue
            if ($nginxProcess) {
                Write-Host "   ✓ Nginx started" -ForegroundColor Green
            } else {
                Write-Host "   ❌ Failed to start Nginx" -ForegroundColor Red
            }
        }
    } else {
        Write-Host "   ⚠️  Nginx not found at: $NginxPath" -ForegroundColor Yellow
        Write-Host "   Skipping Nginx startup" -ForegroundColor Gray
    }
}

# ============================================================================
# SUMMARY
# ============================================================================

Write-Host ""
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "🎉 AI Voice Agent Started Successfully!" -ForegroundColor Green
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "📊 Service Status:" -ForegroundColor Cyan
Write-Host "   Backend Workers:" -ForegroundColor White
foreach ($job in $BackendJobs) {
    $port = 8000 + $BackendJobs.IndexOf($job)
    Write-Host "      • Worker $port - PID: $($job.Id)" -ForegroundColor Gray
}
Write-Host "   Streamlit UI:" -ForegroundColor White
Write-Host "      • Port $StreamlitPort - PID: $($StreamlitJob.Id)" -ForegroundColor Gray
Write-Host "   Nginx:" -ForegroundColor White
$nginxProcs = Get-Process nginx -ErrorAction SilentlyContinue
if ($nginxProcs) {
    Write-Host "      • Running (PIDs: $($nginxProcs.Id -join ', '))" -ForegroundColor Gray
} else {
    Write-Host "      • Not running" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🌐 Access URLs:" -ForegroundColor Cyan
Write-Host "   • Main UI (via Nginx):  http://localhost" -ForegroundColor White
Write-Host "   • Streamlit Direct:     http://localhost:8501" -ForegroundColor Gray
Write-Host "   • Backend (Worker 1):   http://localhost:8000/health" -ForegroundColor Gray
Write-Host "   • Backend (via Nginx):  http://localhost/health" -ForegroundColor Gray

Write-Host ""
Write-Host "📝 Next Steps:" -ForegroundColor Cyan
Write-Host "   1. Open http://localhost in your browser" -ForegroundColor White
Write-Host "   2. Check backend health: http://localhost/health" -ForegroundColor White
Write-Host "   3. Click 'Start Recording' to test voice agent" -ForegroundColor White

Write-Host ""
Write-Host "⚠️  To stop all services, run: .\stop_all.ps1" -ForegroundColor Yellow
Write-Host ""

# Save PIDs for stop script
$pids = @{
    Backend = $BackendJobs.Id
    Streamlit = $StreamlitJob.Id
    Timestamp = Get-Date
}

$pids | ConvertTo-Json | Out-File -FilePath (Join-Path $ProjectRoot "scripts\.running_pids.json") -Encoding utf8

Write-Host "✅ All services started. Press Ctrl+C in each window to stop services." -ForegroundColor Green
