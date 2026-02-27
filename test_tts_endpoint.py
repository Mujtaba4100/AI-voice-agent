"""Simple test script to verify /tts endpoint works"""
import requests

def test_tts_endpoint():
    url = "http://localhost:8000/tts"
    payload = {"text": "Hello from the AI voice agent!"}
    
    print(f"Testing {url}...")
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        # Save the generated WAV file
        with open("tts_test_output.wav", "wb") as f:
            f.write(response.content)
        print(f"✓ Success! Generated {len(response.content)} bytes")
        print(f"✓ Saved to: tts_test_output.wav")
        return True
    else:
        print(f"✗ Failed: {response.status_code}")
        print(response.text)
        return False

if __name__ == "__main__":
    test_tts_endpoint()
