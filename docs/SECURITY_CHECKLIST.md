# AI Voice Agent - Security and Stability Checklist

## 📋 Overview

This document provides comprehensive checks for:
- ✅ Windows firewall rule automation
- ✅ Port 80 binding conflicts
- ✅ Audio buffer memory leaks
- ✅ WebSocket stability
- ✅ Concurrent user safety

---

## 🔥 Windows Firewall Configuration

### Automated Firewall Setup

#### ✅ Verification Steps

1. **Run Firewall Setup Script**:
   ```powershell
   # Run as Administrator
   .\scripts\setup_firewall.ps1
   ```

2. **Verify Rules Created**:
   ```powershell
   Get-NetFirewallRule -DisplayName "AI Voice Agent*" | Format-Table DisplayName, Enabled, Direction, Action
   ```

3. **Expected Output**:
   ```
   DisplayName                    Enabled Direction Action
   -----------                    ------- --------- ------
   AI Voice Agent - HTTP          True    Inbound   Allow
   AI Voice Agent - Backend API   True    Inbound   Allow
   AI Voice Agent - Streamlit     True    Inbound   Allow
   ```

4. **Test Port Access**:
   ```powershell
   # Test from another machine on network
   Test-NetConnection -ComputerName YOUR_LOCAL_IP -Port 80
   
   # Should show: TcpTestSucceeded : True
   ```

#### 🔴 Common Issues

**Issue**: Script fails with "Access Denied"
- **Solution**: Must run PowerShell as Administrator
  ```powershell
  # Check if running as admin
  ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
  ```

**Issue**: Rules created but port still blocked
- **Solution**: Check Windows Defender additional settings
  ```powershell
  # Open Windows Security
  Start-Process "windowsdefender:"
  # Navigate to: Firewall & network protection → Advanced settings
  ```

**Issue**: Rules conflict with existing IIS rules
- **Solution**: Stop IIS service
  ```powershell
  Stop-Service W3SVC
  Set-Service W3SVC -StartupType Disabled
  ```

#### 🛡️ Security Best Practices

1. **Limit Profile Scope**:
   ```powershell
   # For home networks, use only Domain and Private
   Set-NetFirewallRule -DisplayName "AI Voice Agent - HTTP" -Profile Domain,Private
   ```

2. **Add Remote Address Restriction**:
   ```powershell
   # Only allow specific IP ranges
   Set-NetFirewallRule -DisplayName "AI Voice Agent - HTTP" -RemoteAddress 192.168.1.0/24
   ```

3. **Regular Audit**:
   ```powershell
   # Review all rules monthly
   Get-NetFirewallRule | Where-Object Enabled -eq True | Format-Table DisplayName, Direction, Action
   ```

---

## 🌐 Port 80 Binding Conflicts

### Pre-Flight Conflict Detection

#### ✅ Verification Steps

1. **Check Port 80 Availability**:
   ```powershell
   # Before starting services
   Get-NetTCPConnection -LocalPort 80 -ErrorAction SilentlyContinue
   
   # If empty, port is free
   # If output shown, port is in use
   ```

2. **Identify Process Using Port 80**:
   ```powershell
   # Find process ID
   $connection = Get-NetTCPConnection -LocalPort 80 -ErrorAction SilentlyContinue
   if ($connection) {
       $processId = $connection.OwningProcess
       Get-Process -Id $processId | Select-Object ProcessName, Id, Path
   }
   ```

3. **Test Nginx Binding**:
   ```powershell
   # Start nginx and check logs
   cd C:\nginx
   .\nginx.exe
   
   # Check error log
   Get-Content logs\error.log -Tail 20
   ```

#### 🔴 Common Conflicts

**Conflict 1: IIS (Internet Information Services)**
```powershell
# Stop IIS
Stop-Service W3SVC -Force
Set-Service W3SVC -StartupType Disabled

# Verify
Get-Service W3SVC
# Should show: Status = Stopped, StartType = Disabled
```

**Conflict 2: Windows HTTP Server (http.sys)**
```powershell
# Check URL reservations
netsh http show urlacl

# Remove conflicting reservation
netsh http delete urlacl url=http://+:80/
```

**Conflict 3: Other Web Servers (Apache, XAMPP)**
```powershell
# Stop Apache
net stop Apache2.4

# Or stop XAMPP
Stop-Process -Name httpd -Force
```

**Conflict 4: Skype/Teams**
```powershell
# Skype sometimes uses port 80
# Disable in: Skype → Settings → Advanced → Connection
# Uncheck "Use port 80 and 443"
```

#### 🛠️ Resolution Strategy

