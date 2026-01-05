"""
Test script to verify the calculate_rubric_score function logic
"""

def calculate_rubric_score(rubric_data, question_index, answer_text):
    """
    Calculate score based on Boolean Logic Gates from Phase 3 requirements.
    Returns: (score, gap_reason)
    """
    checklist = rubric_data.get("checklist", {})
    
    # RED FLAG OVERRIDE (CRITICAL)
    if checklist.get("red_flags") == True:
        return 1, "Toxic Behavior Detected"
    
    # Q1 (Background) Logic
    if question_index == "Q1" or question_index == "Q2":  # Q2 evaluates Q1 answer
        score = 0
        if checklist.get("relevant_history") == True:
            score += 3  # Base score
        if checklist.get("communicated_clearly") == True:
            score += 1  # Bonus
        if checklist.get("relevant_history") == False:
            score = 2  # Penalty for irrelevant history
        
        # Clamp to 1-5 range
        return max(1, min(5, score)), None
    
    # Q2-Q6 (Behavioral) Logic
    else:
        score = 0
        if checklist.get("star_situation") == True:
            score += 1
        if checklist.get("star_action") == True:
            score += 1
        if checklist.get("star_result") == True:
            score += 1
        if checklist.get("has_metrics") == True:
            score += 1  # Numbers/ROI bonus
        if checklist.get("delivery_organized") == True:
            score += 1  # UNICORN bonus
        
        # PENALTY: If no Action (vague/magic wand), max score = 2
        if checklist.get("star_action") == False:
            score = min(score, 2)
        
        # Clamp to 1-5 range
        return max(1, min(5, score)), None

# Test Cases
print("=" * 60)
print("RUBRIC SCORING TEST SUITE")
print("=" * 60)

# Test 1: Red Flag Override
print("\n[TEST 1] Red Flag Override")
rubric = {
    "checklist": {
        "relevant_history": True,
        "communicated_clearly": True,
        "red_flags": True  # CRITICAL
    }
}
score, reason = calculate_rubric_score(rubric, "Q1", "test")
print(f"  Input: Background with red flag")
print(f"  Expected: Score=1, Reason='Toxic Behavior Detected'")
print(f"  Actual: Score={score}, Reason={reason}")
print(f"  ✓ PASS" if score == 1 and reason == "Toxic Behavior Detected" else "  ✗ FAIL")

# Test 2: Q1 Perfect Answer
print("\n[TEST 2] Q1 Perfect Background")
rubric = {
    "checklist": {
        "relevant_history": True,
        "communicated_clearly": True,
        "red_flags": False
    }
}
score, reason = calculate_rubric_score(rubric, "Q1", "test")
print(f"  Input: Relevant history + Clear communication")
print(f"  Expected: Score=4 (3+1)")
print(f"  Actual: Score={score}")
print(f"  ✓ PASS" if score == 4 else "  ✗ FAIL")

# Test 3: Q1 Irrelevant History
print("\n[TEST 3] Q1 Irrelevant Background")
rubric = {
    "checklist": {
        "relevant_history": False,
        "communicated_clearly": True,
        "red_flags": False
    }
}
score, reason = calculate_rubric_score(rubric, "Q1", "test")
print(f"  Input: Irrelevant history (penalty)")
print(f"  Expected: Score=2")
print(f"  Actual: Score={score}")
print(f"  ✓ PASS" if score == 2 else "  ✗ FAIL")

# Test 4: Q3 Perfect STAR + Metrics
print("\n[TEST 4] Q3 Perfect STAR with Metrics")
rubric = {
    "checklist": {
        "star_situation": True,
        "star_action": True,
        "star_result": True,
        "has_metrics": True,
        "delivery_organized": True,
        "red_flags": False
    }
}
score, reason = calculate_rubric_score(rubric, "Q3", "test")
print(f"  Input: Full STAR + Metrics + Organized (UNICORN)")
print(f"  Expected: Score=5 (1+1+1+1+1)")
print(f"  Actual: Score={score}")
print(f"  ✓ PASS" if score == 5 else "  ✗ FAIL")

# Test 5: Q4 Missing Action (Magic Wand Penalty)
print("\n[TEST 5] Q4 Missing Action (Magic Wand)")
rubric = {
    "checklist": {
        "star_situation": True,
        "star_action": False,  # PENALTY
        "star_result": True,
        "has_metrics": True,
        "delivery_organized": True,
        "red_flags": False
    }
}
score, reason = calculate_rubric_score(rubric, "Q4", "test")
print(f"  Input: Situation+Result+Metrics+Organized BUT no Action")
print(f"  Expected: Score=2 (capped due to missing Action)")
print(f"  Actual: Score={score}")
print(f"  ✓ PASS" if score == 2 else "  ✗ FAIL")

# Test 6: Q5 Partial STAR
print("\n[TEST 6] Q5 Partial STAR (Situation + Action only)")
rubric = {
    "checklist": {
        "star_situation": True,
        "star_action": True,
        "star_result": False,
        "has_metrics": False,
        "delivery_organized": False,
        "red_flags": False
    }
}
score, reason = calculate_rubric_score(rubric, "Q5", "test")
print(f"  Input: Only Situation + Action")
print(f"  Expected: Score=2 (1+1)")
print(f"  Actual: Score={score}")
print(f"  ✓ PASS" if score == 2 else "  ✗ FAIL")

print("\n" + "=" * 60)
print("TEST SUITE COMPLETE")
print("=" * 60)
