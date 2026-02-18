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

print("--- TEST 2+++: REALISTIC QUESTIONS ANTI-NAG ---")
high_perf_history = [
    {"question": "Walk me through your background and why you are the right fit for this role?", "answer": "I have 15 years in AI leadership and built the Total Package platform with $35M EBITDA growth.", "internal_score": 4},
    {"question": "Can you provide an example of a time when you translated complex data insights into actionable business strategies?", "answer": "At New Tech Direct, I increased conversion by 25% and reduced costs by 30% through predictive analytics.", "internal_score": 4},
    {"question": "Can you describe a time when you faced a significant challenge in driving data-informed decision making?", "answer": "I managed 300+ systems with 100% compliance during the AI launch despite significant server latency issues.", "internal_score": 4},
]

res_turn8 = run_get_feedback("GENERATE_REPORT", 8, history=high_perf_history)
report = res_turn8['response']['formatted_report']

print("\n--- SCOREBOARD ---")
if "Business Impact Scoreboard" in report:
    import re
    kpis = re.findall(r'<div[^>]*p-2[^>]*>(.*?)</div>', report, re.DOTALL)
    for k in kpis:
        print(f"✓ {k.strip()}")
    if not kpis:
        scoreboard = report.split("Business Impact Scoreboard")[1].split("</div>")[0]
        print(scoreboard)

print("\n--- GROWTH AREAS ---")
if "Growth Areas" in report:
    growth_section = report.split("Growth Areas")[1].split("</ul>")[0]
    print(growth_section)
    if any(x in growth_section.lower() for x in ["metric", "quantify", "measurable"]):
         print("\n❌ FAILURE: AI is STILL nagging about metrics despite metrics being extracted.")
    else:
         print("\n✅ SUCCESS: Anti-Nag instruction followed! No metric nagging found.")
else:
    print("❌ FAILURE: Growth Areas not found.")
