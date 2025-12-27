import requests
import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# CONFIGURATION
# Corrected Endpoint: The user originally said /api/speak but codebase uses /api/get-feedback for scoring
API_URL = "http://127.0.0.1:5001" 
OPENAI_CLIENT = OpenAI(api_key=os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY_"))

# THE CANDIDATE PERSONAS
PERSONAS = {
    "The Executive (5/5)": "You are a perfect candidate. Answer using strict STAR method. Include metrics ($/%) in every result.",
    "The Junior (3/5)": "You are a junior employee. Give vague answers. Describe the situation well, but forget to mention the result.",
    "The Quitter (1/5)": "You are terrible. Give one-sentence answers. Cut off your sentences mid-thought. Be rude."
}

def run_simulation(persona_name, max_turns=8):
    print(f"\n🚀 STARTING SIMULATION: {persona_name}")
    print("="*60)
    
    # 1. Start the Session (Initialize Roadmap)
    # We need to hit the endpoint with isStart=True first to generate the roadmap
    start_payload = {
        "email": "test_bot@example.com",
        "jobPosting": "MISSION BRIEFING:\nTarget Role: Director of Analytics at Acme Corp.\n\nMISSION PRIORITIES (FOCUS AREAS):\n1. Drive Enterprise Strategy\n2. Reduce Data Costs by 20%\n3. Build a High-Performance Team",
        "isStart": True
    }
    
    try:
        # Start Request
        resp = requests.post(f"{API_URL}/api/get-feedback", json=start_payload)
        print(f"Start Response: {resp.status_code} - {resp.text[:200]}")
        # We don't need the response here, just triggering the roadmap gen
    except Exception as e:
        print(f"Start Error: {e}")

    # Mock Initial State
    history = []
    last_ai_question = "Tell me about yourself."
    
    # 2. Loop through the Interview
    # Default 6 turns (Intro + 5 Questions)
    # We want to verify it stops at the right time.
    # max_turns arg is used directly 
    
    for turn in range(1, max_turns + 1):
        # A. GENERATE THE CANDIDATE'S ANSWER
        system_instruction = PERSONAS.get(persona_name, PERSONAS["The Executive (5/5)"])
        candidate_prompt = f"""
        {system_instruction}
        
        The Interviewer just asked: "{last_ai_question}"
        
        Write your spoken response (Keep it under 3 sentences for speed).
        """
        
        candidate_response = OPENAI_CLIENT.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": candidate_prompt}]
        )
        answer_text = candidate_response.choices[0].message.content
        print(f"🗣️ CANDIDATE (Turn {turn}): {answer_text}")

        # B. SEND TO YOUR APP (The Test)
        payload = {
            "email": "test_bot@example.com",
            "text_override": answer_text,
            "message": answer_text,
            "history": history,
            "questionCount": turn + 1
        }
        
        try:
            response = requests.post(f"{API_URL}/api/get-feedback", json=payload)
            data = response.json()
            
            # Check for completion
            if data.get('is_complete'):
                print("🏁 INTERVIEW COMPLETE (Signal Received)")
                
                # C. GENERATE FINAL REPORT
                print("\n📄 GENERATING FINAL REPORT...")
                report_payload = {
                    "action": "generate_report",
                    "email": "test_bot@example.com",
                    "history": history
                }
                report_resp = requests.post(f"{API_URL}/api", json=report_payload)
                report_data = report_resp.json()
                
                if report_data.get('report') or (report_data.get('data') and report_data['data'].get('report')):
                    report_content = report_data.get('report') or report_data['data']['report']
                    print(f"✅ REPORT GENERATED ({len(report_content)} bytes)")
                    if "Executive Summary" in report_content:
                         print("✅ VERIFIED: Contains 'Executive Summary'")
                    else:
                         print("⚠️ WARNING: 'Executive Summary' not found in report.")
                else:
                    print(f"❌ REPORT FAILED: {report_data}")
                
                break
                
            ai_resp = data.get('response', {})
            ai_grade = ai_resp.get('score', 0)
            ai_feedback = ai_resp.get('feedback', 'No feedback')
            next_q = ai_resp.get('next_question', 'End')
            
            print(f"🤖 APP JUDGE: Score {ai_grade}/5")
            print(f"📝 FEEDBACK: {str(ai_feedback)[:100]}...") 
            
            print("-" * 60)
            
            # Update history and loop
            history.append({"role": "user", "content": answer_text})
            # IMPORTANT: The history expects the AI's question, not just the feedback
            history.append({"role": "assistant", "content": next_q})
            last_ai_question = next_q
            
        except Exception as e:
            print(f"💥 CRASH: {e}")
            break

# RUN THE TESTS
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run AI Interview Simulation")
    parser.add_argument("--persona", type=str, default="The Executive (5/5)", 
                        help="Persona to simulate: 'The Executive (5/5)', 'The Junior (3/5)', 'The Quitter (1/5)'")
    parser.add_argument("--turns", type=int, default=8, help="Max turns to run")
    parser.add_argument("--url", type=str, default="http://127.0.0.1:5001", help="Target API URL (e.g. https://your-app.com)")
    parser.add_argument("--list-personas", action="store_true", help="List available personas")
    
    args = parser.parse_args()
    
    # Update Global API_URL based on CLI arg
    API_URL = args.url
    
    if args.list_personas:
        print("Available Personas:")
        for p in PERSONAS.keys():
            print(f" - {p}")
    else:
        # Fuzzy match for convenience
        selected_persona = args.persona
        if args.persona not in PERSONAS:
            for p in PERSONAS.keys():
                if args.persona.lower() in p.lower():
                    selected_persona = p
                    break
        
        # Pass turns arg if needed, but run_simulation function needs to accept it.
        # Check if run_simulation is defined to accept max_turns or if it reads from parsing?
        # The run_simulation function I defined takes (persona_name).
        # I need to modify run_simulation signature or use global/args inside it.
        # Let's modify the function definition line first in a separate replace?
        # Or I can just set a global or pass it.
        # I'll modify the function signature in the MultiReplace or just rely on global scope is risky.
        # I'll update the function signature in this same tool call if possible?
        # No, safe to do it in two steps or just update the whole file logic?
        # I'll update line 40 where loop starts to use args.turns if I can pass it.
        
        # Actually, simpler: just update run_simulation to take max_turns param.
        run_simulation(selected_persona, args.turns)
