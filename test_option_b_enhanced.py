# Test script to use Option B scoring with updated prompt
import os
import sys
sys.path.insert(0, '/Users/davidkish/Desktop/AI Career Coach')

# Temporarily replace scoring function with Option B
import api.index as api_module
from scoring_option_b import calculate_rubric_score_option_b

api_module.calculate_rubric_score = calculate_rubric_score_option_b

# Now run the comprehensive test
from test_option_b_full import test_option_b_comprehensive

if __name__ == "__main__":
    try:
        test_option_b_comprehensive()
    finally:
        # Function will be restored by test itself
        pass
