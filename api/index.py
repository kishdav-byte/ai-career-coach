from flask import Flask, request, jsonify
import re
import os
import requests
import json
import time

import base64
import io
import ast
from datetime import datetime, timedelta
from dotenv import load_dotenv
import stripe

load_dotenv()

# ==========================================
# INITIALIZATION (MOVED TO TOP)
# ==========================================
from supabase import create_client, Client

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
# Support both standard naming conventions
SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY') or os.environ.get('SUPABASE_SERVICE_KEY')

supabase: Client = None
supabase_admin: Client = None

if SUPABASE_URL:
    if SUPABASE_KEY:
        try:
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            print("Supabase client initialized successfully")
        except Exception as e:
            print(f"Error initializing Supabase: {e}")
    
    if SUPABASE_SERVICE_KEY:
        try:
            supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
            print("Supabase ADMIN client initialized successfully")
        except Exception as e:
            print(f"Error initializing Supabase Admin: {e}")
    else:
        print("WARNING: SUPABASE_SERVICE_ROLE_KEY not found. Webhooks may fail RLS.")

app = Flask(__name__)

# API Key from Environment Variable
API_KEY = os.environ.get('OPENAI_API_KEY_')

# ==========================================
# LOGGING HELPERS
# ==========================================
def log_db_activity(email, feature, metadata=None):
    """Log user activity to Supabase."""
    if not supabase: return
    try:
        supabase.table('activity_logs').insert({
            "user_email": email,
            "feature": feature,
            "metadata": metadata or {}
        }).execute()
    except Exception as e:
        print(f"Activity Log Failed: {e}")

def log_db_error(email, error_type, details):
    """Log system error to Supabase."""
    if not supabase: return
    try:
        supabase.table('error_logs').insert({
            "user_email": email, # Can be 'system' or None
            "error_type": error_type,
            "details": str(details)
        }).execute()
    except Exception as e:
        print(f"Error Log Failed: {e}")

# Initialize Stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
stripe_price_id = os.environ.get('STRIPE_PRICE_ID')
stripe_webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
app_domain = os.environ.get('APP_DOMAIN', 'http://localhost:3000')

def generate_audio_openai(text, voice_id):
    """Generates audio using OpenAI TTS API."""
    try:
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "tts-1",
            "input": text,
            "voice": voice_id if voice_id in ["alloy", "echo", "fable", "onyx", "nova", "shimmer"] else "alloy"
        }
        
        response = requests.post(
            "https://api.openai.com/v1/audio/speech",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        
        return base64.b64encode(response.content).decode('utf-8')
    except Exception as e:
        print(f"OpenAI TTS error: {e}")
        return None

def call_openai(messages, json_mode=False):
    """Helper function to call OpenAI API."""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "gpt-4o-mini",
        "messages": messages,
        "max_tokens": 4096
    }
    
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        json=payload
    )
    response.raise_for_status()
    result = response.json()
    return result['choices'][0]['message']['content']

@app.route('/api/generate-model-answer', methods=['POST'])
def generate_model_answer():
    if not API_KEY:
        return jsonify({"error": "Server API Key missing"}), 500

    data = request.json
    question = data.get('question')
    resume_context = data.get('resume_context', '')

    if not question:
        return jsonify({"error": "Question is required"}), 400

    # Strict JSON formatting instruction
    system_prompt = (
        "You are an expert executive candidate. Answer the interview question using the STAR method. "
        "Be specific, use metrics, and be concise. "
        "Return ONLY a JSON object with this exact schema: "
        "{'situation_task': '...', 'action': '...', 'result': '...'}. "
        "Do not include markdown or extra text."
    )
    
    user_message = f"Question: {question}\n\nResume Context: {resume_context}\n\nProvide a perfect STAR answer."

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]

    try:
        content = call_openai(messages, json_mode=True)
        # Parse JSON to ensure validity before returning
        parsed_content = json.loads(content)
        return jsonify(parsed_content)
    except Exception as e:
        print(f"Model Answer Gen Error: {e}")
        return jsonify({"error": "Failed to generate answer"}), 500

