"""
AI Voice Agent Backend Server
FastAPI-based async server for voice conversation system
Supports: Faster-Whisper STT, Google Gemini LLM, Piper TTS
Optimized for CPU inference on Windows 10/11
"""

import os
import io
import time
import logging
import asyncio
import tempfile
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

import torch
import numpy as np
from fastapi import FastAPI, File, UploadFile, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import tts_service
import google.generativeai as genai
from faster_whisper import WhisperModel
import soundfile as sf

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# GLOBAL CONFIGURATION
# ============================================================================

# Model paths
MODELS_DIR = Path("models")
WHISPER_MODEL_NAME = "tiny"  # Options: tiny, base, small, medium, large

# API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logger.warning("GEMINI_API_KEY not set. LLM functionality will be limited.")

# System prompt for LLM
SYSTEM_PROMPT = """You are a helpful AI voice assistant. Answer user questions clearly and concisely.
Use counterfactual thinking to provide well-reasoned responses. Keep answers brief and conversational 
since this is a voice interaction. Aim for 2-3 sentences unless more detail is specifically requested."""

# Global model instances (loaded once, reused across requests)
whisper_model: Optional[WhisperModel] = None

# ============================================================================
# MODEL INITIALIZATION
# ============================================================================

def load_whisper_model():
    """
    Load Faster-Whisper model optimized for CPU inference.
    Uses INT8 quantization for faster processing.
    """
    global whisper_model
    try:
        logger.info(f"Loading Whisper model: {WHISPER_MODEL_NAME}")
        # CPU-optimized settings: int8 quantization, 4 threads
        whisper_model = WhisperModel(
            WHISPER_MODEL_NAME,
            device="cpu",
            compute_type="int8",
            cpu_threads=4,
            num_workers=1
        )
        logger.info("Whisper model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load Whisper model: {e}")
        raise


# Piper TTS now uses subprocess-based approach via tts_service.py
# No need to load Python package models


def initialize_gemini():
    """Configure Google Gemini API client."""
    if GEMINI_API_KEY:
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            logger.info("Gemini API configured successfully")
        except Exception as e:
            logger.error(f"Failed to configure Gemini API: {e}")
            raise
    else:
        logger.warning("Gemini API not configured - no API key provided")


