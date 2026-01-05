"""
Complete rubric implementation script - applies all changes cleanly
"""
import re

# Read the file
with open('/Users/davidkish/Desktop/AI Career Coach/api/index.py', 'r') as f:
    content = f.read()

# 1. Add calculate_rubric_score function (already done, skip)
# 2. Update prompt (already done skip)
# 3. Add parsing logic after line 682

insertion_point = '''             ai_response_text = chat_completion.choices[0].message.content
             print(f"DEBUG: AI Response: {ai_response_text[:100]}...")
             
             try:
                  ai_json = json.loads(ai_response_text)'''

replacement = '''             ai_response_text = chat_completion.choices[0].message.content
             print(f"DEBUG: AI Response: {ai_response_text[:100]}...")
             
             # v9.0 RUBRIC PARSING: Check for two-part format
             ai_json = None
             if "|||RUBRIC|||" in ai_response_text and question_count > 1:
                 # Parse two-part format
                 parts = ai_response_text.split("|||RUBRIC|||")
                 feedback_text = parts[0].strip()
                 rubric_json_str = parts[1].strip()
                 
                 try:
                     rubric_data = json.loads(rubric_json_str)
                     print(f"DEBUG: Rubric parsed - Q{question_count}")
                     
                     # Calculate score using Boolean Logic Gates
                     calculated_score, override_reason = calculate_rubric_score(
                         rubric_data, 
                         f"Q{question_count}", 
                         message
                     )
                     
                     # Build response with rubric data
                     ai_json = {
                         "feedback": feedback_text,
                         "internal_score": calculated_score,
                         "next_question": rubric_data.get("next_question", ""),
                         "rubric_data": rubric_data,
                         "gap_analysis": override_reason or rubric_data.get("gap_analysis", "")
                     }
                     
                     print(f"DEBUG: Q{question_count} Score={calculated_score}")
                     
                 except Exception as rubric_err:
                     print(f"WARN: Rubric parse error: {rubric_err}")
                     ai_json = None
             
             # Fallback: Standard JSON parsing
             if ai_json is None:
                  try:
                       ai_json = json.loads(ai_response_text)'''

# Replace
if insertion_point in content:
    content = content.replace(insertion_point, replacement)
    print("✓ Added rubric parsing logic")
else:
    print("✗ Parsing insertion point not found")

# 4. Remove response_format constraint
content = re.sub(
    r'(\s+chat_completion = client\.chat\.completions\.create\(\n\s+model="gpt-4o-mini",\n\s+messages=messages),\n\s+response_format=\{ "type": "json_object" \}',
    r'\1',
    content
)
print("✓ Removed JSON response format constraint")

# Write back
with open('/Users/davidkish/Desktop/AI Career Coach/api/index.py', 'w') as f:
    f.write(content)

print("✓ All changes applied successfully!")
