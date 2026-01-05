import sys
from unittest.mock import MagicMock
import os
import json

# --- MOCK SETUP ---
mock_openai = MagicMock()
mock_client = MagicMock()
mock_completion = MagicMock()

# Mock AI Response (Generic Greeting)
mock_completion.choices[0].message.content = json.dumps({
    "feedback": "",
    "internal_score": 0,
    "next_question": "Hello and Welcome.",
    "role_title": "Manager"
})
mock_client.chat.completions.create.return_value = mock_completion
mock_client.audio.speech.create.return_value = MagicMock(content=b"fake_audio")

mock_openai.OpenAI.return_value = mock_client
sys.modules["openai"] = mock_openai
mock_supabase = MagicMock()
sys.modules["supabase"] = mock_supabase

os.environ["OPENAI_API_KEY"] = "dummy"
os.environ["SUPABASE_URL"] = "dummy"
os.environ["SUPABASE_KEY"] = "dummy"

from api.index import app

def run_v2_exclusion_test():
    print("=== START EXCLUSION TEST V2 (Production Scenario) ===")
    
    with app.test_client() as client:
        # TEST: App.js Scenario (questionCount=2, isStart=True)
        print("\n[TEST] Verifying Start (isStart=True, Count=2) is EXCLUDED from Penalty...")
        payload = {
            "action": "feedback",
            "questionCount": 2, # App.js sends 1 + 1 = 2
            "isStart": True,    # Explicit Start Flag
            "history": [],
            "message": "Start"
        }
        
        # We expect internal score to be NONE (missing key or 0), NOT 1.
        resp = client.post('/api/get-feedback', json=payload)
        data = resp.get_json()
        response_data = data['response']
        
        score = response_data.get('score')
        internal_score = response_data.get('internal_score')
        feedback = response_data.get('feedback', '')
        
        print(f"DEBUG Response Score: {score}")
        print(f"DEBUG Feedback: {feedback}")
        
        if score == 1 or internal_score == 1:
             print("❌ FAIL: Score forced to 1! Logic failed to use isStart flag.")
        else:
             print("✅ PASS: Score remains None/Zero. Start excluded via isStart.")

        if "System Note" in feedback:
             print("❌ FAIL: System Note present.")
        else:
             print("✅ PASS: No System Note.")

    print("\n=== TEST COMPLETE ===")

if __name__ == "__main__":
    run_v2_exclusion_test()