# ============================================================================
# LIFESPAN MANAGEMENT
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle.
    Load models on startup, cleanup on shutdown.
    """
    logger.info("Starting AI Voice Agent Backend...")
    
    # Startup: Load all models into memory
    try:
        load_whisper_model()
        initialize_gemini()
        logger.info("All models loaded successfully")
    except Exception as e:
        logger.error(f"Failed to initialize models: {e}")
        raise
    
    yield
    
    # Shutdown: Cleanup resources
    logger.info("Shutting down AI Voice Agent Backend...")
    global whisper_model
    whisper_model = None


# ============================================================================
# FASTAPI APP INITIALIZATION
# ============================================================================

app = FastAPI(
    title="AI Voice Agent API",
    description="CPU-optimized voice conversation system with STT, LLM, and TTS",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class TextRequest(BaseModel):
    text: str

class TextResponse(BaseModel):
    text: str
    processing_time: float

class VoiceResponse(BaseModel):
    transcription: str
    llm_response: str
    processing_time: float

# ============================================================================
# CORE PROCESSING FUNCTIONS
# ============================================================================

async def transcribe_audio(audio_data: bytes) -> str:
    """
    Transcribe audio using Faster-Whisper.
    Runs in thread pool to avoid blocking async loop.
    
    Args:
        audio_data: Raw audio bytes (WAV format)
        
    Returns:
        Transcribed text
    """
    if whisper_model is None:
        raise HTTPException(status_code=503, detail="Whisper model not loaded")
    
    try:
        # Save audio to temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            tmp_file.write(audio_data)
            tmp_path = tmp_file.name
        
        # Run transcription in thread pool (blocking operation)
        loop = asyncio.get_event_loop()
        segments, info = await loop.run_in_executor(
            None,
            lambda: whisper_model.transcribe(tmp_path, beam_size=1, language="en")
        )
        
        # Extract text from segments
        transcription = " ".join([segment.text for segment in segments])
        
        # Cleanup temporary file
        os.unlink(tmp_path)
        
        logger.info(f"Transcription: {transcription}")
        return transcription.strip()
        
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


async def generate_llm_response(user_text: str) -> str:
    """
    Generate response using Google Gemini API.
    
    Args:
        user_text: User's input text
        
    Returns:
        AI-generated response text
    """
    if not GEMINI_API_KEY:
        return "I'm sorry, the AI service is not configured. Please set GEMINI_API_KEY."
    
    try:
        # Use Gemini 1.5 Flash for fast responses
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Combine system prompt with user input
        full_prompt = f"{SYSTEM_PROMPT}\n\nUser: {user_text}\n\nAssistant:"
        
        # Generate response (async API call)
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: model.generate_content(full_prompt)
        )
        
        ai_response = response.text.strip()
        logger.info(f"LLM Response: {ai_response}")
        return ai_response
        
    except Exception as e:
        logger.error(f"LLM generation error: {e}")
        return "I'm sorry, I encountered an error processing your request."


async def synthesize_speech(text: str) -> bytes:
    """
    Convert text to speech using Piper TTS subprocess.
    
    Args:
        text: Text to synthesize
        
    Returns:
        WAV audio bytes
    """
    try:
        # Use subprocess-based TTS service
        loop = asyncio.get_event_loop()
        output_file = await loop.run_in_executor(
            None,
            lambda: tts_service.speak(text)
        )
        
        # Read the generated file
        with open(output_file, "rb") as f:
            audio_data = f.read()
        
        # Clean up temp file
        try:
            Path(output_file).unlink()
        except Exception:
            pass
        
        logger.info(f"Synthesized {len(audio_data)} bytes of audio")
        return audio_data
        
    except Exception as e:
        logger.error(f"TTS error: {e}")
        raise HTTPException(status_code=500, detail=f"Speech synthesis failed: {str(e)}")





# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "online",
        "service": "AI Voice Agent API",
        "version": "1.0.0",
        "models": {
            "whisper": "loaded" if whisper_model else "not loaded",
            "piper": "subprocess-based (native binary)",
            "gemini": "configured" if GEMINI_API_KEY else "not configured"
        }
    }


@app.get("/health")
async def health_check():
    """Detailed health check for monitoring."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "models_loaded": {
            "whisper": whisper_model is not None,
            "piper": "subprocess",
            "gemini": GEMINI_API_KEY is not None
        }
    }


