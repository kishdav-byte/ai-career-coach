import requests
import json
import base64
import os

API_KEY = 'AIzaSyBjDuL6BfoG_VfkE6qymgEBtRKr0Gcqq74'

def test_gemini_audio():
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={API_KEY}"
    
    prompt = "Hello! This is a test of the Gemini audio generation capabilities. I hope I sound natural."
    
    # Try placing responseModalities inside generationConfig
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "responseModalities": ["AUDIO"]
        }
    }
    
    print(f"Sending request to {url}...")
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        result = response.json()
        
        # print(json.dumps(result, indent=2))
        
        if 'candidates' in result and result['candidates']:
            parts = result['candidates'][0]['content']['parts']
            audio_data = None
            for part in parts:
                if 'inline_data' in part and part['inline_data']['mime_type'].startswith('audio'):
                    audio_data = part['inline_data']['data']
                    break
            
            if audio_data:
                print("Audio data found!")
                with open("gemini_audio.wav", "wb") as f:
                    f.write(base64.b64decode(audio_data))
                print(f"Saved to gemini_audio.wav ({os.path.getsize('gemini_audio.wav')} bytes)")
            else:
                print("No audio data found in response.")
        else:
            print("Invalid response structure.")
            
    except Exception as e:
        print(f"Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")

if __name__ == "__main__":
    test_gemini_audio()
