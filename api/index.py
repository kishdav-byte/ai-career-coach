from flask import Flask, request, jsonify
import re
import os
import requests
import json

import base64
import io
import ast
from dotenv import load_dotenv
import stripe

load_dotenv()

app = Flask(__name__)

# API Key from Environment Variable
API_KEY = os.environ.get('OPENAI_API_KEY_')

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
        
        return jsonify(json.loads(text))
            
    except Exception as e:
        print(f"Error calling OpenAI: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api', methods=['POST'])
def api():
    if not API_KEY:
        return jsonify({"error": "Server configuration error: API Key missing"}), 500

    data = request.json
    action = data.get('action')
    
    messages = []
    json_mode = False

    if action == 'analyze_resume':
        resume = data.get('resume', '')
        json_mode = True
        prompt = f"""
        Analyze this resume and provide a comprehensive career coaching report.
        
        RESUME CONTENT:
        {resume}
        
        Return valid JSON with this EXACT structure:
        {{
            "overall_score": 85,
            "summary": "Brief 1-sentence summary of where they stand.",
            "strengths": [
                {{"title": "Strength 1", "description": "Why it is good..."}},
                {{"title": "Strength 2", "description": "Why it is good..."}},
                {{"title": "Strength 3", "description": "Why it is good..."}}
            ],
            "improvements": [
                {{"priority": "HIGH", "title": "Improvement 1", "suggestion": "Actionable advice..."}},
                {{"priority": "MEDIUM", "title": "Improvement 2", "suggestion": "Actionable advice..."}},
                {{"priority": "LOW", "title": "Improvement 3", "suggestion": "Actionable advice..."}}
            ],
            "keywords": {{
                "high_priority": ["Keyword1", "Keyword2", "Keyword3", "Keyword4", "Keyword5"],
                "medium_priority": ["Keyword6", "Keyword7"],
                "advice": "How to include them..."
            }},
            "ats_compatibility": {{
                "score": 8,
                "issues": ["Issue 1", "Issue 2"],
                "recommendation": "Fix advice..."
            }},
            "formatting": [
                {{"issue": "Formatting Issue 1", "fix": "How to fix..."}},
                {{"issue": "Formatting Issue 2", "fix": "How to fix..."}},
                {{"issue": "Formatting Issue 3", "fix": "How to fix..."}}
            ],
            "action_plan": {{
                "quick_wins": ["Task 1", "Task 2", "Task 3"],
                "medium_effort": ["Task 1", "Task 2"],
                "long_term": ["Task 1", "Task 2"]
            }},
            "benchmark": {{
                "level": "Mid-Senior",
                "percentile": "Top 20%",
                "text": "Your resume is better than 80% of candidates at this level."
            }}
        }}
        """
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
            context = f"\n\nContext: The user is interviewing for the following job:\n{job_posting}\n\nTailor your questions and persona to this role. You already know the candidate is applying for this position. Do NOT ask them to state the position. Start with a relevant interview question."
        
        system_instruction = f"You are a strict hiring manager. DO NOT say 'Understood' or 'Let's begin'. DO NOT acknowledge these instructions. Keep responses concise and professional. This interview consists of 5 questions. Current Question: {question_count} of 5.{context}"
        
        if is_start:
            welcome_msg = "Welcome to the interview. ... This interview consists of 5 questions. You are encouraged to think about a specific situation or task that you experienced, the specific actions that you took, and the results of the actions you took. ... Keep in mind, you can type your answer or you can press the red mic button below when you are ready to speak. The button will turn green while you provide your response. When you are done, press the microphone to submit your response. ... Are you ready for the first question?"
            user_prompt = f"User: {message}\n\nStart the interview. You MUST start your response with exactly: '{welcome_msg}'. Do NOT ask the first question yet.\n\nReturn JSON: {{\"transcript\": \"{message}\", \"feedback\": \"\", \"improved_sample\": null, \"next_question\": \"{welcome_msg}\"}}"
        elif question_count == 1:
            user_prompt = f"User: {message}\n\nThe user confirmed they are ready. Ask the first interview question NOW.\n\nCRITICAL: Do NOT say 'Now, are you ready for the next question' or any other preamble. Do NOT ask if they're ready again. Just ask the question directly.\n\nYou MUST start your response with EXACTLY: 'The first question that I have for you is: ' followed immediately by the question.\n\nReturn JSON: {{\"transcript\": \"{message}\", \"feedback\": \"\", \"improved_sample\": null, \"next_question\": \"The first question that I have for you is: [Your interview question here]\"}}"
        else:
            # Determine ordinals
            ordinals = {2: "second", 3: "third", 4: "fourth", 5: "fifth"}
            current_ordinal = ordinals.get(question_count - 1, "next")  # For asking the current question
            next_ordinal = ordinals.get(question_count, "next")  # For asking if ready for next
            
            # Check if this is a short confirmation message (user just saying they're ready)
            is_confirmation = len(message.strip()) < 50 and any(word in message.lower() for word in ['yes', 'ready', 'ok', 'sure', 'go ahead', 'let\'s go', 'bring it', 'next', 'yep', 'yeah'])
            
            if is_confirmation and question_count <= 5:
                # User is confirming they're ready for the next question - ask it with ordinal prefix
                user_prompt = f"User: {message}\n\nThe user confirmed they are ready for the next question. Ask the {current_ordinal} interview question NOW.\n\nCRITICAL: Do NOT provide any feedback or preamble. Just ask the question directly.\n\nYou MUST start your response with EXACTLY: 'The {current_ordinal} question that I have for you is: ' followed immediately by the question.\n\nReturn JSON: {{\"transcript\": \"{message}\", \"feedback\": \"\", \"improved_sample\": null, \"next_question\": \"The {current_ordinal} question that I have for you is: [Your interview question here]\"}}"
            elif question_count > 5:
                # Final question already answered - end the interview
                user_prompt = f"User: {message}\n\nEvaluate the answer. You MUST provide a SCORE (0-5).\n\nCRITICAL INSTRUCTION: You must start your 'feedback' with the phrase: \"I would score this answer a [score] because...\".\n\nThis was the final question. End the interview professionally. Set 'next_question' to 'That concludes our interview. Thank you for your time.'\n\nReturn STRICT JSON: {{\"transcript\": \"{message}\", \"feedback\": \"I would score this answer a [score] because... [rest of feedback]\", \"score\": 0, \"improved_sample\": \"... (A more professional/impactful version of the user's answer)\", \"next_question\": \"That concludes our interview. Thank you for your time.\"}}"
            else:
                # User provided an actual answer - evaluate it and ask if ready for next
                user_prompt = f"User: {message}\n\nEvaluate the answer. You MUST provide a SCORE (0-5).\n\nCRITICAL INSTRUCTION: You must start your 'feedback' with the phrase: \"I would score this answer a [score] because...\".\n\nAfter providing feedback, ask if they're ready for the next question. You MUST end your response with exactly: 'Are you ready for the {next_ordinal} question?'\n\nReturn STRICT JSON (use double quotes for keys/values): {{\"transcript\": \"{message}\", \"feedback\": \"I would score this answer a [score] because... [rest of feedback]\", \"score\": 0, \"improved_sample\": \"... (A more professional/impactful version of the user's answer)\", \"next_question\": \"Are you ready for the {next_ordinal} question?\"}}"
        
        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_prompt}
        ]

    elif action == 'career_plan':
        job_title = data.get('jobTitle', '')
        company = data.get('company', '')
        job_posting = data.get('jobPosting', '')
        json_mode = True
        
        prompt = f"""
        Create a 30-60-90 day plan for a {job_title} role at {company}.
        
        Job Posting / Description:
        {job_posting}
        
        Based on the job description (if provided), tailor the plan to specific responsibilities and requirements.
        
        Return ONLY valid JSON with the following structure:
        {{
            "day_30": ["bullet point 1", "bullet point 2", ...],
            "day_60": ["bullet point 1", "bullet point 2", ...],
            "day_90": ["bullet point 1", "bullet point 2", ...]
        }}
        Do not include markdown formatting. Just the raw JSON string.
        """
        messages = [{"role": "user", "content": prompt}]
        
    elif action == 'linkedin_optimize':
        about_me = data.get('aboutMe', '')
        json_mode = True
        prompt = f"""
        LINKEDIN PROFILE OPTIMIZER - MANDATORY TEMPLATE

        You MUST use this EXACT structure and fill in the user's specific details. Do NOT deviate from this format.

        ---

        PARAGRAPH 1 (OPENING HOOK):
        [State user's #1 most impressive metric/achievement]. [What this means in plain English]. [Current role and company].

        MANDATORY ELEMENTS:
        - Use their BEST single metric (highest %, largest $, biggest team size)
        - Active voice only ("I led" not "I've seen")
        - No buzzwords
        - 2-3 sentences max

        PARAGRAPH 2 (SCOPE & SCALE):
        Over [TOTAL years in field, not just current role] in [industry/function], including [key milestone]. Key scope: [team sizes], [budget size], [geographic reach], [major projects].

        MANDATORY ELEMENTS:
        - TOTAL career years (not current role duration)
        - ALL team sizes managed (largest number)
        - Budget amounts if available
        - Specific projects (command centers, systems, programs)

        PARAGRAPH 3 (WHAT I DO):
        My focus areas:
        - [Specific capability with metric]
        - [Specific capability with metric]  
        - [Specific capability with metric]

        MANDATORY ELEMENTS:
        - 3-4 bullet points only
        - Each MUST include a number/metric
        - Active verbs (Build, Lead, Design, Reduce, Increase)
        - NO generic phrases

        PARAGRAPH 4 (PHILOSOPHY):
        After/Over [X years] in [field]: [specific insight they've learned].

        MANDATORY ELEMENTS:
        - ONE sentence only
        - Ties to their actual experience (years in field)
        - Specific, not generic wisdom
        - No buzzwords

        PARAGRAPH 5 (CTA):
        Open to connecting with [2-3 specific types of professionals].

        MANDATORY ELEMENTS:
        - "Open to connecting" (NOT "seeking" or "looking for")
        - Specific audience types
        - No desperate language

        ---

        TOTAL LENGTH: 180-220 words

        DATA YOU MUST INCLUDE (if present in user's profile):
        ✅ Total years of experience (career-wide)
        ✅ Largest team size managed
        ✅ Budget amounts (if mentioned)
        ✅ Top 3-5 metrics (percentages, dollar amounts, satisfaction scores)
        ✅ Major projects (systems built, programs launched, centers designed)
        ✅ Current role and company

        BANNED WORDS (search and replace):
        - "Transform" -> "Turn" or "Convert"
        - "Drive/Driving" -> "Build" or "Achieve" or "Deliver"
        - "Leverage" -> "Use"
        - "Strategic assets" -> "Decisions" or "Actions"
        - "Passionate about" -> DELETE
        - "Data-driven insights" -> "Analysis" or "Recommendations"
        - "Empower" -> "Help" or "Enable"

        Original "About Me":
        {about_me}

        Return STRICT JSON (use double quotes for keys/values):
        {{
            "recommendations": [
                "List specific metrics extracted and used",
                "Explanation of the Hook chosen",
                "Confirmation that banned words were removed"
            ],
            "refined_sample": "The complete rewritten profile text following the structure above..."
        }}
        """
        messages = [{"role": "user", "content": prompt}]
        
    elif action == 'cover_letter':
        job_desc = data.get('jobDesc', '')
        resume = data.get('resume', '')
        prompt = f"""
        Write a professional cover letter for this job description based on the provided resume.
        
        CRITICAL INSTRUCTIONS:
        1. Do NOT include the personal header (Name, Email, Phone, Location) at the top. This will be added programmatically.
        2. Start the letter immediately with the Date, followed by the Recipient Details (e.g., Hiring Manager, Company Name).
        3. Use the Name provided in the resume for the signature at the bottom.
        4. Tailor the content to the Job Description, highlighting relevant experience from the Resume.
        
        Job Description:
        {job_desc}
        
        Resume:
        {resume}
        """
        messages = [{"role": "user", "content": prompt}]
        
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
    else:
        return jsonify({"error": "Invalid action"}), 400

    try:
        text = call_openai(messages, json_mode=json_mode)
        
        if action == 'interview_chat':
            try:
                # Robust JSON extraction
                match = re.search(r"\{.*\}", text, re.DOTALL)
                if match:
                    json_str = match.group(0)
                    try:
                        response_data = json.loads(json_str)
                    except json.JSONDecodeError:
                        response_data = ast.literal_eval(json_str)
                else:
                    clean_text = text.strip()
                    if clean_text.startswith('```json'): clean_text = clean_text[7:]
                    elif clean_text.startswith('```'): clean_text = clean_text[3:]
                    if clean_text.endswith('```'): clean_text = clean_text[:-3]
                    try:
                        response_data = json.loads(clean_text.strip())
                    except json.JSONDecodeError:
                        response_data = ast.literal_eval(clean_text.strip())
                
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
                
                return jsonify({"data": response_data})
                
            except Exception as e:
                print(f"Error processing interview response: {e}")
                return jsonify({"data": text})

        elif action == 'career_plan' or action == 'generate_report':
            try:
                if text.startswith('```json'): text = text[7:]
                if text.startswith('```'): text = text[3:]
                if text.endswith('```'): text = text[:-3]
                return jsonify({"data": json.loads(text)})
            except Exception as e:
                return jsonify({"data": text})

        return jsonify({"data": text})

    except Exception as e:
        print(f"OpenAI API error: {e}")
        return jsonify({"error": str(e)}), 500