@app.post("/api/transcribe", response_model=TextResponse)
async def transcribe_endpoint(audio: UploadFile = File(...)):
    """
    Transcribe audio file to text.
    
    Args:
        audio: Audio file upload (WAV format preferred)
        
    Returns:
        Transcribed text and processing time
    """
    start_time = time.time()
    
    try:
        # Read audio file
        audio_data = await audio.read()
        
        # Transcribe
        transcription = await transcribe_audio(audio_data)
        
        processing_time = time.time() - start_time
        
        return TextResponse(
            text=transcription,
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Transcription endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat", response_model=TextResponse)
async def chat_endpoint(request: TextRequest):
    """
    Generate LLM response from text input.
    
    Args:
        request: Text input from user
        
    Returns:
        AI response and processing time
    """
    start_time = time.time()
    
    try:
        response = await generate_llm_response(request.text)
        processing_time = time.time() - start_time
        
        return TextResponse(
            text=response,
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/synthesize")
async def synthesize_endpoint(request: TextRequest):
    """
    Convert text to speech.
    
    Args:
        request: Text to synthesize
        
    Returns:
        WAV audio file
    """
    try:
        audio_data = await synthesize_speech(request.text)
        
        # Return audio as streaming response
        return StreamingResponse(
            io.BytesIO(audio_data),
            media_type="audio/wav",
            headers={
                "Content-Disposition": "attachment; filename=speech.wav"
            }
        )
        
    except Exception as e:
        logger.error(f"Synthesize endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tts")
async def tts_endpoint(request: TextRequest):
    """Simple TTS endpoint that uses the external Piper binary via subprocess.

    Returns the generated WAV file as an attachment.
    """
    try:
        # Create a temporary output file and call the reusable TTS service
        import tempfile, io
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp_path = tmp.name

        # Call the subprocess-based Piper wrapper
        out_file = tts_service.speak(request.text, output_path=tmp_path)

        # Read bytes, remove temp file, and return streaming response
        with open(out_file, "rb") as f:
            audio_bytes = f.read()

        try:
            Path(out_file).unlink()
        except Exception:
            pass

        return StreamingResponse(
            io.BytesIO(audio_bytes),
            media_type="audio/wav",
            headers={"Content-Disposition": "attachment; filename=speech.wav"},
        )

    except Exception as e:
        logger.error(f"/tts endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/voice-chat", response_model=VoiceResponse)
async def voice_chat_endpoint(audio: UploadFile = File(...)):
    """
    Complete voice conversation pipeline:
    1. Speech to Text (Whisper)
    2. LLM Response (Gemini)
    3. Text to Speech (Piper)
    
    Args:
        audio: Audio file from user
        
    Returns:
        Transcription, LLM response, and processing time
    """
    start_time = time.time()
    
    try:
        # Step 1: Transcribe audio
        audio_data = await audio.read()
        transcription = await transcribe_audio(audio_data)
        
        # Step 2: Generate LLM response
        llm_response = await generate_llm_response(transcription)
        
        # Step 3: Synthesize speech (handled by separate endpoint to reduce response time)
        # Client should call /api/synthesize separately with the LLM response
        
        processing_time = time.time() - start_time
        
        return VoiceResponse(
            transcription=transcription,
            llm_response=llm_response,
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Voice chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/voice-chat-complete")
async def voice_chat_complete_endpoint(audio: UploadFile = File(...)):
    """
    Complete voice conversation with audio response.
    Returns both JSON metadata and allows fetching audio.
    
    Args:
        audio: Audio file from user
        
    Returns:
        JSON with transcription, response text, and audio data URL
    """
    start_time = time.time()
    
    try:
        # Step 1: Transcribe
        audio_data = await audio.read()
        transcription = await transcribe_audio(audio_data)
        
        # Step 2: Generate response
        llm_response = await generate_llm_response(transcription)
        
        # Step 3: Synthesize
        audio_response = await synthesize_speech(llm_response)
        
        processing_time = time.time() - start_time
        
        # Encode audio as base64 for JSON response
        import base64
        audio_base64 = base64.b64encode(audio_response).decode('utf-8')
        
        return JSONResponse({
            "transcription": transcription,
            "llm_response": llm_response,
            "audio_base64": audio_base64,
            "processing_time": processing_time
        })
        
    except Exception as e:
        logger.error(f"Voice chat complete endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# WEBSOCKET ENDPOINT (for real-time streaming)
# ============================================================================

@app.websocket("/ws/voice")
async def websocket_voice_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time voice conversation.
    
    Protocol:
    - Client sends: audio chunks (binary)
    - Server sends: JSON with transcription and response
    """
    await websocket.accept()
    logger.info("WebSocket connection established")
    
    try:
        while True:
            # Receive audio data
            audio_data = await websocket.receive_bytes()
            
            # Process voice input
            try:
                transcription = await transcribe_audio(audio_data)
                llm_response = await generate_llm_response(transcription)
                
                # Send text response
                await websocket.send_json({
                    "type": "text_response",
                    "transcription": transcription,
                    "response": llm_response
                })
                
                # Generate and send audio response
                audio_response = await synthesize_speech(llm_response)
                
                # Send audio in chunks to avoid memory issues
                chunk_size = 8192
                for i in range(0, len(audio_response), chunk_size):
                    chunk = audio_response[i:i+chunk_size]
                    await websocket.send_bytes(chunk)
                
                # Send completion message
                await websocket.send_json({
                    "type": "audio_complete"
                })
                
            except Exception as e:
                logger.error(f"WebSocket processing error: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })
                
    except WebSocketDisconnect:
        logger.info("WebSocket connection closed")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    # Run single worker for development
    uvicorn.run(
        "backend:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        workers=1
    )
