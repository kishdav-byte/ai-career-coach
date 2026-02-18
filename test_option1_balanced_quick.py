import os
import sys
sys.path.insert(0, '/Users/davidkish/Desktop/AI Career Coach')

from scoring_option1_balanced import calculate_rubric_score_option1_balanced

# Quick unit test without API calls
def quick_test_balanced():
    print("="*70)
    print("OPTION 1 BALANCED - UNIT TEST")
    print("="*70)
    
    test_cases = [
        # Exceptional answers (should score 5)
        {
            "answer": "I facilitated cross-functional sessions and implemented safeguards. This resulted in $35M EBITDA growth and 15% cost reduction.",
            "ai_checklist": {"star_situation": True, "star_action": True, "star_result": True, "has_metrics": True, "delivery_organized": True, "red_flags": False},
            "expected": 5,
            "label": "Exceptional: Full STAR + Metrics"
        },
        # Mid-grade answers (should score 3)
        {
            "answer": "I organized meetings with the team. We reassigned tasks and got the project done.",
            "ai_checklist": {"star_situation": False, "star_action": False, "star_result": False, "has_metrics": False, "delivery_organized": True, "red_flags": False},
            "expected": 3,
            "label": "Mid-grade: Organized but vague"
        },
        {
            "answer": "I worked on dashboards and collaborated with stakeholders. The projects were completed successfully.",
            "ai_checklist": {"star_situation": False, "star_action": False, "star_result": False, "has_metrics": False, "delivery_organized": True, "red_flags": False},
            "expected": 3,
            "label": "Mid-grade: Action + Result detected by backend"
        },
        # Weak answer (should score 1)
        {
            "answer": "The company needed better data quality. After some time, it improved.",
            "ai_checklist": {"star_situation": True, "star_action": False, "star_result": True, "has_metrics": False, "delivery_organized": False, "red_flags": False},
            "expected": 1,
            "label": "Weak: Missing Action entirely"
        },
    ]
    
    passed = 0
    failed = 0
    
    for test in test_cases:
        score, _ = calculate_rubric_score_option1_balanced(
            {"checklist": test["ai_checklist"]},
            "Q3",
            test["answer"]
        )
        
        if score == test["expected"]:
            print(f"✅ {test['label']}: {score}/{test['expected']}")
            passed += 1
        else:
            print(f"✗ {test['label']}: {score} (expected {test['expected']})")
            failed += 1
    
    print(f"\n{'='*70}")
    print(f"RESULTS: {passed} passed, {failed} failed")
    print(f"{'='*70}")
    
    return failed == 0

if __name__ == "__main__":
    success = quick_test_balanced()
    exit(0 if success else 1)
