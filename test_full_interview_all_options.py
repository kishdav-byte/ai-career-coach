import os
import json
import sys
sys.path.insert(0, '/Users/davidkish/Desktop/AI Career Coach')

from api.index import app

# Import all three options
from scoring_option1 import calculate_rubric_score_option1
from scoring_option2 import calculate_rubric_score_option2
from scoring_option3 import calculate_rubric_score_option3

def test_full_interview_with_option(option_name, scoring_function):
    """
    Run a complete 8-turn interview using the specified scoring function
    """
    # Temporarily replace the scoring function in the app
    import api.index as api_module
    original_function = api_module.calculate_rubric_score
    api_module.calculate_rubric_score = scoring_function
    
    try:
        client = app.test_client()
        print(f"\n{'='*70}")
        print(f"FULL INTERVIEW TEST: {option_name}")
        print(f"{'='*70}")
        
        history = []
        scores = []
        issues = []
        
        # Turn 1: Handshake
        print(f"\n[TURN 1] Handshake")
        res = client.post('/api/get-feedback', json={
            "message": "READY",
            "isStart": True,
            "questionCount": 1,
            "history": [],
            "jobPosting": "Senior Manager of AI Analytics at TechCorp",
            "resumeText": "MBA, 15 years in strategy and analytics.",
            "job_title": "Senior Manager of AI Analytics"
        })
        
        if res.status_code != 200:
            issues.append(f"Turn 1: HTTP {res.status_code}")
            return None
        
        data = res.get_json()
        ai_json = data.get('response', {})
        
        if ai_json.get('feedback') != "":
            issues.append("Turn 1: Feedback should be silent but wasn't")
        else:
            print("  ✓ Feedback silent (correct)")
        
        if ai_json.get('internal_score', 0) != 0:
            issues.append(f"Turn 1: Score should be 0, got {ai_json.get('internal_score')}")
        else:
            print("  ✓ Score is 0 (correct)")
        
        # Add to history
        history.append({
            "question": ai_json.get('next_question', ''),
            "answer": "READY",
            "feedback": "",
            "internal_score": 0
        })
        
        # Define test answers for questions 2-7
        test_answers = [
            # Turn 2: Background
            {
                "turn": 2,
                "message": "I'm a strategic leader with an MBA and 15 years of experience driving $35M in EBITDA growth through data-driven P&L management and AI product development.",
                "expected_score": 4,
                "description": "Background with metrics"
            },
            # Turn 3: Behavioral Q1
            {
                "turn": 3,
                "message": "During my time as VP at One Call, we faced resistance to a pricing overhaul. I facilitated cross-functional sessions, built data-backed business cases, and implemented safeguards. This resulted in $35M EBITDA growth and 15% cost reduction over 2 years.",
                "expected_score": 5,
                "description": "Full STAR + Metrics"
            },
            # Turn 4: Behavioral Q2
            {
                "turn": 4,
                "message": "I managed multiple AI projects at Strategy Lab by recruiting specialized talent, supervising product roadmaps, and coaching teams. We successfully delivered all projects on time.",
                "expected_score": 3,
                "description": "Good STAR but vague metrics"
            },
            # Turn 5: Behavioral Q3
            {
                "turn": 5,
                "message": "At Sentry, I implemented a compliance-first framework for 300+ hospital systems. I designed automated de-identification protocols and led cross-functional audits to mitigate bias. Result: 100% regulatory compliance with zero data incidents.",
                "expected_score": 5,
                "description": "Full STAR + Compliance Metrics"
            },
            # Turn 6: Behavioral Q4
            {
                "turn": 6,
                "message": "I presented a value creation roadmap to PE sponsors showing how pricing optimizations would drive $35M in EBITDA. I used visual frameworks translating data insights to business outcomes. The board approved the strategy, leading to successful execution.",
                "expected_score": 5,
                "description": "Stakeholder Communication"
            },
            # Turn 7: Behavioral Q5 (Q6 answer)
            {
                "turn": 7,
                "message": "Post-launch of an AI sales tool, I evaluated success using three lenses: 22% revenue increase (North Star metric), reduced CAC, improved conversion rates, and shortened sales cycles. I also tracked model precision over time to prevent drift. This multi-layered approach proved the initiative was a core P&L driver.",
                "expected_score": 5,
                "description": "Post-Launch Evaluation"
            }
        ]
        
        # Test turns 2-7
        for test in test_answers:
            turn = test["turn"]
            print(f"\n[TURN {turn}] {test['description']}")
            
            res = client.post('/api/get-feedback', json={
                "message": test["message"],
                "isStart": False,
                "questionCount": turn,
                "history": history,
                "jobPosting": "Senior Manager of AI Analytics at TechCorp",
                "resumeText": "MBA, 15 years in strategy and analytics.",
                "job_title": "Senior Manager of AI Analytics"
            })
            
            if res.status_code != 200:
                issues.append(f"Turn {turn}: HTTP {res.status_code}")
                continue
            
            data = res.get_json()
            ai_json = data.get('response', {})
            
            # Check for JSON leak
            feedback = ai_json.get('feedback', '')
            has_json_leak = '{' in feedback or'[' in feedback
            if has_json_leak:
                issues.append(f"Turn {turn}: JSON leak in feedback")
                print(f"  ✗ JSON leak detected")
            else:
                print(f"  ✓ No JSON leak")
            
            # Check score
            actual_score = ai_json.get('internal_score', 0)
            expected_score = test["expected_score"]
            scores.append(actual_score)
            
            if actual_score == expected_score:
                print(f"  ✓ Score: {actual_score} (correct)")
            else:
                issues.append(f"Turn {turn}: Expected {expected_score}, got {actual_score}")
                print(f"  ✗ Score: {actual_score} (expected {expected_score})")
            
            # Check feedback structure
            has_structure = ("What Worked" in feedback or "✅" in feedback) and ("To Strengthen" in feedback or "💡" in feedback)
            if has_structure:
                print(f"  ✓ Structured feedback")
            else:
                if feedback:  # Only warn if feedback exists
                    issues.append(f"Turn {turn}: Missing structured feedback format")
                    print(f"  ✗ Feedback not structured")
            
            # Add to history
            history.append({
                "question": ai_json.get('next_question', ''),
                "answer": test["message"],
                "feedback": feedback,
                "internal_score": actual_score
            })
        
        # Turn 8: Final Report Generation
        print(f"\n[TURN 8] Final Report Generation")
        res = client.post('/api/get-feedback', json={
            "message": "Thank you.",
            "isStart": False,
            "questionCount": 8,
            "history": history,
            "jobPosting": "Senior Manager of AI Analytics at TechCorp",
            "resumeText": "MBA, 15 years in strategy and analytics.",
            "job_title": "Senior Manager of AI Analytics"
        })
        
        if res.status_code != 200:
            issues.append(f"Turn 8: HTTP {res.status_code}")
            print(f"  ✗ Report generation failed")
        else:
            data = res.get_json()
            ai_json = data.get('response', {})
            
            if "formatted_report" in ai_json:
                print(f"  ✓ Report generated successfully")
                
                # Check for Business Impact Scoreboard
                if "Business Impact Scoreboard" in ai_json['formatted_report']:
                    print(f"  ✓ Business Impact Scoreboard present")
                else:
                    issues.append("Turn 8: Business Impact Scoreboard missing")
                    print(f"  ✗ Business Impact Scoreboard missing")
                
                # Check average score
                actual_avg = ai_json.get('average_score', 0)
                expected_avg = round(sum(scores) / len(scores), 1)
                print(f"  → Average Score: {actual_avg} (expected ~{expected_avg})")
                
                if abs(actual_avg - expected_avg) > 0.3:
                    issues.append(f"Turn 8: Average score mismatch ({actual_avg} vs {expected_avg})")
                    print(f"  ✗ Score calculation off")
                else:
                    print(f"  ✓ Average score accurate")
            else:
                issues.append("Turn 8: Report missing")
                print(f"  ✗ Report missing")
        
        # Summary
        print(f"\n{'='*70}")
        print(f"SUMMARY: {option_name}")
        print(f"{'='*70}")
        print(f"Scores: {scores}")
        print(f"Average: {round(sum(scores)/len(scores), 1) if scores else 0}")
        print(f"Issues: {len(issues)}")
        if issues:
            print(f"\nIssues detected:")
            for issue in issues:
                print(f"  • {issue}")
        else:
            print(f"✓ NO ISSUES - CLEAN RUN")
        
        return {
            "option": option_name,
            "scores": scores,
            "avg_score": round(sum(scores)/len(scores), 1) if scores else 0,
            "issues": issues,
            "issue_count": len(issues),
            "success": len(issues) == 0
        }
    
    finally:
        # Restore original function
        api_module.calculate_rubric_score = original_function