1. **Use Alternative Port**:
   ```nginx
   # In nginx.conf
   server {
       listen 8080;  # Instead of 80
       # ... rest of configuration
   }
   ```

2. **Bind to Specific IP**:
   ```nginx
   # Only listen on specific network interface
   server {
       listen 127.0.0.1:80;  # Localhost only
       # or
       listen 192.168.1.100:80;  # Specific IP
   }
   ```

3. **Monitor Port Status**:
   ```powershell
   # Create monitoring script
   while ($true) {
       $port80 = Get-NetTCPConnection -LocalPort 80 -ErrorAction SilentlyContinue
       if ($port80) {
           $proc = Get-Process -Id $port80.OwningProcess
           Write-Host "Port 80 in use by: $($proc.ProcessName) (PID: $($proc.Id))"
       } else {
           Write-Host "Port 80 is free"
       }
       Start-Sleep -Seconds 10
   }
   ```

---

## 💾 Audio Buffer Memory Leak Prevention

### Memory Management Verification

#### ✅ Verification Steps

1. **Monitor Memory Usage**:
   ```powershell
   # Monitor Python processes
   while ($true) {
       $processes = Get-Process python* -ErrorAction SilentlyContinue
       $processes | Select-Object ProcessName, Id, 
           @{Name="Memory(MB)";Expression={[math]::Round($_.WS/1MB, 2)}},
           @{Name="CPU(%)";Expression={$_.CPU}} | Format-Table
       Start-Sleep -Seconds 5
   }
   ```

2. **Load Testing**:
   ```powershell
   # Send multiple requests
   for ($i = 1; $i -le 20; $i++) {
       Write-Host "Request $i"
       $response = Invoke-WebRequest -Uri http://localhost/health -Method GET
       Start-Sleep -Seconds 2
   }
   ```

3. **Check for Memory Growth**:
   ```powershell
   # Before and after comparison
   $before = (Get-Process python*).WS | Measure-Object -Sum
   
   # Perform 10 voice interactions
   
   $after = (Get-Process python*).WS | Measure-Object -Sum
   $growth = ($after.Sum - $before.Sum) / 1MB
   
   Write-Host "Memory growth: $([math]::Round($growth, 2)) MB"
   # Should be < 100MB for 10 interactions
   ```

#### 🔴 Memory Leak Indicators

1. **Steadily increasing memory** without user activity
2. **Memory not released** after completing requests
3. **Process memory > 2GB** after moderate use

#### 🛠️ Memory Leak Prevention

**In backend.py** (already implemented):

```python
# ✅ Proper file cleanup
with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
    tmp_file.write(audio_data)
    tmp_path = tmp_file.name

# Process file...

# ✅ Cleanup
os.unlink(tmp_path)  # Properly implemented
```

```python
# ✅ BytesIO cleanup
wav_io = io.BytesIO()
sf.write(wav_io, audio_array, sample_rate, format='WAV')
wav_io.seek(0)
audio_bytes = wav_io.read()
wav_io.close()  # Explicit close
```

**Additional safeguards**:

```python
# Add to backend.py if memory issues occur

import gc

# After processing large audio buffers
gc.collect()  # Force garbage collection

# Limit audio file size
MAX_AUDIO_SIZE = 10 * 1024 * 1024  # 10MB
if len(audio_data) > MAX_AUDIO_SIZE:
    raise HTTPException(status_code=413, detail="Audio file too large")
```

**Monitoring Script** (create `monitor_memory.ps1`):

```powershell
$logFile = "memory_log.txt"

while ($true) {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $processes = Get-Process python* -ErrorAction SilentlyContinue
    
    foreach ($proc in $processes) {
        $memMB = [math]::Round($proc.WS / 1MB, 2)
        "$timestamp | PID: $($proc.Id) | Memory: $memMB MB" | 
            Add-Content $logFile
        
        # Alert if memory exceeds threshold
        if ($memMB -gt 2000) {
            Write-Host "⚠️ WARNING: Process $($proc.Id) using $memMB MB" -ForegroundColor Red
        }
    }
    
    Start-Sleep -Seconds 60
}
```

---

## 🔌 WebSocket Stability

### Connection Stability Verification

#### ✅ Verification Steps

1. **Test WebSocket Connection**:
   ```powershell
   # Use wscat tool
   npm install -g wscat
   
   # Connect to WebSocket endpoint
   wscat -c ws://localhost/ws/voice
   ```

