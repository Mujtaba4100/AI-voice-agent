# AI Voice Agent - Project Structure

## 📁 Complete File Tree

```
C:\AIVoiceAgent\
│
├── 📄 README.md                          # Main project documentation
├── 📄 .gitignore                         # Git ignore rules
│
├── 🐍 backend.py                         # FastAPI backend server (main)
├── 🎨 ui.py                              # Streamlit frontend (main)
├── ⚙️ nginx.conf                         # Nginx reverse proxy configuration
├── 📋 requirements.txt                   # Python dependencies
│
├── 🔽 download_models.py                 # Model downloader (Python)
├── 🔽 download_models.ps1                # Model downloader (PowerShell)
│
├── 📂 models/                            # AI models directory
│   ├── 📂 piper/                         # Piper TTS models
│   │   ├── en_US-lessac-medium.onnx      # Voice model (ONNX)
│   │   └── en_US-lessac-medium.onnx.json # Voice config
│   └── (Whisper models auto-cached)      # In user .cache folder
│
├── 📂 docs/                              # Documentation
│   ├── 📄 INSTALLATION.md                # Complete installation guide
│   ├── 📄 SECURITY_CHECKLIST.md          # Security & stability checks
│   └── 📄 PORT_FORWARDING.md             # External access guide
│
├── 📂 scripts/                           # Helper scripts
│   ├── ⚡ start_all.ps1                  # Start all services
│   ├── 🛑 stop_all.ps1                   # Stop all services
│   ├── 🔥 setup_firewall.ps1             # Configure Windows Firewall
│   ├── 🚀 quick_setup.ps1                # Automated setup
│   └── .running_pids.json                # Runtime PIDs (auto-generated)
│
├── 📂 logs/                              # Log files (auto-generated)
│   ├── backend.log
│   └── error.log
│
└── 📂 venv/                              # Python virtual environment
    └── (Python packages)
```

---

## 🏗️ System Architecture

### Component Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                        User's Browser                         │
│                      (http://localhost)                       │
└────────────────────────────┬─────────────────────────────────┘
                             │ HTTP Port 80
                             ▼
┌──────────────────────────────────────────────────────────────┐
│                    Nginx Reverse Proxy                        │
│                         (Port 80)                             │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  • Load balancing (round-robin)                        │  │
│  │  • WebSocket upgrade handling                          │  │
│  │  • Request buffering & timeouts                        │  │
│  └────────────────────────────────────────────────────────┘  │
└─────────┬────────────────────────────────────┬───────────────┘
          │                                    │
          │ API requests                       │ UI requests
          ▼                                    ▼
┌───────────────────────────┐    ┌────────────────────────────┐
│   Backend API Workers     │    │     Streamlit UI           │
│   (FastAPI + Uvicorn)     │    │     (Port 8501)            │
│                           │    │                            │
│  Worker 1: Port 8000      │    │  • Audio recording         │
│  Worker 2: Port 8001      │    │  • Response display        │
│  Worker 3: Port 8002      │    │  • Conversation history    │
│                           │    │  • Settings UI             │
│  ┌─────────────────────┐ │    └────────────────────────────┘
│  │  AI Processing      │ │
│  │  ─────────────────  │ │
│  │  1. Speech-to-Text  │ │
│  │     (Faster-Whisper)│ │
│  │                     │ │
│  │  2. LLM Response    │ │
│  │     (Gemini API)    │ │
│  │                     │ │
│  │  3. Text-to-Speech  │ │
│  │     (Piper TTS)     │ │
│  └─────────────────────┘ │
└───────────────────────────┘
```

### Data Flow

```
1. User clicks "Start Recording" in Streamlit UI
   │
   ▼
2. Browser captures microphone audio (5 seconds)
   │
   ▼
3. Audio sent to Nginx (http://localhost/api/voice-chat-complete)
   │
   ▼
4. Nginx forwards to available backend worker (8000/8001/8002)
   │
   ▼
5. Backend processes request:
   │
   ├─▶ a) Faster-Whisper transcribes audio → text
   │
   ├─▶ b) Gemini API generates response → text
   │
   └─▶ c) Piper TTS synthesizes speech → audio
   │
   ▼
6. Backend returns JSON with:
   - transcription: "user's spoken text"
   - llm_response: "AI's text response"
   - audio_base64: "encoded audio data"
   - processing_time: 2.5 seconds
   │
   ▼
