# ============================================================================
# AI Voice Agent - Model Downloader (PowerShell Script)
# ============================================================================
# Downloads all required AI models for the voice agent
# Usage: .\download_models.ps1
# ============================================================================

Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "🚀 AI VOICE AGENT - MODEL DOWNLOADER" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# CONFIGURATION
# ============================================================================

$ModelsDir = "models"
$PiperDir = Join-Path $ModelsDir "piper"

# Piper TTS model URLs (High-quality US English voice)
$PiperModels = @{
    "en_US-lessac-medium" = @{
        OnnxUrl = "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx"
        JsonUrl = "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json"
    }
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

function Download-File {
    param(
        [string]$Url,
        [string]$OutputPath,
        [string]$Description
    )
    
    Write-Host "📥 Downloading $Description..." -ForegroundColor Yellow
    Write-Host "   URL: $Url" -ForegroundColor Gray
    Write-Host "   Destination: $OutputPath" -ForegroundColor Gray
    
    try {
        # Use WebClient for progress display
        $webClient = New-Object System.Net.WebClient
        
        # Register progress event
        Register-ObjectEvent -InputObject $webClient -EventName DownloadProgressChanged -SourceIdentifier WebClient.DownloadProgressChanged -Action {
            $percent = $EventArgs.ProgressPercentage
            $downloaded = [math]::Round($EventArgs.BytesReceived / 1MB, 2)
            $total = [math]::Round($EventArgs.TotalBytesToReceive / 1MB, 2)
            Write-Progress -Activity "Downloading $Description" -Status "$downloaded MB / $total MB" -PercentComplete $percent
        } | Out-Null
        
        # Download file synchronously
        $webClient.DownloadFile($Url, $OutputPath)
        
        # Cleanup event
        Unregister-Event -SourceIdentifier WebClient.DownloadProgressChanged
        Write-Progress -Activity "Downloading $Description" -Completed
        
        Write-Host "   ✅ Downloaded successfully: $(Split-Path $OutputPath -Leaf)" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "   ❌ Error downloading: $_" -ForegroundColor Red
        return $false
    }
    finally {
        $webClient.Dispose()
    }
}

function Create-DirectoryStructure {
    Write-Host "📁 Creating directory structure..." -ForegroundColor Yellow
    
    $directories = @($ModelsDir, $PiperDir)
    
    foreach ($dir in $directories) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            Write-Host "   ✓ Created: $dir" -ForegroundColor Green
        } else {
            Write-Host "   ✓ Exists: $dir" -ForegroundColor Gray
        }
    }
    
    Write-Host "✅ Directory structure ready" -ForegroundColor Green
}

function Download-PiperModels {
    param([string]$VoiceName = "en_US-lessac-medium")
    
    Write-Host ""
    Write-Host "========================================================================"
    Write-Host "Downloading Piper TTS Model: $VoiceName"
    Write-Host "========================================================================"
    
    if (-not $PiperModels.ContainsKey($VoiceName)) {
        Write-Host "❌ Voice '$VoiceName' not found in available models." -ForegroundColor Red
        return $false
    }
    
    $modelInfo = $PiperModels[$VoiceName]
    
    # Download ONNX model file
    $onnxPath = Join-Path $PiperDir "$VoiceName.onnx"
    if (Test-Path $onnxPath) {
        Write-Host "⏭️  Model already exists: $(Split-Path $onnxPath -Leaf)" -ForegroundColor Yellow
    } else {
        $success = Download-File -Url $modelInfo.OnnxUrl -OutputPath $onnxPath -Description "$VoiceName.onnx"
        if (-not $success) { return $false }
    }
    
    # Download JSON config file
    $jsonPath = Join-Path $PiperDir "$VoiceName.onnx.json"
    if (Test-Path $jsonPath) {
        Write-Host "⏭️  Config already exists: $(Split-Path $jsonPath -Leaf)" -ForegroundColor Yellow
    } else {
        $success = Download-File -Url $modelInfo.JsonUrl -OutputPath $jsonPath -Description "$VoiceName.onnx.json"
        if (-not $success) { return $false }
    }
    
    Write-Host "✅ Piper model '$VoiceName' downloaded successfully!" -ForegroundColor Green
    return $true
}

