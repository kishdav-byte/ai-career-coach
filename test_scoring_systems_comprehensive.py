import sys
sys.path.insert(0, '/Users/davidkish/Desktop/AI Career Coach')

# Test all answer quality levels with different scoring systems
def test_scoring_systems():
    print("="*80)
    print("COMPREHENSIVE SCORING SYSTEM COMPARISON")
    print("Testing: Terrible, Weak, Mid-Grade, Strong, Exceptional answers")
    print("="*80)
    
    # Define test cases across all quality levels
    test_cases = [
        # TERRIBLE ANSWERS (Red flags, toxic, nonsense)
        {
            "answer": "I don't really remember what I did. It was a while ago. Can we skip this question?",
            "ai_checklist": {"star_situation": False, "star_action": False, "star_result": False, "has_metrics": False, "delivery_organized": False, "red_flags": False},
            "label": "TERRIBLE: Non-answer, no effort",
            "quality": "terrible"
        },
        {
            "answer": "The client was being difficult, so I told them they were wrong and stopped responding to their emails.",
            "ai_checklist": {"star_situation": True, "star_action": True, "star_result": False, "has_metrics": False, "delivery_organized": False, "red_flags": True},
            "label": "TERRIBLE: Toxic behavior (red flag)",
            "quality": "terrible"
        },
        
        # WEAK ANSWERS (Vague buzzwords, missing structure)
        {
            "answer": "The company needed better data quality. After some time, it improved.",
            "ai_checklist": {"star_situation": True, "star_action": False, "star_result": True, "has_metrics": False, "delivery_organized": False, "red_flags": False},
            "label": "WEAK: Gap Logic (missing Action)",
            "quality": "weak"
        },
        {
            "answer": "I'm passionate about data and I always give 110%. I work hard and my team appreciates my positive energy.",
            "ai_checklist": {"star_situation": False, "star_action": False, "star_result": False, "has_metrics": False, "delivery_organized": False, "red_flags": False},
            "label": "WEAK: Magic Wand (feelings, no mechanics)",
            "quality": "weak"
        },
        
        # MID-GRADE ANSWERS (Competent, organized, but no wow factor)
        {
            "answer": "I organized meetings with the team. We reassigned tasks and got the project done on time.",
            "ai_checklist": {"star_situation": False, "star_action": False, "star_result": False, "has_metrics": False, "delivery_organized": True, "red_flags": False},
            "label": "MID-GRADE: Has structure but vague",
            "quality": "mid"
        },
        {
            "answer": "I worked on dashboards and collaborated with stakeholders to understand their needs. The projects were completed successfully.",
            "ai_checklist": {"star_situation": False, "star_action": False, "star_result": False, "has_metrics": False, "delivery_organized": True, "red_flags": False},
            "label": "MID-GRADE: Action + Result but vague",
            "quality": "mid"
        },
        
        # STRONG ANSWERS (Clear STAR, some metrics)
        {
            "answer": "I led a team of 5 analysts to redesign our reporting system. I created new dashboards and trained 20 users. The adoption rate was 85% within 3 months.",
            "ai_checklist": {"star_situation": True, "star_action": True, "star_result": True, "has_metrics": True, "delivery_organized": True, "red_flags": False},
            "label": "STRONG: Full STAR + some metrics",
            "quality": "strong"
        },
        
        # EXCEPTIONAL ANSWERS (Full STAR + multiple strong metrics)
        {
            "answer": "During my time as VP, we faced resistance to a pricing overhaul. I facilitated cross-functional sessions, built data-backed business cases, and implemented safeguards. This resulted in $35M EBITDA growth and 15% cost reduction over 2 years.",
            "ai_checklist": {"star_situation": True, "star_action": True, "star_result": True, "has_metrics": True, "delivery_organized": True, "red_flags": False},
            "label": "EXCEPTIONAL: Full STAR + multiple strong metrics",
            "quality": "exceptional"
        }
    ]
    
    # Define three scoring systems
    def score_system_135(checklist, has_metrics, answer_lower):
        """Current: 1, 3, 5"""
        has_star_a = checklist.get("star_action", False)
        has_star_r = checklist.get("star_result", False)
        has_star_s = checklist.get("star_situation", False)
        is_organized = checklist.get("delivery_organized", False)
        has_red_flags = checklist.get("red_flags", False)
        
        # Backend keyword detection
        import re
        if not has_star_a:
            action_kw = ['led', 'managed', 'organized', 'created', 'implemented', 'collaborated', 'worked on']
            if any(word in answer_lower for word in action_kw):
                has_star_a = True
        if not has_star_r:
            result_kw = ['completed', 'finished', 'delivered', 'achieved', 'successful', 'done', 'got it done']
            if any(word in answer_lower for word in result_kw):
                has_star_r = True
        
        if has_red_flags:
            return 1
        
        complete_star = has_star_s and has_star_a and has_star_r
        partial_star = has_star_a and has_star_r
        
        if complete_star and has_metrics:
            return 5
        elif partial_star and has_metrics:
            return 5
        elif complete_star or partial_star:
            return 3
        elif has_star_a or (is_organized and has_star_r):
            return 3
        else:
            return 1
    
    def score_system_2345(checklist, has_metrics, answer_lower):
        """Option A: 2.5, 3, 4, 5"""
        has_star_a = checklist.get("star_action", False)
        has_star_r = checklist.get("star_result", False)
        has_star_s = checklist.get("star_situation", False)
        is_organized = checklist.get("delivery_organized", False)
        has_red_flags = checklist.get("red_flags", False)
        
        # Backend keyword detection
        import re
        if not has_star_a:
            action_kw = ['led', 'managed', 'organized', 'created', 'implemented', 'collaborated', 'worked on']
            if any(word in answer_lower for word in action_kw):
                has_star_a = True
        if not has_star_r:
            result_kw = ['completed', 'finished', 'delivered', 'achieved', 'successful', 'done', 'got it done']
            if any(word in answer_lower for word in result_kw):
                has_star_r = True
        
        if has_red_flags:
            return 1  # Red flags still get 1
        
        complete_star = has_star_s and has_star_a and has_star_r
        partial_star = has_star_a and has_star_r
        
        if complete_star and has_metrics:
            return 5  # Exceptional
        elif partial_star and has_metrics:
            return 4  # Strong
        elif complete_star:
            return 3  # Competent
        elif partial_star or (is_organized and has_star_r):
            return 2.5  # Barely competent
        else:
            return 2  # Weak but not terrible
    
    def score_system_234(checklist, has_metrics, answer_lower):
        """Option B: 2, 3, 4"""
        has_star_a = checklist.get("star_action", False)
        has_star_r = checklist.get("star_result", False)
        has_star_s = checklist.get("star_situation", False)
        is_organized = checklist.get("delivery_organized", False)
        has_red_flags = checklist.get("red_flags", False)
        
        # Backend keyword detection
        import re
        if not has_star_a:
            action_kw = ['led', 'managed', 'organized', 'created', 'implemented', 'collaborated', 'worked on']
            if any(word in answer_lower for word in action_kw):
                has_star_a = True
        if not has_star_r:
            result_kw = ['completed', 'finished', 'delivered', 'achieved', 'successful', 'done', 'got it done']
            if any(word in answer_lower for word in result_kw):
                has_star_r = True
        
        if has_red_flags:
            return 1  # Red flags still get 1
        
        complete_star = has_star_s and has_star_a and has_star_r
        partial_star = has_star_a and has_star_r
        
        if complete_star and has_metrics:
            return 4  # Exceptional
        elif partial_star and has_metrics:
            return 4  # Strong (same as exceptional in 3-tier)
        elif complete_star or partial_star:
            return 3  # Competent
        elif has_star_a or is_organized:
            return 3  # Competent (generous)
        else:
            return 2  # Weak
    
    # Test all systems
    systems = [
        ("Current 1/3/5", score_system_135),
        ("Option A: 2.5/3/4/5", score_system_2345),
        ("Option B: 2/3/4", score_system_234)
    ]
    
    for system_name, score_func in systems:
        print(f"\n{'='*80}")
        print(f"{system_name}")
        print(f"{'='*80}")
        
        scores_by_quality = {
            "terrible": [],
            "weak": [],
            "mid": [],
            "strong": [],
            "exceptional": []
        }
        
        for test in test_cases:
            score = score_func(
                test["ai_checklist"],
                test["ai_checklist"]["has_metrics"],
                test["answer"].lower()
            )
            
            quality = test["quality"]
            scores_by_quality[quality].append(score)
            
            print(f"{score:>4} | {test['label']}")
        
        # Calculate averages
        print(f"\n{'-'*80}")
        print("AVERAGES BY QUALITY:")
        for quality in ["terrible", "weak", "mid", "strong", "exceptional"]:
            if scores_by_quality[quality]:
                avg = sum(scores_by_quality[quality]) / len(scores_by_quality[quality])
                print(f"  {quality.upper():12} → {avg:.2f}")
        
        all_scores = [s for scores in scores_by_quality.values() for s in scores]
        overall_avg = sum(all_scores) / len(all_scores)
        score_range = max(all_scores) - min(all_scores if min(all_scores) != 1 else [s for s in all_scores if s > 1])
        
        print(f"\n  Overall Average: {overall_avg:.2f}")
        print(f"  Score Range (excluding red flags): {score_range:.1f}")
    
    # Recommendation
    print(f"\n{'='*80}")
    print("RECOMMENDATION")
    print(f"{'='*80}")
    print("""
Option B (2/3/4 system) is recommended because:

1. **Simpler for users**: Easy to understand (Weak, Competent, Strong)
2. **Appropriate granularity**: Most answers fall in 2-4 range anyway
3. **Still differentiates**: Clearly separates performance levels
4. **Fair scoring**:
   - 2 = Weak but made an effort
   - 3 = Competent, acceptable answer
   - 4 = Strong, impressive answer
5. **1 reserved for red flags**: Toxic behavior, complete non-answers

The 1/3/5 system is too wide - we almost never see true "1" answers except red flags.
The 2.5/3/4/5 system adds unnecessary complexity with the .5 increment.
    """)

if __name__ == "__main__":
    test_scoring_systems()
