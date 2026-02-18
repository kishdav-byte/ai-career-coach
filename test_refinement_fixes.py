#!/usr/bin/env python3
import os
import sys
import json
import base64

# Setup paths
sys.path.insert(0, '/Users/davidkish/Desktop/AI Career Coach')

from api.index import app
import api.index as api_module

# Helper to run a request
def run_get_feedback(message, question_count, history=[], is_start=False):
    client = app.test_client()
    data = {
        "message": message,
        "questionCount": question_count,
        "history": history,
        "isStart": is_start,
        "job_title": "Senior AI Manager",
        "jobPosting": "Leading AI product transition and analytics.",
        "resumeText": "AI expert with 15 years experience."
    }
    response = client.post('/api/get-feedback', json=data)
    return response.get_json()

print("--- TEST 3: STAR PLACEMENT ---")
# Simulating real_q_num = 2 (Candidate answering Background Question)
background_answer = "I have 15 years in AI and built the Total Package platform."
res_turn2 = run_get_feedback(background_answer, 2)
feedback = res_turn2['response']['feedback']
next_q = res_turn2['response']['next_question']

print(f"FEEDBACK (Turn 2): {feedback[:100]}...")
print(f"NEXT QUESTION (Turn 2): {next_q}")

if "STAR method" in next_q:
    print("✅ SUCCESS: STAR method found in next_question.")
elif "STAR method" in feedback:
    print("❌ FAILURE: STAR method found in feedback (wrong location).")
else:
    print("❌ FAILURE: STAR method NOT found.")

print("\n--- TEST 1: SCORE THRESHOLD (3.4) ---")
# We need to trigger the final report generation logic
# I'll mock the internal variables to simulate a 3.4 average
from api.index import calculate_rubric_score

# Mocking a history that averages to ~3.4
# 7 turns total, scores: [4, 3, 3, 4, 3, 3] -> 20/6 = 3.33
# Or [4, 4, 3, 3, 3, 3] -> 20/6 = 3.33
mock_history = [
    {"question": "Q1", "answer": "A1", "internal_score": 4},
    {"question": "Q2", "answer": "A2", "internal_score": 4},
    {"question": "Q3", "answer": "A3", "internal_score": 3},
    {"question": "Q4", "answer": "A4", "internal_score": 3},
    {"question": "Q5", "answer": "A5", "internal_score": 3},
    {"question": "Q6", "answer": "A6", "internal_score": 3},
]

# We trigger Turn 8 (Final Report)
res_turn8 = run_get_feedback("GENERATE_REPORT", 8, history=mock_history)
report = res_turn8['response']['formatted_report']
avg = res_turn8['response']['average_score']

print(f"Report Average Score: {avg}")
if "Well Done" in report and "Average" not in report:
     # Wait, the search might be tricky depending on how it's rendered
     # Label is in a div with text-indigo-300
     import re
     label_match = re.search(r'text-indigo-300[^>]*>([^<]+)<', report)
     if label_match:
         label = label_match.group(1).strip()
         print(f"Label found in report: {label}")
         if label == "Well Done" and avg >= 3.3 and avg < 3.5:
             print("✅ SUCCESS: 3.33 mapped to 'Well Done'.")
         else:
             print(f"❌ FAILURE: Mapping check failed for {avg} -> {label}")
     else:
         print("❌ FAILURE: Could not find label in report.")
else:
    print("❌ FAILURE: 'Well Done' tag not detected in report string.")

print("\n--- TEST 2: ANTI-NAG ---")
# Check if growth areas include 'metrics' when metrics are present
# This requires looking at the actually generated growth areas from AI
# I'll check a few lines of the Growth Areas section
if "Growth Areas" in report:
    growth_section = report.split("Growth Areas")[1].split("</ul>")[0]
    print(f"Growth Areas Content: {growth_section[:200]}...")
    if "metric" in growth_section.lower() or "quantify" in growth_section.lower():
         print("⚠️ WARNING: AI still nagging about metrics? (Check manually if appropriate)")
    else:
         print("✅ SUCCESS: No metric nagging detected in growth areas.")
