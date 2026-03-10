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
import soundfile as sf
import numpy as np
from datetime import datetime, timedelta
import json

# Try to import sounddevice (may not be available in server environments)
try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False

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

# Medical Disclaimer for Health Information
MEDICAL_DISCLAIMER = """
⚠️ **IMPORTANT MEDICAL DISCLAIMER** ⚠️

This tool provides **general health information only** and is **NOT a substitute for professional medical advice, diagnosis, or treatment**.

**Always consult with a qualified healthcare professional** for:
- Any medical concerns or symptoms
- Proper diagnosis and treatment recommendations
- Questions about medications or medical procedures
- Emergency medical situations

**🚨 IN CASE OF EMERGENCY:** Call your local emergency number (911 in US/Canada, 999 in UK, 112 in EU) immediately.

This information is for **educational purposes only** and cannot replace professional medical judgment.
"""

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="AI Health Voice Agent",
    page_icon="🏥",
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

if "health_metrics" not in st.session_state:
    st.session_state.health_metrics = {
        "bmi_records": [],
        "bp_records": [],
        "temp_records": []
    }

if "symptoms_selected" not in st.session_state:
    st.session_state.symptoms_selected = []

# ============================================================================
# HEALTH DATA & CONSTANTS
# ============================================================================

# Symptom categories mapped to health conditions
SYMPTOM_DATABASE = {
    "Headache": ["Cold/Flu", "Fever", "Headache"],
    "Fever/Chills": ["Cold/Flu", "Fever"],
    "Runny/Stuffy Nose": ["Cold/Flu"],
    "Cough": ["Cold/Flu", "Cough"],
    "Sore Throat": ["Cold/Flu", "Sore Throat"],
    "Body Aches": ["Cold/Flu", "Fever", "Body Aches"],
    "Fatigue/Tiredness": ["Cold/Flu", "Fever", "Fatigue"],
    "Nausea/Vomiting": ["Nausea"],
    "Dizziness": ["Fever", "Headache"],
    "Loss of Appetite": ["Nausea", "Cold/Flu"]
}

# Body part to condition mapping
BODY_PARTS = {
    "Head": ["Headache", "Fever"],
    "Throat": ["Sore Throat", "Cold/Flu"],
    "Chest": ["Cough", "Cold/Flu"],
    "Stomach": ["Nausea"],
    "Muscles": ["Body Aches", "Fatigue"],
    "Whole Body": ["Fever", "Cold/Flu", "Fatigue"]
}

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
    if not SOUNDDEVICE_AVAILABLE:
        st.error("❌ Audio recording is not available in this environment (server/Docker). Use text input instead.")
        return None, None
    
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
# HEALTH FEATURES
# ============================================================================

def symptom_checker_tab():
    """Interactive symptom checker with health guidance."""
    st.subheader("🩺 Symptom Checker")
    
    st.info("Select your symptoms to get possible conditions and recommendations")
    
    # Multi-select symptoms
    symptoms = st.multiselect(
        "What symptoms are you experiencing?",
        options=list(SYMPTOM_DATABASE.keys()),
        help="Select all symptoms that apply"
    )
    
    if symptoms:
        st.markdown("### 📋 Possible Conditions")
        
        # Find matching conditions
        possible_conditions = set()
        for symptom in symptoms:
            possible_conditions.update(SYMPTOM_DATABASE[symptom])
        
        # Display conditions
        for condition in possible_conditions:
            with st.expander(f"🔍 {condition}", expanded=True):
                st.markdown(f"""
                **Common Symptoms:** Check your health guidelines for detailed info
                
                **Recommended Actions:**
                - Rest and stay hydrated
                - Monitor your symptoms
                - Over-the-counter relief as appropriate
                - Consult doctor if symptoms worsen
                
                **⚠️ See a doctor if:**
                - Symptoms persist > 3-5 days
                - High fever (>103°F/39.4°C)
                - Difficulty breathing
                - Severe pain
                """)
        
        # Severity assessment
        st.markdown("### 📊 Severity Assessment")
        severity = st.select_slider(
            "How would you rate your overall discomfort?",
            options=["Mild", "Moderate", "Significant", "Severe"],
            value="Mild"
        )
        
        if severity in ["Significant", "Severe"]:
            st.error("⚠️ **Your symptoms may require medical attention. Consider consulting a healthcare provider soon.**")
        else:
            st.success("✅ Your symptoms appear manageable with self-care. Monitor and seek help if they worsen.")
        
        # Ask AI button
        if st.button("🤖 Get AI Advice for These Symptoms", use_container_width=True):
            symptom_text = f"I have the following symptoms: {', '.join(symptoms)}. What should I do?"
            try:
                response = requests.post(
                    f"{API_BASE_URL}/chat",
                    json={"text": symptom_text},
                    timeout=60
                )
                if response.status_code == 200:
                    result = response.json()
                    st.markdown("### 🤖 AI Health Guidance")
                    st.write(result.get("text", ""))
            except Exception as e:
                st.error(f"Error: {str(e)}")
    else:
        st.info("👆 Select symptoms above to get started")


