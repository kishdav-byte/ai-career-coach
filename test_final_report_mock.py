import sys
from unittest.mock import MagicMock
import os
import json

# 1. Setup Mocks BEFORE importing api.index
# Mock OpenAI
mock_openai = MagicMock()
mock_client = MagicMock()
mock_completion = MagicMock()
# Mock the AI returning a valid JSON report
mock_completion.choices[0].message.content = json.dumps({
    "formatted_report": "<div class='ace-report'><h1>Mock Report</h1></div>",
    "average_score": 4.2,
    "q6_score": 4,
    "q6_feedback_spoken": "Good job.",
    "verdict_text": "RECOMMEND"
})
mock_client.chat.completions.create.return_value = mock_completion
# Mock Audio
mock_audio_resp = MagicMock()
mock_audio_resp.content = b"fake_audio_bytes"
mock_client.audio.speech.create.return_value = mock_audio_resp
mock_client.audio.transcriptions.create.return_value = MagicMock(text="Transcribed text")

mock_openai.OpenAI.return_value = mock_client
sys.modules["openai"] = mock_openai

# Mock Supabase
mock_supabase = MagicMock()
sys.modules["supabase"] = mock_supabase

# Set dummy env vars to pass checks
os.environ["OPENAI_API_KEY"] = "dummy"
os.environ["SUPABASE_URL"] = "dummy"
os.environ["SUPABASE_KEY"] = "dummy"

# 2. Import App
try:
    from api.index import app
except ImportError:
    # Handle if api/index.py assumes imports exist at top level (which we fixed!)
    # But just in case
    print("Error importing app")
    sys.exit(1)

# 3. Running Test
print("Starting Mock Test for Final Report (Count 7)...")
try:
    with app.test_client() as client:
        # payload
        payload = {
            "action": "feedback",
            "questionCount": 7,  # Trigger Final Report
            "history": [
                {"question": "Q1", "answer": "A1", "feedback": "Score: 4/5"},
                {"question": "Q2", "answer": "A2", "feedback": "Score: 3.5"},
                {"question": "Q3", "answer": "A3", "feedback": "Score: 5"},
            ],
            "message": "This is my final answer."
        }
        
        response = client.post('/api/get-feedback', json=payload)
        
        print(f"Status Code: {response.status_code}")
        print("Response Data:")
        try:
            data = response.get_json()
            print(json.dumps(data, indent=2))
            
            # Validation
            if response.status_code == 200:
                print("SUCCESS: Endpoint returned 200.")
                if data.get("is_complete") == True:
                    print("SUCCESS: is_complete is True.")
                else:
                    print("FAILURE: is_complete is False.")
                
                if "formatted_report" in data.get("response", {}):
                     print("SUCCESS: formatted_report is present.")
                else:
                     print("FAILURE: formatted_report missing.")
            else:
                print("FAILURE: Endpoint returned non-200.")
                
        except Exception as e:
            print(f"Error parsing response: {e}")
            print(response.data.decode())

except Exception as e:
    import traceback
    print(f"CRITICAL TEST ERROR: {traceback.format_exc()}")
