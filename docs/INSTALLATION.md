# AI Voice Agent - Complete Installation Guide

## 📋 Table of Contents
1. [System Requirements](#system-requirements)
2. [Prerequisites Installation](#prerequisites-installation)
3. [Project Setup](#project-setup)
4. [Model Download](#model-download)
5. [Backend Configuration](#backend-configuration)
6. [Nginx Setup](#nginx-setup)
7. [Running the System](#running-the-system)
8. [Firewall Configuration](#firewall-configuration)
9. [Port Forwarding](#port-forwarding)
10. [Troubleshooting](#troubleshooting)

---

## 🖥️ System Requirements

### Minimum Requirements
- **OS**: Windows 10 (21H2) or Windows 11 (22H2) or later
- **CPU**: Intel Core i5 (4 cores) or AMD Ryzen 5 equivalent
- **RAM**: 8GB (16GB recommended for better performance)
- **Storage**: 5GB free space for models and dependencies
- **Python**: 3.9, 3.10, or 3.11 (64-bit)

### Recommended Requirements
- **CPU**: Intel Core i7/i9 or AMD Ryzen 7/9 (8+ cores)
- **RAM**: 16GB or more
- **Storage**: SSD with 10GB+ free space
- **Internet**: Stable connection for API calls to Gemini

---

## 📦 Prerequisites Installation

### Step 1: Install Python

1. **Download Python**:
   - Visit: https://www.python.org/downloads/
   - Download Python 3.11.x (recommended) or 3.10.x
   - **Important**: Choose Windows installer (64-bit)

2. **Install Python**:
   ```
   ✅ Check "Add Python to PATH" during installation
   ✅ Choose "Install for all users" if possible
   ✅ Enable "pip" installation
   ```

3. **Verify Installation**:
   ```powershell
   python --version
   # Should output: Python 3.11.x or 3.10.x
   
   pip --version
   # Should output: pip 23.x or newer
   ```

### Step 2: Install Git (Optional but Recommended)

1. Download from: https://git-scm.com/download/win
2. Install with default settings
3. Verify: `git --version`

### Step 3: Install Visual C++ Redistributable

Some Python packages require Visual C++ runtime:
- Download from: https://aka.ms/vs/17/release/vc_redist.x64.exe
- Run installer and follow prompts
- Restart if required

### Step 4: Install FFmpeg (for audio processing)

1. **Download FFmpeg**:
   - Visit: https://www.gyan.dev/ffmpeg/builds/
   - Download "ffmpeg-release-essentials.zip"

2. **Install FFmpeg**:
   ```powershell
   # Extract to C:\ffmpeg
   # Add to PATH
   [Environment]::SetEnvironmentVariable(
       "Path",
       "$env:Path;C:\ffmpeg\bin",
       [EnvironmentVariableTarget]::Machine
   )
   ```

3. **Verify**:
   ```powershell
   ffmpeg -version
   ```

### Step 5: Get Google Gemini API Key

1. Visit: https://makersuite.google.com/app/apikey
2. Sign in with Google account
3. Click "Create API Key"
4. Copy the API key (keep it secure!)

---

## 🚀 Project Setup

### Step 1: Create Project Directory

```powershell
# Create project directory
New-Item -ItemType Directory -Path C:\AIVoiceAgent -Force
cd C:\AIVoiceAgent

# Or use your preferred location
```

### Step 2: Copy Project Files

Copy all project files to your project directory:
```
C:\AIVoiceAgent\
├── backend.py
├── ui.py
├── requirements.txt
├── nginx.conf
├── download_models.py
├── download_models.ps1
├── docs\
└── scripts\
```

### Step 3: Create Python Virtual Environment

```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# If you get execution policy error, run:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Step 4: Upgrade pip

```powershell
python -m pip install --upgrade pip setuptools wheel
```

### Step 5: Install PyTorch (CPU version)

```powershell
# Install PyTorch CPU version (smaller, faster for CPU-only)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### Step 6: Install Project Dependencies

```powershell
# Install all requirements
pip install -r requirements.txt

# This will take 5-10 minutes depending on your internet speed
```

### Step 7: Verify Installation

```powershell
# Test imports
python -c "import fastapi; import streamlit; import faster_whisper; print('✅ All imports successful')"
```

---

## 📥 Model Download

### Method 1: Using Python Script

```powershell
# Make sure virtual environment is activated
python download_models.py
```

### Method 2: Using PowerShell Script

```powershell
# Run PowerShell script
.\download_models.ps1
```

### Method 3: Manual Download

If automatic download fails:

1. **Piper TTS Model**:
   - Visit: https://huggingface.co/rhasspy/piper-voices
   - Navigate to: `en/en_US/lessac/medium/`
   - Download both:
     - `en_US-lessac-medium.onnx`
     - `en_US-lessac-medium.onnx.json`
   - Place in: `models/piper/`

2. **Whisper Model**:
   - Will download automatically on first backend run
   - No manual action needed

---

## ⚙️ Backend Configuration

### Step 1: Set Environment Variables

**Option A: Using PowerShell (Session-only)**
```powershell
$env:GEMINI_API_KEY = "your-api-key-here"
```

**Option B: Using System Environment Variables (Permanent)**
```powershell
# Run as Administrator
[Environment]::SetEnvironmentVariable(
    "GEMINI_API_KEY",
    "your-api-key-here",
    [EnvironmentVariableTarget]::User
)
```

**Option C: Using .env File**
```powershell
# Create .env file in project root
"GEMINI_API_KEY=your-api-key-here" | Out-File -FilePath .env -Encoding utf8
```

### Step 2: Test Backend

```powershell
# Activate virtual environment if not already activated
.\venv\Scripts\Activate.ps1

# Test single worker
python backend.py

# Should see:
# INFO:     Started server process [PID]
# INFO:     Uvicorn running on http://0.0.0.0:8000
```

Press `Ctrl+C` to stop the test server.

---

## 🌐 Nginx Setup

### Step 1: Download Nginx for Windows

1. Visit: http://nginx.org/en/download.html
2. Download: `nginx-1.24.0` (or latest stable version for Windows)
3. Extract to: `C:\nginx`

### Step 2: Configure Nginx

```powershell
# Copy our nginx.conf to nginx directory
Copy-Item nginx.conf C:\nginx\conf\nginx.conf -Force

# Or manually edit: C:\nginx\conf\nginx.conf
# Replace contents with our nginx.conf file
```

### Step 3: Test Nginx Configuration

```powershell
cd C:\nginx
.\nginx.exe -t

# Should output:
# nginx: configuration file C:\nginx/conf/nginx.conf test is successful
```

### Step 4: Start Nginx

```powershell
cd C:\nginx
Start-Process nginx.exe
```

### Step 5: Verify Nginx is Running

```powershell
# Check if nginx is running
Get-Process nginx

# Should show nginx processes
```

---

## ▶️ Running the System

### Method 1: Manual Startup (Recommended for Testing)

**Terminal 1 - Backend Worker 1:**
```powershell
cd C:\AIVoiceAgent
.\venv\Scripts\Activate.ps1
$env:GEMINI_API_KEY = "your-api-key"
uvicorn backend:app --host 0.0.0.0 --port 8000 --workers 1
```

**Terminal 2 - Backend Worker 2:**
```powershell
cd C:\AIVoiceAgent
.\venv\Scripts\Activate.ps1
$env:GEMINI_API_KEY = "your-api-key"
uvicorn backend:app --host 0.0.0.0 --port 8001 --workers 1
```

**Terminal 3 - Backend Worker 3:**
```powershell
cd C:\AIVoiceAgent
.\venv\Scripts\Activate.ps1
$env:GEMINI_API_KEY = "your-api-key"
uvicorn backend:app --host 0.0.0.0 --port 8002 --workers 1
```

**Terminal 4 - Streamlit UI:**
```powershell
cd C:\AIVoiceAgent
.\venv\Scripts\Activate.ps1
$env:API_BASE_URL = "http://localhost/api"
streamlit run ui.py --server.port 8501
```

**Terminal 5 - Nginx:**
```powershell
cd C:\nginx
.\nginx.exe
```

### Method 2: Using Startup Script (See scripts section)

```powershell
.\scripts\start_all.ps1
```

### Verify All Services

1. **Backend Health**:
   - Open browser: http://localhost:8000/health
   - Should show: `{"status": "healthy", ...}`

2. **Nginx**:
   - Open browser: http://localhost/health
   - Should route to backend

3. **Streamlit UI**:
   - Open browser: http://localhost
   - Should show AI Voice Agent interface

---

## 🔥 Firewall Configuration

### Option 1: Manual Configuration

1. **Open Windows Firewall**:
   - Press `Win + R`
   - Type: `wf.msc`
   - Press Enter

2. **Create Inbound Rule for Port 80**:
   - Click "Inbound Rules" → "New Rule"
   - Rule Type: Port
   - Protocol: TCP
   - Port: 80
   - Action: Allow the connection
   - Profile: All (or as needed)
   - Name: "AI Voice Agent - HTTP"
   - Click Finish

3. **Create Rules for Backend Ports** (if accessing directly):
   - Repeat for ports 8000, 8001, 8002, 8501
   - Names: "AI Voice Agent - Backend 1/2/3" and "AI Voice Agent - Streamlit"

### Option 2: PowerShell Script (Run as Administrator)

```powershell
# Allow HTTP (port 80)
New-NetFirewallRule -DisplayName "AI Voice Agent - HTTP" -Direction Inbound -Protocol TCP -LocalPort 80 -Action Allow

# Allow backend ports (optional, if accessing directly)
New-NetFirewallRule -DisplayName "AI Voice Agent - Backend" -Direction Inbound -Protocol TCP -LocalPort 8000,8001,8002 -Action Allow

# Allow Streamlit (optional)
New-NetFirewallRule -DisplayName "AI Voice Agent - Streamlit" -Direction Inbound -Protocol TCP -LocalPort 8501 -Action Allow
```

### Option 3: Using Automated Script

```powershell
# Run as Administrator
.\scripts\setup_firewall.ps1
```

### Verify Firewall Rules

```powershell
Get-NetFirewallRule -DisplayName "AI Voice Agent*" | Format-Table DisplayName, Enabled, Direction, Action
```

---

## 🌍 Port Forwarding (For External Access)

To access your AI Voice Agent from outside your local network:

### Step 1: Find Your Local IP

```powershell
ipconfig | Select-String "IPv4"

# Note your local IP (usually 192.168.x.x or 10.x.x.x)
```

### Step 2: Access Your Router

1. Open browser and navigate to router admin page:
   - Common addresses: `192.168.1.1`, `192.168.0.1`, `10.0.0.1`
   - Check router manual or sticker on router

2. Login with router credentials

### Step 3: Configure Port Forwarding

Settings vary by router, but generally:

1. Find **Port Forwarding** or **Virtual Server** section
2. Add new rule:
   - **Service Name**: AI Voice Agent
   - **External Port**: 80
   - **Internal IP**: Your computer's local IP
   - **Internal Port**: 80
   - **Protocol**: TCP
   - **Enable**: Yes

3. Save settings

### Step 4: Find Your Public IP

```powershell
# Using PowerShell
(Invoke-WebRequest -Uri "https://api.ipify.org").Content

# Or visit: https://whatismyipaddress.com/
```

### Step 5: Test External Access

From another network (mobile data):
- Navigate to: `http://your-public-ip`
- Should see AI Voice Agent interface

### Security Considerations

⚠️ **Important Security Notes**:

1. **Use HTTPS**: Consider setting up SSL/TLS certificate
2. **Authentication**: Add authentication layer for production
3. **Rate Limiting**: Implement rate limiting to prevent abuse
4. **Firewall**: Keep firewall rules restrictive
5. **Monitoring**: Monitor access logs regularly

---

## 🔧 Troubleshooting

### Issue: Python not found

**Solution**:
```powershell
# Check if Python is in PATH
$env:Path

# Add Python to PATH manually
[Environment]::SetEnvironmentVariable("Path", "$env:Path;C:\Python311;C:\Python311\Scripts", [EnvironmentVariableTarget]::User)
```

### Issue: pip install fails

**Possible Causes & Solutions**:

1. **No internet connection**:
   - Check internet connectivity
   - Try: `ping google.com`

2. **Proxy issues**:
   ```powershell
   # Set proxy if behind corporate firewall
   pip install --proxy=http://proxy-server:port package-name
   ```

3. **Permission denied**:
   ```powershell
   # Run PowerShell as Administrator
   pip install --user -r requirements.txt
   ```

### Issue: Backend fails to start

**Check logs**:
```powershell
# Run backend with verbose output
python backend.py 2>&1 | Tee-Object -FilePath backend.log
```

**Common causes**:
- Missing GEMINI_API_KEY
- Port already in use
- Missing models
- Dependencies not installed

### Issue: Nginx won't start

1. **Port 80 already in use**:
   ```powershell
   # Check what's using port 80
   netstat -ano | findstr :80
   
   # Stop IIS if running
   iisreset /stop
   ```

2. **Configuration error**:
   ```powershell
   cd C:\nginx
   .\nginx.exe -t
   # Check error messages
   ```

3. **Restart Nginx**:
   ```powershell
   # Stop nginx
   .\nginx.exe -s stop
   
   # Start nginx
   Start-Process nginx.exe
   ```

### Issue: WebSocket connection fails

1. **Check Nginx configuration**: Ensure WebSocket upgrade headers are set
2. **Check firewall**: Ensure WebSocket traffic is allowed
3. **Browser console**: Check for JavaScript errors

### Issue: Audio recording not working

1. **Check microphone permissions**:
   - Windows Settings → Privacy → Microphone
   - Allow apps to access microphone

2. **Check browser permissions**:
   - Click lock icon in address bar
   - Allow microphone access

3. **Test microphone**:
   - Windows Settings → Sound → Input
   - Test your microphone

### Issue: Slow performance

**Optimization tips**:

1. **Use smaller Whisper model**:
   - Change `WHISPER_MODEL_NAME` in `backend.py` to "tiny"

2. **Reduce backend workers**:
   - Start with 1-2 workers instead of 3

3. **Close other applications**:
   - Free up RAM and CPU resources

4. **Check system resources**:
   ```powershell
   # Monitor CPU and RAM usage
   Get-Process | Sort-Object CPU -Descending | Select-Object -First 10
   ```

### Getting Help

If you encounter issues not covered here:

1. Check backend logs: `backend.log`
2. Check nginx logs: `C:\nginx\logs\error.log`
3. Check Windows Event Viewer: `eventvwr.msc`
4. Search for error messages online
5. Check project repository for known issues

---

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Faster-Whisper GitHub](https://github.com/guillaumekln/faster-whisper)
- [Piper TTS Documentation](https://github.com/rhasspy/piper)
- [Google Gemini API](https://ai.google.dev/)
- [Nginx Documentation](https://nginx.org/en/docs/)

---

## ✅ Installation Checklist

Use this checklist to ensure complete setup:

- [ ] Python 3.9+ installed and in PATH
- [ ] Visual C++ Redistributable installed
- [ ] FFmpeg installed and in PATH
- [ ] Virtual environment created and activated
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] Models downloaded (Piper TTS)
- [ ] GEMINI_API_KEY environment variable set
- [ ] Nginx downloaded and configured
- [ ] Firewall rules created for port 80
- [ ] All services tested individually
- [ ] Full system tested end-to-end
- [ ] Port forwarding configured (if needed)

---

**🎉 Congratulations! Your AI Voice Agent is ready to use!**

Access your voice agent at: **http://localhost**
