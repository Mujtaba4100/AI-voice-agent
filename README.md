# 🎤 AI Voice Agent - Local CPU-Based System

<div align="center">

**Complete AI voice conversation system running locally on Windows**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.31-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

</div>

---

## 🌟 Features

- **🎙️ Speech Recognition**: Faster-Whisper (CPU-optimized) for real-time speech-to-text
- **🤖 AI Responses**: Google Gemini 1.5 Flash for intelligent conversation
- **🔊 Text-to-Speech**: Piper TTS (ONNX) for natural voice synthesis
- **⚡ High Performance**: Async FastAPI backend with multi-worker support
- **🌐 Web Interface**: Clean Streamlit UI with microphone recording
- **🔒 Local Processing**: All AI inference runs on CPU (no GPU required)
- **🚀 Production Ready**: Nginx reverse proxy with load balancing
- **🪟 Windows Optimized**: Full support for Windows 10/11

---

## 🏗️ Architecture

```
┌─────────────┐
│   Browser   │
│ (Port 80)   │
└──────┬──────┘
       │
       v
┌─────────────────┐
│     Nginx       │
│  (Port 80)      │
│  Load Balancer  │
└────┬───────┬────┘
     │       │
     v       v
┌─────────────────────────┐     ┌──────────────┐
│  Backend Workers        │     │  Streamlit   │
│  • Port 8000           │     │  UI          │
│  • Port 8001           │     │  (Port 8501) │
│  • Port 8002           │     └──────────────┘
│                         │
│  AI Components:         │
│  • Faster-Whisper (STT) │
│  • Gemini API (LLM)     │
│  • Piper TTS (TTS)      │
└─────────────────────────┘
```

---

## 📋 Requirements

### System Requirements
- **OS**: Windows 10/11 (64-bit)
- **CPU**: 4+ cores (Intel i5/Ryzen 5 or better)
- **RAM**: 8GB minimum (16GB recommended)
- **Storage**: 5GB free space
- **Internet**: For Gemini API calls

### Software Requirements
- Python 3.9, 3.10, or 3.11 (64-bit)
- Nginx for Windows
- FFmpeg (for audio processing)
- Google Gemini API key

---

## 🚀 Quick Start

### 1. Clone or Download Project

```powershell
cd C:\
git clone <repository-url> AIVoiceAgent
# Or extract downloaded ZIP to C:\AIVoiceAgent
```

### 2. Install Python Dependencies

```powershell
cd C:\AIVoiceAgent

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install --upgrade pip
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```

### 3. Download AI Models

```powershell
# Option 1: Python script
python download_models.py

# Option 2: PowerShell script
.\download_models.ps1
```

### 4. Set Up Gemini API Key

```powershell
# Set environment variable (replace with your key)
$env:GEMINI_API_KEY = "your-gemini-api-key-here"

# Or add to system environment variables permanently
```

### 5. Install and Configure Nginx

```powershell
# Download Nginx from http://nginx.org/en/download.html
# Extract to C:\nginx

# Copy configuration file
Copy-Item nginx.conf C:\nginx\conf\nginx.conf -Force

# Test configuration
cd C:\nginx
.\nginx.exe -t
```

### 6. Start All Services

```powershell
# Option 1: Use startup script
.\scripts\start_all.ps1

# Option 2: Manual startup (see docs/INSTALLATION.md)
```

### 7. Open in Browser

Open your browser and navigate to:
```
http://localhost
```

---

## 📁 Project Structure

```
C:\AIVoiceAgent\
│
├── backend.py                 # FastAPI backend server
├── ui.py                      # Streamlit frontend
├── nginx.conf                 # Nginx configuration
├── requirements.txt           # Python dependencies
│
├── download_models.py         # Model downloader (Python)
├── download_models.ps1        # Model downloader (PowerShell)
│
├── models/                    # AI models directory
│   └── piper/                 # Piper TTS models
│       ├── en_US-lessac-medium.onnx
│       └── en_US-lessac-medium.onnx.json
│
├── docs/                      # Documentation
│   ├── INSTALLATION.md        # Complete installation guide
│   ├── SECURITY_CHECKLIST.md  # Security and stability guide
│   └── PORT_FORWARDING.md     # External access guide
│
└── scripts/                   # Helper scripts
    ├── start_all.ps1          # Start all services
    ├── stop_all.ps1           # Stop all services
    └── setup_firewall.ps1     # Configure Windows Firewall
```

---

## 🎯 Usage

### Recording and Conversing

1. **Click "🎤 Start Recording"**
2. **Speak your question** (clearly, 2-10 seconds)
3. **Wait for processing**:
   - Speech-to-text transcription
   - AI response generation
   - Text-to-speech synthesis
4. **Listen to response** (plays automatically)
5. **View conversation history** below

### API Endpoints

The backend provides several REST API endpoints:

```http
GET  /                          # Health check
GET  /health                    # Detailed health status
POST /api/transcribe            # Speech-to-text only
POST /api/chat                  # Text-to-text (LLM)
POST /api/synthesize            # Text-to-speech only
POST /api/voice-chat            # Complete pipeline (no audio return)
POST /api/voice-chat-complete   # Complete pipeline (with audio)
WS   /ws/voice                  # WebSocket for streaming
```

