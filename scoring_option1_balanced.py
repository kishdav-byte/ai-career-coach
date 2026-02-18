# OPTION 1 BALANCED: Aggressive Backend Override (Fair to All Levels)
# Strategy: Aggressive metric detection + Fair assessment of structure

def calculate_rubric_score_option1_balanced(rubric_data, question_index, answer_text):
    """
    Option 1 Balanced: Aggressive Backend Override but fair to mid-grade answers
    - Aggressive metric detection
    - Backend validates STAR but doesn't over-credit vague answers
    - Fair 1/3/5 scoring for all performance levels
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
        r'\bzero\s+(incidents|errors|failures)\b',  # Zero incidents
        r'\b100%\s+(compliance|accuracy)\b',  # Perfect compliance
        r'\b\d+\+\s+(systems|clients)\b',  # 300+ systems
    ]
    
    business_keywords = [
        'ebitda', 'revenue', 'roi', 'profit', 'margin', 'savings', 
        'growth', 'efficiency', 'reduction', 'increase', 'cost',
        'sales', 'earnings', 'performance', 'productivity'
    ]
    
    answer_lower = answer_text.lower()
    
    # Detect metrics
    has_metrics = checklist.get("has_metrics", False)
    
    # Backend override if metrics exist
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
        # If metrics present, bump to 4
        if has_metrics: 
            score = max(score, 4)
        if checklist.get("relevant_history") == False: score = 2
        return max(1, min(5, score)), None
    
    # Q2-Q6 (Behavioral) - BALANCED LOGIC
    else:
        has_star_s = checklist.get("star_situation", False)
        has_star_a = checklist.get("star_action", False)
        has_star_r = checklist.get("star_result", False)
        is_organized = checklist.get("delivery_organized", False)
        
        # BACKEND STAR VALIDATION (only if AI is uncertain)
        # Only override if AI says False but we see clear evidence
        if not has_star_a:
            action_keywords = [
                'led', 'managed', 'built', 'created', 'developed', 'implemented',
                'designed', 'facilitated', 'recruited', 'supervised', 'organized',
                'coordinated', 'established'
            ]
            if any(word in answer_lower for word in action_keywords):
                has_star_a = True
        
        if not has_star_r:
            result_keywords = [
                'result', 'outcome', 'achieved', 'delivered', 'generated',
                'increased', 'reduced', 'improved', 'successful', 'completed',
                'finished', 'done'
            ]
            if any(word in answer_lower for word in result_keywords):
                has_star_r = True
        
        complete_star = has_star_s and has_star_a and has_star_r
        partial_star = has_star_a and has_star_r  # A+R is decent
        
        # BALANCED 1/3/5 SCORING
        if complete_star and has_metrics:
            score = 5  # Exceptional: Full STAR + Metrics
        elif partial_star and has_metrics:
            score = 5  # Strong: Good structure + Metrics
        elif complete_star:
            score = 3  # Competent: Full STAR but no metrics
        elif partial_star:
            score = 3  # Competent: A+R is good enough
        elif has_star_a or (is_organized and has_star_r):
            score = 3  # Competent: Has Action OR organized with Result
        else:
            score = 1  # Weak: Missing critical elements (Gap Logic, Magic Wand, etc.)
        
        return score, None
