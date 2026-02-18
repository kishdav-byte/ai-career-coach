import sys
sys.path.insert(0, '/Users/davidkish/Desktop/AI Career Coach')

from scoring_option1 import calculate_rubric_score_option1
from scoring_option2 import calculate_rubric_score_option2
from scoring_option3 import calculate_rubric_score_option3

# Test scenarios based on our previous test run
test_scenarios = [
    {
        "name": "Turn 2: Background with metrics",
        "answer": "I'm a strategic leader with an MBA and 15 years of experience driving $35M in EBITDA growth through data-driven P&L management and AI product development.",
        "ai_checklist": {
            "relevant_history": True,
            "communicated_clearly": True,
            "star_situation": False,
            "star_action": False,
            "star_result": False,
            "has_metrics": False,  # AI missed this!
            "red_flags": False
        },
        "question_index": "Q2",
        "expected_score": 4,
        "rationale": "Strong background with clear $35M EBITDA metric"
    },
    {
        "name": "Turn 3: Full STAR + Metrics",
        "answer": "During my time as VP at One Call, we faced resistance to a pricing overhaul. I facilitated cross-functional sessions, built data-backed business cases, and implemented safeguards. This resulted in $35M EBITDA growth and 15% cost reduction over 2 years.",
        "ai_checklist": {
            "relevant_history": False,
            "communicated_clearly": True,
            "star_situation": True,
            "star_action": True,
            "star_result": True,
            "has_metrics": True,
            "red_flags": False
        },
        "question_index": "Q3",
        "expected_score": 5,
        "rationale": "Perfect STAR + multiple metrics"
    },
    {
        "name": "Turn 4: Good STAR but vague metrics",
        "answer": "I managed multiple AI projects at Strategy Lab by recruiting specialized talent, supervising product roadmaps, and coaching teams. We successfully delivered all projects on time.",
        "ai_checklist": {
            "relevant_history": False,
            "communicated_clearly": True,
            "star_situation": False,  # AI marked False
            "star_action": False,  # AI marked False (should be True!)
            "star_result": True,
            "has_metrics": False,
            "red_flags": False
        },
        "question_index": "Q4",
        "expected_score": 3,
        "rationale": "Has action words (managed, recruiting, supervising) and result (delivered)"
    },
    {
        "name": "Turn 5: Full STAR + Compliance Metrics",
        "answer": "At Sentry, I implemented a compliance-first framework for 300+ hospital systems. I designed automated de-identification protocols and led cross-functional audits to mitigate bias. Result: 100% regulatory compliance with zero data incidents.",
        "ai_checklist": {
            "relevant_history": False,
            "communicated_clearly": True,
            "star_situation": True,
            "star_action": True,
            "star_result": True,
            "has_metrics": True,
            "red_flags": False
        },
        "question_index": "Q5",
        "expected_score": 5,
        "rationale": "Full STAR + multiple metrics (300+, 100%, zero)"
    },
    {
        "name": "Turn 6: Stakeholder Communication",
        "answer": "I presented a value creation roadmap to PE sponsors showing how pricing optimizations would drive $35M in EBITDA. I used visual frameworks translating data insights to business outcomes. The board approved the strategy, leading to successful execution.",
        "ai_checklist": {
            "relevant_history": False,
            "communicated_clearly": True,
            "star_situation": True,
            "star_action": True,
            "star_result": True,
            "has_metrics": True,
            "red_flags": False
        },
        "question_index": "Q6",
        "expected_score": 5,
        "rationale": "Full STAR + $35M metric"
    },
    {
        "name": "Turn 7: Post-Launch Evaluation",
        "answer": "Post-launch of an AI sales tool, I evaluated success using three lenses: 22% revenue increase (North Star metric), reduced CAC, improved conversion rates, and shortened sales cycles. I also tracked model precision over time to prevent drift. This multi-layered approach proved the initiative was a core P&L driver.",
        "ai_checklist": {
            "relevant_history": False,
            "communicated_clearly": True,
            "star_situation": True,
            "star_action": True,
            "star_result": True,
            "has_metrics": True,
            "red_flags": False
        },
        "question_index": "Q7",
        "expected_score": 5,
        "rationale": "Full STAR + 22% metric + detailed approach"
    }
]

def test_option(option_name, scoring_function):
    """Test a scoring option"""
    print(f"\n{'='*70}")
    print(f"TESTING: {option_name}")
    print(f"{'='*70}")
    
    scores = []
    errors = 0
    
    for scenario in test_scenarios:
        score, _ = scoring_function(
            {"checklist": scenario["ai_checklist"]},
            scenario["question_index"],
            scenario["answer"]
        )
        
        scores.append(score)
        expected = scenario["expected_score"]
        status = "✓" if score == expected else "✗"
        
        print(f"\n{status} {scenario['name']}")
        print(f"  Expected: {expected} | Got: {score} | Rationale: {scenario['rationale']}")
        
        if score != expected:
            errors += 1
            print(f"  ⚠️  MISMATCH")
    
    avg_score = round(sum(scores) / len(scores), 1)
    expected_avg = round(sum([s["expected_score"] for s in test_scenarios]) / len(test_scenarios), 1)
    
    print(f"\n{'='*70}")
    print(f"SUMMARY for {option_name}")
    print(f"{'='*70}")
    print(f"Individual Scores: {scores}")
    print(f"Average Score: {avg_score} (Expected: {expected_avg})")
    print(f"Errors: {errors}/{len(test_scenarios)}")
    print(f"Accuracy: {((len(test_scenarios) - errors) / len(test_scenarios) * 100):.1f}%")
    
    return {
        "option": option_name,
        "scores": scores,
        "avg_score": avg_score,
        "expected_avg": expected_avg,
        "errors": errors,
        "accuracy": ((len(test_scenarios) - errors) / len(test_scenarios) * 100)
    }

if __name__ == "__main__":
    print("="*70)
    print("SCORING OPTIONS COMPARISON TEST")
    print("="*70)
    
    results = []
    
    # Test Option 1
    results.append(test_option("Option 1: Aggressive Backend Override", calculate_rubric_score_option1))
    
    # Test Option 2
    results.append(test_option("Option 2: 1/3/4/5 Hybrid System", calculate_rubric_score_option2))
    
    # Test Option 3
    results.append(test_option("Option 3: Prompt-Enhanced + Backend Safety Net", calculate_rubric_score_option3))
    
    # Final Comparison
    print(f"\n{'='*70}")
    print("FINAL COMPARISON")
    print(f"{'='*70}")
    print(f"{'Option':<50} {'Accuracy':<12} {'Avg Score':<12} {'Errors'}")
    print("-"*70)
    
    for r in results:
        print(f"{r['option']:<50} {r['accuracy']:>6.1f}%     {r['avg_score']:>6.1f}      {r['errors']}")
    
    # Recommendation
    best = max(results, key=lambda x: (x['accuracy'], -abs(x['avg_score'] - x['expected_avg'])))
    print(f"\n{'='*70}")
    print(f"RECOMMENDED: {best['option']}")
    print(f"Reason: {best['accuracy']:.1f}% accuracy, Average score {best['avg_score']} (target: {best['expected_avg']})")
    print(f"{'='*70}")