2. **Long-Duration Test**:
   ```powershell
   # Monitor WebSocket for 1 hour
   $startTime = Get-Date
   $client = New-Object System.Net.WebSockets.ClientWebSocket
   $uri = [System.Uri]"ws://localhost/ws/voice"
   
   $client.ConnectAsync($uri, [System.Threading.CancellationToken]::None).Wait()
   
   while (((Get-Date) - $startTime).TotalMinutes -lt 60) {
       if ($client.State -ne 'Open') {
           Write-Host "Connection lost after $((Get-Date) - $startTime)" -ForegroundColor Red
           break
       }
       Start-Sleep -Seconds 10
   }
   ```

3. **Connection Pool Check**:
   ```powershell
   # Check active WebSocket connections
   Get-NetTCPConnection -State Established | 
       Where-Object LocalPort -in 80,8501 | 
       Measure-Object | 
       Select-Object Count
   ```

#### 🔴 Common Issues

**Issue 1: Connection drops after timeout**
- **Solution**: Increase timeout in nginx.conf
  ```nginx
  location /ws/ {
      proxy_read_timeout 3600s;  # 1 hour
      proxy_send_timeout 3600s;
  }
  ```

**Issue 2: Connection refused under load**
- **Solution**: Increase worker connections
  ```nginx
  events {
      worker_connections 2048;  # Increase from 1024
  }
  ```

**Issue 3: Ping/Pong timeout**
- **Solution**: Implement keep-alive in backend.py
  ```python
  @app.websocket("/ws/voice")
  async def websocket_voice_endpoint(websocket: WebSocket):
      await websocket.accept()
      
      # Send periodic ping
      async def keep_alive():
          while True:
              await asyncio.sleep(30)
              await websocket.send_json({"type": "ping"})
      
      asyncio.create_task(keep_alive())
      
      # ... rest of handler
  ```

#### 🛠️ Stability Improvements

**Add connection recovery in ui.py**:

```python
# Add to Streamlit UI for production use
import websocket
import json

def ws_connect_with_retry(url, max_retries=3):
    """Connect to WebSocket with retry logic"""
    for attempt in range(max_retries):
        try:
            ws = websocket.WebSocket()
            ws.connect(url, timeout=10)
            return ws
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                raise e
```

**Monitor WebSocket health**:

```powershell
# Create ws_monitor.ps1
$logFile = "websocket_log.txt"

while ($true) {
    $connections = Get-NetTCPConnection -State Established | 
        Where-Object LocalPort -eq 80
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp | Active WS Connections: $($connections.Count)" | 
        Add-Content $logFile
    
    Start-Sleep -Seconds 30
}
```

---

## 👥 Concurrent User Safety

### Multi-User Testing

#### ✅ Verification Steps

1. **Simulate Concurrent Users**:
   ```powershell
   # Test script: concurrent_test.ps1
   $jobs = @()
   
   for ($i = 1; $i -le 5; $i++) {
       $job = Start-Job -ScriptBlock {
           param($userId)
           
           $uri = "http://localhost/health"
           $response = Invoke-WebRequest -Uri $uri -Method GET
           
           Write-Output "User $userId : $($response.StatusCode)"
       } -ArgumentList $i
       
       $jobs += $job
   }
   
   # Wait for all jobs
   $jobs | Wait-Job | Receive-Job
   $jobs | Remove-Job
   ```

2. **Load Test with Multiple Voice Requests**:
   ```powershell
   # Requires test audio file: test.wav
   
   $jobs = @()
   for ($i = 1; $i -le 3; $i++) {
       $job = Start-Job -ScriptBlock {
           param($userId)
           
           $uri = "http://localhost/api/transcribe"
           $audioData = [System.IO.File]::ReadAllBytes("test.wav")
           
           $boundary = [System.Guid]::NewGuid().ToString()
           $headers = @{
               "Content-Type" = "multipart/form-data; boundary=$boundary"
           }
           
           # Create multipart content
           # ... (simplified for example)
           
           Write-Output "User $userId completed"
       } -ArgumentList $i
       
       $jobs += $job
       Start-Sleep -Milliseconds 500  # Stagger requests
   }
   
   $jobs | Wait-Job | Receive-Job
   ```

3. **Monitor Resource Contention**:
   ```powershell
   # During load test, monitor CPU
   Get-Counter '\Processor(_Total)\% Processor Time' -SampleInterval 1 -MaxSamples 30
   ```

#### 🔴 Concurrency Issues

**Issue 1: Model access contention**
- **Status**: ✅ HANDLED - Models loaded once globally
- **Verification**:
  ```python
  # In backend.py - models are global singletons
  whisper_model: Optional[WhisperModel] = None  # Shared across requests
  piper_voice = None  # Shared across requests
  ```

