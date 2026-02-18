import os
import json
import sys
sys.path.insert(0, '/Users/davidkish/Desktop/AI Career Coach')

from api.index import app
from scoring_option1 import calculate_rubric_score_option1

def test_midgrade_answers():
    """
    Test Option 1 with mid-grade (average/competent) answers
    Expected scores should be mostly 2-3, not inflated to 4-5
    """
    # Temporarily replace scoring function
    import api.index as api_module
    original_function = api_module.calculate_rubric_score
    api_module.calculate_rubric_score = calculate_rubric_score_option1
    
    try:
        client = app.test_client()
        print(f"\n{'='*70}")
        print(f"MID-GRADE ANSWERS TEST - Option 1")
        print(f"Testing: Average candidate with decent but not exceptional answers")
        print(f"{'='*70}")
        
        history = []
        scores = []
        expected_scores = []
        
        test_answers = [
            # Turn 1: Handshake
            {
                "turn": 1,
                "message": "READY",
                "is_start": True,
                "expected_score": 0,
                "description": "Handshake"
            },
            # Turn 2: Background - relevant but not impressive
            {
                "turn": 2,
                "message": "I have a bachelor's degree in Computer Science and about 5 years of experience in data analytics. I've worked on various projects involving dashboards and reporting for business teams.",
                "expected_score": 3,
                "description": "Background: Relevant but no metrics/impact"
            },
            # Turn 3: Partial STAR - missing result metrics
            {
                "turn": 3,
                "message": "We had a project that was running late. I organized some meetings with the team to figure out what was wrong. We reassigned some tasks and eventually got it done.",
                "expected_score": 3,
                "description": "Partial STAR: Has S+A+R but vague, no metrics"
            },
            # Turn 4: Vague actions
            {
                "turn": 4,
                "message": "I worked on several dashboards at the same time. I collaborated with stakeholders to understand their needs. The projects were completed successfully.",
                "expected_score": 3,
                "description": "Vague: 'worked on', 'collaborated' - buzzwords"
            },
            # Turn 5: Missing Action (Gap Logic)
            {
                "turn": 5,
                "message": "The company needed better data quality. The situation was that our reports had errors. After some time, the data quality improved.",
                "expected_score": 1,
                "description": "Gap Logic: S+R but missing Action entirely"
            },
            # Turn 6: Decent STAR but still vague
            {
                "turn": 6,
                "message": "I presented some analysis to my manager about customer trends. I used PowerPoint to show the data. They liked it and used it for planning.",
                "expected_score": 3,
                "description": "Decent but vague: Has STAR but no specifics"
            },
            # Turn 7: Slightly better - has some detail
            {
                "turn": 7,
                "message": "I created a new reporting process for our team. I documented the steps and trained everyone on how to use it. People said it was helpful and we use it now.",
                "expected_score": 3,
                "description": "Competent: Clear STAR, decent but no ROI"
            }
        ]
        
        for test in test_answers:
            turn = test["turn"]
            print(f"\n[TURN {turn}] {test['description']}")
            
            res = client.post('/api/get-feedback', json={
                "message": test["message"],
                "isStart": test.get("is_start", False),
                "questionCount": turn,
                "history": history,
                "jobPosting": "Senior Data Analyst at MidCorp",
                "resumeText": "BS in Computer Science, 5 years experience.",
                "job_title": "Senior Data Analyst"
            })
            
            if res.status_code != 200:
                print(f"  ✗ HTTP {res.status_code}")
                continue
            
            data = res.get_json()
            ai_json = data.get('response', {})
            
            if turn == 1:
                print(f"  → Greeting delivered (silent feedback)")
                history.append({
                    "question": ai_json.get('next_question', ''),
                    "answer": test["message"],
                    "feedback": "",
                    "internal_score": 0
                })
                continue
            
            # Check score
            actual_score = ai_json.get('internal_score', 0)
            expected_score = test["expected_score"]
            scores.append(actual_score)
            expected_scores.append(expected_score)
            
            feedback = ai_json.get('feedback', '')
            
            if actual_score == expected_score:
                print(f"  ✅ Score: {actual_score}/{expected_score}")
            elif actual_score > expected_score:
                print(f"  ⚠️  OVER-SCORED: {actual_score} (expected {expected_score})")
            else:
                print(f"  ⚠️  UNDER-SCORED: {actual_score} (expected {expected_score})")
            
            print(f"  → Feedback: {feedback[:80]}...")
            
            # Add to history
            history.append({
                "question": ai_json.get('next_question', ''),
                "answer": test["message"],
                "feedback": feedback,
                "internal_score": actual_score
            })
        
        # Turn 8: Final Report
        print(f"\n[TURN 8] Final Report Generation")
        res = client.post('/api/get-feedback', json={
            "message": "Thank you.",
            "isStart": False,
            "questionCount": 8,
            "history": history,
            "jobPosting": "Senior Data Analyst at MidCorp",
            "resumeText": "BS in Computer Science, 5 years experience.",
            "job_title": "Senior Data Analyst"
        })
        
        if res.status_code == 200:
            data = res.get_json()
            ai_json = data.get('response', {})
            
            if "formatted_report" in ai_json:
                actual_avg = ai_json.get('average_score', 0)
                expected_avg = round(sum(expected_scores) / len(expected_scores), 1)
                
                print(f"  ✅ Report generated")
                print(f"  → Average Score: {actual_avg} (expected ~{expected_avg})")
                
                if abs(actual_avg - expected_avg) < 0.3:
                    print(f"  ✅ Score accurate for mid-grade performance")
                else:
                    print(f"  ⚠️  Score mismatch")
        
        # Summary
        print(f"\n{'='*70}")
        print(f"MID-GRADE TEST SUMMARY")
        print(f"{'='*70}")
        print(f"Expected Scores: {expected_scores}")
        print(f"Actual Scores:   {scores}")
        print(f"Expected Avg:    {round(sum(expected_scores)/len(expected_scores), 1)}")
        print(f"Actual Avg:      {round(sum(scores)/len(scores), 1)}")
        
        over_scored = sum(1 for i, s in enumerate(scores) if s > expected_scores[i])
        under_scored = sum(1 for i, s in enumerate(scores) if s < expected_scores[i])
        correct = sum(1 for i, s in enumerate(scores) if s == expected_scores[i])
        
        print(f"\nAccuracy Breakdown:")
        print(f"  ✅ Correct scores: {correct}/{len(scores)}")
        print(f"  ⬆️  Over-scored: {over_scored}/{len(scores)}")
        print(f"  ⬇️  Under-scored: {under_scored}/{len(scores)}")
        
        if over_scored > len(scores) / 2:
            print(f"\n⚠️  WARNING: System is too generous (over-scoring mid-grade answers)")
        elif correct >= len(scores) * 0.7:
            print(f"\n✅ PASS: System accurately assesses mid-grade performance")
        else:
            print(f"\n⚠️  System needs calibration")
        
        print(f"{'='*70}")
        
    finally:
        # Restore original function
        api_module.calculate_rubric_score = original_function

if __name__ == "__main__":
    test_midgrade_answers()
