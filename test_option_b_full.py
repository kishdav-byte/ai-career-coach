import os
import sys
sys.path.insert(0, '/Users/davidkish/Desktop/AI Career Coach')

from api.index import app
from scoring_option_b import calculate_rubric_score_option_b

def test_option_b_comprehensive():
    """
    Comprehensive test of Option B (2/3/4 system) with full 8-turn interviews
    Tests: Exceptional, Mid-Grade, and Weak candidates
    """
    import api.index as api_module
    original_function = api_module.calculate_rubric_score
    api_module.calculate_rubric_score = calculate_rubric_score_option_b
    
    try:
        client = app.test_client()
        
        # Define three test profiles
        test_profiles = [
            {
                "name": "EXCEPTIONAL CANDIDATE",
                "expected_avg": 3.7,  # Mostly 4s, one 3
                "answers": [
                    {"turn": 1, "message": "READY", "is_start": True, "expected": 0},
                    {"turn": 2, "message": "I'm a strategic leader with an MBA and 15 years driving $35M in EBITDA growth through data-driven P&L management.", "expected": 4},
                    {"turn": 3, "message": "At One Call, we faced resistance to a pricing overhaul. I facilitated cross-functional sessions, built data-backed cases, and implemented safeguards. Result: $35M EBITDA growth and 15% cost reduction.", "expected": 4},
                    {"turn": 4, "message": "I managed multiple AI projects by recruiting specialized talent, supervising roadmaps, and coaching teams. We delivered all projects on time.", "expected": 3},
                    {"turn": 5, "message": "At Sentry, I implemented a compliance framework for 300+ hospital systems. I designed automated protocols and led audits. Result: 100% compliance with zero data incidents.", "expected": 4},
                    {"turn": 6, "message": "I presented a value roadmap to PE sponsors showing how pricing optimizations would drive $35M in EBITDA. I used visual frameworks translating insights to outcomes. The board approved it.", "expected": 4},
                    {"turn": 7, "message": "Post-launch, I evaluated success using three lenses: 22% revenue increase (North Star), reduced CAC, improved conversion, shortened cycles. I tracked model precision over time. This proved it was a P&L driver.", "expected": 4}
                ]
            },
            {
                "name": "MID-GRADE CANDIDATE",
                "expected_avg": 2.8,  # Mostly 3s, some 2s
                "answers": [
                    {"turn": 1, "message": "READY", "is_start": True, "expected": 0},
                    {"turn": 2, "message": "I have a bachelor's in Computer Science and 5 years in data analytics. I've worked on various projects with dashboards and reporting.", "expected": 3},
                    {"turn": 3, "message": "We had a project running late. I organized meetings to figure out what was wrong. We reassigned tasks and got it done.", "expected": 3},
                    {"turn": 4, "message": "I worked on several dashboards simultaneously. I collaborated with stakeholders to understand needs. Projects were completed successfully.", "expected": 3},
                    {"turn": 5, "message": "I identified data quality issues in our reports. I worked with IT to improve validation. The accuracy got better over time.", "expected": 3},
                    {"turn": 6, "message": "I presented analysis to my manager about customer trends using PowerPoint. They liked it and used it for planning.", "expected": 3},
                    {"turn": 7, "message": "I created a new reporting process for our team. I documented steps and trained everyone. People said it was helpful.", "expected": 3}
                ]
            },
            {
                "name": "WEAK CANDIDATE",
                "expected_avg": 2.2,  # Mostly 2s, some 3s
                "answers": [
                    {"turn": 1, "message": "READY", "is_start": True, "expected": 0},
                    {"turn": 2, "message": "I went to college and studied business. I've had a few jobs in analytics.", "expected": 2},
                    {"turn": 3, "message": "There was a problem with data quality. After some time, it improved.", "expected": 2},
                    {"turn": 4, "message": "I'm passionate about data and always give 110%. My team appreciates my positive energy.", "expected": 2},
                    {"turn": 5, "message": "I helped with some reports. They needed updates. I worked on them.", "expected": 2},
                    {"turn": 6, "message": "I talked to stakeholders sometimes about their needs. Communication is important.", "expected": 2},
                    {"turn": 7, "message": "I used Excel and made some charts. People found them useful I think.", "expected": 3}
                ]
            }
        ]
        
        results = []
        
        for profile in test_profiles:
            print(f"\n{'='*80}")
            print(f"TESTING: {profile['name']}")
            print(f"Expected Average: ~{profile['expected_avg']}/4.0")
            print(f"{'='*80}")
            
            history = []
            scores = []
            errors = 0
            
            for test in profile["answers"]:
                turn = test["turn"]
                
                res = client.post('/api/get-feedback', json={
                    "message": test["message"],
                    "isStart": test.get("is_start", False),
                    "questionCount": turn,
                    "history": history,
                    "jobPosting": "Senior Data Analyst at TechCorp",
                    "resumeText": "Background in analytics",
                    "job_title": "Senior Data Analyst"
                })
                
                if res.status_code != 200:
                    print(f"[TURN {turn}] ✗ HTTP {res.status_code}")
                    errors += 1
                    continue
                
                data = res.get_json()
                ai_json = data.get('response', {})
                
                if turn == 1:
                    history.append({
                        "question": ai_json.get('next_question', ''),
                        "answer": test["message"],
                        "feedback": "",
                        "internal_score": 0
                    })
                    print(f"[TURN {turn}] Greeting delivered")
                    continue
                
                actual_score = ai_json.get('internal_score', 0)
                expected_score = test["expected"]
                scores.append(actual_score)
                
                feedback = ai_json.get('feedback', '')
                
                if actual_score == expected_score:
                    print(f"[TURN {turn}] ✅ Score {actual_score}/{expected_score}")
                else:
                    print(f"[TURN {turn}] ⚠️  Score {actual_score} (expected {expected_score})")
                    errors += 1
                
                history.append({
                    "question": ai_json.get('next_question', ''),
                    "answer": test["message"],
                    "feedback": feedback,
                    "internal_score": actual_score
                })
            
            # Turn 8: Final Report
            print(f"\n[TURN 8] Generating Final Report...")
            res = client.post('/api/get-feedback', json={
                "message": "Thank you.",
                "isStart": False,
                "questionCount": 8,
                "history": history,
                "jobPosting": "Senior Data Analyst at TechCorp",
                "resumeText": "Background in analytics",
                "job_title": "Senior Data Analyst"
            })
            
            if res.status_code == 200:
                data = res.get_json()
                ai_json = data.get('response', {})
                
                if "formatted_report" in ai_json:
                    actual_avg = ai_json.get('average_score', 0)
                    expected_avg = profile["expected_avg"]
                    
                    print(f"✅ Report generated")
                    print(f"→ Average Score: {actual_avg}/4.0 (expected ~{expected_avg})")
                    
                    if abs(actual_avg - expected_avg) < 0.4:
                        print(f"✅ Score within acceptable range")
                    else:
                        print(f"⚠️  Score outside expected range")
                        errors += 1
            
            results.append({
                "profile": profile["name"],
                "scores": scores,
                "actual_avg": round(sum(scores)/len(scores), 1) if scores else 0,
                "expected_avg": profile["expected_avg"],
                "errors": errors
            })
            
            print(f"\n{'='*80}")
            print(f"SUMMARY: {profile['name']}")
            print(f"Scores: {scores}")
            print(f"Average: {round(sum(scores)/len(scores), 1)}/4.0")
            print(f"Errors: {errors}")
            print(f"{'='*80}")
        
        # Final Summary
        print(f"\n{'='*80}")
        print("FINAL RESULTS - OPTION B (2/3/4 System)")
        print(f"{'='*80}")
        
        for r in results:
            status = "✅ PASS" if r["errors"] <= 2 else "❌ FAIL"
            print(f"{r['profile']:<25} Avg: {r['actual_avg']}/4.0 (exp: {r['expected_avg']})  {status}")
        
        total_errors = sum(r["errors"] for r in results)
        
        if total_errors <= 4:
            print(f"\n✅ OPTION B VALIDATED - Ready for deployment")
            print(f"   Total minor discrepancies: {total_errors}")
        else:
            print(f"\n⚠️  OPTION B needs adjustment")
            print(f"   Total errors: {total_errors}")
        
        print(f"{'='*80}")
        
    finally:
        api_module.calculate_rubric_score = original_function

if __name__ == "__main__":
    test_option_b_comprehensive()
