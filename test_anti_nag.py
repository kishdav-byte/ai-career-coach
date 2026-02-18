#!/usr/bin/env python3
import os
import sys
import json

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

print("--- TEST 2+: REAL ANTI-NAG ---")
# Providing a high-performance history WITH metrics
high_perf_history = [
    {"question": "Q1", "answer": "I have 15 years in AI and built the Total Package platform with $35M EBITDA growth.", "internal_score": 4},
    {"question": "Q2", "answer": "At New Tech Direct, I increased conversion by 25% and reduced costs by 30%.", "internal_score": 4},
    {"question": "Q3", "answer": "I managed 300+ systems with 100% compliance during the AI launch.", "internal_score": 4},
]

# We trigger Turn 8 (Final Report)
res_turn8 = run_get_feedback("GENERATE_REPORT", 8, history=high_perf_history)
report = res_turn8['response']['formatted_report']

print("\n--- GROWTH AREAS (Audit) ---")
if "Growth Areas" in report:
    growth_section = report.split("Growth Areas")[1].split("</ul>")[0]
    print(growth_section)
    if "metric" in growth_section.lower() or "quantify" in growth_section.lower():
         print("\n❌ FAILURE: AI is STILL nagging about metrics despite $35M, 25%, and 100% being present.")
    else:
         print("\n✅ SUCCESS: Anti-Nag instruction followed! No metric nagging found.")
else:
    print("❌ FAILURE: Growth Areas not found.")
