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
    "next_question": "Hello and Welcome.",
    # No score provided by AI for greeting
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

def run_exclusion_test():
    print("=== GREETING EXCLUSION TEST ===")
    
    with app.test_client() as client:
        # TEST: Greeting (Turn 1)
        print("\n[TEST] Verifying Greeting (Q1) is EXCLUDED from Penalty...")
        payload = {
            "action": "feedback",
            "questionCount": 1, # GREETING
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
             print("❌ FAIL: Score forced to 1! Logic failed to exclude Q1.")
        else:
             print("✅ PASS: Score remains None/Zero. Greeting excluded.")

        if "System Note" in feedback:
             print("❌ FAIL: System Note present.")
        else:
             print("✅ PASS: No System Note.")

    print("\n=== TEST COMPLETE ===")

if __name__ == "__main__":
    run_exclusion_test()
