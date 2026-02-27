"""
AI Voice Agent - Streamlit Frontend
Interactive voice conversation interface with microphone recording
"""

import os
import io
import time
import base64
import requests
import streamlit as st
import sounddevice as sd
import soundfile as sf
import numpy as np
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================

# Backend API URL - defaults to direct backend connection
# If using Nginx proxy, set API_BASE_URL=http://localhost/api in .env
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api")

# Audio recording settings
SAMPLE_RATE = 16000  # 16kHz for Whisper
CHANNELS = 1  # Mono audio
DTYPE = np.int16  # 16-bit audio

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="AI Voice Agent",
    page_icon="🎤",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

if "is_recording" not in st.session_state:
    st.session_state.is_recording = False

if "audio_data" not in st.session_state:
    st.session_state.audio_data = None

if "processing" not in st.session_state:
    st.session_state.processing = False

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def check_backend_health():
    """
    Check if backend API is accessible.
    
    Returns:
        tuple: (is_healthy, status_message)
    """
    try:
        response = requests.get(f"{API_BASE_URL.replace('/api', '')}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return True, data
        else:
            return False, f"Backend returned status code {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "Cannot connect to backend. Make sure the server is running."
    except Exception as e:
        return False, f"Error checking backend: {str(e)}"


def record_audio(duration: int = 5) -> tuple:
    """
    Record audio from microphone.
    
    Args:
        duration: Recording duration in seconds
        
    Returns:
        tuple: (audio_array, sample_rate)
    """
    try:
        st.info(f"🎤 Recording for {duration} seconds... Speak now!")
        
        # Record audio
        audio_data = sd.rec(
            int(duration * SAMPLE_RATE),
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype=DTYPE
        )
        sd.wait()  # Wait until recording is finished
        
        st.success("✅ Recording complete!")
        return audio_data, SAMPLE_RATE
        
    except Exception as e:
        st.error(f"❌ Recording error: {str(e)}")
        return None, None


def audio_to_wav_bytes(audio_array: np.ndarray, sample_rate: int) -> bytes:
    """
    Convert numpy array to WAV bytes.
    
    Args:
        audio_array: Audio data as numpy array
        sample_rate: Sample rate in Hz
        
    Returns:
        WAV file as bytes
    """
    wav_io = io.BytesIO()
    sf.write(wav_io, audio_array, sample_rate, format='WAV')
    wav_io.seek(0)
    return wav_io.read()


def send_voice_message(audio_bytes: bytes) -> dict:
    """
    Send audio to backend for complete voice chat processing.
    
    Args:
        audio_bytes: WAV audio file bytes
        
    Returns:
        dict: Response with transcription and LLM response
    """
    try:
        files = {"audio": ("recording.wav", audio_bytes, "audio/wav")}
        
        response = requests.post(
            f"{API_BASE_URL}/voice-chat-complete",
            files=files,
            timeout=60  # Allow time for processing
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"❌ API error: {response.status_code}")
            return None
            
    except requests.exceptions.Timeout:
        st.error("❌ Request timeout. The server took too long to respond.")
        return None
    except Exception as e:
        st.error(f"❌ Error sending audio: {str(e)}")
        return None


def play_audio_from_base64(audio_base64: str):
    """
    Play audio from base64 encoded string.
    
    Args:
        audio_base64: Base64 encoded audio data
    """
    try:
        # Decode base64 audio
        audio_bytes = base64.b64decode(audio_base64)
        
        # Create audio player
        st.audio(audio_bytes, format="audio/wav")
        
    except Exception as e:
        st.error(f"❌ Error playing audio: {str(e)}")


def add_to_history(user_text: str, ai_text: str, audio_base64: str = None):
    """
    Add conversation to history.
    
    Args:
        user_text: User's input text
        ai_text: AI's response text
        audio_base64: Optional base64 encoded audio
    """
    st.session_state.conversation_history.append({
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "user": user_text,
        "ai": ai_text,
        "audio": audio_base64
    })


def display_conversation_history():
    """Display conversation history in chat format."""
    if not st.session_state.conversation_history:
        st.info("👋 Start a conversation by recording your voice!")
        return
    
    for idx, entry in enumerate(st.session_state.conversation_history):
        # User message
        with st.chat_message("user"):
            st.write(f"**[{entry['timestamp']}]** {entry['user']}")
        
        # AI response
        with st.chat_message("assistant"):
            st.write(f"**[{entry['timestamp']}]** {entry['ai']}")
            
            # Play audio response if available
            if entry.get("audio"):
                with st.expander("🔊 Play AI Response"):
                    play_audio_from_base64(entry["audio"])


# ============================================================================
# MAIN UI
# ============================================================================

def main():
    """Main application UI."""
    
    # Header
    st.title("🎤 AI Voice Agent")
    st.markdown("*Powered by Faster-Whisper, Google Gemini, and Piper TTS*")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Backend health check
        st.subheader("Backend Status")
        if st.button("🔄 Check Status"):
            with st.spinner("Checking backend..."):
                is_healthy, status = check_backend_health()
                
            if is_healthy:
                st.success("✅ Backend is online")
                with st.expander("View Details"):
                    st.json(status)
            else:
                st.error(f"❌ {status}")
        
        st.divider()
        
        # Recording settings
        st.subheader("Recording Settings")
        recording_duration = st.slider(
            "Recording Duration (seconds)",
            min_value=2,
            max_value=10,
            value=5,
            step=1
        )
        
        st.divider()
        
        # History management
        st.subheader("Conversation")
        if st.button("🗑️ Clear History"):
            st.session_state.conversation_history = []
            st.rerun()
        
        st.metric("Messages", len(st.session_state.conversation_history))
        
        st.divider()
        
        # API Configuration
        st.subheader("API Configuration")
        st.text_input(
            "API Base URL",
            value=API_BASE_URL,
            disabled=True,
            help="Configure via API_BASE_URL environment variable"
        )
        
        st.divider()
        
        # Info
        st.subheader("ℹ️ About")
        st.markdown("""
        **How to use:**
        1. Click the microphone button
        2. Speak your question
        3. Wait for AI response
        4. Listen to the audio response
        
        **Features:**
        - Real-time voice recording
        - Speech-to-text via Whisper
        - AI responses via Gemini
        - Text-to-speech via Piper
        """)
    
    # Main content area
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### 🎙️ Voice Input")
        
        # Recording button
        if not st.session_state.processing:
            if st.button("🎤 **Start Recording**", use_container_width=True, type="primary"):
                # Record audio
                audio_array, sample_rate = record_audio(recording_duration)
                
                if audio_array is not None:
                    st.session_state.audio_data = audio_to_wav_bytes(audio_array, sample_rate)
                    st.session_state.processing = True
                    st.rerun()
        
        else:
            st.info("⏳ Processing your message...")
            
            # Process the recorded audio
            if st.session_state.audio_data:
                with st.spinner("🔄 Transcribing, thinking, and generating response..."):
                    result = send_voice_message(st.session_state.audio_data)
                
                if result:
                    # Display results
                    st.success("✅ Response received!")
                    
                    # Show transcription
                    with st.expander("📝 Your message", expanded=True):
                        st.write(result.get("transcription", "N/A"))
                    
                    # Show AI response
                    with st.expander("🤖 AI Response", expanded=True):
                        st.write(result.get("llm_response", "N/A"))
                    
                    # Show processing time
                    st.caption(f"⏱️ Processing time: {result.get('processing_time', 0):.2f}s")
                    
                    # Play audio response
                    if result.get("audio_base64"):
                        st.markdown("### 🔊 Audio Response")
                        play_audio_from_base64(result["audio_base64"])
                    
                    # Add to history
                    add_to_history(
                        result.get("transcription", ""),
                        result.get("llm_response", ""),
                        result.get("audio_base64")
                    )
                
                # Reset processing state
                st.session_state.processing = False
                st.session_state.audio_data = None
                
                # Add button to continue
                if st.button("🎤 Record Another Message", use_container_width=True):
                    st.rerun()
    
    # Conversation history
    st.markdown("---")
    st.markdown("## 💬 Conversation History")
    display_conversation_history()
    
    # Footer
    st.markdown("---")
    st.caption("AI Voice Agent v1.0.0 | CPU-Optimized | Windows 10/11")


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"❌ Application error: {str(e)}")
        st.exception(e)
