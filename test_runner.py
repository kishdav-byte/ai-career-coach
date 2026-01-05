import requests
import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# CONFIGURATION
API_URL = "http://127.0.0.1:5001" 
OPENAI_CLIENT = OpenAI(api_key=os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY_"))

def run_simulation(persona_name, max_turns=8):
    print(f"\n🚀 STARTING SIMULATION: {persona_name} (INTEGRITY TEST MODE)")
    print("="*60)
    
    # 1. Start the Session
    start_payload = {
        "email": "testuser@gmail.com",
        "jobPosting": "MISSION BRIEFING:\nTarget Role: Operations Team Lead at Academy Sports + Outdoors.\n\nMISSION PRIORITIES:\n1. Efficiency\n2. Compliance\n3. Team Leadership",
        "isStart": True
    }
    
    # HISTORY TRACKING (Simulating Frontend Memory)
    frontend_history = []
    
    try:
        resp = requests.post(f"{API_URL}/api/get-feedback", json=start_payload)
        data = resp.json()
        print(f"Start Response: {resp.status_code}")
        last_ai_question = data['response']['next_question']
    except Exception as e:
        print(f"Start Error: {e}")
        return

    
    for turn in range(1, max_turns + 1):
        # A. GENERATE THE CANDIDATE'S ANSWER
        if turn == 1:
             # TURN 1: Background (Safe Answer)
             answer_text = "I have 4 years experience as Front End Supervisor. I love the outdoors."
        elif turn == 2:
             # TURN 2: INTEGRITY VIOLATION (The Academy Sports Scenario)
             answer_text = "We had a long line at returns. Corporate policy said to open every box. I told my team to skip opening boxes if the customer looked trustworthy to speed things up. It worked, we cleared the line, but I took a risk on inventory accuracy."
        elif turn >= 3:
             # TURN 3+: GOOD ANSWERS
             answer_text = "I followed all procedures perfectly and led my team to success."
        
        print(f"🗣️ CANDIDATE (Turn {turn}): {answer_text[:100]}...")

        # B. SEND TO APP (With History!)
        payload = {
            "email": "testuser@gmail.com",
            "message": answer_text,
            "questionCount": turn + 1,
            "interviewer_intel": "Operations Team Lead. Academy Sports.",
            "job_title": "Operations Team Lead",
            "history": frontend_history # <--- MEMORY PATCH
        }
        
        try:
            response = requests.post(f"{API_URL}/api/get-feedback", json=payload)
            data = response.json()
            
            # MEMORY PATCH (Frontend Side Logic Simulation)
            frontend_history.append({"question": last_ai_question, "answer": answer_text})
            
            # Check for completion
            ai_resp = data.get('response', {})
            ai_feedback = ai_resp.get('feedback', 'No feedback')
            next_q = ai_resp.get('next_question', 'End')
            
            if turn > 5:
                # FINAL REPORT CHECK
                print(f"🤖 RAW RESPONSE: {json.dumps(ai_resp, indent=2)}")
                print(f"🤖 APP JUDGE (FULL): {str(ai_feedback)}")
            else:
                print(f"🤖 APP JUDGE: {str(ai_feedback)[:200]}...")
                print(f"NEXT Q: {str(next_q)[:200]}...")

            if data.get('is_complete'):
                print("🏁 INTERVIEW COMPLETE")
                break
            
            last_ai_question = next_q
            print("-" * 60)
            
        except Exception as e:
            print(f"💥 CRASH: {e}")
            break

import argparse
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--turns", type=int, default=7)
    parser.add_argument("--url", type=str, default="http://127.0.0.1:5001")
    args = parser.parse_args()
    API_URL = args.url
    run_simulation("The Rule Breaker", args.turns)
