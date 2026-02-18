#!/usr/bin/env python3
import os
import sys
import json
import re

# Setup paths
sys.path.insert(0, '/Users/davidkish/Desktop/AI Career Coach')

from api.index import app
import api.index as api_module

client = app.test_client()

def run_interview(profile_name, answers):
    print(f"\n🚀 RUNNING INTERVIEW: {profile_name}")
    history = []
    
    # Question 1: Greeting / Start
    # Turn 1
    res = client.post('/api/get-feedback', json={
        "message": "START",
        "questionCount": 1,
        "isStart": True,
        "job_title": "Senior AI Manager",
        "jobPosting": "Looking for leadership in AI product transition and analytics.",
        "resumeText": "AI expert with deep technical and business strategy experience."
    })
    data = res.get_json()
    ai_msg = data['response']['next_question']
    history.append({"question": ai_msg, "answer": "START", "feedback": "", "internal_score": 0})
    
    # Turns 2-7
    for i in range(2, 8):
        current_answer = answers[i-2]
        res = client.post('/api/get-feedback', json={
            "message": current_answer,
            "questionCount": i,
            "history": history,
            "isStart": False,
            "job_title": "Senior AI Manager",
            "jobPosting": "Looking for leadership in AI product transition and analytics.",
            "resumeText": "AI expert with deep technical and business strategy experience."
        })
        data = res.get_json()
        resp = data['response']
        
        # Check STAR placement on Turn 2
        if i == 2:
            if "STAR method" in resp['next_question']:
                print("   ✅ STAR Placement: CORRECT (Found in next_question)")
            else:
                print("   ❌ STAR Placement: FAILED (Not found in next_question)")
        
        history.append({
            "question": resp.get('next_question', ''),
            "answer": current_answer,
            "feedback": resp.get('feedback', ''),
            "internal_score": resp.get('internal_score', 0)
        })
    
    # Turn 8: Final Report
    res = client.post('/api/get-feedback', json={
        "message": "GENERATE_REPORT",
        "questionCount": 8,
        "history": history,
        "isStart": False,
        "job_title": "Senior AI Manager",
        "jobPosting": "Looking for leadership in AI product transition and analytics.",
        "resumeText": "AI expert with deep technical and business strategy experience."
    })
    data = res.get_json()
    report = data['response']['formatted_report']
    avg_score = data['response']['average_score']
    
    # Extract label
    label_match = re.search(r'text-indigo-300[^>]*>([^<]+)<', report)
    label = label_match.group(1).strip() if label_match else "UNKNOWN"
    
    # Check for Metric Nagging in Growth Areas
    nagging = False
    if "Growth Areas" in report:
        growth = report.split("Growth Areas")[1].split("</ul>")[0]
        if any(x in growth.lower() for x in ["metric", "quantify", "measurable"]):
            nagging = True
            
    print(f"   📊 Final Result: {avg_score} / 4.0 -> {label}")
    if nagging and profile_name == "HIGH":
        print("   ❌ Anti-Nag Check: FAILED (Still nagging despite metrics)")
    elif not nagging and profile_name == "HIGH":
        print("   ✅ Anti-Nag Check: PASSED (No metric nagging)")
    
    return {"avg": avg_score, "label": label, "nagging": nagging}

# --- CANDIDATE PROFILES ---

HIGH_ANSWERS = [
    "I have 15 years in AI leadership and built the Total Package platform with $35M EBITDA growth.", # Q1 (Background)
    "I led a 15-person team through an AI migration where churn was at 15%. My task was to stabilize the platform. I optimized our API throughput by 200%. As a result, we reduced churn to 4% and saved $4M.", # Q2
    "Data was siloed across systems. I built an automated data pipeline using Python. This unified our source of truth and increased reporting efficiency by 50%.", # Q3
    "Sales team resisted the AI shift. I ran a 'low-stakes' pilot with a 25% conversion lift. This won them over and we launched the full Career Ecosystem strategy.", # Q4
    "Investors didn't get ML. I used a 'Traffic Light' visual to explain risk scores for churn. This secured a $10M funding round for the AI roadmap.", # Q5
    "API latency spiked 400% during launch. I performed a Pareto Analysis and disabled non-essential sub-routines. Error rates dropped to zero and saved the launch." # Q6
]

MID_ANSWERS = [
    "I am a project manager with some AI experience. I've worked on tools and content for several years.",
    "We had slow servers. My task was to fix it. I worked with the IT team to upgrade the ram and optimize the database. The site was faster afterward.",
    "Data was fragmented. I brought it together into one sheet. This helped the managers see what was happening with the customers.",
    "The team didn't want to change. I talked to them and explained why it was better. We eventually agreed to try the new system and it worked well.",
    "I had to explain a complex report to the board. I used simple language and avoided the hard technical terms. They understood it better.",
    "We had a deadline that was approaching fast. I re-assigned some tasks to other people. We managed to finish the project on time."
]

LOW_ANSWERS = [
    "I do data. I like computers.",
    "It was good. I did the work. It went well.",
    "I used excel and it was fine.",
    "I just did it. No one complained.",
    "I told them what to do.",
    "I don't know, it just worked."
]

if __name__ == "__main__":
    results = {}
    
    # Run High
    results['HIGH'] = run_interview("HIGH", HIGH_ANSWERS)
    
    # Run Mid
    results['MID'] = run_interview("MID", MID_ANSWERS)
    
    # Run Low
    results['LOW'] = run_interview("LOW", LOW_ANSWERS)
    
    print("\n" + "="*60)
    print("FINAL VALIDATION SUMMARY")
    print("="*60)
    print(f"{'Profile':<10} {'Score':<10} {'Label':<15} {'Status'}")
    print("-"*60)
    
    # Logic Checks
    # High: label="Well Done", nag=False
    high = results['HIGH']
    print(f"{'HIGH':<10} {high['avg']:<10} {high['label']:<15} {'✅' if high['label'] == 'Well Done' and not high['nagging'] else '❌'}")
    
    # Mid: label="Average"
    mid = results['MID']
    print(f"{'MID':<10} {mid['avg']:<10} {mid['label']:<15} {'✅' if mid['label'] == 'Average' else '❌'}")
    
    # Low: label="Needs Work"
    low = results['LOW']
    print(f"{'LOW':<10} {low['avg']:<10} {low['label']:<15} {'✅' if low['label'] == 'Needs Work' else '❌'}")
    
    print("="*60)
