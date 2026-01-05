import sys
from unittest.mock import MagicMock
import os
import json
import time

# --- MOCK SETUP ---
mock_openai = MagicMock()
mock_client = MagicMock()
mock_completion = MagicMock()

# Mock Response (Default)
mock_completion.choices[0].message.content = json.dumps({
    "feedback": "Good job.",
    "next_question": "Next question?",
    "q6_score": 4, 
    "internal_score": 4
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

# Import App
from api.index import app

def run_verification():
    print("=== STARTING VERIFICATION SUITE ===")
    
    with app.test_client() as client:
        # TEST 1: Double Question Fix (Turn 3 Prompt Check)
        print("\n[TEST 1] Verifying Double Question Prompt Logic (Turn 3)...")
        payload_q3 = {
            "action": "feedback",
            "questionCount": 3,
            "history": [{"question": "Q1", "answer": "A1"}],
            "message": "My answer to Q2."
        }
        client.post('/api/get-feedback', json=payload_q3)
        
        # Inspect Mock Call Args
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args[1]['messages']
        last_user_msg = messages[-1]['content']
        
        if "Put ONLY this critique in 'feedback' field" in last_user_msg:
             print("✅ PASS: Prompt contains strict 'feedback' field instruction.")
        else:
             print(f"❌ FAIL: Prompt missing instruction. Content:\n{last_user_msg}")

        if "Put this in 'next_question' field" in last_user_msg:
             print("✅ PASS: Prompt contains strict 'next_question' field instruction.")
        else:
             print(f"❌ FAIL: Prompt missing next_question instruction.")


        # TEST 2: Final Report Logic (Turn 7 JSON Check)
        print("\n[TEST 2] Verifying Final Report Prompt & Keys (Turn 7)...")
        
        # Update Mock for Final Report to return EXPECTED structure
        mock_completion.choices[0].message.content = json.dumps({
            "formatted_report": "<html>Valid Report</html>",
            "average_score": 4.2,
            "q6_feedback_spoken": "Done."
        })
        
        payload_q7 = {
            "action": "feedback",
            "questionCount": 7,
            "history": [{"question": "Q", "answer": "A", "score": 4}] * 5,
            "message": "Final Answer"
        }
        resp = client.post('/api/get-feedback', json=payload_q7)
        
        # Inspect Prompt
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args[1]['messages']
        system_prompt = messages[0]['content'] # System prompt is first
        
        if "OUTPUT JSON FORMAT (Critical)" in system_prompt:
            print("✅ PASS: System Prompt enforces 'OUTPUT JSON FORMAT'.")
        else:
            print("❌ FAIL: System prompt missing JSON enforcement.")

        if "formatted_report" in system_prompt:
             print("✅ PASS: System Prompt requires 'formatted_report' key.")
        else:
             print("❌ FAIL: System prompt missing 'formatted_report' key requirement.")
             
        # Verify Response
        if resp.status_code == 200:
             print(f"✅ PASS: API returned 200 OK.")
             data = resp.get_json()
             if data['response'].get('formatted_report') == "<html>Valid Report</html>":
                 print("✅ PASS: Response contains correct 'formatted_report'.")
             else:
                 print(f"❌ FAIL: Response missing report. keys: {data['response'].keys()}")
        else:
             print(f"❌ FAIL: API Error {resp.status_code}")

    print("\n=== VERIFICATION COMPLETE ===")

if __name__ == "__main__":
    run_verification()
