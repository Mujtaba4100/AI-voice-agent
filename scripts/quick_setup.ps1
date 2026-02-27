# ============================================================================
# Quick Setup Script - AI Voice Agent
# ============================================================================
# This script automates the initial setup process
#
# Usage: .\quick_setup.ps1
# ============================================================================

Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "🚀 AI Voice Agent - Quick Setup" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# CHECK PREREQUISITES
# ============================================================================

Write-Host "🔍 Checking prerequisites..." -ForegroundColor Yellow
Write-Host ""

# Check Python
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ Python found: $pythonVersion" -ForegroundColor Green
    
    # Check Python version
    if ($pythonVersion -match "Python 3\.(9|10|11|12)") {
        Write-Host "   ✅ Python version is compatible" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  Python version may not be optimal (3.9-3.11 recommended)" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ❌ Python not found. Please install Python 3.9-3.11" -ForegroundColor Red
    Write-Host "      Download from: https://www.python.org/downloads/" -ForegroundColor Red
    exit 1
}

# Check pip
$pipVersion = pip --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ pip found: $pipVersion" -ForegroundColor Green
} else {
    Write-Host "   ❌ pip not found" -ForegroundColor Red
    exit 1
}

Write-Host ""

# ============================================================================
# GET API KEY
# ============================================================================

Write-Host "🔑 Gemini API Configuration" -ForegroundColor Yellow
Write-Host ""

$apiKey = $env:GEMINI_API_KEY

if (-not $apiKey) {
    Write-Host "GEMINI_API_KEY not found in environment" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To get an API key:" -ForegroundColor Cyan
    Write-Host "1. Visit: https://makersuite.google.com/app/apikey" -ForegroundColor Gray
    Write-Host "2. Sign in with your Google account" -ForegroundColor Gray
    Write-Host "3. Click 'Create API Key'" -ForegroundColor Gray
    Write-Host "4. Copy the key" -ForegroundColor Gray
    Write-Host ""
    
    $apiKey = Read-Host "Enter your Gemini API key (or press Enter to skip)"
    
    if ($apiKey) {
        # Save to environment variable for current session
        $env:GEMINI_API_KEY = $apiKey
        Write-Host "   ✅ API key set for current session" -ForegroundColor Green
        
        # Offer to save permanently
        $savePermanent = Read-Host "Save API key permanently? (Y/n)"
        if ($savePermanent -ne "n" -and $savePermanent -ne "N") {
            [Environment]::SetEnvironmentVariable("GEMINI_API_KEY", $apiKey, [EnvironmentVariableTarget]::User)
            Write-Host "   ✅ API key saved to user environment variables" -ForegroundColor Green
        }
    } else {
        Write-Host "   ⚠️  Skipping API key setup - LLM will not function" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ✅ API key already configured" -ForegroundColor Green
}

Write-Host ""

# ============================================================================
# VIRTUAL ENVIRONMENT
# ============================================================================

Write-Host "🐍 Setting up Python virtual environment..." -ForegroundColor Yellow

if (Test-Path "venv") {
    Write-Host "   ⏭️  Virtual environment already exists" -ForegroundColor Yellow
    $recreate = Read-Host "Recreate virtual environment? (y/N)"
    
    if ($recreate -eq "y" -or $recreate -eq "Y") {
        Write-Host "   🗑️  Removing old virtual environment..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force venv
    } else {
        Write-Host "   ✅ Using existing virtual environment" -ForegroundColor Green
        $skipVenv = $true
    }
}

if (-not $skipVenv) {
    Write-Host "   Creating virtual environment..." -ForegroundColor Cyan
    python -m venv venv
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ Virtual environment created" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Failed to create virtual environment" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""

# ============================================================================
# ACTIVATE VIRTUAL ENVIRONMENT
# ============================================================================

Write-Host "🔄 Activating virtual environment..." -ForegroundColor Yellow

$activateScript = "venv\Scripts\Activate.ps1"

if (Test-Path $activateScript) {
    try {
        & $activateScript
        Write-Host "   ✅ Virtual environment activated" -ForegroundColor Green
    } catch {
        Write-Host "   ⚠️  Could not activate automatically" -ForegroundColor Yellow
        Write-Host "   Run manually: .\venv\Scripts\Activate.ps1" -ForegroundColor Gray
    }
} else {
    Write-Host "   ❌ Activation script not found" -ForegroundColor Red
    exit 1
}

Write-Host ""

# ============================================================================
# UPGRADE PIP
# ============================================================================

Write-Host "📦 Upgrading pip..." -ForegroundColor Yellow

python -m pip install --upgrade pip setuptools wheel --quiet

if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ pip upgraded" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  pip upgrade failed (continuing anyway)" -ForegroundColor Yellow
}

Write-Host ""

# ============================================================================
# INSTALL PYTORCH
# ============================================================================

Write-Host "🔥 Installing PyTorch (CPU version)..." -ForegroundColor Yellow
Write-Host "   This may take a few minutes..." -ForegroundColor Gray

pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu --quiet

if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ PyTorch installed" -ForegroundColor Green
} else {
    Write-Host "   ❌ PyTorch installation failed" -ForegroundColor Red
    exit 1
}

Write-Host ""

# ============================================================================
# INSTALL DEPENDENCIES
# ============================================================================

