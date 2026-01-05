import sys
from unittest.mock import MagicMock
import os
import json

# --- MOCK SETUP ---
mock_openai = MagicMock()
mock_client = MagicMock()
mock_completion = MagicMock()

# Mock AI Response (The Auditor's Output)
# We make it explicitly return "Automation" as the topic for Q5 to prove Dynamic Anchoring works.
mock_completion.choices[0].message.content = json.dumps({
    "formatted_report": "<html>...</html>",
    "average_score": 3.0,
    "q6_feedback_spoken": "Good job.",
    "verdict_text": "RECOMMEND",
    # MOCKING THE INTERNAL DECISION PROCESS (Usually hidden, but we verify the output structure)
    "debug_topic_q5": "Automation" 
})
mock_client.chat.completions.create.return_value = mock_completion

mock_openai.OpenAI.return_value = mock_client
sys.modules["openai"] = mock_openai
mock_supabase = MagicMock()
sys.modules["supabase"] = mock_supabase

os.environ["OPENAI_API_KEY"] = "dummy"
os.environ["SUPABASE_URL"] = "dummy"
os.environ["SUPABASE_KEY"] = "dummy"

from api.index import app

def run_auditor_test():
    print("=== AUDITOR ARCHITECTURE VERIFICATION (v6.2) ===")
    
    with app.test_client() as client:
        # TEST: Simulate Mismatch Topic (Q5: Automation vs Motivation)
        print("\n[TEST] Verifying Dynamic Anchoring (Q5: Automation)...")
        
        # We need to trigger the FINAL REPORT generation.
        # This usually happens when 'action' is 'feedback' and 'questionCount' is 6? 
        # Or maybe there's a specific flag. 
        # Looking at code: if question_count >= 6, it generates report? No, checking logic...
        # It generates report if `question_count` sent is 6 AND it's finish time?
        # Actually, let's just inspect the PROMPT generation by mocking the request.
        
        # We'll rely on inspecting the CALL ARGS to `client.chat.completions.create` 
        # to ensure the SYSTEM PROMPT contains our new instructions.
        
        payload = {
            "action": "feedback",
            "questionCount": 7, # Needs to be > 6 to trigger Final Report
            "history": [
                {"role": "assistant", "content": "Q1"}, {"role": "user", "content": "A1"},
                {"role": "assistant", "content": "Q2"}, {"role": "user", "content": "A2"},
                {"role": "assistant", "content": "Q3"}, {"role": "user", "content": "A3"},
                {"role": "assistant", "content": "Q4"}, {"role": "user", "content": "A4"},
                {"role": "assistant", "content": "Q5: Tell me about Automation."}, {"role": "user", "content": "I used Python."},
            ],
            "message": "Final Answer"
        }
        
        client.post('/api/get-feedback', json=payload)
        
        # Verify the System Prompt sent to OpenAI
        call_args = mock_client.chat.completions.create.call_args_list
        # We might have multiple calls (Feedback vs Auditor). We want the one with "ACE INTERVIEW REPORT".
        
        auditor_call = None
        for call in call_args:
            args, kwargs = call
            messages = kwargs.get('messages', [])
            for m in messages:
                if "ACE INTERVIEW REPORT" in m['content']:
                    auditor_call = m['content']
                    break
        
        if auditor_call:
            print("✅ PASS: Auditor Prompt Found.")
            if "DYNAMIC ANCHORING" in auditor_call:
                print("✅ PASS: 'DYNAMIC ANCHORING' instruction present.")
            else:
                print("❌ FAIL: Old 'CONTENT ANCHORING' or missing instruction.")
                
            if "DEFAULT FLOOR" in auditor_call:
                 print("✅ PASS: 'DEFAULT FLOOR' instruction present.")
            else:
                 print("❌ FAIL: 'DEFAULT FLOOR' instruction missing.")
                 
            if "Do NOT force hard-coded topics" in auditor_call:
                 print("✅ PASS: 'No hard-coded topics' instruction present.")
            else:
                 print("❌ FAIL: Hard-coded topic warning missing.")
        else:
            print("❌ FAIL: Auditor Prompt NOT found in API calls.")

    print("\n=== TEST COMPLETE ===")

if __name__ == "__main__":
    run_auditor_test()
