#!/usr/bin/env python3
# Quick test to verify score label mapping

def get_score_label(score):
    """Map numeric score to user-friendly label"""
    if score >= 3.5:
        return "Well Done"
    elif score >= 2.5:
        return "Average"
    else:
        return "Needs Work"

# Test all score ranges
test_scores = [
    (2.0, "Needs Work"),
    (2.4, "Needs Work"),
    (2.5, "Average"),
    (2.8, "Average"),
    (3.0, "Average"),
    (3.4, "Average"),
    (3.5, "Well Done"),
    (3.8, "Well Done"),
    (4.0, "Well Done"),
]

print("="*60)
print("SCORE LABEL MAPPING TEST")
print("="*60)
print(f"{'Score':<10} {'Expected Label':<20} {'Actual Label':<20} {'Status'}")
print("-"*60)

all_pass = True
for score, expected in test_scores:
    actual = get_score_label(score)
    status = "✅" if actual == expected else "❌"
    if actual != expected:
        all_pass = False
    print(f"{score:<10.1f} {expected:<20} {actual:<20} {status}")

print("="*60)
if all_pass:
    print("✅ ALL TESTS PASSED")
else:
    print("❌ SOME TESTS FAILED")
print("="*60)

# Show examples of what users will see
print("\nEXAMPLE USER-FACING SCORES:")
print("-"*60)
print("Exceptional candidate (3.8/4.0): 'Well Done'")
print("Mid-grade candidate (2.8/4.0): 'Average'")
print("Weak candidate (2.2/4.0): 'Needs Work'")
print("="*60)
