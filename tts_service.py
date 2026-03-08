"""Reusable TTS service that calls the native Piper Windows binary via subprocess.

Design goals:
- Use `piper.exe` subprocess (no piper-tts Python package)
- Configurable binary and model paths via .env file
- Pathlib usage and clear error handling
- Fallback to silent mode if Piper unavailable (for HF deployment)
"""
from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional
import logging
from dotenv import load_dotenv
import uuid

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

# Configurable paths from .env or defaults
PROJECT_ROOT = Path(__file__).resolve().parent
PIPER_EXE_PATH = Path(os.getenv("PIPER_EXE_PATH", "piper_windows_amd64/piper/piper.exe"))
PIPER_MODEL_PATH = Path(os.getenv("PIPER_MODEL_PATH", "piper_windows_amd64/piper/models/en_US-lessac-medium.onnx"))

# Make paths absolute if they're relative
if not PIPER_EXE_PATH.is_absolute():
    PIPER_EXE_PATH = PROJECT_ROOT / PIPER_EXE_PATH
if not PIPER_MODEL_PATH.is_absolute():
    PIPER_MODEL_PATH = PROJECT_ROOT / PIPER_MODEL_PATH

# Check if Piper is available (for Windows local development)
PIPER_AVAILABLE = PIPER_EXE_PATH.exists() and PIPER_MODEL_PATH.exists()

if not PIPER_AVAILABLE:
    logger.warning(f"Piper TTS not available. Expected at: {PIPER_EXE_PATH}")
    logger.warning("Using silent mode for HF Spaces deployment. Audio output disabled.")
    logger.warning("To enable TTS locally, download Piper: https://github.com/rhasspy/piper/releases")


class PiperError(RuntimeError):
    pass


def _validate_paths() -> None:
    if not PIPER_EXE_PATH.exists():
        raise FileNotFoundError(f"Piper executable not found at: {PIPER_EXE_PATH}")
    if not PIPER_MODEL_PATH.exists():
        raise FileNotFoundError(f"Piper model not found at: {PIPER_MODEL_PATH}")


def _create_silent_wav(output_path: Path) -> None:
    """Create a minimal silent WAV file for HF deployment when Piper unavailable."""
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


def speak(text: str, output_path: Optional[str] = None) -> str:
    """Synthesize speech by invoking the native Piper binary (or create silent file if unavailable).

    Args:
        text: Text to synthesize. Must be non-empty.
        output_path: Destination WAV file path. If omitted, a temporary file is created.

    Returns:
        Absolute path to the generated WAV file.

    Raises:
        ValueError: If `text` is empty.
        PiperError: If piper.exe fails to synthesize audio.
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

    # If Piper not available (HF Spaces), create silent fallback
    if not PIPER_AVAILABLE:
        logger.info("Piper TTS not available. Creating placeholder audio for HF Spaces.")
        _create_silent_wav(out_path)
        return str(out_path.absolute())

    # Piper is available locally - use it
    # Build command
    cmd = [str(PIPER_EXE_PATH), "--model", str(PIPER_MODEL_PATH), "--output_file", str(out_path)]

    logger.info("Running Piper: %s", cmd)

    try:
        proc = subprocess.run(
            cmd,
            input=text.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except Exception as e:
        # OSError, FileNotFoundError, etc.
        raise PiperError(f"Failed to execute Piper binary: {e}")

    if proc.returncode != 0:
        stderr = proc.stderr.decode("utf-8", errors="replace")
        stdout = proc.stdout.decode("utf-8", errors="replace")
        msg = f"Piper failed (code={proc.returncode}). stdout: {stdout!r} stderr: {stderr!r}"
        logger.error(msg)
        # Clean up possibly-created file
        try:
            if out_path.exists():
                out_path.unlink()
        except Exception:
            pass
        raise PiperError(msg)

    # Validate output file
    if not out_path.exists() or out_path.stat().st_size == 0:
        raise PiperError(f"Piper reported success but output file is missing or empty: {out_path}")

    logger.info("Piper produced audio: %s (%d bytes)", out_path, out_path.stat().st_size)
    return str(out_path.resolve())


__all__ = ["speak", "PIPER_EXE_PATH", "PIPER_MODEL_PATH", "PiperError"]
