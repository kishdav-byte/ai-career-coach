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
    
    # Question 0: GREETING (START)
    # real_q_num = 0, isStart = True
    res = client.post('/api/get-feedback', json={
        "message": "START",
        "questionCount": 0,
        "isStart": True,
        "job_title": "Senior AI Manager",
        "jobPosting": "Looking for leadership in AI product transition and analytics.",
        "resumeText": "AI expert with deep technical and business strategy experience."
    })
    data = res.get_json()
    ai_msg = data['response']['next_question']
    # history.append is handled by frontend AFTER receiving response usually, but for simulation:
    # lastAiQuestion = ai_msg
    history.append({"question": ai_msg, "answer": "START", "feedback": "", "internal_score": 0})
    
    # Answers 1-6
    # real_q_num 1: Answers Q1, gets STAR instructions
    # real_q_num 2-4: Behavioral
    # real_q_num 5: Answers Q5, gets Q6 prep
    # real_q_num 6: Answers Q6, gets Closing
    
    for q_num in range(1, 7):
        current_answer = answers[q_num-1]
        res = client.post('/api/get-feedback', json={
            "message": current_answer,
            "questionCount": q_num,
            "history": history,
            "isStart": False,
            "job_title": "Senior AI Manager",
            "jobPosting": "Looking for leadership in AI product transition and analytics.",
            "resumeText": "AI expert with deep technical and business strategy experience."
        })
        data = res.get_json()
        resp = data['response']
        
        # Check STAR placement on Turn 1 (Answering Background)
        if q_num == 1:
            if "STAR method" in resp.get('next_question', ''):
                print("   ✅ STAR Placement Check: PASSED (Found after Background answer)")
            else:
                print(f"   ❌ STAR Placement Check: FAILED (Not found in: {resp.get('next_question')[:50]}...)")
        
        # Check Completion flag
        if q_num == 6:
            if data.get('is_complete'):
                print("   ✅ Completion Flag Check: PASSED (Turn 6 is complete)")
            else:
                print("   ❌ Completion Flag Check: FAILED (Turn 6 NOT marked complete)")

        history.append({
            "question": resp.get('next_question', ''),
            "answer": current_answer,
            "feedback": resp.get('feedback', ''),
            "internal_score": resp.get('internal_score', 0)
        })

    # Turn 7+: FINAL REPORT
    res = client.post('/api/get-feedback', json={
        "message": "GENERATE_REPORT",
        "questionCount": 7,
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
    
    # Check for / 4.0 in report
    has_four_scale = "/ 4.0" in report
    
    # Check for Metric Nagging in Growth Areas
    nagging = False
    if "Growth Areas" in report:
        parts = report.split("Growth Areas")
        if len(parts) > 1:
            growth = parts[1].split("</ul>")[0]
            if any(x in growth.lower() for x in ["metric", "quantify", "measurable"]):
                nagging = True
            
    print(f"   📊 Final Result: {avg_score} / 4.0 -> {label}")
    print(f"   📏 Scale Check: {'PASSED (/ 4.0 found)' if has_four_scale else 'FAILED (/ 4.0 NOT found)'}")
    
    if nagging and profile_name == "EXCELLENT":
        print("   ⚠️  Anti-Nag Note: Found metrics references in growth areas (might be legitimate AI advice or a false positive)")
    
    return {"avg": avg_score, "label": label, "nagging": nagging, "scale_ok": has_four_scale}

# --- CANDIDATE PROFILES ---

EXCELLENT_ANSWERS = [
    "I have 15 years in AI leadership and built the Total Package platform with $35M EBITDA growth.", # Q1 (Background)
    "I led a 15-person team through an AI migration where churn was at 15%. My task was to stabilize the platform. I optimized our API throughput by 200%. As a result, we reduced churn to 4% and saved $4M.", # Q2
    "Data was siloed across systems. I built an automated data pipeline using Python. This unified our source of truth and increased reporting efficiency by 50%.", # Q3
    "Sales team resisted the AI shift. I ran a 'low-stakes' pilot with a 25% conversion lift. This won them over and we launched the full Career Ecosystem strategy.", # Q4
    "Investors didn't get ML. I used a 'Traffic Light' visual to explain risk scores for churn. This secured a $10M funding round for the AI roadmap.", # Q5
    "API latency spiked 400% during launch. I performed a Pareto Analysis and disabled non-essential sub-routines. Error rates dropped to zero and saved the launch." # Q6
]

AVERAGE_ANSWERS = [
    "I am a project manager with some AI experience. I've worked on tools and content for several years.",
    "We had slow servers. My task was to fix it. I worked with the IT team to upgrade the ram and optimize the database. The site was faster afterward.",
    "Data was fragmented. I brought it together into one sheet. This helped the managers see what was happening with the customers.",
    "The team didn't want to change. I talked to them and explained why it was better. We eventually agreed to try the new system and it worked well.",
    "I had to explain a complex report to the board. I used simple language and avoided the hard technical terms. They understood it better.",
    "We had a deadline that was approaching fast. I re-assigned some tasks to other people. We managed to finish the project on time."
]

WEAK_ANSWERS = [
    "I do data. I like computers.",
    "It was good. I did the work. It went well.",
    "I used excel and it was fine.",
    "I just did it. No one complained.",
    "I told them what to do.",
    "I don't know, it just worked."
]

if __name__ == "__main__":
    results = {}
    
    # Run Excellent
    results['EXCELLENT'] = run_interview("EXCELLENT", EXCELLENT_ANSWERS)
    
    # Run Average
    results['AVERAGE'] = run_interview("AVERAGE", AVERAGE_ANSWERS)
    
    # Run Weak
    results['WEAK'] = run_interview("WEAK", WEAK_ANSWERS)
    
    print("\n" + "="*60)
    print("V15 INTEGRATION TEST SUMMARY")
    print("="*60)
    print(f"{'Profile':<10} {'Score':<10} {'Label':<15} {'Scale':<10} {'Overall'}")
    print("-"*60)
    
    for name, res in results.items():
        status = "✅"
        if not res['scale_ok']: status = "❌"
        
        # Scoring sanity check
        if name == "EXCELLENT" and res['avg'] < 3.3: status = "❌ (Low Score)"
        if name == "WEAK" and res['avg'] > 2.5: status = "❌ (High Score)"
        
        print(f"{name:<10} {res['avg']:<10} {res['label']:<15} {'4.0':<10} {status}")
    
    print("="*60)
