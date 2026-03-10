"""
Test Multi-Engine TTS Integration
Quick test to verify TTS engines are working before deployment
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

import tts_service

def test_tts():
    """Test TTS with multi-engine fallback"""
    print("=" * 60)
    print("Testing Multi-Engine TTS Service")
    print("=" * 60)
    
    # Check engine availability
    print("\n📊 TTS Engine Status:")
    print(f"  Piper (offline):      {'✅ Available' if tts_service.PIPER_AVAILABLE else '❌ Not available'}")
    print(f"  Edge-TTS (cloud):     {'✅ Available' if tts_service.EDGE_TTS_AVAILABLE else '❌ Not available'}")
    print(f"  gTTS (fallback):      {'✅ Available' if tts_service.GTTS_AVAILABLE else '❌ Not available'}")
    
    # Test synthesis
    test_text = "Hello! This is a test of the voice synthesis system. If you can hear this, TTS is working perfectly."
    
    print(f"\n🎤 Test Text: {test_text}")
    print("\n⏳ Synthesizing audio...")
    
    try:
        output_file = tts_service.speak(test_text)
        print(f"\n✅ SUCCESS! Audio generated at: {output_file}")
        
        # Check file size
        file_size = Path(output_file).stat().st_size
        print(f"📁 File size: {file_size:,} bytes ({file_size / 1024:.1f} KB)")
        
        # Determine which engine was used
        if file_size < 10000:
            print("\n⚠️  WARNING: Very small file (likely silent fallback)")
            print("   Install TTS engines: pip install edge-tts gTTS")
        elif file_size > 200000:
            print("\n✅ High quality audio! (Piper or Edge-TTS)")
        else:
            print("\n✅ Audio generated! (likely gTTS)")
        
        print(f"\n🔊 Play the audio file to verify: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        print("\n💡 TIP: Install TTS engines with: pip install edge-tts gTTS")
        return False

if __name__ == "__main__":
    print("\n🧪 Multi-Engine TTS Test Script\n")
    
    success = test_tts()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Test completed. Check the audio file above.")
        print("📦 Ready to deploy to Hugging Face Spaces!")
    else:
        print("❌ Test failed. Fix the errors above before deploying.")
    print("=" * 60)
