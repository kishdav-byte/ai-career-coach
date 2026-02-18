# OPTION B: 2/3/4 Scoring System
# Strategy: Clear tiers - Weak (2), Competent (3), Strong (4), Red Flag (1)

def calculate_rubric_score_option_b(rubric_data, question_index, answer_text):
    """
    Option B: 2/3/4 Scoring System
    - 1 = Red Flag (toxic, unethical)
    - 2 = Weak (missing STAR, vague)
    - 3 = Competent (clear structure)
    - 4 = Strong/Exceptional (STAR + metrics)
    """
    import re
    
    checklist = rubric_data.get("checklist", {})
    
    # RED FLAG OVERRIDE (Always 1)
    if checklist.get("red_flags") == True:
        return 1, "Toxic Behavior Detected"
    
    # AGGRESSIVE METRIC SCANNER
    metric_patterns = [
        r'\$\d+',  # Dollar amounts
        r'\d+(\.\d+)?%',  # Percentages
        r'\d+[KMB]',  # 35M, 22K, etc.
        r'\b\d+\s*(million|billion|thousand)\b',  # Written numbers
        r'\bzero\s+(incidents|errors|failures)\b',  # Zero incidents
        r'\b100%\s+(compliance|accuracy)\b',  # Perfect compliance
        r'\b\d+\+\s+(systems|clients|users)\b',  # 300+ systems
    ]
    
    business_keywords = [
        'ebitda', 'revenue', 'roi', 'profit', 'margin', 'savings', 
        'growth', 'efficiency', 'reduction', 'increase', 'cost',
        'sales', 'earnings', 'performance', 'productivity'
    ]
    
    answer_lower = answer_text.lower()
    
    # Detect metrics (AI + Backend)
    has_metrics = checklist.get("has_metrics", False)
    
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
    
    # Q1/Q2 (Background) Logic
    if question_index == "Q1" or question_index == "Q2":
        has_relevant = checklist.get("relevant_history", False)
        is_clear = checklist.get("communicated_clearly", False)
        
        if not has_relevant:
            return 2, None  # Weak background
        elif has_metrics:
            return 4, None  # Strong background with metrics
        elif is_clear:
            return 3, None  # Competent background
        else:
            return 2, None  # Weak
    
    # Q3-Q7 (Behavioral) - 2/3/4 SYSTEM
    else:
        has_star_s = checklist.get("star_situation", False)
        has_star_a = checklist.get("star_action", False)
        has_star_r = checklist.get("star_result", False)
        is_organized = checklist.get("delivery_organized", False)
        
        # BACKEND VALIDATION (only if AI says False)
        if not has_star_a:
            action_keywords = [
                'led', 'managed', 'built', 'created', 'developed', 'implemented',
                'designed', 'facilitated', 'recruited', 'supervised', 'organized',
                'coordinated', 'established', 'worked on', 'collaborated'
            ]
            if any(word in answer_lower for word in action_keywords):
                has_star_a = True
        
        if not has_star_r:
            result_keywords = [
                'result', 'outcome', 'achieved', 'delivered', 'generated',
                'increased', 'reduced', 'improved', 'successful', 'completed',
                'finished', 'done', 'got it done'
            ]
            if any(word in answer_lower for word in result_keywords):
                has_star_r = True
        
        complete_star = has_star_s and has_star_a and has_star_r
        partial_star = has_star_a and has_star_r  # A+R is good enough
        
        # 2/3/4 TIERED SCORING
        if (complete_star or partial_star) and has_metrics:
            return 4, None  # Strong/Exceptional: STAR + Metrics
        elif complete_star or partial_star:
            return 3, None  # Competent: Good STAR structure
        elif has_star_a or (is_organized and has_star_r):
            return 3, None  # Competent: At least organized with some structure
        else:
            return 2, None  # Weak: Missing critical elements
