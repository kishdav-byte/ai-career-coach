import re

def extract_education(resume_text):
    print(f"\nAnalyzing Text (Length: {len(resume_text)} chars)...")
    extracted_edu_lines = []
    
    # Simulate the logic in api/index.py
    # 1. Split lines
    lines = resume_text.split('\n')
    
    # 2. Iterate
    for i, line in enumerate(lines):
        line = line.strip() # Simulating strip
        if not line: continue
        
        # Condition A: Length Check
        if len(line) > 300: 
            print(f"Skipping Line {i} (Length {len(line)} > 300): {line[:50]}...")
            continue 
            
        l = line.lower()
        # Condition B: Keyword Check
        if any(x in l for x in ['bachelor', 'master', 'mba', 'phd', 'associate', 'university', 'college', 'institute', 'degree']):
             print(f"Match Found Line {i}: {line}")
             extracted_edu_lines.append(line)
        else:
             # print(f"No Match Line {i}: {line}")
             pass
             
    return extracted_edu_lines

def identity_check(current_name, real_name, real_email):
    print(f"\nChecking Identity: Current='{current_name}' | Real='{real_name}' | Email='{real_email}'")
    
    # Fallback Logic
    if not real_name and real_email:
        name_part = real_email.split('@')[0]
        real_name = ' '.join([n.capitalize() for n in re.split(r'[._-]', name_part)])
        print(f"Derived Name from Email: {real_name}")

    # Override Logic
    # UPDATED LOGIC TO TEST: Case Insensitivity + Partial Match
    if not current_name or current_name in ["N/A", "Your Name", "Full Name", ""] or "your name" in current_name.lower() or len(current_name) < 3:
        final_name = real_name or "Executive Candidate"
        print(f"Override Triggered. Final Name: {final_name}")
        return final_name
    
    print("No Override. Keeping Current Name.")
    return current_name

# --- SCENARIOS ---

print("=== SCENARIO 1: Standard Format ===")
text1 = """
David Kish
Strayer University
Bachelor of Business Administration - BBA
2018 - 2025
"""
res1 = extract_education(text1)
print(f"Result 1: {res1}")

print("\n=== SCENARIO 2: Blob Format (One Line) ===")
# This simulates PDF parsing failure where newlines are lost
text2 = "David Kish Strayer University Bachelor of Business Administration - BBA 2018 - 2025 Experience Manager at Verizon..."
res2 = extract_education(text2)
print(f"Result 2: {res2}")

print("\n=== SCENARIO 3: Identity Check ===")
identity_check("Your Name", None, "david.kish@example.com")
identity_check("your name", None, "kishdav@example.com")