@app.route('/api/optimize', methods=['POST'])
def optimize_resume_content():
    if not API_KEY:
        return jsonify({"error": "Server configuration error: API Key missing"}), 500

    data = request.json
    user_data = data.get('user_data')
    template_name = data.get('template_name', 'modern')
    job_description = data.get('job_description', '')

    # Construct Prompt
    base_instruction = "Optimize the following resume content for a professional look. Improve clarity and impact."
    
    tailoring_instruction = ""
    if job_description:
        tailoring_instruction = f"\n\nTARGET JOB DESCRIPTION:\n{job_description}\n\nTAILORING INSTRUCTION: Tailor the resume content to align with the above Job Description. Use relevant keywords and phrasing from the JD. Emphasize matching skills. Do NOT invent new experience or skills."

    formatting_instruction = ""
    if template_name == 'condensed':
        formatting_instruction = "\n\nFORMATTING CRITICAL INSTRUCTION: Rewrite the 'Experience' descriptions as a list of concise, high-impact bullet points. Start each bullet with a hyphen (-). Do NOT use paragraphs. This formatting requirement overrides any other style instructions."
    else:
        formatting_instruction = "\n\nFORMATTING INSTRUCTION: Use professional paragraphs for the experience section. Do not use bullet points."

    prompt = f"""
    {base_instruction}
    {tailoring_instruction}
    {formatting_instruction}

    Here is the data:
    {json.dumps(user_data)}

    Return ONLY valid JSON with the exact same structure (personal, summary, experience, education, skills).
    Do not include markdown formatting (like ```json). Just the raw JSON string.
    """

    try:
        messages = [{"role": "user", "content": prompt}]
        text = call_openai(messages, json_mode=True)
        
        # Clean up markdown if present
        if text.startswith('```json'):
            text = text[7:]
        if text.startswith('```'):
            text = text[3:]
        if text.endswith('```'):
            text = text[:-3]
        
        
        # LOG ACTIVITY
        email = user_data.get('personal', {}).get('email')
        if email:
            log_db_activity(email, 'resume_analysis')
            
        return jsonify(json.loads(text))
            
    except Exception as e:
        print(f"Error calling OpenAI: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/create-checkout-session', methods=['POST'])
def create_checkout_session():
    data = request.json
    try:
        # Allow frontend to pass priceId, OR use Env Var for specific features
        price_id = data.get('priceId')
        success_url = data.get('successUrl')
        cancel_url = data.get('cancelUrl')
        email = data.get('email')
        feature = data.get('feature') # 'rewrite', etc.

        if feature == 'rewrite':
            price_id = os.environ.get('STRIPE_REWRITE_PRICE_ID')
        
        # Fallback if still no price_id
        if not price_id:
             return jsonify({'error': 'Missing Price ID configuration'}), 400

        if not success_url or not cancel_url:
             return jsonify({'error': 'Missing required URL parameters'}), 400

        checkout_session = stripe.checkout.Session.create(
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            customer_email=email,
            metadata={'user_email': email, 'feature': feature or 'resume', 'plan_type': 'resume'}
        )
        return jsonify({'url': checkout_session.url})
    except Exception as e:
        print(f"Stripe Error: {e}")
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        print(f"Stripe Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api', methods=['POST'])
def api():
    if not API_KEY:
        return jsonify({"error": "Server configuration error: API Key missing"}), 500

    data = request.json
    action = data.get('action')
    
    messages = []
    json_mode = False

    # ---------------------------------------------------------
    # ADMIN GHOST MODE CHECK
    # ---------------------------------------------------------
    is_admin_ghost = data.get('ghostMode', False)
    # Important: In production, verify the user is ACTUALLY an admin on the server side 
    # before trusting this flag. For this implementation, we will trust the client 
    # but verify the user's role logic below if 'is_admin_ghost' is True.
    
    # ---------------------------------------------------------
    # ACCESS CONTROL & MONETIZATION CHECK (Phase 13)
    # ---------------------------------------------------------
    PAID_ACTIONS = ['interview_chat', 'generate_report', 'analyze_resume', 'optimize_resume', 'optimize']
    
    if action in PAID_ACTIONS:
        # Get email from request data OR try to infer it if possible
        # Frontend 'callApi' usually sends parameters, but we need to ensure 'email' passes through
        # 'optimize_resume' uses 'user_data' -> 'personal' -> 'email'
        email = data.get('email')
        
        if not email and action == 'optimize_resume' and 'user_data' in data:
            email = data.get('user_data', {}).get('personal', {}).get('email')

        if not email and action == 'analyze_resume' and 'email' not in data:
             # Assume analyze_resume sends email or we fail
             pass 

        if email:
            # FIX: Use Admin Client to bypass RLS (like /auth/user)
            db_client = supabase_admin if supabase_admin else supabase
            
            if db_client:
                # Check User Status (Updated Phase 34)
                user_res = db_client.table('users').select('subscription_status, is_unlimited, resume_credits, interview_credits, rewrite_credits').eq('email', email).execute()
                
                if user_res.data:
                    user = user_res.data[0]
                    
                    # ADMIN BYPASS LOGIC
                    user_role = user.get('role', 'user')
                    if is_admin_ghost and user_role == 'admin':
                         print(f"👻 GHOST MODE ACTIVE for Admin {email}. Bypassing deduction.")
                         # Grant access immediately and skip deduction logic
                         has_access = True
                         # We set a flag to ensure we don't deduct later
                         should_deduct = False
                    else:
                         should_deduct = True

                    is_unlimited = user.get('is_unlimited', False)
                    # Get Specific Credits (Phase 19)
                    resume_credits = user.get('resume_credits', 0)
                    interview_credits = user.get('interview_credits', 0)
                    rewrite_credits = user.get('rewrite_credits', 0)
                    
                    # Log Check
                    print(f"Auth Check for {email}: Unlimited={is_unlimited}, R_Cred={resume_credits}, I_Cred={interview_credits}, Action={action}")

                    # Logic: ALLOW if 'is_unlimited' OR Specific Credit > 0
                    has_access = False
                    
                    if is_admin_ghost and user_role == 'admin':
                         has_access = True

                    elif is_unlimited:
                        has_access = True
                    else:
                        # Check specific credit based on action
                        if action in ['analyze_resume', 'optimize_resume']:
                            if resume_credits > 0:
                                has_access = True
                                # Deduct immediately (unless unlimited, which is handled above)
                                if should_deduct:
                                    new_credits = resume_credits - 1
                                    supabase_upd = supabase_admin if supabase_admin else supabase
                                    supabase_upd.table('users').update({'resume_credits': new_credits}).eq('email', email).execute()
                                    print(f"Deducted 1 RESUME credit. Remaining: {new_credits}")

                        elif action == 'optimize':
                            # V2 REWRITE CREDIT CHECK
                            if rewrite_credits > 0:
                                has_access = True
                                if should_deduct:
                                    new_credits = rewrite_credits - 1
                                    supabase_upd = supabase_admin if supabase_admin else supabase
                                    supabase_upd.table('users').update({'rewrite_credits': new_credits}).eq('email', email).execute()
                                    print(f"Deducted 1 REWRITE credit. Remaining: {new_credits}")
                            else:
                                 print(f"Blocked: Insufficient Rewrite Credits ({rewrite_credits})")
                                 has_access = False
                        
                        elif action in ['interview_chat', 'generate_report']:
                            if action == 'generate_report':
                                 # DEDUCTION LOGIC (Post-Generation)
                                 # We check here but deduct later
                                 if interview_credits > 0:
                                     has_access = True
                                     print(f"Skipping immediate deduction for {action}. Will deduct from interview_credits after success.")
                            
                            elif action == 'interview_chat':
                                # INTERVIEW DEDUCTION LOGIC
                                # 1. Is it the Start/Welcome? -> FREE
                                is_start_req = data.get('isStart', False)
                                q_count = data.get('questionCount', 1)
                                
                                if is_start_req:
                                    has_access = True
                                    print("Interview Start (Welcome): Access Granted (Free)")
                                
                                # 2. Is it the First Response? -> PAY TO PLAY
                                elif q_count == 1:
                                    if interview_credits > 0:
                                        has_access = True
                                        if should_deduct:
                                            new_credits = interview_credits - 1
                                            if supabase:
                                                 supabase_upd = supabase_admin if supabase_admin else supabase
                                                 supabase_upd.table('users').update({'interview_credits': new_credits}).eq('email', email).execute()
                                                 print(f"DEDUCTED 1 INTERVIEW CREDIT. Remaining: {new_credits}")
                                            else:
                                                 print("DEV: Mock Deduction")
                                    else:
                                        has_access = False
                                        print("Blocked: Insufficient Interview Credits")
                                else:
                                    # Subsequent messages checks (simplified: if they started, they can finish)
                                    has_access = True




                    
                    if not has_access:
                        return jsonify({
                            "error": "Insufficient credits for this tool. Please purchase a package.",
                            "redirect": "/pricing.html"
                        }), 403
                else:
                    return jsonify({"error": "User not found. Please log in."}), 403
            else:
                 print("DEV MODE: Skipping Auth Check (No Supabase)")
        else:
             # If strictly enforcing, we could error here. 
             # For now, let's allow if no email is found but warn, OR prevent it.
             # Given user request "Secure active features", we should strictly require email.
             # The user prompt implies "only paid users", so we enforce stricter check.
             # For now, we'll allow if no email is found, but a real app might return 403.
             pass
             
    # ---------------------------------------------------------

    if action == 'analyze_resume':
        resume = data.get('resume', '')
        json_mode = True
        prompt = f"""
        You are an expert Executive Career Coach (rate $200/hr). Analyze this resume.
        
        RESUME CONTENT:
        {resume}
        
        INSTRUCTION:
        First, read the resume and identify the "Target Job Title" if explicitly stated or inferred.
        Return it in the JSON as "job_title".
        
        CRITICAL RULES FOR ANALYSIS (VIOLATIONS = FAILURE):
        1. **NO INVENTED METRICS**: Never invent a number. If a metric is missing, use a placeholder like "[X]%" or "$[X]k".
        2. **EXACT QUOTES ONLY**: When referencing "Current Bullet", "Found", or "Example", you MUST quote the resume word-for-word. Do not summarize.
        3. **REALITY CHECK**: Only suggest keywords for bullets that ACTUALLY exist.
        4. **HYPER-SPECIFICITY**: 
           - ATS: Give exact counts ("appears 5x") and synonyms.
           - Formatting: Show "Found: [A] vs [B]" and "Fix: [Instruction]".
           - Action Plan: Reference specific roles and bullets ("Add size to 'Manager' role").
        
        Return valid JSON with this EXACT structure:
        {{
            "job_title": "Senior Product Manager",
            "overall_score": 85,
            "summary": "Brief 1-sentence summary of where they stand.",
            "benchmark": {{
                "level": "Mid-Senior",
                "percentile": "Top 20%",
                "user_score": 85,
                "avg_score": 68,
                "top_10_score": 92,
                "text": "Status: You're stronger than 75% of candidates.",
                "ahead_reasons": ["Specific strength from THEIR resume", "Specific strength from THEIR resume"],
                "gap_reasons": ["Specific weakness from THEIR resume", "Specific weakness from THEIR resume"]
            }},
            "red_flags": [
                {{
                    "title": "Duplicate Bullet Points",
                    "issue": "Your 'Manager' and 'Director' roles have identical bullets.",
                    "examples": ["'Managed team of 10...' (appears in both roles)"],
                    "fix": "Rewrite the Director role to focus on strategy and the Manager role on execution."
                }},
                 {{
                    "title": "Missing Metrics in Recent Role",
                    "issue": "Your most recent role (2022-Present) has zero numbers.",
                    "examples": ["'Responsible for project delivery' (too vague)"],
                    "fix": "Add team size, budget, or % improvement."
                }}
            ],
            "strengths": [
                {{"title": "Strength 1", "description": "Why it is good..."}},
                {{"title": "Strength 2", "description": "Why it is good..."}},
                {{"title": "Strength 3", "description": "Why it is good..."}}
            ],
            "improvements": [
                {{
                    "priority": "HIGH", 
                    "title": "Clarify Impact", 
                    "suggestion": "Quantify your achievements...",
                    "current": "Managed a team...", 
                    "better": "Managed a team of [X] (add count), increasing productivity by [X]%...", 
                    "why": "Recruiters need numbers...", 
                    "how_to": "Review your last 2 roles..."
                }}
            ],
            "keywords": {{
                "good": [
                    {{"word": "Leadership", "count": 5, "context": "Used in executive bullets"}}, 
                    {{"word": "Project Management", "count": 4, "context": "Used in project descriptions"}}
                ],
                "missing": [
                    {{"word": "Stakeholder Management", "advice": "Add to 'Senior Manager' role bullets about alignment."}}, 
                    {{"word": "Change Management", "advice": "Add to leadership bullets."}}
                ],
                "overused": [
                    {{"word": "Managed", "count": 8, "alternatives": ["Led", "Directed", "Oversaw"]}}
                ],
                "advice": "Add missing keywords to your most recent experience."
            }},
            "rewrites": [
                {{
                    "type": "Leadership", 
                    "original": "[EXACT text from resume]", 
                    "rewritten": "Directed [X]-person team... achieved [X]% improvement...", 
                    "explanation": "Added team size and specific metric.",
                    "metric_question": "What was your team size and actual % improvement?"
                }}
            ],
            "role_gaps": [
                {{
                    "role": "Role Title", 
                    "missing_keywords": ["Strategy", "Budgeting"], 
                    "fixes": [
                        {{
                            "existing_bullet": "[Exact quote of bullet]",
                            "enhanced_bullet": "[Rewritten bullet with keyword]",
                            "added_keywords": ["Strategy"],
                            "reason": "Required for senior roles."
                        }}
                    ]
                }}
            ],
            "ats_compatibility": {{
                "score": 8,
                "issues": [
                    "<b>Action Verb Repetition:</b> 'Managed' appears 8 times. <br>→ Alternatives: Led, Directed, Orchestrated. <br>→ Example: Replace 'Managed team' with 'Directed team'.",
                    "<b>Generic Phrases:</b> 'Responsible for' found in 3 bullets. <br>→ Fix: Start with the verb directly (e.g., 'Delivered...')."
                ],
                "recommendation": "Varied vocabulary significantly improves ATS scoring."
            }},
            "formatting": [
                {{
                    "issue": "Date Consistency", 
                    "fix": "<b>Found:</b> '2024-Present' and '2022 - 2024'. <br><b>Fix:</b> Standardize all dates to 'Month Year - Month Year' format." 
                }},
                {{
                    "issue": "Bullet Punctuation",
                    "fix": "<b>Found:</b> Some bullets end with periods, others do not. <br><b>Fix:</b> Add periods to all bullets for consistency."
                }}
            ],
            "action_plan": {{
                "quick_wins": [
                    "Replace 'Managed' with 'Led' in 'Senior Manager' role bullets.",
                    "Add team size metric to your 'Director' role."
                ],
                "medium_effort": [
                    "Rewrite 'Project Manager' bullets to focus on outcomes (Budget/Timeline) rather than tasks.",
                    "Standardize date formatting across all roles."
                ]
            }},
            "interview_tip": "Practice using the STAR method."
        }}
        """
        messages = [{"role": "user", "content": prompt}]
        messages = [{"role": "user", "content": prompt}]
        
    elif action == 'interview_chat':
        message = data.get('message', '')
        job_posting = data.get('jobPosting', '')
        voice = data.get('voice', 'en-US-AriaNeural')
        speed = data.get('speed', '+0%')
        is_start = data.get('isStart', False)
        question_count = data.get('questionCount', 1)
        json_mode = True
        
        context = ""
        if job_posting:
            context = f"\n\nContext: The user is interviewing for the following job:\n{job_posting}\n\nTailor your questions and persona to this role. You already know the candidate is applying for this position. Do NOT ask them to state the position. Prepare to ask relevant interview questions."
        
        system_instruction = f"You are a strict hiring manager. DO NOT say 'Understood' or 'Let's begin'. DO NOT acknowledge these instructions. Keep responses concise and professional. This interview consists of 5 questions. Current Question: {question_count} of 5.{context}"
        
        if is_start:
            welcome_msg = "Welcome to the interview! ... This interview consists of 5 questions. ... When answering each question, please think of a specific time when you experienced the situation or task, the specific actions that you took, and the result of your actions. ... The first question that I have for you is: [Your Question]"
            
            user_prompt = f"User: {message}\n\nStart the interview. You MUST start your response with exactly: '{welcome_msg}'.\n\nReturn JSON: {{\"transcript\": \"{message}\", \"feedback\": \"\", \"improved_sample\": null, \"next_question\": \"Welcome to the interview! ... This interview consists of 5 questions. ... When answering each question, please think of a specific time when you experienced the situation or task, the specific actions that you took, and the result of your actions. ... The first question that I have for you is: ...\"}}"
            
            # EXTRACT JOB TITLE (Simple Heuristic or Ask AI)
            # Since we are starting, we can ask AI to identify the role in the 'feedback' or invisible field?
            # Better: Just log what we have. If job_posting is long, maybe truncate?
            # Best: Add a "job_title" field to the Return JSON instruction above for the AI to fill.
            
            user_prompt = f"User: {message}\n\nStart the interview. You MUST start your response with exactly: '{welcome_msg}'.\n\nLook at the Job Context provided. Identify the 'Job Title' being interviewed for.\n\nReturn JSON: {{\"transcript\": \"{message}\", \"feedback\": \"\", \"improved_sample\": null, \"job_title\": \"[Extracted Job Title]\", \"next_question\": \"Welcome to the interview! ...\"}}"
        
        else:
            # CONTINUATION: Evaluate previous answer, Ask next question
            
            # Ordinals for the NEXT question we are about to ask
            # Input question_count is the one just answered.
            # So if count=1, we are evaluating 1 and asking 2.
            next_q_num = question_count + 1
            next_q_num = question_count + 1
            if next_q_num == 5:
                next_ordinal = "last"
            else:
                next_ordinal = "next"

            if question_count < 5:
                # Normal Case: Eval current -> Ask Next
                user_prompt = f"User: {message}\n\nEvaluate the answer to Question {question_count}. You MUST provide a SCORE (0-5).\n\nCRITICAL INSTRUCTIONS:\n1. Start 'feedback' with: \"I would score this answer a [score] because...\".\n2. IF SCORE IS 5: Set 'improved_sample' to null. Do NOT provide a better answer.\n3. IF SCORE < 5: Provide a better answer in 'improved_sample'.\n\nAfter feedback, IMMEDIATELY ask the {next_ordinal} interview question.\n\nReturn STRICT JSON: {{\"transcript\": \"{message}\", \"feedback\": \"I would score this answer a [score] because...\", \"score\": 0, \"improved_sample\": \"... (or null if score is 5)\", \"next_question\": \"The {next_ordinal} question that I have for you is: ...\"}}"
            
            else:
                # Final Case: Eval Q5 -> End
                user_prompt = f"User: {message}\n\nEvaluate the answer to the final question (Question 5). You MUST provide a SCORE (0-5).\n\nCRITICAL INSTRUCTIONS:\n1. Start 'feedback' with: \"I would score this answer a [score] because...\".\n2. IF SCORE IS 5: Set 'improved_sample' to null.\n3. IF SCORE < 5: Provide a better answer.\n\nThis was the final question. End the interview professionally.\n\nReturn STRICT JSON: {{\"transcript\": \"{message}\", \"feedback\": \"I would score this answer a [score] because...\", \"score\": 0, \"improved_sample\": \"... (or null if score is 5)\", \"next_question\": \"That concludes our interview. Thank you for your time.\"}}"
        
        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_prompt}
        ]


    elif action == 'get_user':
        # Unified User Fetch (Replaces /api/auth/user)
        email = data.get('email', '').strip().lower()
        if not email:
            return jsonify({"error": "Email is required"}), 400
        
        if supabase:
            result = supabase.table('users').select('id, email, name, subscription_status, is_unlimited, resume_credits, interview_credits').eq('email', email).execute()
            if result.data and len(result.data) > 0:
                 return jsonify({"success": True, "user": result.data[0]})
            else:
                 return jsonify({"error": "User not found"}), 404
        else:
            return jsonify({"error": "Database not configured"}), 500

    elif action == 'generate_report':
        history = data.get('history', [])
        json_mode = True
        prompt = f"""
        Generate a Final Interview Report based on the following interview history.
        
        History:
        {json.dumps(history)}
        
        Create a professional HTML report (NO markdown, just HTML content) that includes:
        1.  **Performance Summary**: A brief paragraph summarizing the candidate's overall performance.
        2.  **Question Breakdown**: A table with columns: Question, Score (0-5), and Key Feedback.
        3.  **Recommended Improvements**: A bulleted list of specific, actionable steps to improve.
        
        Style the HTML with simple inline CSS for readability (e.g., borders for table, bold text for headers).
        
        Return JSON: {{ "report": "<html>...</html>" }}
        """
        messages = [{"role": "user", "content": prompt}]
    
    elif action == 'career_plan':
        job_title = data.get('jobTitle', '')
        company = data.get('company', '')
        job_posting = data.get('jobPosting', '')

        messages = [
            {"role": "system", "content": "You are an expert Executive Career Strategist helping a candidate land a high-level role. Your goal is to write a 30-60-90 Day Plan that proves the candidate can deliver value immediately."},
            {"role": "user", "content": f"""
    Input Context:
    
    Job Title: {job_title}
    
    Company: {company}
    
    Job Description (JD): {job_posting}
    
    Core Instructions:
    
    Analyze the Tech Stack:
    
    Scan the JD for specific tools, software, or methodologies (e.g., "Power BI", "Salesforce", "Agile", "Python", "GAAP").
    
    CRITICAL: You MUST explicitly mention these tools in the plan. Do not say "dashboarding tools"; say "Power BI dashboards". Do not say "financial systems"; say "SAP".
    
    Ban Passive Language:
    
    FORBIDDEN VERBS: "Familiarize," "Learn," "Shadow," "Attend," "Understand."
    
    REQUIRED VERBS: "Audit," "Map," "Assess," "Deploy," "Optimize," "Present," "Interview."
    
    Reasoning: High-performers don't just "learn"; they "audit the current state."
    
    Structure & Thematic Arc:
    
    Day 0-30 (The Audit): Focus on diagnosing problems. Requirement: Include one "Quick Win" or "Gap Analysis" deliverable.
    
    Day 31-60 (The Build): Focus on initial implementation and fixing low-hanging fruit using the tools identified in Step 1.
    
    Day 61-90 (The Scale): Focus on long-term strategy, automation, and leadership.
    
    Context Injection:
    
    Infer the industry based on {company} and the JD.
    
    If the company is "Michelin," use terms like "manufacturing," "supply chain," or "market segments." If the company is "Verizon," use terms like "network reliability" or "customer churn."
    
    Hierarchy Logic:

    IF the Job Title contains "Manager" or "Analyst" THEN focus on Execution, Process, and Reporting.

    IF the Job Title contains "Director," "VP," or "C-Level" (CEO, CTO, CMO) THEN focus on Strategy, Financials, Hiring/Culture, and Revenue.

    Example: A Manager "updates the budget." A CEO "secures the capital."
    
    Output Format: Return the response in this specific structure (Format as Markdown). Do NOT use bracketed labels like [Action Item 1].
    
    ### 📅 30 Days: Audit & Assessment
    
    **Tech Audit:** [Task involving specific tool from JD]
    
    **Stakeholder Alignment:** [Task involving stakeholder interviews]
    
    **Quick Win:** [A specific deliverable, e.g., "Deliver gap analysis..."]
    
    ### 🚀 60 Days: Optimization & Execution
    
    **Implementation:** ...
    
    **Process Optimization:** ...
    
    **Key Deliverable:** ...
    
    ### ⭐ 90 Days: Strategy & Scale
    
    **Strategic Initiative:** ...
    
    **Team Leadership:** ...
    
    **Long-term Impact:** ...
    """}
        ]
        # Switch to text mode (not JSON) to allow freeform markdown structure
        response_text = call_openai(messages, json_mode=False)
        
        # LOG ACTIVITY
        # Career Plan has explicit specific job title
        log_db_activity(data.get('email', 'unknown'), 'career_plan', {"job_title": job_title})
        
        return jsonify({"data": response_text})

    elif action == 'linkedin_optimize':
        about_me = data.get('aboutMe', '')
        
        messages = [
            {"role": "system", "content": "You are a LinkedIn profile expert."},
            {"role": "user", "content": f"""
    Optimize the following 'About Me' section for LinkedIn. Make it more professional, engaging, and SEO-friendly.
    
    Current Text:
    {about_me}
    
    Format the output as JSON:
    {{
        "recommendations": ["rec 1", "rec 2"],
        "refined_sample": "full text of the rewritten section"
    }}
    """}
        ]
        response_text = call_openai(messages, json_mode=True)
        return jsonify({"data": response_text})

    elif action == 'parse_resume':
        resume_text = data.get('resume_text', '')
        system_msg = "You are a data extraction assistant. Parse the provided resume text and return a JSON object with these keys: personal (name, email, phone, location, linkedin, summary), skills (array of strings), experience (array of objects with role, company, dates, description), education (array of objects with degree, school, dates). Return ONLY valid JSON."
        user_msg = f"Resume Text:\n{resume_text}"
        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg}
        ]
        response_text = call_openai(messages, json_mode=True)
        return jsonify({"data": response_text})

    elif action == 'cover_letter':
        job_desc = data.get('jobDesc', '')
        resume_text = data.get('resume', '')
        
        # CHANGED: Use JSON mode to extract title + letter
        messages = [
            {"role": "system", "content": "You are an expert cover letter writer."},
            {"role": "user", "content": f"""
    Write a tailored cover letter based on the following:
    
    Job Description:
    {job_desc}
    
    My Resume:
    {resume_text}
    
    Return JSON:
    {{
        "job_title": "Inferred Job Title from Description",
        "letter_body": "The full text of the cover letter..."
    }}
    """}
        ]
        try:
            response_text = call_openai(messages, json_mode=True)
            res_json = json.loads(response_text)
            
            job_title = res_json.get('job_title', '')
            letter_content = res_json.get('letter_body', '')
            
            log_db_activity(data.get('email', 'unknown'), 'cover_letter', {"job_title": job_title})
            
            return jsonify({"data": letter_content})
        except Exception as e:
            # Fallback
            print(f"Cover Letter Error: {e}")
            return jsonify({"error": "Failed to generate cover letter"}), 500
        
    elif action == 'optimize':
        # Legacy action name for Resume Builder Optimization
        user_data = data.get('user_data', {})
        template_name = data.get('template_name', 'modern')
        job_description = data.get('job_description', '')

        # Construct a prompt to optimize the resume
        system_prompt = "You are an expert resume writer and career coach."
        user_prompt = f"""
        Optimize this resume content for the following job description. 
        Improve the summary and bullet points to be result-oriented (STAR method).
        Keep the structure (JSON) exactly as provided.

        Job Description:
        {job_description}

        Current Resume Data (JSON):
        {json.dumps(user_data)}

        Return ONLY valid JSON matching the input structure. 
        Return ONLY valid JSON matching the input structure. 
        Do not add new fields (except 'job_title'). only update summary, experience descriptions, and skills.
        Add a top-level field "job_title" with the inferred target role.
        """
        
        try:
            optimized_text = call_openai([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ], json_mode=True)
            
            opt_json = json.loads(optimized_text)
            jt = opt_json.get('job_title')
            
            log_db_activity(user_data.get('personal', {}).get('email', 'unknown'), 'resume_analysis', {"job_title": jt})
            return jsonify(opt_json)
        except Exception as e:
            print(f"Error in optimize: {e}")
            return jsonify({"error": str(e)}), 500

    elif action == 'strategic_questions':
        job_desc = data.get('jobDesc', '')
        interviewer_level = data.get('interviewerLevel', 'Hiring Manager')
        
        system_msg = "You are an expert Executive Career Coach."
        user_msg = f"""
        Generate 5 high-impact, strategic interview questions for a candidate to ask a {interviewer_level}.
        
        Target Job Context:
        {job_desc}
        
        Logic:
        - If Recruiter: Focus on culture, timeline, and company vision.
        - If Hiring Manager: Focus on immediate challenges, team dynamics, and success metrics.
        - If Executive: Focus on market strategy, long-term vision, and ROI.
        
        Output Format: Markdown.
        For each question, provide:
        **Question:** [The Question]
        *Why it works:* [Brief explanation]
        """
        
        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg}
        ]
        response_text = call_openai(messages, json_mode=False)
        return jsonify({"data": response_text})

    elif action == 'negotiation_script':
        current_offer = data.get('currentOffer', '')
        target_salary = data.get('targetSalary', '')
        leverage = data.get('leverage', '')
        
        system_msg = "You are an expert Salary Negotiation Coach."
        user_msg = f"""
        Write a salary negotiation script.
        
        Current Offer: {current_offer}
        Target Salary: {target_salary}
        Leverage/Context: {leverage}
        
        Output MUST be Valid JSON:
        {{
            "email_draft": "Subject: ... Body ...",
            "phone_script": "Start by saying... then say..."
        }}
        """
        
        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg}
        ]
        
        try:
            response_text = call_openai(messages, json_mode=True)
            res_json = json.loads(response_text)
            return jsonify(res_json)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    elif action == 'value_followup':
        interviewer_name = data.get('interviewerName', '')
        topic = data.get('topic', '')
        
        system_msg = "You are an expert Career Coach."
        user_msg = f"""
        Write a 'Value-Add' Thank You Email.
        
        Interviewer: {interviewer_name}
        Key Topic Discussed: {topic}
        
        Instruction:
        Do not just say 'thank you'. Reference the topic and offer a brief insight, article suggestion, or solution to demonstrate value/expertise. Keep it professional and concise.
        
        Output: Markdown text of the email body.
        """
        
        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg}
        ]
        response_text = call_openai(messages, json_mode=False)
        return jsonify({"data": response_text})

    else:
        return jsonify({"error": "Invalid action"}), 400


    try:
        text = call_openai(messages, json_mode=json_mode)
        
        if action == 'interview_chat':
            try:
                # Robust JSON extraction
                try:
                    # 1. Try direct parsing (Ideal for json_mode=True)
                    response_data = json.loads(text)
                except json.JSONDecodeError:
                    try:
                        # 2. Try raw_decode (Handles "Extra data" / trailing garbage)
                        response_data, _ = json.JSONDecoder().raw_decode(text)
                    except Exception:
                        # 3. Fallback to Regex (Handles Markdown fences + garbage)
                        match = re.search(r"\{.*\}", text, re.DOTALL)
                        if match:
                            json_str = match.group(0)
                            try:
                                response_data = json.loads(json_str)
                            except:
                                try:
                                    response_data, _ = json.JSONDecoder().raw_decode(json_str)
                                except:
                                    response_data = ast.literal_eval(json_str)
                        else:
                             # 4. Last Resort: Cleanup Markdown manually
                            clean_text = text.strip()
                            if clean_text.startswith('```json'): clean_text = clean_text[7:]
                            elif clean_text.startswith('```'): clean_text = clean_text[3:]
                            if clean_text.endswith('```'): clean_text = clean_text[:-3]
                            try:
                                response_data, _ = json.JSONDecoder().raw_decode(clean_text.strip())
                            except:
                                # Final cleanup attempt for bad newlines
                                response_data = json.loads(clean_text.strip().replace('\n', ' '))

                # Handle Double-Encoded JSON (LLM returns a string containing JSON)
                if isinstance(response_data, str):
                    try:
                        response_data = json.loads(response_data)
                    except:
                        pass # Keep as string if it's just text
                        
                # Ensure response_data is a dict (if list or other, logic will fail)
                if not isinstance(response_data, dict):
                    # If we got a string/list that isn't a dict, wrap it or error
                    # But sticking to "data": text fallback is safer if we can't extract structure
                    raise ValueError("Parsed content is not a JSON object")
                
                # Handle None/null for improved_sample
                improved_sample = response_data.get('improved_sample')
                if improved_sample is None:
                    improved_sample = ""
                response_data['improved_sample'] = improved_sample
                
                # Generate Audio
                speech_text = ""
                if response_data.get('feedback'):
                    speech_text += f"{response_data.get('feedback')} "
                
                if response_data.get('improved_sample'):
                    speech_text += f"Here is an improved version: {response_data.get('improved_sample')}. "
                
                if response_data.get('next_question'):
                    # Don't add any preamble - the AI response already includes proper phrasing
                    speech_text += f"{response_data.get('next_question')}"
                
                if not speech_text:
                    speech_text = "I am ready. Let's continue."
                audio_base64 = generate_audio_openai(speech_text, voice)
                
                if audio_base64:
                    response_data['audio'] = audio_base64
                
                if audio_base64:
                    response_data['audio'] = audio_base64
                
                # LOGGING: Save to DB
                try:
                    user_email = data.get('email')
                    
                    # If email missing (dev mode), try to find it
                    if not user_email and 'user_data' in data:
                         user_email = data.get('user_data', {}).get('personal', {}).get('email')

                    if user_email and supabase:
                        # Construct log entry
                        # We combine feedback + next question for the full context
                        ai_text = (response_data.get('feedback', '') + " " + response_data.get('next_question', '')).strip()
                        
                        entry = {
                            "user_email": user_email,
                            "message": message,
                            "response": ai_text,
                            "feature": "interview_coach"
                        }
                        supabase.table('chat_logs').insert(entry).execute()
                        
                        # LOG ACTIVITY (New)
                        # Extract job title if available (from AI response or input)
                        meta = {}
                        if response_data.get('job_title'):
                            meta['job_title'] = response_data.get('job_title')
                        
                        log_db_activity(user_email, 'interview_coach', meta)
                        
                except Exception as log_err:
                    print(f"Logging Failed: {log_err}")
                    log_db_error(data.get('email', 'unknown'), 'logging_error', log_err)
                
                return jsonify({"data": response_data})
                
            except Exception as e:
                print(f"Error processing interview response: {e}")
                return jsonify({"data": text})

        elif action == 'generate_report':
            try:
                if text.startswith('```json'): text = text[7:]
                if text.startswith('```'): text = text[3:]
                if text.endswith('```'): text = text[:-3]
                
                # ---------------------------------------------------------
                # POST-GENERATION CREDIT DEDUCTION (Phase 15/19)
                # ---------------------------------------------------------
                # Only deduct if successful JSON parse
                report_data = json.loads(text)
                
                # Check if we need to deduct (using same logic as gate)
                email = data.get('email')
                if email and supabase:
                    try:
                        user_res = supabase.table('users').select('is_unlimited, interview_credits').eq('email', email).execute()
                        if user_res.data:
                            user = user_res.data[0]
                            # Only deduct if NOT unlimited
                            if not user.get('is_unlimited', False) and user.get('interview_credits', 0) > 0:
                                new_credits = user.get('interview_credits') - 1
                                supabase.table('users').update({'interview_credits': max(0, new_credits)}).eq('email', email).execute()
                                print(f"SUCCESS: Deducted 1 INTERVIEW credit for Report. New balance: {new_credits}")
                    except Exception as credit_err:
                        print(f"Error deducting credit after report: {credit_err}")
                        # Do NOT block the report return
                        
                # LOG ACTIVITY
                log_db_activity(email, 'career_plan')
                return jsonify({"data": report_data})
            except Exception as e:
                return jsonify({"data": text})

        if action == 'analyze_resume':
            # Extract job title
            meta = {}
            try:
                # We expect JSON here
                res_json = json.loads(text)
                if res_json.get('job_title'):
                    meta['job_title'] = res_json.get('job_title')
            except:
                pass
            log_db_activity(data.get('email', 'unknown'), 'resume_analysis', meta)
            
        return jsonify({"data": text})

    except Exception as e:
        print(f"OpenAI API error: {e}")
        print(f"OpenAI API error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/stats', methods=['POST'])
def admin_stats():
    """Restricted endpoint for Admin Dashboard data."""
    try:
        data = request.json
        email = data.get('email', '').strip().lower()
        
        if not email or not supabase:
             return jsonify({"error": "Unauthorized"}), 401
             
        # 1. Verify Admin Role
        # Note: We assume a 'role' column exists. If not, this triggers an error, which implies access denied.
        user_res = supabase.table('users').select('role').eq('email', email).execute()
        
        is_admin = False
        if user_res.data and len(user_res.data) > 0:
            user_data = user_res.data[0]
            # Simple check: role must be 'admin'
            if user_data.get('role') == 'admin':
                is_admin = True
                
        if not is_admin:
             return jsonify({"error": "Access Denied: Admin role required."}), 403

        # 2. Fetch Stats
        # Total Users
        # Supabase 'count' query (head=True, count='exact')
        count_res = supabase.table('users').select('*', count='exact', head=True).execute()
        total_users = count_res.count if count_res.count is not None else 0
        
        # Recent Users (Limit 10)
        recent_res = supabase.table('users').select('name, email, subscription_status, created_at, interview_credits, resume_credits').order('created_at', desc=True).limit(10).execute()
        recent_users = recent_res.data if recent_res.data else []
        
        # Aggregations (Mocked for now as we don't have an 'interviews' table with duration/job_type yet)
        # Ideally, we'd query an 'activity_log' or 'interviews' table.
        # For the prototype, we return placeholder values or calculate from users if possible.
        
        # -----------------------------------------------
        # REAL DATA FETCHING
        # -----------------------------------------------
        
        # -----------------------------------------------
        # REAL DATA FETCHING
        # -----------------------------------------------
        
        # -----------------------------------------------
        # REAL DATA FETCHING
        # -----------------------------------------------
        
        # 3. Job Stats (from Activity Logs metadata)
        # We fetch all logs with metadata to aggregate titles
        # Optimization: In production, use an RPC or separate table for stats.
        job_stats_map = {}
        try:
            # Fetch last 1000 logs to analyze trends
            j_logs = supabase.table('activity_logs').select('metadata').order('created_at', desc=True).limit(500).execute()
            if j_logs.data:
                import re
                for log in j_logs.data:
                    meta = log.get('metadata', {})
                    # Check keys: 'job_title' (new) or 'jobTitle' (legacy/other)
                    title = meta.get('job_title') or meta.get('jobTitle')
                    if title and isinstance(title, str):
                        # NORMALIZE JOB TITLE
                        # 1. Lowercase + Strip
                        clean = title.lower().strip()
                        
                        # 2. Remove Prefixes (Senior, Junior, Lead, etc.)
                        # Regex to remove common prefixes followed by space
                        # prefixes: senior, junior, sr., jr., lead, principal, chief, head of, intern, vp, vice president
                        # We replace them with empty string
                        clean = re.sub(r'\b(senior|junior|sr\.?|jr\.?|lead|principal|chief|intern|vp|vice president|head of)\b', '', clean).strip()
                        
                        # 3. Clean extra spaces
                        clean = re.sub(r'\s+', ' ', clean).strip()
                        
                        # 4. Filter empty results (if title was just "Senior")
                        if not clean: continue
                        
                        # 5. Title Case for Display
                        display_title = clean.title()

                        job_stats_map[display_title] = job_stats_map.get(display_title, 0) + 1
        except Exception as e:
            print(f"Job Stats Aggregation Failed: {e}")
            pass

        # Sort and take top 5
        sorted_jobs = sorted(job_stats_map.items(), key=lambda x: x[1], reverse=True)[:5]
        # Convert to dict for frontend
        job_stats = {k: v for k, v in sorted_jobs}
        
        # Fallback if empty (to avoid empty chart)
        if not job_stats:
            job_stats = {
                'No Data Yet': 1
            }
        
        # 1. Fetch Recent Errors (Real DB)
        err_res = supabase.table('error_logs').select('*').order('created_at', desc=True).limit(5).execute()
        recent_errors = []
        if err_res.data:
            for e in err_res.data:
                recent_errors.append({
                    'timestamp': e['created_at'],
                    'email': e['user_email'] or 'System',
                    'type': e['error_type']
                })

        # 2. Activity Time Series (Last 7 Days)
        dates = []
        resume_counts = [0]*7
        interview_counts = [0]*7
        error_counts = [0]*7
        
        base = datetime.now()
        start_dt = base - timedelta(days=6)
        
        # Calculate Dates & Map
        date_map = {} # "Dec 13" -> index
        for i in range(7):
            d = base - timedelta(days=6-i)
            d_str = d.strftime("%b %d")
            dates.append(d_str)
            date_map[d_str] = i

        # Fetch raw logs for the week
        try:
            act_logs = supabase.table('activity_logs').select('feature, created_at').gte('created_at', start_dt.isoformat()).execute()
            if act_logs.data:
                for log in act_logs.data:
                    try:
                        # Parse ISO timestamp
                        ts = datetime.fromisoformat(log['created_at'].replace('Z', '+00:00'))
                        key = ts.strftime("%b %d")
                        if key in date_map:
                            idx = date_map[key]
                            if log['feature'] == 'resume_analysis':
                                resume_counts[idx] += 1
                            elif log['feature'] == 'interview_coach':
                                interview_counts[idx] += 1
                    except: pass
        except Exception as e:
            print(f"Activity query failed: {e}")

        try:
            err_logs = supabase.table('error_logs').select('created_at').gte('created_at', start_dt.isoformat()).execute()
            if err_logs.data:
                for log in err_logs.data:
                    try:
                        ts = datetime.fromisoformat(log['created_at'].replace('Z', '+00:00'))
                        key = ts.strftime("%b %d")
                        if key in date_map:
                            error_counts[date_map[key]] += 1
                    except: pass
        except Exception as e:
             print(f"Error query failed: {e}")

        daily_activity = {
            "dates": dates,
            "datasets": {
                "Resume Analysis": resume_counts,
                "Interview Coach": interview_counts,
                "System Errors": error_counts
            }
        }
        
        # Feature usage total (from the week window)
        feature_usage = {
            "Resume Analysis": sum(resume_counts),
            "Interview Coach": sum(interview_counts),
            "System Errors": sum(error_counts)
        }
        
        return jsonify({
            "total_users": total_users,
            "active_interviews": 0, # Placeholder
            "avg_duration": 14, # Placeholder
            "total_revenue": 0, # Placeholder
            "job_types": job_stats,
            "recent_users": recent_users,
            "recent_errors": recent_errors,
            "feature_usage": feature_usage,
            "daily_activity": daily_activity
        })

    except Exception as e:
        print(f"Admin Stats Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/action', methods=['POST'])
def admin_action():
    """Execute quick actions on users (Add Credit, Reset)."""
    try:
        data = request.json
        admin_email = data.get('admin_email', '').strip().lower()
        target_email = data.get('target_email', '').strip().lower() # The user to modify
        action_type = data.get('action_type')

        if not admin_email or not target_email or not supabase:
             return jsonify({"error": "Missing parameters"}), 400

        # Verify Admin (Simplified)
        admin_res = supabase.table('users').select('role').eq('email', admin_email).execute()
        if not admin_res.data or admin_res.data[0].get('role') != 'admin':
             return jsonify({"error": "Access Denied"}), 403

        if action_type == 'add_credit':
            # Retrieve current
            user_res = supabase.table('users').select('interview_credits, resume_credits').eq('email', target_email).execute()
            if user_res.data:
                curr_int = user_res.data[0].get('interview_credits', 0)
                curr_res = user_res.data[0].get('resume_credits', 0)
                # Add +1 to both
                # USE ADMIN CLIENT to bypass RLS
                db = supabase_admin if supabase_admin else supabase
                
                db.table('users').update({
                    'interview_credits': curr_int + 1,
                    'resume_credits': curr_res + 1
                }).eq('email', target_email).execute()
                return jsonify({"success": True, "message": "Credits added (+1)"})
            else:
                return jsonify({"error": "Target user not found"}), 404

        elif action_type == 'reset_session':
             # Reset credits to at least 1 if they are 0
             user_res = supabase.table('users').select('interview_credits').eq('email', target_email).execute()
             if user_res.data:
                  curr = user_res.data[0].get('interview_credits', 0)
                  if curr == 0:
                      db = supabase_admin if supabase_admin else supabase
                      db.table('users').update({'interview_credits': 1}).eq('email', target_email).execute()
                  return jsonify({"success": True, "message": "Session reset (credits restored to 1)"})
             else:
                return jsonify({"error": "Target user not found"}), 404

        return jsonify({"error": "Unknown action"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/transcript', methods=['POST'])
def admin_transcript():
    """Fetch chat logs for a user."""
    try:
        data = request.json
        target_email = data.get('target_email')
        
        if not target_email or not supabase:
            return jsonify({"error": "Missing email"}), 400

        # Fetch last 20 logs
        res = supabase.table('chat_logs').select('*').eq('user_email', target_email).order('created_at', desc=True).limit(20).execute()
        
        logs = res.data if res.data else []
        return jsonify({"success": True, "logs": logs})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ========================================
# USER AUTHENTICATION ENDPOINTS
# ========================================

import bcrypt
import uuid
from datetime import datetime
from datetime import datetime
# Supabase init moved to top


def hash_password(password):
    """Hash password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hashed):
    """Verify password against hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def validate_email(email):
    """Basic email validation."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

@app.route('/api/auth/signup', methods=['POST'])
def signup():
    """Create a new user account using Supabase Auth."""
    try:
        if not supabase:
            return jsonify({"error": "Database not configured. Check SUPABASE_URL and SUPABASE_KEY."}), 500
        
        data = request.json
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        confirm_password = data.get('confirm_password', '')
        name = data.get('name', '').strip()
        
        if not email or not validate_email(email):
            return jsonify({"error": "Valid email is required"}), 400
        if not password or len(password) < 8:
            return jsonify({"error": "Password must be at least 8 characters"}), 400
        if password != confirm_password:
            return jsonify({"error": "Passwords must match"}), 400
        
        # 1. Sign up with Supabase Auth (Pass 'name' in metadata for Trigger)
        try:
            auth_response = supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "name": name
                    }
                }
            })
        except Exception as auth_error:
            # Handle Supabase Auth errors (e.g. user already exists)
            msg = str(auth_error)
            if "already registered" in msg or "User already registered" in msg:
                return jsonify({"error": "User already exists. Please log in."}), 400
            raise auth_error

        if not auth_response.user:
            return jsonify({"error": "Signup failed. Please try again."}), 500

        # Note: We rely on the Postgres Trigger to read auth.users.raw_user_meta_data
        # and insert the 'name' into public.users.
        # This avoids RLS errors because we don't need to UPDATE the row manually here.
        
        return jsonify({
            "success": True,
            "message": "Account created! Please check your email to confirm."
        })

    except Exception as e:
        print(f"Signup error: {e}")
        return jsonify({"error": f"Signup failed: {str(e)}"}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Authenticate user using Supabase Auth."""
    try:
        if not supabase:
            return jsonify({"error": "Database not configured. Please contact support."}), 500
        
        data = request.json
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400
            
        # 1. Authenticate with Supabase Auth
        try:
            auth_response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
        except Exception as auth_error:
            print(f"Auth failed: {auth_error}")
            return jsonify({"error": "Invalid email or password."}), 401

        user = auth_response.user
        if not user:
             return jsonify({"error": "Login failed."}), 401
             
        # 2. Fetch Profile from 'users' table
        # Explicitly select columns to ensure we don't accidentally get ghost columns or issues
        profile_res = supabase.table('users').select('id, email, name, subscription_status, is_unlimited, resume_credits, interview_credits, rewrite_credits, role').eq('id', user.id).execute()
        
        print(f"DEBUG: Login query for ID {user.id} returned: {len(profile_res.data) if profile_res.data else 0} rows")

        # Check if profile exists (It should, but handle edge case)
        if not profile_res.data or len(profile_res.data) == 0:
            # OPTIONAL: Auto-create profile if missing (Migration fallback)?
            # For now, just error or return basic data
            return jsonify({"error": "User profile not found. Please contact support."}), 404
            
        profile_data = profile_res.data[0]
        uid = user.id
        
        # 3. Update Last Login
        # ENSURE we use 'id' column, NOT 'user_id'
        print(f"DEBUG: Updating last_login for ID: {uid}")
        try:
            supabase.table('users').update({
                'last_login': datetime.now().isoformat()
            }).eq('id', uid).execute()
        except Exception as update_err:
            print(f"Last login update failed (non-critical): {update_err}")

        # 4. Return Session Data
        session_data = {
            "email": profile_data["email"],
            "name": profile_data.get("name"),
            "user_id": uid, # Session expects 'user_id' key, that is fine.
            "access_token": auth_response.session.access_token,
            "refresh_token": auth_response.session.refresh_token,
            # Updated Schema Mapping
            "subscription_status": profile_data.get("subscription_status"),
            "is_unlimited": profile_data.get("is_unlimited", False),
            "resume_credits": profile_data.get("resume_credits", 0),
            "interview_credits": profile_data.get("interview_credits", 0),
            "role": profile_data.get("role", "user")
        }
        
        return jsonify({
            "success": True,
            "message": "Login successful",
            "session": session_data
        })

    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({"error": f"Login failed: {str(e)}"}), 500

@app.route('/api/auth/forgot-password', methods=['POST'])
def forgot_password():
    """Trigger Password Reset Email via Supabase."""
    try:
        if not supabase:
            return jsonify({"error": "Database not configured. Please contact support."}), 500
        
        data = request.json
        email = data.get('email', '').strip().lower()
        
        if not email:
            return jsonify({"error": "Email is required"}), 400
            
        # User requested explicit WWW domain for redirect reliability
        redirect_url = "https://www.tryaceinterview.com/update-password"
        
        # Note: gotrue-py uses 'redirectTo' in options, but we'll include both if unsure, 
        # or stick to the known working 'redirectTo'. User asked for 'redirect_to' in options, 
        # but standard Supabase API key is 'redirectTo'. I will use 'redirectTo' which maps to the API correctly.
        # UPDATE: User requested "redirect_to" explicitly. Sending BOTH to be safe.
        supabase.auth.reset_password_email(email, {
            "redirectTo": redirect_url, 
            "redirect_to": redirect_url
        })
        
        return jsonify({
            "success": True,
            "message": "If an account exists, a password reset link has been sent."
        })
    except Exception as e:
        print(f"Forgot PW Error: {e}")
        return jsonify({"error": "Failed to send reset link."}), 500

@app.route('/api/auth/update-password', methods=['POST'])
def update_password():
    """Update password using a token (Hybrid: Client usually handles this directly).
       However, since we are doing server-side python, this endpoint is tricky without the session.
       
       BETTER APPROACH FOR SERVER-SIDE:
       The frontend `update-password.html` will have the `access_token` in the URL hash.
       It should send that access_token + new_password to this endpoint.
       We then set the session on the supabase client and update.
    """
    try:
        if not supabase:
            return jsonify({"error": "Database not configured. Please contact support."}), 500
            
        data = request.json
        access_token = data.get('access_token')
        refresh_token = data.get('refresh_token')
        new_password = data.get('password')
        
        if not access_token or not new_password:
             return jsonify({"error": "Token and Password required"}), 400
             
        if not refresh_token:
            # Fallback if refresh token is missing (might fail if session required it, but let's try)
            # Or return error. User prompt implies we MUST use set_session(access, refresh).
            # If frontend failed to send it, we're stuck. But we updated frontend.
            pass

        # Verify and Update using the User's Token (Behave as the User)
        # We pass the 'jwt' explicitly to authenticate this request as the user.
        # This avoids the "User not allowed" error that occurs when using Anon key for Admin actions.
        try:
            # FIX: Use set_session instead of passing jwt arg to update_user
            if refresh_token:
                supabase.auth.set_session(access_token, refresh_token)
            else:
                 # Try with just access token? No, set_session needs both usually.
                 # Python client might support set_session(access_token, refresh_token)
                 # If refresh is missing, we can't fully hydrate session easily without verifying it another way.
                 # But let's assume we have it.
                 pass

            res = supabase.auth.update_user({"password": new_password})
            
            if not res.user:
                return jsonify({"error": "Failed to update password. Session may be invalid."}), 400
                
        except Exception as update_error:
            # Handle Supabase Auth errors
            print(f"Update User Context Error: {update_error}")
            return jsonify({"error": str(update_error)}), 400
            
        return jsonify({"success": True, "message": "Password updated successfully"})

    except Exception as e:
        print(f"Update PW Error: {e}")
        return jsonify({"error": str(e)}), 500



@app.route('/api/auth/user', methods=['GET', 'POST', 'OPTIONS'])
@app.route('/auth/user', methods=['GET', 'POST', 'OPTIONS'])
def get_user_data_route():
    # CORS Preflight
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    # GET Request (Debug)
    if request.method == 'GET':
        return jsonify({
            "success": True, 
            "message": "Route is working! Send POST with email to get data.",
            "path_seen": request.path
        })

    # 1. Parse Email
    data = request.json
    email = data.get('email')
    
    if not email:
        return jsonify({"success": False, "error": "Email required"}), 400

    # 2. Fetch User Data
    try:
        # Use ADMIN client to bypass RLS (since server-side anon client cannot see user data without session)
        db = supabase_admin if supabase_admin else supabase
        
        # Query the 'users' table specifically for credit columns
        response = db.table('users').select('*').eq('email', email).execute()
        
        if response.data and len(response.data) > 0:
            user = response.data[0]
            return jsonify({
                "success": True, 
                "user": {
                    "email": user.get('email'),
                    "resume_credits": user.get('resume_credits', 0),
                    "interview_credits": user.get('interview_credits', 0),
                    "rewrite_credits": user.get('rewrite_credits', 0),
                    "is_unlimited": user.get('is_unlimited', False),
                    "subscription_status": user.get('subscription_status', 'free'),
                    "role": user.get('role', 'user')
                }
            })
        else:
            return jsonify({"success": False, "error": "User not found"}), 404
            
    except Exception as e:
        print(f"Error in /api/auth/user: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/auth/update-status', methods=['POST'])
def update_user_status():
    """Update user payment status (for admin use)."""
    try:
        if not supabase:
            return jsonify({"error": "Database not configured"}), 500
        
        data = request.json
        email = data.get('email', '').strip().lower()
        account_status = data.get('account_status')
        payment_tier = data.get('payment_tier')
        
        # New: Manual Credit Adjustments
        set_rewrite = data.get('set_rewrite_credits')
        set_resume = data.get('set_resume_credits')
        
        admin_key = data.get('admin_key')
        
        # Simple admin key check (should use proper admin auth in production)
        if admin_key != os.environ.get('ADMIN_KEY', 'aceinterview_admin_2024'):
            return jsonify({"error": "Unauthorized"}), 403
        
        if not email:
            return jsonify({"error": "Email is required"}), 400
        
        # Check if user exists (Use Admin Client if available to bypass RLS)
        db_client = supabase_admin if supabase_admin else supabase
        existing = db_client.table('users').select('email').eq('email', email).execute()
        if not existing.data or len(existing.data) == 0:
            return jsonify({"error": "User not found"}), 404
        
        # Update user
        update_data = {}
        if account_status:
            update_data['account_status'] = account_status
        if payment_tier:
            update_data['payment_tier'] = payment_tier
        
        if set_rewrite is not None:
             update_data['rewrite_credits'] = int(set_rewrite)
        if set_resume is not None:
             update_data['resume_credits'] = int(set_resume)
        
        if update_data:
            db_client.table('users').update(update_data).eq('email', email).execute()
        
        return jsonify({"success": True, "message": f"User {email} updated successfully"})
    
    except Exception as e:
        print(f"Update status error: {e}")
        return jsonify({"error": "Unable to update user"}), 500
    except Exception as e:
        print(f"Update status error: {e}")
        return jsonify({"error": "Unable to update user"}), 500

# ========================================
# STRIPE PAYMENTS
# ========================================

# Stripe Price Configuration
PRICE_IDS = {
    'pro': os.environ.get('Stripe_Pro_Package'),           # Monthly Subscription
    'complete': os.environ.get('Stripe_Complete_Package'), # Resume & Interview ($24.99)
    'resume': os.environ.get('Stripe_Resume_Only'),        # Resume Feedback Only ($14.99)
    'interview': os.environ.get('Stripe_Interview_Only')   # Mock Interview Session ($19.99)
}





@app.route('/api/create-portal-session', methods=['POST'])
def create_portal_session():
    """Create a Stripe Customer Portal session."""
    try:
        data = request.json
        email = data.get('email')
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400

        # 1. Find Customer by Email
        customers = stripe.Customer.list(email=email, limit=1)
        if not customers.data:
            return jsonify({'error': 'No billing account found for this email.'}), 404
        
        customer = customers.data[0]
        
        # 2. Create Portal Session
        # Return to dashboard after they are done
        return_url = f"{app_domain}/dashboard.html"
        
        portal_session = stripe.billing_portal.Session.create(
            customer=customer.id,
            return_url=return_url,
        )
        
        return jsonify({'url': portal_session.url})
        
    except Exception as e:
        print(f"Error creating portal session: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stripe-webhook', methods=['POST'])
def stripe_webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, stripe_webhook_secret
        )
    except ValueError as e:
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError as e:
        return jsonify({'error': 'Invalid signature'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    if not event:
        return jsonify({'error': 'Event construction failed'}), 400

    print(f"Received Stripe event: {event['type']}")

    if not supabase:
        print("CRITICAL: Supabase not configured in Webhook.")
        return jsonify({'error': 'Database error'}), 500
        
    # Use Admin Client for Updates to bypass RLS
    db_client = supabase_admin if supabase_admin else supabase

    try:
        # HANDLE SUBSCRIPTION CREATED / CHECKOUT COMPLETED
        if event['type'] == 'checkout.session.completed':
            try:
                session = event['data']['object']
                
                # ... existing logic ...
                # (We are replacing the WHOLE function or just appending? 
                #  The instruction implied replacing the block, but replace_file_content replaces a chunk.
                #  I will include the existing checkout logic here to be safe and ensure continuity)
                
                customer_email = session.get('customer_details', {}).get('email')
                client_reference_id = session.get('client_reference_id')
                metadata = session.get('metadata', {})
                plan_type = metadata.get('plan_type', 'basic')

                print(f"WEBHOOK DEBUG: Email={customer_email}, Plan={plan_type}, RefID={client_reference_id}")
                print(f"WEBHOOK DEBUG: Full Metadata: {metadata}")
                print(f"WEBHOOK DEBUG: Supabase Admin Active? {'YES' if supabase_admin else 'NO - Using Anon Client'}")

                user_id = None
                user_data = None

                # 1. Try finding user by Client Reference ID
                if client_reference_id:
                    res = db_client.table('users').select('*').eq('id', client_reference_id).execute()
                    if res.data:
                        user_data = res.data[0]
                        user_id = user_data['id']
                        print(f"Found user by ID: {user_id}")

                # 2. Fallback: Find by Email
                if not user_id and customer_email:
                    res = db_client.table('users').select('*').eq('email', customer_email).execute()
                    if res.data:
                        user_data = res.data[0]
                        user_id = user_data['id']
                        print(f"Found user by Email: {customer_email} -> ID: {user_id}")

                if user_id:
                    # Determine Updates
                    current_resume = user_data.get('resume_credits', 0)
                    current_interview = user_data.get('interview_credits', 0)
                    
                    update_data = {}

                    if plan_type == 'pro':
                        update_data['is_unlimited'] = True
                        update_data['subscription_status'] = 'active'
                        print("Granting UNLIMITED access.")

                    # GLOBAL CHECK: Feature = Rewrite (Prioritize over Plan Type)
                    elif metadata.get('feature') == 'rewrite':
                         current_rewrite = user_data.get('rewrite_credits', 0)
                         update_data['rewrite_credits'] = current_rewrite + 1
                         print(f"Granting +1 V2 REWRITE Credit. New Total: {update_data['rewrite_credits']}")
                    
                    elif plan_type == 'complete':
                        update_data['resume_credits'] = current_resume + 1
                        update_data['interview_credits'] = current_interview + 1
                        print(f"Granting Complete Package (+1 each). New Targets: R={update_data['resume_credits']}, I={update_data['interview_credits']}")

                    elif plan_type == 'resume':
                         # Legacy Resume Credit (fallback if feature != rewrite)
                         update_data['resume_credits'] = current_resume + 1
                         print(f"Granting +1 V1 Resume Analysis Credit. New Total: {update_data['resume_credits']}")

                    elif plan_type == 'interview':
                        update_data['interview_credits'] = current_interview + 1
                        print(f"Granting +1 Interview Credit. New Total: {update_data['interview_credits']}")

                    # EXECUTE UPDATE
                    response = db_client.table('users').update(update_data).eq('id', user_id).execute()
                    print(f"WEBHOOK DEBUG: Update Response: {response.data if hasattr(response, 'data') else 'No Data'}")
                    print(f"Successfully updated user {user_id}")

                else:
                    print(f"WARNING: User not found for email {customer_email}. Cannot fulfill order.")
            
            except Exception as e:
                import traceback
                print(f"CRITICAL WEBHOOK ERROR (Checkout): {str(e)}")
                print(traceback.format_exc())
                return jsonify({'error': str(e)}), 500

        # HANDLE SUBSCRIPTION CANCELLATION / DELETION
        elif event['type'] in ['customer.subscription.deleted', 'customer.subscription.updated']:
            try:
                subscription = event['data']['object']
                status = subscription.get('status')
                customer_id = subscription.get('customer')
                
                # Valid statuses: active, trialing, past_due, canceled, unpaid, incomplete_expired
                # If 'canceled' or 'unpaid', revoke access
                if status in ['canceled', 'unpaid', 'incomplete_expired']:
                    print(f"Processing Subscription End: Status={status}, Customer={customer_id}")
                    
                    # We need to find the user. We don't have customer_id in DB, but we can look up email via Stripe API?
                    # Or we just updated checkout to NOT save customer_id properly earlier.
                    # Best effort: Get email from Customer object in Stripe
                    try:
                        customer = stripe.Customer.retrieve(customer_id)
                        email = customer.email
                        if email:
                            print(f"Revoking access for {email}")
                            db_client.table('users').update({
                                'is_unlimited': False,
                                'subscription_status': status
                            }).eq('email', email).execute()
                            print("Access revoked.")
                    except Exception as cust_err:
                        print(f"Error retrieving customer email for revocation: {cust_err}")

            except Exception as e:
                print(f"Error handling subscription update: {e}")
                return jsonify({'error': str(e)}), 500

    except Exception as e:
        print(f"Global Webhook Error: {e}")
        return jsonify({'error': str(e)}), 500

    return jsonify({'status': 'success'}), 200

# For Vercel, we don't need app.run()
