"""
Script to update api/index.py with rubric parsing logic
"""

# Read the file
with open('/Users/davidkish/Desktop/AI Career Coach/api/index.py', 'r') as f:
    lines = f.readlines()

# Find the insertion point (after line 683, which is print statement with index 682)
insert_idx = 684  # After the blank line

# Create the new rubric parsing block
rubric_block = '''             # v9.0 RUBRIC PARSING: Check for two-part format
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
'''

# Insert the block
lines.insert(insert_idx, rubric_block)

# Write back
with open('/Users/davidkish/Desktop/AI Career Coach/api/index.py', 'w') as f:
    f.writelines(lines)

print("✓ Successfully inserted rubric parsing logic at line", insert_idx)