def health_metrics_tab():
    """Health metrics dashboard with BMI, BP, and temperature tracking."""
    st.subheader("📊 Health Metrics Dashboard")
    
    tabs = st.tabs(["BMI Calculator", "Blood Pressure Log", "Temperature Log"])
    
    # BMI Calculator Tab
    with tabs[0]:
        st.markdown("### 🧮 BMI Calculator")
        
        col1, col2 = st.columns(2)
        with col1:
            weight = st.number_input("Weight (kg)", min_value=20.0, max_value=300.0, value=70.0, step=0.5)
        with col2:
            height = st.number_input("Height (cm)", min_value=100.0, max_value=250.0, value=170.0, step=1.0)
        
        if st.button("Calculate BMI", use_container_width=True):
            bmi = weight / ((height / 100) ** 2)
            
            # Categorize BMI
            if bmi < 18.5:
                category = "Underweight"
                color = "blue"
            elif bmi < 25:
                category = "Normal weight"
                color = "green"
            elif bmi < 30:
                category = "Overweight"
                color = "orange"
            else:
                category = "Obese"
                color = "red"
            
            st.metric("Your BMI", f"{bmi:.1f}", category)
            st.markdown(f"**Category:** :{color}[{category}]")
            
            # Save to history
            st.session_state.health_metrics["bmi_records"].append({
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "weight": weight,
                "height": height,
                "bmi": round(bmi, 1),
                "category": category
            })
            
            st.success("✅ BMI recorded!")
        
        # Show history
        if st.session_state.health_metrics["bmi_records"]:
            st.markdown("#### 📈 BMI History")
            for record in st.session_state.health_metrics["bmi_records"][-5:]:
                st.caption(f"{record['date']}: BMI {record['bmi']} ({record['category']})")
    
    # Blood Pressure Log Tab
    with tabs[1]:
        st.markdown("### 🩺 Blood Pressure Tracker")
        
        col1, col2 = st.columns(2)
        with col1:
            systolic = st.number_input("Systolic (top number)", min_value=70, max_value=200, value=120, step=1)
        with col2:
            diastolic = st.number_input("Diastolic (bottom number)", min_value=40, max_value=130, value=80, step=1)
        
        if st.button("Log Blood Pressure", use_container_width=True):
            # Categorize BP
            if systolic < 120 and diastolic < 80:
                category = "Normal"
                color = "green"
            elif systolic < 130 and diastolic < 80:
                category = "Elevated"
                color = "orange"
            elif systolic < 140 or diastolic < 90:
                category = "High BP Stage 1"
                color = "red"
            else:
                category = "High BP Stage 2"
                color = "red"
            
            st.metric("Blood Pressure", f"{systolic}/{diastolic} mmHg", category)
            st.markdown(f"**Status:** :{color}[{category}]")
            
            if category != "Normal":
                st.warning("⚠️ Consider consulting your healthcare provider about your blood pressure.")
            
            # Save to history
            st.session_state.health_metrics["bp_records"].append({
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "systolic": systolic,
                "diastolic": diastolic,
                "category": category
            })
            
            st.success("✅ Blood pressure recorded!")
        
        # Show history
        if st.session_state.health_metrics["bp_records"]:
            st.markdown("#### 📈 BP History (Last 5)")
            for record in st.session_state.health_metrics["bp_records"][-5:]:
                st.caption(f"{record['date']}: {record['systolic']}/{record['diastolic']} mmHg ({record['category']})")
    
    # Temperature Log Tab
    with tabs[2]:
        st.markdown("### 🌡️ Temperature Tracker")
        
        temp_unit = st.radio("Unit", ["Fahrenheit (°F)", "Celsius (°C)"], horizontal=True)
        
        if "Fahrenheit" in temp_unit:
            temp = st.number_input("Temperature (°F)", min_value=95.0, max_value=108.0, value=98.6, step=0.1)
            temp_c = (temp - 32) * 5/9
            
            if temp < 97:
                status = "Low (Hypothermia risk)"
                color = "blue"
            elif temp < 100.4:
                status = "Normal"
                color = "green"
            elif temp < 103:
                status = "Fever (Mild)"
                color = "orange"
            else:
                status = "High Fever (Seek medical care)"
                color = "red"
        else:
            temp = st.number_input("Temperature (°C)", min_value=35.0, max_value=42.0, value=37.0, step=0.1)
            temp_c = temp
            
            if temp < 36:
                status = "Low (Hypothermia risk)"
                color = "blue"
            elif temp < 38:
                status = "Normal"
                color = "green"
            elif temp < 39.4:
                status = "Fever (Mild)"
                color = "orange"
            else:
                status = "High Fever (Seek medical care)"
                color = "red"
        
        if st.button("Log Temperature", use_container_width=True):
            st.metric("Temperature", f"{temp:.1f}°{'F' if 'Fahrenheit' in temp_unit else 'C'}", status)
            st.markdown(f"**Status:** :{color}[{status}]")
            
            if "High Fever" in status:
                st.error("🚨 High fever detected. Consider seeking medical attention.")
            
            # Save to history
            st.session_state.health_metrics["temp_records"].append({
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "temp_f": temp if "Fahrenheit" in temp_unit else round(temp * 9/5 + 32, 1),
                "temp_c": round(temp_c, 1),
                "status": status
            })
            
            st.success("✅ Temperature recorded!")
        
        # Show history
        if st.session_state.health_metrics["temp_records"]:
            st.markdown("#### 📈 Temperature History (Last 5)")
            for record in st.session_state.health_metrics["temp_records"][-5:]:
                st.caption(f"{record['date']}: {record['temp_f']}°F / {record['temp_c']}°C ({record['status']})")