function Verify-WhisperModels {
    Write-Host ""
    Write-Host "========================================================================"
    Write-Host "Verifying Whisper Models"
    Write-Host "========================================================================"
    
    Write-Host "ℹ️  Faster-Whisper models are downloaded automatically on first use." -ForegroundColor Cyan
    Write-Host "   Models will be cached in:" -ForegroundColor Gray
    
    $cacheLocations = @(
        Join-Path $env:USERPROFILE ".cache\huggingface\hub",
        Join-Path $env:LOCALAPPDATA "huggingface\hub"
    )
    
    foreach ($location in $cacheLocations) {
        if (Test-Path $location) {
            Write-Host "   ✓ $location" -ForegroundColor Green
        } else {
            Write-Host "   ○ $location (will be created on first use)" -ForegroundColor Gray
        }
    }
    
    Write-Host ""
    Write-Host "📝 Available Whisper models:" -ForegroundColor Cyan
    Write-Host "   - tiny    (39M parameters, fastest, ~1GB RAM)" -ForegroundColor Gray
    Write-Host "   - base    (74M parameters, balanced, ~1.5GB RAM)" -ForegroundColor Gray
    Write-Host "   - small   (244M parameters, better quality, ~2GB RAM)" -ForegroundColor Gray
    Write-Host "   - medium  (769M parameters, high quality, ~5GB RAM)" -ForegroundColor Gray
    
    Write-Host ""
    Write-Host "💡 The backend is configured to use 'tiny' by default." -ForegroundColor Yellow
    Write-Host "   Change WHISPER_MODEL_NAME in backend.py to use a different model." -ForegroundColor Gray
    
    return $true
}

function Display-Summary {
    Write-Host ""
    Write-Host "========================================================================"
    Write-Host "📊 DOWNLOAD SUMMARY"
    Write-Host "========================================================================"
    
    Write-Host ""
    Write-Host "📂 Model Directory Structure:" -ForegroundColor Cyan
    Write-Host "   $ModelsDir\"
    Write-Host "   └── piper\"
    
    $piperFiles = Get-ChildItem -Path $PiperDir -Filter "*.onnx" -ErrorAction SilentlyContinue
    if ($piperFiles) {
        foreach ($file in $piperFiles) {
            $sizeMB = [math]::Round($file.Length / 1MB, 1)
            Write-Host "       ├── $($file.Name) ($sizeMB MB)" -ForegroundColor Green
            
            $jsonFile = Join-Path $PiperDir "$($file.Name).json"
            if (Test-Path $jsonFile) {
                Write-Host "       ├── $($file.Name).json" -ForegroundColor Green
            }
        }
    } else {
        Write-Host "       └── (no models downloaded)" -ForegroundColor Gray
    }
    
    Write-Host ""
    Write-Host "✅ Model download complete!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📝 Next steps:" -ForegroundColor Cyan
    Write-Host "   1. Set up your GEMINI_API_KEY environment variable" -ForegroundColor Gray
    Write-Host "   2. Run: pip install -r requirements.txt" -ForegroundColor Gray
    Write-Host "   3. Start backend servers (see docs\INSTALLATION.md)" -ForegroundColor Gray
    Write-Host "   4. Start Streamlit UI" -ForegroundColor Gray
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

try {
    # Create directories
    Create-DirectoryStructure
    
    # Download Piper TTS models
    $success = Download-PiperModels -VoiceName "en_US-lessac-medium"
    
    if (-not $success) {
        Write-Host ""
        Write-Host "⚠️  Some downloads failed. Please check the errors above." -ForegroundColor Yellow
        Write-Host "💡 You can try downloading manually from:" -ForegroundColor Yellow
        Write-Host "   https://huggingface.co/rhasspy/piper-voices" -ForegroundColor Gray
        exit 1
    }
    
    # Verify Whisper setup
    Verify-WhisperModels
    
    # Display summary
    Display-Summary
    
    exit 0
}
catch {
    Write-Host ""
    Write-Host "❌ Unexpected error: $_" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor Red
    exit 1
}
