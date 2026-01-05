import sys
from unittest.mock import MagicMock
import os
import json

# --- MOCK SETUP ---
mock_openai = MagicMock()
mock_client = MagicMock()
mock_completion = MagicMock()

# Mock AI Response
mock_completion.choices[0].message.content = json.dumps({
    "formatted_report": "<html>...<h4>Q1: Python Automation</h4>...</html>",
    "average_score": 4.0,
    "q6_feedback_spoken": "Great.",
    "verdict_text": "RECOMMEND"
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

def run_smart_header_test():
    print("=== SMART HEADER & PURGE VERIFICATION (v6.3) ===")
    
    with app.test_client() as client:
        # TEST: Transcript with "Start" noise
        print("\n[TEST] Verifying Transcript Purge & Prompt Instructions...")
        
        payload = {
            "action": "feedback",
            "questionCount": 7,
            "history": [
                {"question": "Intro", "answer": "Start", "feedback": "None"}, # Should be PURGED
                {"question": "Q1: Tell me about yourself", "answer": "I am a Data Analyst.", "feedback": "Good"},
                {"question": "Q2: Conflict", "answer": "I resolved a conflict.", "feedback": "Okay"}
            ],
            "message": "Final Answer"
        }
        
        client.post('/api/get-feedback', json=payload)
        
        # Verify the System Prompt sent to OpenAI
        call_args = mock_client.chat.completions.create.call_args_list
        
        # Debug: Print all calls
        # print(call_args)
        
        auditor_sys_prompt = ""
        user_prompt = ""
        
        for call in call_args:
            args, kwargs = call
            messages = kwargs.get('messages', [])
            for m in messages:
                if "ACE INTERVIEW REPORT" in str(m.get('content')):
                    auditor_sys_prompt = m['content']
                if "TRANSCRIPT:" in str(m.get('content')):
                    user_prompt = m['content']

        # CHECK 1: Purge Logic
        if "Start" in user_prompt:
             print("❌ FAIL: 'Start' message found in Transcript. Purge failed.")
        elif "Q: Intro" in user_prompt:
             # Wait, if Q is short filtering might catch it. "Intro" is len 5.
             print("❌ FAIL: 'Intro'/'Start' pair found.")
        else:
             print("✅ PASS: 'Start' message purged from Transcript.")

        # CHECK 2: Smart Header Instruction
        if "Smart Header" in auditor_sys_prompt:
             print("✅ PASS: 'Smart Header' generation instruction found.")
        else:
             print("❌ FAIL: Smart Header instruction missing.")

        # CHECK 3: HTML Template placeholders
        if "{{Q1_SMART_HEADER}}" in auditor_sys_prompt:
             print("✅ PASS: HTML Template uses {{Q1_SMART_HEADER}}.")
        else:
             print("❌ FAIL: HTML Template logic missing.")

    print("\n=== TEST COMPLETE ===")

if __name__ == "__main__":
    run_smart_header_test()
