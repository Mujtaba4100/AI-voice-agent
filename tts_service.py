"""Reusable TTS service for cloud deployment (Hugging Face Spaces).

Design goals:
- Multi-engine reliability: Piper (local binary) → Edge-TTS → gTTS → Silent
- Piper: High quality offline TTS (Windows .exe or Linux binary)
- Edge-TTS: Cloud TTS, but may get 403 errors
- gTTS: Reliable Google TTS fallback
- Silent fallback: Last resort when all engines fail
- Async-first: Proper async handling for FastAPI integration
- Cross-platform: Works on Windows and Linux
"""
from __future__ import annotations

import os
import sys
import subprocess
import tempfile
import asyncio
from pathlib import Path
from typing import Optional
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

# Detect platform
IS_LINUX = sys.platform.startswith('linux')
IS_WINDOWS = sys.platform.startswith('win')

# Piper configuration (platform-specific)
PROJECT_ROOT = Path(__file__).resolve().parent

if IS_WINDOWS:
    # Windows: Check for piper_windows_amd64 folder
    PIPER_EXE_PATH = PROJECT_ROOT / "piper_windows_amd64" / "piper" / "piper.exe"
    PIPER_MODEL_PATH = PROJECT_ROOT / "piper_windows_amd64" / "piper" / "models" / "en_US-lessac-medium.onnx"
elif IS_LINUX:
    # Linux: Check for piper folder (downloaded in Docker)
    PIPER_EXE_PATH = PROJECT_ROOT / "piper" / "piper"
    PIPER_MODEL_PATH = PROJECT_ROOT / "piper" / "models" / "en_US-lessac-medium.onnx"
else:
    # Other platforms: No Piper support
    PIPER_EXE_PATH = Path("/nonexistent")
    PIPER_MODEL_PATH = Path("/nonexistent")

# Check if Piper is available
PIPER_AVAILABLE = PIPER_EXE_PATH.exists() and PIPER_MODEL_PATH.exists()

if PIPER_AVAILABLE:
    logger.info(f"✅ Piper TTS available at: {PIPER_EXE_PATH}")
    logger.info(f"   Platform: {'Linux' if IS_LINUX else 'Windows'}")
else:
    logger.info(f"⚠️ Piper TTS not available (platform: {sys.platform})")

# Try to import edge-tts (high quality, but unreliable due to 403 errors)
try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
    logger.info("✅ Edge-TTS available (cloud TTS, may have 403 errors)")
except ImportError:
    EDGE_TTS_AVAILABLE = False
    logger.info("⚠️ edge-tts not installed")

# Try to import gTTS (reliable Google TTS)
try:
    from gtts import gTTS as GoogleTTS
    GTTS_AVAILABLE = True
    logger.info("✅ gTTS available (reliable Google TTS)")
except ImportError:
    GTTS_AVAILABLE = False
    logger.info("⚠️ gTTS not installed")

if not PIPER_AVAILABLE and not EDGE_TTS_AVAILABLE and not GTTS_AVAILABLE:
    logger.warning("⚠️ No TTS engines available. Audio will be silent.")


