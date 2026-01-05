import sys
from unittest.mock import MagicMock
import os
import json

# --- MOCK SETUP ---
mock_openai = MagicMock()
mock_client = MagicMock()
mock_completion = MagicMock()
mock_completion.choices[0].message.content = "{}"
mock_client.chat.completions.create.return_value = mock_completion
mock_openai.OpenAI.return_value = mock_client
sys.modules["openai"] = mock_openai
mock_supabase = MagicMock()
sys.modules["supabase"] = mock_supabase

os.environ["OPENAI_API_KEY"] = "dummy"
# Import App
from api.index import app

def run_v6_4_test():
    print("=== PROTOCOL v6.4 VERIFICATION (Firewall & Gag Rule) ===")
    
    with app.test_client() as client:
        # TEST 1: INTERVIEWER PROMPT (Phase 3) -> Gag Rule
        print("\n[TEST 1] Verifying Phase 3 Output Gag Rule...")
        client.post('/api/get-feedback', json={
            "action": "feedback", "questionCount": 3, "history": [], "message": "Test"
        })
        
        calls = mock_client.chat.completions.create.call_args_list
        interviewer_prompt = ""
        for call in calls:
            args, kwargs = call
            for m in kwargs.get('messages', []):
                if "Role: You are" in str(m.get('content')):
                    interviewer_prompt = m['content']
        
        if "NEGATIVE CONSTRAINT" in interviewer_prompt and "STRICTLY FORBIDDEN" in interviewer_prompt:
             print("✅ PASS: Gag Rule (Negative Constraint) found in Interviewer Prompt.")
        else:
             print("❌ FAIL: Gag Rule missing.")

        # TEST 2: AUDITOR PROMPT (Phase 5) -> Greeting Firewall
        print("\n[TEST 2] Verifying Phase 5 Greeting Firewall...")
        client.post('/api/get-feedback', json={
            "action": "feedback", "questionCount": 7, "history": [], "message": "Final"
        })
        
        calls = mock_client.chat.completions.create.call_args_list
        auditor_prompt = ""
        for call in calls:
            args, kwargs = call
            for m in kwargs.get('messages', []):
                if "ACE INTERVIEW REPORT" in str(m.get('content')):
                    auditor_prompt = m['content']

        if "STEP 0: GREETING FILTER" in auditor_prompt:
             print("✅ PASS: Greeting Firewall (Step 0) found in Auditor Prompt.")
        else:
             print("❌ FAIL: Greeting Firewall missing.")
             
        if "Index 0" in auditor_prompt and "biographical details" in auditor_prompt:
             print("✅ PASS: 'Biographical Check' logic confirmed.")
        else:
             print("❌ FAIL: Detailed Firewall logic missing.")

    print("\n=== TEST COMPLETE ===")

if __name__ == "__main__":
    run_v6_4_test()
