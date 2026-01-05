"""
Apply all three bug fixes cleanly
"""
import re

# Read the file
with open('/Users/davidkish/Desktop/AI Career Coach/api/index.py', 'r') as f:
    content = f.read()

# Fix 1: Change > 1 to >= 1 for Q1 rubric parsing
content = content.replace(
    'if "|||RUBRIC|||" in ai_response_text and question_count > 1:',
    'if "|||RUBRIC|||" in ai_response_text and question_count >= 1:'
)
print("✓ Bug 1 fixed: Q1 rubric parsing enabled")

# Fix 2: Remove "silent score" terminology
content = content.replace(
    '"2. Session_Metadata (The hidden SILENT SCORES assigned during live session)\\n\\n"',
    '"2. Question_Scores (The scores assigned to each question during the interview)\\n\\n"'
)
content = content.replace(
    '"Instruction: Compile the final report using Topic Anchoring and Silent Retrieval.\\n\\n"',
    '"Instruction: Compile the final report using Topic Anchoring and the provided scores.\\n\\n"'
)
content = content.replace(
    '"When reviewing the Silent Scores from Session Metadata:\\n"',
    '"Use the provided Question Scores from the session data:\\n"'
)
content = content.replace(
    '"- TRUST the Silent Scores UNLESS they violate these rules:\\n"',
    '"- TRUST the provided scores UNLESS they violate these rules:\\n"'
)
content = content.replace(
    '"  * IF Silent Score = 1 but answer is substantial -> OVERRIDE to Score = 2.\\n\\n"',
    '"  * IF score is 1 but answer has 20+ words -> OVERRIDE to Score = 2.\\n"'
    '                 "- CRITICAL: Do NOT mention \\'scores\\', \\'metadata\\', or any internal system terminology in the analysis text visible to the user.\\n\\n"'
)
print("✓ Bug 2 fixed: Silent score meta-talk removed")

# Fix 3: Move regex scrubbing outside fallback block
# Find the section with v7.2 REGEX within the try block and remove it
old_regex_block = '''                      
                      # v7.2 REGEX SAFETY NET
                      import re
                      score_pattern = r'\\b(Score|Rating):\\s*\\d+/\\d+\\b'
                      
                      if "feedback" in ai_json:
                          feedback = ai_json["feedback"]
                          feedback = re.sub(score_pattern, '', feedback, flags=re.IGNORECASE)
                          feedback = re.sub(r'\\b\\d+/\\d+\\b', '', feedback)
                          feedback = re.sub(r'\\s+', ' ', feedback).strip()
                          ai_json["feedback"] = feedback
                      
                      if "next_question" in ai_json:
                          next_q = ai_json["next_question"]
                          next_q = re.sub(score_pattern, '', next_q, flags=re.IGNORECASE)
                          next_q = re.sub(r'\\b\\d+/\\d+\\b', '', next_q)
                          next_q = re.sub(r'\\s+', ' ', next_q).strip()
                          ai_json["next_question"] = next_q
                          '''

new_regex_placement = '''
              
              # v9.1 UNIVERSAL REGEX SCRUBBING: Apply to ALL feedback (rubric or JSON)
              import re
              score_pattern = r'\\b(Score|Rating):\\s*\\d+/\\d+\\b'
              
              if ai_json and "feedback" in ai_json:
                  feedback = ai_json["feedback"]
                  feedback = re.sub(score_pattern, '', feedback, flags=re.IGNORECASE)
                  feedback = re.sub(r'\\b\\d+/\\d+\\b', '', feedback)
                  feedback = re.sub(r'\\s+', ' ', feedback).strip()
                  ai_json["feedback"] = feedback
              
              if ai_json and "next_question" in ai_json:
                  next_q = ai_json["next_question"]
                  next_q = re.sub(score_pattern, '', next_q, flags=re.IGNORECASE)
                  next_q = re.sub(r'\\b\\d+/\\d+\\b', '', next_q)
                  next_q = re.sub(r'\\s+', ' ', next_q).strip()
                  ai_json["next_question"] = next_q
'''

# Remove the old regex block from within the try
content = content.replace(old_regex_block, '')

# Add the new one after the except block (before REPORT FORMATTING BRIDGE)
content = content.replace(
    '              # REPORT FORMATTING BRIDGE',
    new_regex_placement + '\n              # REPORT FORMATTING BRIDGE'
)

print("✓ Bug 3 fixed: Universal regex scrubbing applied")

# Write back
with open('/Users/davidkish/Desktop/AI Career Coach/api/index.py', 'w') as f:
    f.write(content)

print("✓ All three bug fixes applied successfully!")