def _speak_piper(text: str, output_path: Path) -> str:
    """Synthesize speech using Piper (cross-platform binary).
    
    Args:
        text: Text to synthesize
        output_path: Output WAV file path
    
    Returns:
        Absolute path to generated WAV file
    
    Raises:
        Exception: If synthesis fails
    """
    if not PIPER_AVAILABLE:
        raise RuntimeError("Piper not available")
    
    # Build command
    cmd = [str(PIPER_EXE_PATH), "--model", str(PIPER_MODEL_PATH), "--output_file", str(output_path)]

    logger.info(f"Running Piper: {' '.join(cmd[:3])}")

    try:
        proc = subprocess.run(
            cmd,
            input=text.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=30  # 30 second timeout
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError("Piper TTS timeout (30s)")
    except Exception as e:
        raise RuntimeError(f"Failed to execute Piper: {e}")

    if proc.returncode != 0:
        stderr = proc.stderr.decode("utf-8", errors="replace")
        raise RuntimeError(f"Piper failed (code={proc.returncode}): {stderr}")

    # Validate output file
    if not output_path.exists() or output_path.stat().st_size == 0:
        raise RuntimeError(f"Piper output missing or empty: {output_path}")

    file_size = output_path.stat().st_size
    logger.info(f"Piper synthesized audio: {output_path} ({file_size:,} bytes)")
    return str(output_path.resolve())


def _create_silent_wav(output_path: Path) -> None:
    """Create a minimal silent WAV file when TTS unavailable.
    
    Args:
        output_path: Path where silent WAV file will be created
        
    Raises:
        Exception: If WAV file creation fails
    """
    import wave
    import struct
    try:
        # Create a simple silent WAV file (1 second of silence at 16kHz)
        with wave.open(str(output_path), 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(16000)  # 16kHz
            # 1 second of silence = 16000 samples of 0
            silence = struct.pack('<h', 0) * 16000
            wav_file.writeframes(silence)
        logger.info(f"Created silent placeholder WAV: {output_path}")
    except Exception as e:
        logger.error(f"Failed to create silent WAV: {e}")
        raise


async def _speak_edge_tts(text: str, output_path: Path, voice: str = "en-US-AriaNeural") -> None:
    """Synthesize speech using Microsoft Edge TTS (cloud-based).
    
    Args:
        text: Text to synthesize
        output_path: Output WAV file path
        voice: Voice name (default: en-US-AriaNeural - natural female voice)
               Popular options: en-US-AriaNeural, en-US-GuyNeural, en-GB-SoniaNeural
    
    Raises:
        ImportError: If edge-tts not installed
        Exception: If synthesis fails (including 403 errors)
    """
    if not EDGE_TTS_AVAILABLE:
        raise ImportError("edge-tts not installed")
    
    try:
        # Create Edge-TTS communicator
        communicate = edge_tts.Communicate(text, voice)
        
        # Save to file (async operation)
        await communicate.save(str(output_path))
        
        # Log success with file size
        file_size = output_path.stat().st_size
        logger.info(f"Edge-TTS synthesized audio: {output_path} ({file_size:,} bytes)")
    except Exception as e:
        logger.error(f"Edge-TTS synthesis failed: {e}")
        raise


def _speak_gtts(text: str, output_path: Path, lang: str = "en") -> None:
    """Synthesize speech using Google Text-to-Speech (gTTS).
    
    Reliable fallback when Edge-TTS fails with 403 errors.
    
    Args:
        text: Text to synthesize
        output_path: Output MP3 file path
        lang: Language code (default: "en" for English)
    
    Raises:
        ImportError: If gTTS not installed
        Exception: If synthesis fails
    """
    if not GTTS_AVAILABLE:
        raise ImportError("gTTS not installed")
    
    try:
        # Create gTTS object
        tts = GoogleTTS(text=text, lang=lang, slow=False)
        
        # Save to file (sync operation - gTTS is not async)
        tts.save(str(output_path))
        
        # Log success with file size
        file_size = output_path.stat().st_size
        logger.info(f"gTTS synthesized audio: {output_path} ({file_size:,} bytes)")
    except Exception as e:
        logger.error(f"gTTS synthesis failed: {e}")
        raise


async def speak_async(text: str, output_path: Optional[str] = None, voice: str = "en-US-AriaNeural") -> str:
    """Async text-to-speech synthesis with multi-engine fallback.
    
    Fallback chain: Piper (offline) → Edge-TTS (cloud) → gTTS (reliable) → Silent
    Designed for cross-platform deployment (Windows, Linux, HF Spaces).
    
    Args:
        text: Text to synthesize. Must be non-empty.
        output_path: Destination audio file path. If omitted, a temporary file is created.
        voice: Edge-TTS voice name (default: en-US-AriaNeural - natural female voice)

    Returns:
        Absolute path to the generated audio file.

    Raises:
        ValueError: If `text` is empty.
    """
    if not text or not text.strip():
        raise ValueError("`text` must be a non-empty string")

    # Prepare output file
    if output_path:
        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        out_path = Path(tmp.name)
        tmp.close()

    # Try Piper first (best quality, offline, fast)
    if PIPER_AVAILABLE:
        try:
            logger.info("🎙️ Using Piper TTS (offline, high quality)")
            # Run Piper in thread pool to not block event loop
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, _speak_piper, text, out_path)
            return result
        except Exception as e:
            logger.warning(f"Piper TTS failed: {e}. Trying Edge-TTS...")

    # Try Edge-TTS second (cloud, high quality, but may fail with 403)
    if EDGE_TTS_AVAILABLE:
        try:
            logger.info("🌐 Using Edge-TTS (cloud, high quality)")
            await _speak_edge_tts(text, out_path, voice)
            return str(out_path.absolute())
        except Exception as e:
            logger.warning(f"Edge-TTS failed: {e}. Trying gTTS...")
    
    # Try gTTS third (reliable Google TTS)
    if GTTS_AVAILABLE:
        try:
            logger.info("📡 Using gTTS (reliable Google TTS)")
            # Change extension to .mp3 for gTTS
            gtts_path = out_path.with_suffix(".mp3")
            # Run gTTS in thread pool (it's sync)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, _speak_gtts, text, gtts_path, "en")
            return str(gtts_path.absolute())
        except Exception as e:
            logger.warning(f"gTTS failed: {e}. Using silent fallback...")
    
    # Final fallback: silent audio
    logger.info("🔇 All TTS engines failed. Creating silent placeholder.")
    _create_silent_wav(out_path)
    return str(out_path.absolute())


def speak(text: str, output_path: Optional[str] = None, voice: str = "en-US-AriaNeural") -> str:
    """Synchronous wrapper for speak_async(). Use speak_async() in async contexts.
    
    Fallback chain: Piper → Edge-TTS → gTTS → Silent
    
    Args:
        text: Text to synthesize. Must be non-empty.
        output_path: Destination audio file path. If omitted, a temporary file is created.
        voice: Edge-TTS voice name (default: en-US-AriaNeural - natural female voice)

    Returns:
        Absolute path to the generated audio file.

    Raises:
        ValueError: If `text` is empty.
    """
    # Use asyncio.run() for sync contexts (CLI, scripts, tests)
    return asyncio.run(speak_async(text, output_path, voice))


__all__ = ["speak", "speak_async", "PIPER_AVAILABLE", "EDGE_TTS_AVAILABLE", "GTTS_AVAILABLE"]