def body_diagram_tab():
    """Interactive body diagram for pain location mapping."""
    st.subheader("🧍 Body Part Pain Mapper")
    
    st.info("Select the body part where you're experiencing pain or discomfort")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Body part selector
        body_part = st.selectbox(
            "Select Body Part:",
            options=list(BODY_PARTS.keys())
        )
        
        pain_level = st.slider(
            "Pain Level (1-10):",
            min_value=1,
            max_value=10,
            value=5,
            help="1 = Mild discomfort, 10 = Severe pain"
        )
        
        pain_type = st.radio(
            "Pain Type:",
            ["Aching", "Sharp/Stabbing", "Burning", "Throbbing", "Dull"],
            horizontal=True
        )
        
        duration = st.select_slider(
            "Duration:",
            options=["< 1 hour", "Few hours", "1 day", "2-3 days", "4-7 days", "> 1 week"]
        )
    
    with col2:
        # Simple body diagram (text-based for now)
        st.markdown("### 🧍 Body Reference")
        st.markdown("""
        ```
            HEAD
             |
        THROAT/NECK
             |
          CHEST
             |
         STOMACH
             |
        MUSCLES (ARMS/LEGS)
             |
        WHOLE BODY
        ```
        """)
    
    if st.button("🔍 Analyze Pain", use_container_width=True, type="primary"):
        st.markdown("### 🩺 Analysis Results")
        
        # Get possible conditions
        conditions = BODY_PARTS[body_part]
        
        st.markdown(f"**Location:** {body_part}")
        st.markdown(f"**Pain Level:** {pain_level}/10")
        st.markdown(f"**Type:** {pain_type}")
        st.markdown(f"**Duration:** {duration}")
        
        st.markdown("#### Possible Related Conditions:")
        for condition in conditions:
            st.write(f"• {condition}")
        
        # Recommendations based on pain level
        if pain_level >= 8 or duration in ["> 1 week", "4-7 days"]:
            st.error("⚠️ **Severe or persistent pain detected. Strongly recommend consulting a healthcare provider.**")
        elif pain_level >= 5:
            st.warning("⚠️ **Moderate pain. Monitor closely and consider medical advice if it worsens or persists.**")
        else:
            st.info("ℹ️ **Mild pain. Rest, basic care, and monitoring recommended.**")
        
        # Get AI recommendation
        query = f"I have {pain_type.lower()} pain in my {body_part.lower()} at level {pain_level}/10 for {duration}. What should I do?"
        try:
            response = requests.post(
                f"{API_BASE_URL}/chat",
                json={"text": query},
                timeout=60
            )
            if response.status_code == 200:
                result = response.json()
                st.markdown("#### 🤖 AI Recommendations:")
                st.write(result.get("text", ""))
        except Exception as e:
            st.error(f"Error getting AI advice: {str(e)}")