if __name__ == "__main__":
    print("="*70)
    print("COMPREHENSIVE FULL INTERVIEW TEST - ALL 8 TURNS")
    print("="*70)
    
    results = []
    
    # Test Option 1
    result1 = test_full_interview_with_option(
        "Option 1: Aggressive Backend Override",
        calculate_rubric_score_option1
    )
    if result1: results.append(result1)
    
    # Test Option 2
    result2 = test_full_interview_with_option(
        "Option 2: 1/3/4/5 Hybrid System",
        calculate_rubric_score_option2
    )
    if result2: results.append(result2)
    
    # Test Option 3
    result3 = test_full_interview_with_option(
        "Option 3: Prompt-Enhanced + Backend Safety Net",
        calculate_rubric_score_option3
    )
    if result3: results.append(result3)
    
    # Final Comparison
    print(f"\n{'='*70}")
    print("FINAL COMPARISON - FULL INTERVIEW")
    print(f"{'='*70}")
    print(f"{'Option':<50} {'Issues':<10} {'Avg Score':<12} {'Status'}")
    print("-"*70)
    
    for r in results:
        status = "✓ CLEAN" if r['success'] else f"✗ {r['issue_count']} issues"
        print(f"{r['option']:<50} {r['issue_count']:<10} {r['avg_score']:<12.1f} {status}")
    
    # Recommendation
    clean_runs = [r for r in results if r['success']]
    if clean_runs:
        best = min(clean_runs, key=lambda x: abs(x['avg_score'] - 4.5))
        print(f"\n{'='*70}")
        print(f"RECOMMENDED: {best['option']}")
        print(f"Reason: Clean run with average score {best['avg_score']}")
        print(f"{'='*70}")
    else:
        print(f"\n⚠️  No clean runs detected. Review issues above.")
