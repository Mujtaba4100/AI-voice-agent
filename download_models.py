# ============================================================================
# AI Voice Agent - Model Downloader (Python Script)
# ============================================================================
# This script downloads all required AI models for the voice agent:
# - Faster-Whisper models (automatic via first run)
# - Piper TTS voice models
#
# Usage: python download_models.py
# ============================================================================

import os
import sys
import urllib.request
import zipfile
import tarfile
from pathlib import Path

# ============================================================================
# CONFIGURATION
# ============================================================================

# Base directory for models
MODELS_DIR = Path("models")
PIPER_DIR = MODELS_DIR / "piper"

# Piper TTS model URLs
# Using high-quality US English voice (lessac)
PIPER_MODELS = {
    "en_US-lessac-medium": {
        "onnx_url": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx",
        "json_url": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json",
    }
}

# Alternative Piper voices (faster but lower quality)
ALTERNATIVE_VOICES = {
    "en_US-lessac-low": {
        "onnx_url": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/low/en_US-lessac-low.onnx",
        "json_url": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/low/en_US-lessac-low.onnx.json",
    },
    "en_US-amy-medium": {
        "onnx_url": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/amy/medium/en_US-amy-medium.onnx",
        "json_url": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/amy/medium/en_US-amy-medium.onnx.json",
    }
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def download_file(url: str, dest_path: Path, description: str = "file"):
    """
    Download a file with progress indication.
    
    Args:
        url: URL to download from
        dest_path: Destination file path
        description: Description for progress display
    """
    print(f"📥 Downloading {description}...")
    print(f"   URL: {url}")
    print(f"   Destination: {dest_path}")
    
    try:
        def report_progress(block_num, block_size, total_size):
            downloaded = block_num * block_size
            percent = min(downloaded * 100 / total_size, 100)
            bar_length = 40
            filled = int(bar_length * percent / 100)
            bar = '█' * filled + '░' * (bar_length - filled)
            print(f"\r   [{bar}] {percent:.1f}% ({downloaded / 1024 / 1024:.1f}MB)", end='')
        
        urllib.request.urlretrieve(url, dest_path, report_progress)
        print()  # New line after progress bar
        print(f"✅ Downloaded successfully: {dest_path.name}")
        return True
        
    except Exception as e:
        print(f"\n❌ Error downloading {description}: {e}")
        return False


def create_directory_structure():
    """Create necessary directories for models."""
    print("📁 Creating directory structure...")
    
    directories = [
        MODELS_DIR,
        PIPER_DIR,
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"   ✓ {directory}")
    
    print("✅ Directory structure created")


def download_piper_models(voice_name: str = "en_US-lessac-medium"):
    """
    Download Piper TTS model files.
    
    Args:
        voice_name: Name of the voice to download
    """
    print(f"\n{'='*70}")
    print(f"Downloading Piper TTS Model: {voice_name}")
    print(f"{'='*70}")
    
    if voice_name not in PIPER_MODELS:
        print(f"❌ Voice '{voice_name}' not found in available models.")
        print(f"Available voices: {', '.join(PIPER_MODELS.keys())}")
        return False
    
    model_info = PIPER_MODELS[voice_name]
    
    # Download ONNX model file
    onnx_path = PIPER_DIR / f"{voice_name}.onnx"
    if onnx_path.exists():
        print(f"⏭️  Model already exists: {onnx_path.name}")
    else:
        if not download_file(model_info["onnx_url"], onnx_path, f"{voice_name}.onnx"):
            return False
    
    # Download JSON config file
    json_path = PIPER_DIR / f"{voice_name}.onnx.json"
    if json_path.exists():
        print(f"⏭️  Config already exists: {json_path.name}")
    else:
        if not download_file(model_info["json_url"], json_path, f"{voice_name}.onnx.json"):
            return False
    
    print(f"✅ Piper model '{voice_name}' downloaded successfully!")
    return True


def verify_whisper_models():
    """
    Verify Faster-Whisper models.
    Note: Faster-Whisper downloads models automatically on first use.
    """
    print(f"\n{'='*70}")
    print("Verifying Whisper Models")
    print(f"{'='*70}")
    
    print("ℹ️  Faster-Whisper models are downloaded automatically on first use.")
    print("   Models will be cached in:")
    
    # Check common cache locations
    cache_locations = [
        Path.home() / ".cache" / "huggingface" / "hub",
        Path(os.getenv("XDG_CACHE_HOME", Path.home() / ".cache")) / "huggingface",
    ]
    
    for location in cache_locations:
        if location.exists():
            print(f"   ✓ {location}")
    
    print("\n📝 Available Whisper models:")
    print("   - tiny    (39M parameters, fastest, ~1GB RAM)")
    print("   - base    (74M parameters, balanced, ~1.5GB RAM)")
    print("   - small   (244M parameters, better quality, ~2GB RAM)")
    print("   - medium  (769M parameters, high quality, ~5GB RAM)")
    
    print("\n💡 The backend is configured to use 'tiny' by default.")
    print("   Change WHISPER_MODEL_NAME in backend.py to use a different model.")
    
    return True


def display_summary():
    """Display summary of downloaded models."""
    print(f"\n{'='*70}")
    print("📊 DOWNLOAD SUMMARY")
    print(f"{'='*70}")
    
    print("\n📂 Model Directory Structure:")
    print(f"   {MODELS_DIR}/")
    
    # Check Piper models
    print(f"   ├── piper/")
    piper_files = list(PIPER_DIR.glob("*.onnx"))
    if piper_files:
        for file in piper_files:
            print(f"   │   ├── {file.name} ({file.stat().st_size / 1024 / 1024:.1f}MB)")
            json_file = file.with_suffix(".onnx.json")
            if json_file.exists():
                print(f"   │   ├── {json_file.name}")
    else:
        print(f"   │   └── (no models downloaded)")
    
    print("\n✅ Model download complete!")
    print("\n📝 Next steps:")
    print("   1. Set up your GEMINI_API_KEY environment variable")
    print("   2. Run the backend servers (see docs/INSTALLATION.md)")
    print("   3. Start the Streamlit UI")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function."""
    print("="*70)
    print("🚀 AI VOICE AGENT - MODEL DOWNLOADER")
    print("="*70)
    print()
    
    # Create directories
    create_directory_structure()
    
    # Download Piper TTS models
    success = download_piper_models("en_US-lessac-medium")
    
    if not success:
        print("\n⚠️  Some downloads failed. Please check the errors above.")
        print("💡 You can try alternative voices or download manually from:")
        print("   https://huggingface.co/rhasspy/piper-voices")
        return 1
    
    # Verify Whisper setup
    verify_whisper_models()
    
    # Display summary
    display_summary()
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Download cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