**Issue 2: Temporary file conflicts**
- **Status**: ✅ HANDLED - Uses unique temp files
- **Verification**:
  ```python
  # Each request gets unique temp file
  with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
      # Unique filename per request
  ```

**Issue 3: Thread pool exhaustion**
- **Status**: ✅ HANDLED - Async with thread pool executor
- **Verification**:
  ```python
  # Non-blocking execution
  loop = asyncio.get_event_loop()
  result = await loop.run_in_executor(None, blocking_function)
  ```

#### 🛠️ Concurrency Safeguards

**Verify Thread Safety**:

```powershell
# Add to backend.py for monitoring
import threading

@app.middleware("http")
async def log_requests(request: Request, call_next):
    thread_id = threading.current_thread().ident
    logger.info(f"Request {request.url.path} on thread {thread_id}")
    response = await call_next(request)
    return response
```

**Add Rate Limiting** (for production):

```python
# Add to backend.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/api/voice-chat-complete")
@limiter.limit("10/minute")  # Max 10 requests per minute per IP
async def voice_chat_complete_endpoint(request: Request, audio: UploadFile = File(...)):
    # ... existing code
```

**Add Request Queuing** (for resource protection):

```python
# Add to backend.py
from asyncio import Semaphore

# Limit concurrent model inference
inference_semaphore = Semaphore(3)  # Max 3 concurrent inferences

async def transcribe_audio(audio_data: bytes) -> str:
    async with inference_semaphore:
        # Only 3 transcriptions at a time
        # ... existing transcription code
```

---

## 📊 Comprehensive Health Check Script

Create `health_check.ps1`:

```powershell
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "🏥 AI Voice Agent - Health Check" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Firewall Rules
Write-Host "1️⃣ Checking Firewall Rules..." -ForegroundColor Yellow
$fwRules = Get-NetFirewallRule -DisplayName "AI Voice Agent*" -ErrorAction SilentlyContinue
if ($fwRules -and $fwRules.Enabled) {
    Write-Host "   ✅ Firewall rules active" -ForegroundColor Green
} else {
    Write-Host "   ❌ Firewall rules missing or disabled" -ForegroundColor Red
}

# 2. Port Availability
Write-Host "2️⃣ Checking Port 80..." -ForegroundColor Yellow
$port80 = Get-NetTCPConnection -LocalPort 80 -ErrorAction SilentlyContinue
if ($port80) {
    $proc = Get-Process -Id $port80.OwningProcess
    Write-Host "   ✅ Port 80 in use by: $($proc.ProcessName)" -ForegroundColor Green
} else {
    Write-Host "   ❌ Port 80 not in use" -ForegroundColor Red
}

# 3. Memory Usage
Write-Host "3️⃣ Checking Memory Usage..." -ForegroundColor Yellow
$pythonProcs = Get-Process python* -ErrorAction SilentlyContinue
if ($pythonProcs) {
    $totalMemMB = ($pythonProcs | Measure-Object -Property WS -Sum).Sum / 1MB
    Write-Host "   📊 Python processes using: $([math]::Round($totalMemMB, 2)) MB" -ForegroundColor Cyan
    
    if ($totalMemMB -lt 2000) {
        Write-Host "   ✅ Memory usage normal" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️ High memory usage" -ForegroundColor Yellow
    }
}

# 4. WebSocket Connections
Write-Host "4️⃣ Checking WebSocket Connections..." -ForegroundColor Yellow
$wsConnections = Get-NetTCPConnection -State Established |
    Where-Object LocalPort -in 80,8501
Write-Host "   📊 Active connections: $($wsConnections.Count)" -ForegroundColor Cyan

# 5. Backend Health
Write-Host "5️⃣ Checking Backend API..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost/health" -Method GET -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "   ✅ Backend API healthy" -ForegroundColor Green
    }
} catch {
    Write-Host "   ❌ Backend API not responding" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "Health check complete" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan
```

---

## ✅ Production Readiness Checklist

- [ ] Windows Firewall rules configured and tested
- [ ] Port 80 conflict resolution verified
- [ ] Memory leak testing completed (20+ requests)
- [ ] WebSocket stability tested (1+ hour)
- [ ] Concurrent user testing completed (3-5 users)
- [ ] Rate limiting implemented
- [ ] Request queuing configured
- [ ] Health monitoring script created
- [ ] Log rotation configured
- [ ] Backup and recovery plan documented
- [ ] Security audit completed
- [ ] Performance benchmarks recorded

---

**Last Updated**: Document creation date  
**Next Review**: Monthly or after major updates
