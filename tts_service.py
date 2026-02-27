"""Reusable TTS service that calls the native Piper Windows binary via subprocess.

Design goals:
- Use `piper.exe` subprocess (no piper-tts Python package)
- Configurable binary and model paths via .env file
- Pathlib usage and clear error handling
"""
from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional
import logging
from dotenv import load_dotenv

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


class PiperError(RuntimeError):
    pass


def _validate_paths() -> None:
    if not PIPER_EXE_PATH.exists():
        raise FileNotFoundError(f"Piper executable not found at: {PIPER_EXE_PATH}")
    if not PIPER_MODEL_PATH.exists():
        raise FileNotFoundError(f"Piper model not found at: {PIPER_MODEL_PATH}")


def speak(text: str, output_path: Optional[str] = None) -> str:
    """Synthesize speech by invoking the native Piper binary.

    Args:
        text: Text to synthesize. Must be non-empty.
        output_path: Destination WAV file path. If omitted, a temporary file is created.

    Returns:
        Absolute path to the generated WAV file.

    Raises:
        ValueError: If `text` is empty.
        PiperError: If piper.exe fails to synthesize audio.
        FileNotFoundError: If expected files (binary/model) are missing.
    """
    if not text or not text.strip():
        raise ValueError("`text` must be a non-empty string")

    _validate_paths()

    # Prepare output file
    if output_path:
        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        out_path = Path(tmp.name)
        tmp.close()

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
