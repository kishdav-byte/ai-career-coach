# OPTION 2: 1/3/4/5 Hybrid System
# Strategy: Add a 4-point tier for "Strong but not exceptional" answers

def calculate_rubric_score_option2(rubric_data, question_index, answer_text):
    """
    Option 2: 1/3/4/5 Hybrid System
    - 5 = Exceptional (Full STAR + Multiple metrics + Strategic insight)
    - 4 = Strong (Full STAR + At least one metric)
    - 3 = Competent (Clear STAR structure OR good business context)
    - 1 = Weak (Missing critical elements)
    """
    import re
    
    checklist = rubric_data.get("checklist", {})
    
    # RED FLAG OVERRIDE
    if checklist.get("red_flags") == True:
        return 1, "Toxic Behavior Detected"
    
    # METRIC SCANNER
    metric_patterns = [
        r'\$\d+',
        r'\d+(\.\d+)?%',
        r'\d+[KMB]',
        r'\b\d+\s*(million|billion|thousand)\b',
    ]
    
    business_keywords = [
        'ebitda', 'revenue', 'roi', 'profit', 'margin', 'savings', 
        'growth', 'efficiency', 'reduction', 'increase'
    ]
    
    answer_lower = answer_text.lower()
    
    # Count metrics found
    metric_count = 0
    for pattern in metric_patterns:
        metric_count += len(re.findall(pattern, answer_text, re.IGNORECASE))
    
    for keyword in business_keywords:
        if keyword in answer_lower and re.search(r'\d+', answer_text):
            metric_count += 1
    
    has_metrics = metric_count > 0
    has_multiple_metrics = metric_count >= 2
    
    # Q1 (Background) Logic
    if question_index == "Q1" or question_index == "Q2":
        score = 0
        if checklist.get("relevant_history") == True: score += 3
        if checklist.get("communicated_clearly") == True: score += 1
        if has_metrics: score += 1
        if checklist.get("relevant_history") == False: score = 2
        return max(1, min(5, score)), None
    
    # Q2-Q6 (Behavioral) - 1/3/4/5 SYSTEM
    else:
        has_star_s = checklist.get("star_situation", False)
        has_star_a = checklist.get("star_action", False)
        has_star_r = checklist.get("star_result", False)
        
        complete_star = has_star_s and has_star_a and has_star_r
        partial_star = (has_star_a and has_star_r) or (has_star_s and has_star_a)
        
        # TIERED SCORING
        if complete_star and has_multiple_metrics:
            score = 5  # Exceptional: Full STAR + Multiple metrics
        elif complete_star and has_metrics:
            score = 4  # Strong: Full STAR + At least one metric
        elif complete_star:
            score = 3  # Competent: Full STAR but no metrics
        elif partial_star and has_metrics:
            score = 4  # Strong: Partial STAR but has metrics
        elif partial_star:
            score = 3  # Competent: Partial STAR
        else:
            score = 1  # Weak
        
        return score, None
