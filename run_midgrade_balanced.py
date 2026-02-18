import os
import json
import sys
sys.path.insert(0, '/Users/davidkish/Desktop/AI Career Coach')

from api.index import app
from scoring_option1_balanced import calculate_rubric_score_option1_balanced

# Rerun mid-grade test with balanced scoring
import api.index as api_module
original_function = api_module.calculate_rubric_score
api_module.calculate_rubric_score = calculate_rubric_score_option1_balanced

# Import and run the test
from test_midgrade_answers import test_midgrade_answers

if __name__ == "__main__":
    try:
        test_midgrade_answers()
    finally:
        api_module.calculate_rubric_score = original_function
