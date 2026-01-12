import json
import re

# --- MOCK GUARDRAIL LOGIC (Copied/Adapted from api/index.py) ---
def run_guardrail_test(user_data, ai_json, resume_text):
    print("\n--- TEST RUN ---")
    print(f"INPUT AI JSON: {json.dumps(ai_json['education'], indent=2)}")
    
    # --- EDUCATION GUARDRAIL ---
    output_edu = ai_json.get('education', [])
    input_edu = user_data.get('education', [])
    
    # Check 0: ANTI-HALLUCINATION VALIDATION
    is_education_valid = True
    if output_edu and len(output_edu) > 0:
        for edu in output_edu:
            school = str(edu.get('school', '')).lower()
            degree = str(edu.get('degree', '')).lower()
            dates = str(edu.get('dates', '')).lower()
            
            # Hallucination Signals
            if "relevant field" in degree or "accredited university" in school or "yyyy" in dates or "university name" in school:
                 print(f"GUARDRAIL: Detected Hallucination -> {school} | {degree}")
                 is_education_valid = False
                 break
    
    # Check 1: AI Output is empty OR Invalid?
    if not output_edu or len(output_edu) == 0 or not is_education_valid:
        if not is_education_valid:
            print("GUARDRAIL ALERT: AI Education invalidated due to placeholders.")
        else:
            print("GUARDRAIL ALERT: AI dropped Education.")
        
        # Check 2: Try Input Data
        if input_edu and len(input_edu) > 0:
            print("GUARDRAIL: Restoring from User Input.")
            ai_json['education'] = input_edu
        else:
            # Check 3: Regex Fallback (The Safety Net)
            print("GUARDRAIL: Parsing Raw Text for Education...")
            regex_edu = []
            lines = resume_text.split('\n')
            for line in lines:
                if len(line) > 100: continue 
                l = line.lower()
                if any(x in l for x in ['bachelor', 'master', 'mba', 'phd', 'associate', 'university', 'college', 'institute', 'degree']):
                    regex_edu.append({
                        "school": line.strip(),
                        "degree": "Detected in Resume Text", 
                        "dates": ""
                    })
            
            if regex_edu:
                print(f"GUARDRAIL: Restored {len(regex_edu)} education items from raw text.")
                ai_json['education'] = regex_edu
    
    return ai_json

# --- TEST CASES ---

# Case 1: The "Hallucination" (Should Trigger Fallback)
raw_text = """
David Kish
Strayer University
Bachelor of Business Administration - BBA
2018 - 2025
"""

fail_json = {
    "education": [
        { "school": "An Accredited University", "degree": "Bachelor's Degree in a relevant field", "dates": "YYYY - YYYY" }
    ]
}

user_data_empty = { "education": [] }

print("\n>>> CASE 1: HALLUCINATION (Should Extract 'Strayer University')")
result1 = run_guardrail_test(user_data_empty, fail_json, raw_text)
print(f"RESULT 1: {json.dumps(result1['education'], indent=2)}")


# Case 2: Good Data (Should NOT Trigger Fallback)
good_json = {
    "education": [
        { "school": "Strayer University", "degree": "BBA", "dates": "2025" }
    ]
}
print("\n>>> CASE 2: GOOD DATA (Should Keep Original)")
result2 = run_guardrail_test(user_data_empty, good_json, raw_text)
print(f"RESULT 2: {json.dumps(result2['education'], indent=2)}")