def export_health_report():
    """Generate downloadable health report (text format)."""
    st.subheader("📄 Export Health Report")
    
    if st.button("📥 Generate Report", use_container_width=True, type="primary"):
        report = "=" * 60 + "\n"
        report += "AI HEALTH VOICE AGENT - HEALTH REPORT\n"
        report += "=" * 60 + "\n\n"
        report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        report += "MEDICAL DISCLAIMER\n"
        report += "-" * 60 + "\n"
        report += "This report provides general health information only.\n"
        report += "NOT a substitute for professional medical advice.\n"
        report += "Always consult a healthcare professional for medical concerns.\n\n"
        
        # Health Metrics
        report += "HEALTH METRICS\n"
        report += "-" * 60 + "\n\n"
        
        if st.session_state.health_metrics["bmi_records"]:
            report += "BMI Records:\n"
            for record in st.session_state.health_metrics["bmi_records"]:
                report += f"  {record['date']}: BMI {record['bmi']} ({record['category']})\n"
            report += "\n"
        
        if st.session_state.health_metrics["bp_records"]:
            report += "Blood Pressure Records:\n"
            for record in st.session_state.health_metrics["bp_records"]:
                report += f"  {record['date']}: {record['systolic']}/{record['diastolic']} mmHg ({record['category']})\n"
            report += "\n"
        
        if st.session_state.health_metrics["temp_records"]:
            report += "Temperature Records:\n"
            for record in st.session_state.health_metrics["temp_records"]:
                report += f"  {record['date']}: {record['temp_f']}°F / {record['temp_c']}°C ({record['status']})\n"
            report += "\n"
        
        # Conversation History
        if st.session_state.conversation_history:
            report += "CONVERSATION HISTORY\n"
            report += "-" * 60 + "\n\n"
            for entry in st.session_state.conversation_history:
                report += f"[{entry['timestamp']}] USER: {entry['user']}\n"
                report += f"[{entry['timestamp']}] AI: {entry['ai']}\n\n"
        
        report += "=" * 60 + "\n"
        report += "End of Report\n"
        report += "=" * 60 + "\n"
        
        st.download_button(
            label="💾 Download Health Report (TXT)",
            data=report,
            file_name=f"health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            use_container_width=True
        )
        
        st.success("✅ Report generated! Click above to download.")


# ============================================================================
# MAIN UI
# ============================================================================

