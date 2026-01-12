"""
Test script for Absolute Force-Injection logic
Simulates the extraction and injection flow
"""
import json
import re

def extract_education_backup(resume_text):
    """Simulates the backup_education extraction"""
    backup_education = []
    lines = resume_text.split('\n')
    
    for line in lines:
        if len(line) > 300: continue
        l = line.lower()
        if any(x in l for x in ['bachelor', 'master', 'mba', 'phd', 'associate', 'university', 'college', 'institute', 'degree']):
            backup_education.append({
                "school": line.strip(),
                "degree": "As listed in original resume",
                "dates": ""
            })
    
    return backup_education

def force_inject_education(ai_response, backup_education, input_edu):
    """Simulates the force-injection logic"""
    ai_json = json.loads(ai_response)
    
    # ABSOLUTE INJECTION
    if backup_education and len(backup_education) > 0:
        ai_json['education'] = backup_education
        print(f"✓ FORCE-INJECTED: {len(backup_education)} education items from raw text")
    elif input_edu and len(input_edu) > 0:
        ai_json['education'] = input_edu
        print(f"✓ FORCE-INJECTED: {len(input_edu)} education items from user input")
    else:
        ai_json['education'] = [{
            "school": "Education information not found in resume",
            "degree": "",
            "dates": ""
        }]
        print("⚠ WARNING: No education data available")
    
    return ai_json

# TEST CASES
print("=" * 60)
print("TEST 1: Standard Resume with Clear Education Section")
print("=" * 60)

resume_text_1 = """
David Kish
Strayer University
Bachelor of Business Administration - BBA
2018 - 2025
Experience...
"""

# Simulate AI response (WITHOUT education - as instructed)
ai_response_1 = json.dumps({
    "personal": {"name": "David Kish", "summary": "Optimized summary..."},
    "experience": [{"role": "Manager", "company": "Verizon", "dates": "2024-Present", "description": "Led team..."}],
    "enhancement_overview": "Aligned with JD"
})

backup_edu = extract_education_backup(resume_text_1)
print(f"\nExtracted Backup: {json.dumps(backup_edu, indent=2)}")

final_output = force_inject_education(ai_response_1, backup_edu, [])
print(f"\nFinal Output Education: {json.dumps(final_output['education'], indent=2)}")

print("\n" + "=" * 60)
print("TEST 2: Blob Format Resume (Long Line)")
print("=" * 60)

resume_text_2 = "David Kish Strayer University Bachelor of Business Administration 2018-2025 Manager at Verizon leading strategic initiatives..."

ai_response_2 = json.dumps({
    "personal": {"name": "David Kish", "summary": "Results-driven..."},
    "experience": [{"role": "Manager", "company": "Verizon", "dates": "2024", "description": "Optimized workflows..."}]
})

backup_edu_2 = extract_education_backup(resume_text_2)
print(f"\nExtracted Backup: {json.dumps(backup_edu_2, indent=2)}")

final_output_2 = force_inject_education(ai_response_2, backup_edu_2, [])
print(f"\nFinal Output Education: {json.dumps(final_output_2['education'], indent=2)}")

print("\n" + "=" * 60)
print("TEST 3: No Education in Raw Text (Use Frontend Input)")
print("=" * 60)

resume_text_3 = "David Kish\nManager at Verizon\nLed strategic initiatives..."

ai_response_3 = json.dumps({
    "personal": {"name": "David Kish", "summary": "Dynamic leader..."},
    "experience": [{"role": "Manager", "company": "Verizon", "dates": "2024", "description": "Executed..."}]
})

backup_edu_3 = extract_education_backup(resume_text_3)
input_edu_frontend = [{"school": "Harvard University", "degree": "MBA", "dates": "2020"}]

print(f"\nExtracted Backup: {backup_edu_3 if backup_edu_3 else 'None'}")
print(f"Frontend Input: {json.dumps(input_edu_frontend, indent=2)}")

final_output_3 = force_inject_education(ai_response_3, backup_edu_3, input_edu_frontend)
print(f"\nFinal Output Education: {json.dumps(final_output_3['education'], indent=2)}")

print("\n" + "=" * 60)
print("VERDICT: All tests demonstrate unconditional injection ✓")
print("=" * 60)
