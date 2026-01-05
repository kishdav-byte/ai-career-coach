import sys
from unittest.mock import MagicMock
import os
import json

# --- MOCK SETUP ---
mock_openai = MagicMock()
mock_client = MagicMock()
mock_completion = MagicMock()

# Mock AI Response (Generic)
mock_completion.choices[0].message.content = json.dumps({
    "feedback": "Response OK.",
    "internal_score": 4, 
    "next_question": "Next?"
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

def run_scoring_test():
    print("=== SCORING RULES VERIFICATION (v6.1) ===")
    
    with app.test_client() as client:
        # TEST 1: RUBRIC CHECK (Magic Wand)
        print("\n[TEST 1] Verifying 'Magic Wand' Rule in Prompt...")
        payload_rubric = {
            "action": "feedback",
            "questionCount": 3,
            "history": [],
            "message": "Valid length answer."
        }
        client.post('/api/get-feedback', json=payload_rubric)
        
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args[1]['messages']
        system_prompt = messages[0]['content']
        
        if "Magic Wand Penalty" in system_prompt and "MAX SCORE: 2" in system_prompt:
             print("✅ PASS: System Prompt contains 'Magic Wand Penalty'.")
        else:
             print("❌ FAIL: Magic Wand rule missing from rubric.")

        # TEST 2: WORD COUNT PENALTY (Short Answer)
        print("\n[TEST 2] Verifying Word Count Penalty (<20 words)...")
        short_msg = "This is a very short answer with few words." # ~9 words
        payload_short = {
            "action": "feedback",
            "questionCount": 3,
            "history": [],
            "message": short_msg
        }
        
        # We expect the 'internal_score' to be FORCED to 1, regardless of what AI returns (Mock returns 4)
        resp = client.post('/api/get-feedback', json=payload_short)
        data = resp.get_json()
        
        response_data = data['response']
        score = response_data.get('score')
        internal_score = response_data.get('internal_score')
        feedback = response_data.get('feedback', '')
        
        print(f"DEBUG Response Score: {score}")
        print(f"DEBUG Feedback Snippet: {feedback}")
        
        if score == 1 and internal_score == 1:
            print("✅ PASS: Score forced to 1.")
        else:
            print(f"❌ FAIL: Score not penalized. Got {score}.")

        if "Response was too brief" in feedback:
             print("✅ PASS: Feedback contains system note.")
        else:
             print("❌ FAIL: Feedback missing system penalty note.")

    print("\n=== TEST COMPLETE ===")

if __name__ == "__main__":
    run_scoring_test()
