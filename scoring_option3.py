# OPTION 3: Prompt-Enhanced + Backend Safety Net
# Strategy: Enhance AI prompt for better metric recognition + keep backend as safety

# Enhanced prompt additions for Option 3
OPTION3_PROMPT_ENHANCEMENT = """
### CRITICAL METRIC EXAMPLES (You MUST recognize these)
- "$35M", "$2.5B", "22%", "15% reduction", "3x growth" → has_metrics = TRUE
- "EBITDA", "revenue", "ROI", "profit", "margin", "cost savings" + ANY number → has_metrics = TRUE
- "zero incidents", "100% compliance", "300+ systems" → has_metrics = TRUE

### STAR STRUCTURE RECOGNITION
Action verbs: "Led", "Managed", "Built", "Implemented", "Designed", "Facilitated"
Result indicators: "generated $X", "achieved Y%", "delivered", "increased", "reduced"

If candidate uses THESE words + describes impact = FULL STAR CREDIT
"""

def calculate_rubric_score_option3(rubric_data, question_index, answer_text):
    """
    Option 3: Prompt-Enhanced + Backend Safety Net
    - AI gets enhanced examples in prompt
    - Backend provides safety net for missed metrics
    - Maintains 1/3/5 system for simplicity
    """
    import re
    
    checklist = rubric_data.get("checklist", {})
    
    # RED FLAG OVERRIDE
    if checklist.get("red_flags") == True:
        return 1, "Toxic Behavior Detected"
    
    # COMPREHENSIVE METRIC SCANNER (Safety Net)
    metric_patterns = [
        r'\$\d+',
        r'\d+(\.\d+)?%',
        r'\d+[KMB]',
        r'\b\d+\s*(million|billion|thousand)\b',
        r'\bzero\s+(incidents|errors|failures)\b',
        r'\b100%\s+(compliance|accuracy|success)\b',
        r'\b\d+\+\s+(systems|clients|users|projects)\b',
    ]
    
    business_keywords = [
        'ebitda', 'revenue', 'roi', 'profit', 'margin', 'savings', 
        'growth', 'efficiency', 'reduction', 'increase', 'cost',
        'compliance', 'accuracy', 'quality'
    ]
    
    answer_lower = answer_text.lower()
    
    # Check AI's assessment first
    has_metrics = checklist.get("has_metrics", False)
    
    # Backend override if AI missed obvious metrics
    if not has_metrics:
        for pattern in metric_patterns:
            if re.search(pattern, answer_text, re.IGNORECASE):
                has_metrics = True
                break
        
        if not has_metrics:
            for keyword in business_keywords:
                if keyword in answer_lower and re.search(r'\d+', answer_text):
                    has_metrics = True
                    break
    
    # Q1 (Background) Logic
    if question_index == "Q1" or question_index == "Q2":
        score = 0
        if checklist.get("relevant_history") == True: score += 3
        if checklist.get("communicated_clearly") == True: score += 1
        if has_metrics: score += 1
        if checklist.get("relevant_history") == False: score = 2
        return max(1, min(5, score)), None
    
    # Q2-Q6 (Behavioral) - 1/3/5 WITH ENHANCED DETECTION
    else:
        has_star_s = checklist.get("star_situation", False)
        has_star_a = checklist.get("star_action", False)
        has_star_r = checklist.get("star_result", False)
        
        # Backend STAR validation
        action_keywords = ['led', 'managed', 'built', 'implemented', 'designed', 'facilitated',
                          'created', 'developed', 'recruited', 'supervised', 'coordinated']
        result_keywords = ['generated', 'achieved', 'delivered', 'increased', 'reduced',
                          'improved', 'successful', 'completed', 'saved']
        
        if any(word in answer_lower for word in action_keywords):
            has_star_a = True
        if any(word in answer_lower for word in result_keywords):
            has_star_r = True
        
        complete_star = has_star_s and has_star_a and has_star_r
        partial_star = has_star_a and has_star_r  # A+R is good enough
        
        # SCORING
        if (complete_star or partial_star) and has_metrics:
            score = 5  # Exceptional
        elif complete_star or partial_star:
            score = 3  # Competent
        else:
            score = 1  # Weak
        
        return score, None