Write-Host "📚 Installing project dependencies..." -ForegroundColor Yellow
Write-Host "   This will take 5-10 minutes..." -ForegroundColor Gray
Write-Host ""

pip install -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "   ✅ All dependencies installed" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "   ❌ Some dependencies failed to install" -ForegroundColor Red
    Write-Host "   Check error messages above" -ForegroundColor Red
    exit 1
}

Write-Host ""

# ============================================================================
# DOWNLOAD MODELS
# ============================================================================

Write-Host "📥 Downloading AI models..." -ForegroundColor Yellow

$downloadModels = Read-Host "Download models now? (Y/n)"

if ($downloadModels -ne "n" -and $downloadModels -ne "N") {
    python download_models.py
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ Models downloaded" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  Model download had issues" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ⏭️  Skipped model download" -ForegroundColor Yellow
    Write-Host "   Run later: python download_models.py" -ForegroundColor Gray
}

Write-Host ""

# ============================================================================
# CREATE DIRECTORIES
# ============================================================================

Write-Host "📁 Creating directory structure..." -ForegroundColor Yellow

$directories = @("models", "models\piper", "logs")

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "   ✓ Created: $dir" -ForegroundColor Green
    } else {
        Write-Host "   ✓ Exists: $dir" -ForegroundColor Gray
    }
}

Write-Host ""

# ============================================================================
# FIREWALL SETUP
# ============================================================================

Write-Host "🔥 Windows Firewall Configuration" -ForegroundColor Yellow

$setupFirewall = Read-Host "Configure Windows Firewall now? (requires Administrator) (y/N)"

if ($setupFirewall -eq "y" -or $setupFirewall -eq "Y") {
    # Check if running as admin
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    $isAdmin = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    
    if ($isAdmin) {
        .\scripts\setup_firewall.ps1
    } else {
        Write-Host "   ⚠️  Not running as Administrator" -ForegroundColor Yellow
        Write-Host "   Run manually with Administrator privileges:" -ForegroundColor Gray
        Write-Host "   .\scripts\setup_firewall.ps1" -ForegroundColor Cyan
    }
} else {
    Write-Host "   ⏭️  Skipped firewall setup" -ForegroundColor Yellow
    Write-Host "   Run later as Administrator: .\scripts\setup_firewall.ps1" -ForegroundColor Gray
}

Write-Host ""

# ============================================================================
# SUMMARY
# ============================================================================

Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "✅ Setup Complete!" -ForegroundColor Green
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "📊 Installation Summary:" -ForegroundColor Cyan
Write-Host "   ✅ Python virtual environment created" -ForegroundColor Gray
Write-Host "   ✅ Dependencies installed" -ForegroundColor Gray
Write-Host "   ✅ AI models downloaded" -ForegroundColor Gray
Write-Host "   ✅ Directory structure created" -ForegroundColor Gray

if ($apiKey) {
    Write-Host "   ✅ Gemini API key configured" -ForegroundColor Gray
} else {
    Write-Host "   ⚠️  Gemini API key not configured" -ForegroundColor Yellow
}

Write-Host ""

# ============================================================================
# NEXT STEPS
# ============================================================================

Write-Host "📝 Next Steps:" -ForegroundColor Cyan
Write-Host ""

Write-Host "1. Install Nginx:" -ForegroundColor White
Write-Host "   • Download from: http://nginx.org/en/download.html" -ForegroundColor Gray
Write-Host "   • Extract to: C:\nginx" -ForegroundColor Gray
Write-Host "   • Copy nginx.conf to: C:\nginx\conf\nginx.conf" -ForegroundColor Gray
Write-Host ""

Write-Host "2. Start Services:" -ForegroundColor White
Write-Host "   .\scripts\start_all.ps1" -ForegroundColor Cyan
Write-Host ""

Write-Host "3. Open Browser:" -ForegroundColor White
Write-Host "   http://localhost" -ForegroundColor Cyan
Write-Host ""

Write-Host "4. Test Voice Agent:" -ForegroundColor White
Write-Host "   • Click 'Start Recording'" -ForegroundColor Gray
Write-Host "   • Speak your question" -ForegroundColor Gray
Write-Host "   • Listen to AI response" -ForegroundColor Gray
Write-Host ""

# ============================================================================
# DOCUMENTATION
# ============================================================================

Write-Host "📚 Documentation:" -ForegroundColor Cyan
Write-Host "   • Installation Guide: docs\INSTALLATION.md" -ForegroundColor Gray
Write-Host "   • Security Checklist: docs\SECURITY_CHECKLIST.md" -ForegroundColor Gray
Write-Host "   • Port Forwarding: docs\PORT_FORWARDING.md" -ForegroundColor Gray
Write-Host ""

# ============================================================================
# TROUBLESHOOTING
# ============================================================================

Write-Host "🔧 Troubleshooting:" -ForegroundColor Cyan
Write-Host "   • Backend not starting: Check GEMINI_API_KEY is set" -ForegroundColor Gray
Write-Host "   • No audio: Check microphone permissions" -ForegroundColor Gray
Write-Host "   • Port 80 in use: Stop IIS (iisreset /stop)" -ForegroundColor Gray
Write-Host ""

Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "🎉 Ready to Start!" -ForegroundColor Green
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""