def main():
    """Main application UI."""
    
    # Header
    st.title("� AI Health Voice Agent")
    st.markdown("*Your AI Health Assistant - Powered by Faster-Whisper, Google Gemini, Piper TTS*")
    
    # Compact Medical Disclaimer at Top
    with st.expander("⚠️ Medical Disclaimer - Please Read"):
        st.warning("""
        **IMPORTANT:** This provides general health information only. NOT a substitute for professional medical advice.  
        Always consult a healthcare professional for medical concerns. **🚨 Emergency: Call 911 (US), 999 (UK), 112 (EU)**
        """)
    
    # Health Categories Section
    st.info("""
    **🩺 Health Guidance Categories:**  
    ✅ Cold/Flu • Fever • Headache • Nausea • Cough • Body Aches • Sore Throat • Fatigue  
    *Ask about symptoms, general wellness tips, and home care recommendations*
    """)
    
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
        
        # History management
        st.subheader("Conversation")
        if st.button("🗑️ Clear History"):
            st.session_state.conversation_history = []
            st.rerun()
        
        st.metric("Messages", len(st.session_state.conversation_history))
        
        # Export conversation
        if len(st.session_state.conversation_history) > 0:
            if st.button("📥 Export Conversation"):
                # Create text export
                export_text = "# AI Health Voice Agent - Conversation Export\n\n"
                for entry in st.session_state.conversation_history:
                    export_text += f"**[{entry['timestamp']}] User:** {entry['user']}\n\n"
                    export_text += f"**[{entry['timestamp']}] AI:** {entry['ai']}\n\n"
                    export_text += "---\n\n"
                
                st.download_button(
                    label="💾 Download as Text",
                    data=export_text,
                    file_name=f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )
        
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
        1. **Voice:** Click microphone and speak your question
        2. **Text:** Type your health question below
        3. Wait for AI response with health guidance
        4. Review medical disclaimer before following advice
        
        **Features:**
        - Browser-based voice recording
        - Speech-to-text via Whisper AI
        - Health guidance via Google Gemini
        - Text-to-speech via Piper/Edge-TTS/gTTS (multi-engine)
        - Conversation history & export
        - Text input alternative
        
        **Health Categories Covered:**
        - Cold/Flu, Fever, Headache
        - Nausea, Cough, Body Aches
        - Sore Throat, Fatigue
        
        **⚠️ Remember:** This is NOT medical advice. Always consult a healthcare professional.
        """)
        
        st.divider()
        
        # Emergency Resources
        st.subheader("🚨 Emergency Resources")
        st.markdown("""
        **Emergency Services:**
        - 🇺🇸 US/Canada: 911
        - 🇬🇧 UK: 999
        - 🇪🇺 EU: 112
        
        **Crisis Helplines:**
        - Poison Control: 1-800-222-1222
        - Mental Health Crisis: 988
        """)
    
    # Main content area with tabs
    main_tabs = st.tabs([
        "💬 Chat",
        "🩺 Symptom Checker",
        "📊 Health Metrics",
        "🧍 Body Diagram",
        "📄 Reports & History"
    ])
    
    # TAB 1: Voice/Text Chat
    with main_tabs[0]:
        # Create sub-tabs for Voice and Text input
        chat_tabs = st.tabs(["🎙️ Voice", "⌨️ Text"])
        
        # VOICE INPUT TAB
        with chat_tabs[0]:
            col1, col2, col3 = st.columns([1, 3, 1])
            
            with col2:
                # Check if st.audio_input is available (Streamlit 1.33.0+)
                has_audio_input = hasattr(st, 'audio_input')
                
                # Voice input method selector
                input_method = st.radio(
                    "Choose input method:",
                    ["🎤 Record in Browser", "📁 Upload Audio File"],
                    horizontal=True,
                    help="Select how you want to provide your voice input"
                )
                
                st.markdown("---")
                
                # BROWSER RECORDING
                if input_method == "🎤 Record in Browser":
                    if has_audio_input:
                        st.info("💡 Click the microphone button below and speak your health question")
                        
                        # Native browser recording (Streamlit 1.33.0+)
                        audio_recorded = st.audio_input("🎤 Click to start recording")
                        
                        if audio_recorded is not None:
                            audio_bytes = audio_recorded.getvalue()
                            st.success("✅ Audio recorded successfully!")
                            
                            # Show the recorded audio
                            st.audio(audio_bytes, format="audio/wav")
                            st.caption("👆 Review your recording above")
                            
                            # Action buttons
                            col_a, col_b = st.columns(2)
                            with col_a:
                                if st.button("🚀 Process This Recording", use_container_width=True, type="primary", key="process_recording"):
                                    st.session_state.audio_data = audio_bytes
                                    st.session_state.processing = True
                                    st.rerun()
                            with col_b:
                                if st.button("🔄 Record Again", use_container_width=True, key="clear_recording"):
                                    st.rerun()
                    else:
                        st.warning("⚠️ Browser recording not available in this environment")
                        st.info("💡 Please use the 'Upload Audio File' option instead")
                
                # FILE UPLOAD
                else:
                    st.info("💡 Upload a pre-recorded audio file (WAV, MP3, M4A, OGG, WebM)")
                    
                    audio_file = st.file_uploader(
                        "Drop your audio file here or click to browse:",
                        type=["wav", "mp3", "m4a", "ogg", "webm"],
                        help="Maximum file size: 200MB",
                        key="audio_uploader",
                        label_visibility="collapsed"
                    )
                    
                    if audio_file is not None:
                        audio_bytes = audio_file.getvalue()
                        st.success(f"✅ File uploaded: {audio_file.name}")
                        
                        # Show the uploaded audio
                        st.audio(audio_bytes)
                        st.caption("👆 Review your audio file above")
                        
                        # Action buttons
                        col_a, col_b = st.columns(2)
                        with col_a:
                            if st.button("🚀 Process This File", use_container_width=True, type="primary", key="process_upload"):
                                st.session_state.audio_data = audio_bytes
                                st.session_state.processing = True
                                st.rerun()
                        with col_b:
                            if st.button("🔄 Upload Different File", use_container_width=True, key="clear_upload"):
                                st.rerun()
                
                # PROCESSING SECTION
                if st.session_state.processing and st.session_state.audio_data:
                    st.markdown("---")
                    st.info("⏳ Processing your message...")
                    
                    # Process the recorded audio
                    with st.spinner("🔄 Transcribing speech, analyzing, and generating response..."):
                        result = send_voice_message(st.session_state.audio_data)
                    
                    if result:
                        # Display results
                        st.success("✅ Response received!")
                        
                        # Show transcription
                        with st.expander("📝 What you said", expanded=True):
                            st.write(result.get("transcription", "N/A"))
                        
                        # Show AI response
                        with st.expander("🤖 AI Health Guidance", expanded=True):
                            st.write(result.get("llm_response", "N/A"))
                        
                        # Show processing time
                        st.caption(f"⏱️ Processing time: {result.get('processing_time', 0):.2f}s")
                        
                        # Play audio response (only if not silent/empty)
                        if result.get("audio_base64") and len(result.get("audio_base64", "")) > 1000:
                            st.markdown("### 🔊 Listen to Response")
                            play_audio_from_base64(result["audio_base64"])
                        else:
                            st.caption("💡 Audio synthesis in progress or unavailable")
                        
                        # Add to history
                        add_to_history(
                            result.get("transcription", ""),
                            result.get("llm_response", ""),
                            result.get("audio_base64")
                        )
                    
                    # Reset processing state
                    st.session_state.processing = False
                    st.session_state.audio_data = None
        
        # TEXT INPUT TAB
        with chat_tabs[1]:
            col1, col2, col3 = st.columns([1, 3, 1])
            
            with col2:
                st.info("💡 Type your health question below for instant AI guidance")
                
                text_input = st.text_area(
                    "Your health question:",
                    placeholder="Example: I have a headache and feel tired. What should I do?",
                    height=120,
                    label_visibility="collapsed"
                )
                
                col_a, col_b, col_c = st.columns([1, 2, 1])
                with col_b:
                    send_button = st.button("💬 Get AI Guidance", use_container_width=True, type="primary")
                
                if send_button:
                    if text_input.strip():
                        with st.spinner("🔄 Processing your question..."):
                            try:
                                response = requests.post(
                                    f"{API_BASE_URL}/chat",
                                    json={"text": text_input},
                                    timeout=60
                                )
                                if response.status_code == 200:
                                    result = response.json()
                                    st.success("✅ Response received!")
                                    
                                    # Show AI response
                                    with st.expander("🤖 AI Health Guidance", expanded=True):
                                        st.write(result.get("text", ""))
                                    
                                    # Add to history
                                    add_to_history(text_input, result.get("text", ""), None)
                                else:
                                    st.error(f"❌ Error: Status code {response.status_code}")
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")
                    else:
                        st.warning("⚠️ Please enter a question first")
        
        # Conversation History (shown in both tabs)
        st.markdown("---")
        st.markdown("### 💬 Recent Conversation")
        if st.session_state.conversation_history:
            # Show last 3 conversations
            for entry in st.session_state.conversation_history[-3:]:
                with st.container():
                    col_user, col_ai = st.columns(2)
                    with col_user:
                        st.caption(f"**You** [{entry['timestamp']}]")
                        st.text(entry['user'][:100] + "..." if len(entry['user']) > 100 else entry['user'])
                    with col_ai:
                        st.caption(f"**AI** [{entry['timestamp']}]")
                        st.text(entry['ai'][:100] + "..." if len(entry['ai']) > 100 else entry['ai'])
            
            st.caption("💡 View full history in the '📄 Reports & History' tab")
        else:
            st.info("👋 No conversations yet. Start by asking a health question!")
    
    # TAB 2: Symptom Checker
    with main_tabs[1]:
        symptom_checker_tab()
    
    # TAB 3: Health Metrics
    with main_tabs[2]:
        health_metrics_tab()
    
    # TAB 4: Body Diagram
    with main_tabs[3]:
        body_diagram_tab()
    
    # TAB 5: Reports & History
    with main_tabs[4]:
        export_health_report()
        
        st.markdown("---")
        st.markdown("## 💬 Conversation History")
        display_conversation_history()
    
    # Footer
    st.markdown("---")
    st.caption("🏥 AI Health Voice Agent v1.0 | Educational Health Information Only | Not Medical Advice")
    st.caption("Built with Whisper AI, Google Gemini, Piper TTS, Streamlit • Deployed on Hugging Face Spaces")


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"❌ Application error: {str(e)}")
        st.exception(e)