7. Streamlit displays results and plays audio
   │
   ▼
8. User hears AI response through speakers
```

---

## 📦 Core Components

### 1. Backend API (backend.py)

**Purpose**: Process voice interactions through AI pipeline

**Key Features**:
- Async request handling (FastAPI)
- Model loading at startup (singleton pattern)
- Thread pool execution for CPU-bound tasks
- Multiple endpoints (transcribe, chat, synthesize, complete)
- WebSocket support for real-time streaming
- Comprehensive error handling
- Detailed logging

**Endpoints**:
```python
GET  /                          # Health check
GET  /health                    # Detailed status
POST /api/transcribe            # Audio → Text
POST /api/chat                  # Text → Text (LLM)
POST /api/synthesize            # Text → Audio
POST /api/voice-chat            # Audio → Transcription + Response
POST /api/voice-chat-complete   # Full pipeline with audio return
WS   /ws/voice                  # WebSocket streaming
```

**Dependencies**:
- FastAPI, Uvicorn (web framework)
- Faster-Whisper (speech recognition)
- Google Generative AI (LLM)
- Piper TTS (speech synthesis)
- PyTorch (CPU version)

### 2. Frontend UI (ui.py)

**Purpose**: User interface for voice interaction

**Key Features**:
- Microphone recording with sounddevice
- Visual feedback during processing
- Conversation history display
- Backend health monitoring
- Audio playback
- Configurable recording duration

**UI Components**:
- Main recording interface
- Conversation history (chat format)
- Settings sidebar
- Status indicators

**Dependencies**:
- Streamlit (UI framework)
- SoundDevice (audio recording)
- SoundFile (audio processing)
- Requests (API calls)

### 3. Nginx Reverse Proxy (nginx.conf)

**Purpose**: Route traffic and load balance requests

**Key Features**:
- Listen on port 80 (HTTP)
- Route frontend to Streamlit (8501)
- Load balance API across 3 workers
- WebSocket upgrade support
- Large file upload support (50MB)
- Timeout configuration (300s)
- Request buffering

**Routing Rules**:
```nginx
/                → Streamlit UI (8501)
/_stcore/stream  → Streamlit WebSocket
/api/*           → Backend workers (8000-8002)
/health          → Backend health check
/ws/*            → Backend WebSocket
```

### 4. AI Models

#### Faster-Whisper (Speech-to-Text)
- **Model**: tiny (default), base, small, medium
- **Size**: 39MB - 769MB
- **Location**: Auto-cached in user/.cache/huggingface/
- **Performance**: 0.5-2s per 5-second audio
- **Language**: English (configurable)

#### Google Gemini 1.5 Flash (LLM)
- **API**: Google Generative AI
- **Model**: gemini-1.5-flash
- **Response Time**: 1-2s
- **Cost**: Free tier available
- **Features**: Fast inference, good quality

#### Piper TTS (Text-to-Speech)
- **Model**: en_US-lessac-medium
- **Size**: ~63MB ONNX model
- **Location**: models/piper/
- **Performance**: 0.5-1s per response
- **Quality**: High-quality neural TTS

---

## 🔄 Deployment Scenarios

### Scenario 1: Development (Single Worker)

```powershell
# Terminal 1: Backend
python backend.py

# Terminal 2: Streamlit
streamlit run ui.py

# Access: http://localhost:8501
```

**Use Case**: Development, testing, debugging

### Scenario 2: Local Production (Multi-Worker)

```powershell
# Start all services with script
.\scripts\start_all.ps1

# Access: http://localhost
```

**Use Case**: Local use, 2-3 concurrent users

### Scenario 3: LAN Access (Network Sharing)

```powershell
# Start services
.\scripts\start_all.ps1

# Configure firewall
.\scripts\setup_firewall.ps1

# Access from other devices: http://192.168.1.100
```

**Use Case**: Multiple users on same network

### Scenario 4: Internet Access (Port Forwarding)

```powershell
# Start services
.\scripts\start_all.ps1

# Configure firewall
.\scripts\setup_firewall.ps1

# Configure router port forwarding (see docs/PORT_FORWARDING.md)

# Access: http://YOUR_PUBLIC_IP
```

**Use Case**: Remote access, external users

---

## 🛠️ Configuration Options

### Backend Configuration (backend.py)

```python
# Model selection
WHISPER_MODEL_NAME = "tiny"  # Change to: tiny, base, small, medium

# System prompt
SYSTEM_PROMPT = """Your custom AI assistant instructions"""

# Model paths
PIPER_MODEL_PATH = MODELS_DIR / "piper" / "en_US-lessac-medium.onnx"

# API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
```

### Nginx Configuration (nginx.conf)

```nginx
# Number of worker processes
worker_processes 4;  # Set to CPU cores

# Connection limits
worker_connections 1024;  # Max connections per worker

# Upload size
client_max_body_size 50M;  # Max upload size

# Timeouts
client_body_timeout 300;
proxy_read_timeout 300;
```

### Streamlit Configuration (ui.py)

```python
# Recording duration
recording_duration = st.slider("Duration", 2, 10, 5)

# API URL
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost/api")
```

---

## 🔐 Security Considerations

### Current Implementation (Local Use)

✅ Async processing (no blocking)  
✅ Temporary file cleanup  
✅ Error handling  
✅ Logging  
⚠️ No authentication  
⚠️ HTTP only (no HTTPS)  
⚠️ No rate limiting by default  

### Production Enhancements Needed

For public deployment:

1. **Add Authentication**:
   - OAuth2 / JWT tokens
   - API key validation
   - User sessions

2. **Enable HTTPS**:
   - SSL/TLS certificates
   - Let's Encrypt integration
   - Force HTTPS redirect

3. **Implement Rate Limiting**:
   - Per-IP request limits
   - Per-user quotas
   - DDoS protection

4. **Input Validation**:
   - File size limits
   - Content type validation
   - Sanitize inputs

5. **Monitoring & Logging**:
   - Access logs
   - Error tracking
   - Performance metrics

See `docs/SECURITY_CHECKLIST.md` for detailed checklist.

---

## 📊 Performance Characteristics

### Resource Usage (per worker)

| Component        | RAM Usage | CPU Usage | Notes                    |
|-----------------|-----------|-----------|--------------------------|
| Backend (idle)  | 500MB     | 0-1%      | Models loaded            |
| Backend (active)| 1-2GB     | 30-80%    | During inference         |
| Streamlit       | 200-300MB | 1-5%      | UI rendering             |
| Nginx           | 10-20MB   | 0-1%      | Very lightweight         |
| **Total**       | **2-4GB** | **30-80%**| For 3 workers + UI       |

### Response Times (Intel i7, 16GB RAM)

| Operation                | Time (tiny) | Time (base) |
|-------------------------|-------------|-------------|
| Speech-to-Text (5s)     | 0.5-1.0s    | 1.0-2.0s    |
| LLM Response            | 1.0-2.0s    | 1.0-2.0s    |
| Text-to-Speech          | 0.5-1.0s    | 0.5-1.0s    |
| **Total Pipeline**      | **2-4s**    | **2.5-5s**  |

### Concurrent Users

| Workers | Max Users | Recommendation      |
|---------|-----------|---------------------|
| 1       | 1-2       | Development only    |
| 2       | 2-3       | Home use            |
| 3       | 3-5       | Small team (default)|
| 4+      | 5-10      | Needs 32GB+ RAM     |

---

## 🔧 Maintenance

### Regular Tasks

**Daily**:
- Monitor system resources
- Check error logs

**Weekly**:
- Review access logs
- Check disk space
- Test voice pipeline

**Monthly**:
- Update Python packages
- Review security settings
- Backup configuration

**As Needed**:
- Download new models
- Update nginx config
- Adjust worker count

### Monitoring Commands

```powershell
# Check process status
Get-Process python*, nginx*

# View recent logs
Get-Content logs\backend.log -Tail 50

# Monitor resources
Get-Counter '\Processor(_Total)\% Processor Time'

# Check ports
Get-NetTCPConnection -LocalPort 80,8000,8001,8002,8501
```

---

## 📚 Additional Documentation

- **README.md**: Project overview and quick start
- **INSTALLATION.md**: Complete installation guide
- **SECURITY_CHECKLIST.md**: Security and stability verification
- **PORT_FORWARDING.md**: External access setup

---

## 🤝 Contributing

This is a reference implementation. Feel free to:

- Fork and customize
- Report issues
- Suggest improvements
- Share modifications

---

**Project Version**: 1.0.0  
**Created**: 2026  
**Platform**: Windows 10/11  
**Python**: 3.9-3.11  
**License**: MIT