---

## ⚙️ Configuration

### Backend Configuration

Edit `backend.py` to customize:

```python
# Whisper model size (tiny/base/small/medium)
WHISPER_MODEL_NAME = "tiny"  # Faster, less accurate
# or
WHISPER_MODEL_NAME = "base"  # Balanced

# System prompt for AI assistant
SYSTEM_PROMPT = """Your custom system prompt here"""

# Model paths
PIPER_MODEL_PATH = MODELS_DIR / "piper" / "en_US-lessac-medium.onnx"
```

### Nginx Configuration

Edit `nginx.conf` to customize:

- Number of backend workers
- Port numbers
- Timeout values
- Buffer sizes

### Streamlit Configuration

Edit `ui.py` to customize:

- Recording duration
- API base URL
- UI theme and layout

---

## 🔧 Troubleshooting

### Common Issues

**Issue: Backend fails to start**
- Check GEMINI_API_KEY is set
- Verify models are downloaded
- Check port availability (8000-8002)

**Issue: No audio recording**
- Check microphone permissions in Windows Settings
- Verify browser has microphone access
- Test microphone in Windows Sound settings

**Issue: Nginx won't start**
- Port 80 might be in use (stop IIS: `iisreset /stop`)
- Check nginx.conf syntax: `nginx.exe -t`
- Run as Administrator if needed

**Issue: Slow performance**
- Use smaller Whisper model (tiny)
- Reduce backend workers (1-2 instead of 3)
- Close other resource-intensive applications

See [`docs/INSTALLATION.md`](docs/INSTALLATION.md) for detailed troubleshooting.

---

## 🔒 Security

### For Local Use Only

This system is designed for local use. For production deployment:

- ✅ Enable HTTPS/TLS
- ✅ Add authentication (OAuth2, JWT)
- ✅ Implement rate limiting
- ✅ Add input validation
- ✅ Set up proper logging
- ✅ Use environment variables for secrets
- ✅ Regular security updates

See [`docs/SECURITY_CHECKLIST.md`](docs/SECURITY_CHECKLIST.md) for details.

---

## 🌐 External Access

To access from outside your local network:

1. Configure Windows Firewall (port 80)
2. Set up router port forwarding
3. Use dynamic DNS for stable address
4. Consider security implications

See [`docs/PORT_FORWARDING.md`](docs/PORT_FORWARDING.md) for step-by-step guide.

---

## 📊 Performance

### Benchmarks (Intel Core i7, 16GB RAM)

| Model      | Transcription Time | Response Generation | TTS Time | Total Time |
|------------|-------------------|---------------------|----------|------------|
| Tiny       | 0.5-1.0s          | 1.0-2.0s           | 0.5-1.0s | 2-4s       |
| Base       | 1.0-2.0s          | 1.0-2.0s           | 0.5-1.0s | 2.5-5s     |
| Small      | 2.0-4.0s          | 1.0-2.0s           | 0.5-1.0s | 3.5-7s     |

*Times for 5-second audio input*

### Optimization Tips

1. **Use "tiny" Whisper model** for fastest transcription
2. **Run 2 backend workers** instead of 3 (saves RAM)
3. **Use lower-quality Piper voice** (lessac-low vs. lessac-medium)
4. **Close browser tabs** to free up resources
5. **Disable antivirus real-time scanning** for project directory

---

## 🛠️ Development

### Running in Development Mode

```powershell
# Backend with auto-reload
uvicorn backend:app --reload --port 8000

# Streamlit with auto-reload (automatic)
streamlit run ui.py
```

### Testing

```powershell
# Test backend endpoints
python -m pytest tests/

# Manual API testing
Invoke-WebRequest -Uri http://localhost:8000/health -Method GET
```

---

## 📚 Documentation

- [`docs/INSTALLATION.md`](docs/INSTALLATION.md) - Complete installation guide
- [`docs/SECURITY_CHECKLIST.md`](docs/SECURITY_CHECKLIST.md) - Security and stability checks
- [`docs/PORT_FORWARDING.md`](docs/PORT_FORWARDING.md) - External access setup

---

## 🤝 Contributing

This is a production-ready reference implementation. Feel free to:

- Fork and customize for your needs
- Report issues and bugs
- Suggest improvements
- Share your modifications

---

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.

---

## 🙏 Acknowledgments

Built with these amazing open-source projects:

- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [Streamlit](https://streamlit.io/) - Data app framework
- [Faster-Whisper](https://github.com/guillaumekln/faster-whisper) - Optimized Whisper
- [Piper TTS](https://github.com/rhasspy/piper) - Fast neural TTS
- [Google Gemini](https://ai.google.dev/) - AI language model
- [Nginx](https://nginx.org/) - Web server and reverse proxy

---

## 📞 Support

For issues and questions:

1. Check [`docs/INSTALLATION.md`](docs/INSTALLATION.md) troubleshooting section
2. Review existing GitHub issues
3. Create a new issue with:
   - System specifications
   - Error messages
   - Steps to reproduce

---

<div align="center">

**Made with ❤️ for the AI community**

⭐ Star this repo if you find it useful!

</div>
