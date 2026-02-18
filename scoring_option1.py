# OPTION 1: Aggressive Backend Override
# Strategy: Make backend metric scanner extremely aggressive and override AI scoring more forcefully

def calculate_rubric_score_option1(rubric_data, question_index, answer_text):
    """
    Option 1: Aggressive Backend Override
    - Extremely aggressive metric detection
    - Override AI scoring when clear STAR+metrics present
    """
    import re
    
    checklist = rubric_data.get("checklist", {})
    
    # RED FLAG OVERRIDE
    if checklist.get("red_flags") == True:
        return 1, "Toxic Behavior Detected"
    
    # ULTRA-AGGRESSIVE METRIC SCANNER
    metric_patterns = [
        r'\$\d+',  # Dollar amounts
        r'\d+(\.\d+)?%',  # Percentages
        r'\d+[KMB]',  # 35M, 22K, etc.
        r'\b\d+\s*(million|billion|thousand)\b',  # Written numbers
        r'\b\d+x\b',  # Multipliers (2x growth)
    ]
    
    business_keywords = [
        'ebitda', 'revenue', 'roi', 'profit', 'margin', 'savings', 
        'growth', 'efficiency', 'reduction', 'increase', 'cost',
        'sales', 'earnings', 'performance', 'productivity'
    ]
    
    answer_lower = answer_text.lower()
    
    # Detect metrics
    has_metrics = False
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
        # AGGRESSIVE: If metrics present, auto-bump to 4
        if has_metrics: 
            score = max(score, 4)
        if checklist.get("relevant_history") == False: score = 2
        return max(1, min(5, score)), None
    
    # Q2-Q6 (Behavioral) - AGGRESSIVE OVERRIDE
    else:
        has_star_s = checklist.get("star_situation", False)
        has_star_a = checklist.get("star_action", False)
        has_star_r = checklist.get("star_result", False)
        
        # Check for STAR keywords in text (backend validation)
        has_action_words = any(word in answer_lower for word in [
            'led', 'managed', 'built', 'created', 'developed', 'implemented',
            'designed', 'facilitated', 'recruited', 'supervised'
        ])
        has_result_words = any(word in answer_lower for word in [
            'result', 'outcome', 'achieved', 'delivered', 'generated',
            'increased', 'reduced', 'improved', 'successful'
        ])
        
        # Override if backend detects structure AI missed
        if has_action_words: has_star_a = True
        if has_result_words: has_star_r = True
        
        complete_star = has_star_s and has_star_a and has_star_r
        
        # SCORING LOGIC
        if complete_star and has_metrics:
            score = 5  # Exceptional
        elif has_metrics and (has_star_a or has_star_r):
            score = 5  # Backend override: metrics + partial STAR = 5
        elif complete_star:
            score = 3  # Competent
        elif has_star_a and has_star_r:
            score = 3  # Partial STAR = 3
        else:
            score = 1  # Weak
        
        return score, None
