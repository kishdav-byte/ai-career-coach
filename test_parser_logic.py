import sys
import os
import json

# Add api directory to path so we can import app
sys.path.append(os.path.abspath('api'))

# Mock the environment if needed, but app.py loads dotenv
from app import call_openai

# The "Dirty" Text from the User's Issue
raw_text = """
David Kish
kishdav@gmail.com | 8649099115 |
Professional Summary
Dynamic and results-driven operations leader with over 34 years of diverse experience managing teams.
Experience
Senior Manager, Insights & DecisionsMarch 2024 - Present
Verizon
Verizon logo Verizon Verizon Full-time · 27 yrs 8 mosFull-time · 27 yrs 8 mos
Senior Manager, Strategic Process DesignMarch 2021 - March 2024
Verizon
"""

system_msg = """You are a precise Resume Parsing Engine. Convert raw PDF text into structured JSON.

CRITICAL RULES:
1. Fix Merged Text: PDF extraction often merges Title and Date (e.g., "Senior ManagerMarch 2024"). You MUST split these into Role and Date.
2. Ignore Artifacts: Do not parse lines like "Verizon logo" or repetitive headers as content.
3. Infer Missing Formatting: Capitalize names, fix spacing.

RETURN JSON SCHEMA:
{
    "personal": {"name": "", "email": "", "phone": "", "location": "", "linkedin": "", "summary": ""},
    "skills": ["skill1", "skill2"],
    "experience": [{"role": "", "company": "", "dates": "", "description": ""}],
    "education": [{"degree": "", "school": "", "dates": ""}]
}
Return ONLY valid JSON.
"""

user_msg = f"Resume Text:\n{raw_text}"

messages = [
    {"role": "system", "content": system_msg},
    {"role": "user", "content": user_msg}
]

print("Running AI Parsers Test...")
try:
    response_text = call_openai(messages, json_mode=True)
    print("\n--- RAW RESPONSE ---\n")
    print(response_text)
    
    data = json.loads(response_text)
    print("\n--- PARSED DATA ---\n")
    print(json.dumps(data, indent=2))
    
    # Verification Logic
    exp = data.get('experience', [])
    if len(exp) > 0:
        role = exp[0].get('role')
        date = exp[0].get('dates')
        print(f"\n[VERIFICATION] Role: '{role}' | Date: '{date}'")
        
        if "March 2024" in date and "Manager" in role and "March" not in role:
            print("✅ SUCCESS: Merged text was split correctly!")
        else:
            print("❌ FAILURE: Text was not split correctly.")
            
except Exception as e:
    print(f"Test Failed: {e}")