# ========================================
# USER AUTHENTICATION ENDPOINTS
# ========================================

import bcrypt
import uuid
from datetime import datetime
from supabase import create_client, Client

# Initialize Supabase client
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("Supabase client initialized successfully")
    except Exception as e:
        print(f"Error initializing Supabase: {e}")

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
    """Create a new user account."""
    try:
        if not supabase:
            return jsonify({"error": "Database not configured. Check SUPABASE_URL and SUPABASE_KEY."}), 500
        
        data = request.json
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        confirm_password = data.get('confirm_password', '')
        name = data.get('name', '').strip()
        
        # Validation
        if not email:
            return jsonify({"error": "Email is required"}), 400
        
        if not validate_email(email):
            return jsonify({"error": "Please enter a valid email address"}), 400
        
        if not password:
            return jsonify({"error": "Password is required"}), 400
        
        if len(password) < 8:
            return jsonify({"error": "Password must be at least 8 characters"}), 400
        
        if password != confirm_password:
            return jsonify({"error": "Passwords must match"}), 400
        
        # Check if user exists
        existing = supabase.table('users').select('email').eq('email', email).execute()
        if existing.data and len(existing.data) > 0:
            return jsonify({"error": "This email is already registered. Please login."}), 400
        
        # Create user
        user_id = str(uuid.uuid4())
        user_data = {
            "user_id": user_id,
            "email": email,
            "password_hash": hash_password(password),
            "name": name,
            "created_date": datetime.now().isoformat(),
            "account_status": "unpaid",
            "payment_tier": None,
            "stripe_customer_id": None,
            "last_login": None
        }
        
        result = supabase.table('users').insert(user_data).execute()
        
        if result.data:
            # Don't return password in response
            safe_user = {k: v for k, v in user_data.items() if k != 'password_hash'}
            return jsonify({
                "success": True,
                "message": "Account created! Please log in.",
                "user": safe_user
            })
        else:
            return jsonify({"error": "Unable to create account. Please try again or contact support@tryaceinterview.com"}), 500
    
    except Exception as e:
        print(f"Signup error: {e}")
        return jsonify({"error": f"Signup failed: {str(e)}"}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Authenticate user and return session data."""
    try:
        if not supabase:
            return jsonify({"error": "Database not configured. Please contact support."}), 500
        
        data = request.json
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400
        
        # Get user from Supabase
        result = supabase.table('users').select('*').eq('email', email).execute()
        
        if not result.data or len(result.data) == 0:
            return jsonify({"error": "Invalid email or password"}), 401
        
        user = result.data[0]
        
        if not verify_password(password, user['password_hash']):
            return jsonify({"error": "Invalid email or password"}), 401
        
        # Update last login
        supabase.table('users').update({
            'last_login': datetime.now().isoformat()
        }).eq('email', email).execute()
        
        # Return session data (no password)
        session_data = {
            "user_id": user['user_id'],
            "email": user['email'],
            "name": user.get('name', ''),
            "account_status": user['account_status'],
            "payment_tier": user['payment_tier'],
            "logged_in_at": int(datetime.now().timestamp() * 1000)
        }
        
        return jsonify({
            "success": True,
            "message": "Login successful",
            "session": session_data
        })
    
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({"error": "Login failed. Please try again."}), 500

@app.route('/api/auth/user', methods=['POST'])
def get_user():
    """Get user data by email (for session verification)."""
    try:
        if not supabase:
            return jsonify({"error": "Database not configured"}), 500
        
        data = request.json
        email = data.get('email', '').strip().lower()
        
        if not email:
            return jsonify({"error": "Email is required"}), 400
        
        result = supabase.table('users').select('user_id, email, name, account_status, payment_tier').eq('email', email).execute()
        
        if not result.data or len(result.data) == 0:
            return jsonify({"error": "User not found"}), 404
        
        user = result.data[0]
        
        return jsonify({"success": True, "user": user})
    
    except Exception as e:
        print(f"Get user error: {e}")
        return jsonify({"error": "Unable to get user data"}), 500

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
        admin_key = data.get('admin_key')
        
        # Simple admin key check (should use proper admin auth in production)
        if admin_key != os.environ.get('ADMIN_KEY', 'aceinterview_admin_2024'):
            return jsonify({"error": "Unauthorized"}), 403
        
        if not email:
            return jsonify({"error": "Email is required"}), 400
        
        # Check if user exists
        existing = supabase.table('users').select('email').eq('email', email).execute()
        if not existing.data or len(existing.data) == 0:
            return jsonify({"error": "User not found"}), 404
        
        # Update user
        update_data = {}
        if account_status:
            update_data['account_status'] = account_status
        if payment_tier:
            update_data['payment_tier'] = payment_tier
        
        if update_data:
            supabase.table('users').update(update_data).eq('email', email).execute()
        
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

@app.route('/api/create-checkout-session', methods=['POST'])
def create_checkout_session():
    try:
        data = request.json
        email = data.get('email')
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400

        checkout_session = stripe.checkout.Session.create(
            customer_email=email,
            line_items=[
                {
                    'price': stripe_price_id,
                    'quantity': 1,
                },
            ],
            mode='subscription',
            success_url=app_domain + '/dashboard.html?payment=success',
            cancel_url=app_domain + '/pricing.html?payment=cancelled',
            metadata={
                'user_email': email
            }
        )
        return jsonify({'url': checkout_session.url})
    except Exception as e:
        print(f"Stripe Checkout Error: {e}")
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
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError as e:
        return 'Invalid signature', 400

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        user_email = session.get('metadata', {}).get('user_email')
        customer_id = session.get('customer')
        
        if not user_email:
            print("Error: No email in metadata")
            return jsonify({'error': 'No email in metadata'}), 400

        if not supabase:
            print("Error: Supabase not initialized")
            return jsonify({'error': 'Supabase not connected'}), 500

        try:
            supabase.table('users').update({
                'account_status': 'paid', 
                'payment_tier': 'pro',
                'stripe_customer_id': customer_id
            }).eq('email', user_email).execute()
            print(f"Updated user {user_email} to paid status.")
            return jsonify({'status': 'success'})
        except Exception as e:
            print(f"Error updating Supabase: {e}")
            return jsonify({'error': f"Database update failed: {str(e)}"}), 500

    return jsonify({'status': 'ignored'})
# For Vercel, we don't need app.run()

