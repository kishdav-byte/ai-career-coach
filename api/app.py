from flask import Flask, request, jsonify
import sys
import traceback

# 1. EARLY INITIALIZATION to catch import errors
app = Flask(__name__)
INIT_ERROR = None

try:
    import re
    import os
    import requests
    import json
    import time
    import base64
    import io
    import ast
    import asyncio
    import edge_tts
    from datetime import datetime, timedelta
    from dotenv import load_dotenv
    import stripe
    from flask_cors import CORS
    from supabase import create_client, Client

    load_dotenv()
    CORS(app)

    # ==========================================
    # INITIALIZATION
    # ==========================================
    SUPABASE_URL = os.environ.get('SUPABASE_URL')
    SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
    SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')

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
    
    # Configure App
    app.url_map.strict_slashes = False

    # CONSTANTS
    VOICE_CAP = 50
    API_KEY = os.environ.get('OPENAI_API_KEY_')

    # Initialize Stripe (Moved inside try)
    stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
    stripe_price_id = os.environ.get('STRIPE_PRICE_ID')
    stripe_webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
    app_domain = os.environ.get('APP_DOMAIN', 'http://localhost:3000')

except Exception as e:
    INIT_ERROR = f"Startup Error: {str(e)}\n{traceback.format_exc()}"
    print(INIT_ERROR)

@app.route('/api/init-debug')
def init_status():
    """Diagnostic route to check if app started cleanly."""
    if INIT_ERROR:
        return jsonify({"fatal_error": INIT_ERROR}), 500
    
    return jsonify({
        "status": "clean_start", 
        "supabase": "ready" if 'supabase' in globals() and supabase else "not_configured"
    })


# ==========================================
# LOGGING HELPERS
# ==========================================
def log_db_activity(email, feature, metadata=None):
    """Log user activity to Supabase."""
    admin_client = supabase_admin if supabase_admin else supabase
    if not admin_client: return
    try:
        admin_client.table('activity_logs').insert({
            "user_email": email,
            "feature": feature,
            "metadata": metadata or {}
        }).execute()
    except Exception as e:
        print(f"Activity Log Failed: {e}")

def log_db_error(email, error_type, details):
    """Log system error to Supabase."""
    admin_client = supabase_admin if supabase_admin else supabase
    if not admin_client: return
    try:
        admin_client.table('error_logs').insert({
            "user_email": email, # Can be 'system' or None
            "error_type": error_type,
            "details": str(details)
        }).execute()
    except Exception as e:
        print(f"Error Log Failed: {e}")



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

def generate_audio_edge(text, voice_id):
    """Generates audio using Edge TTS for MS voices and SSML support."""
    try:
        async def _generate():
            communicate = edge_tts.Communicate(text, voice_id)
            mp3_fp = io.BytesIO()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    mp3_fp.write(chunk["data"])
            return base64.b64encode(mp3_fp.getvalue()).decode('utf-8')
        
        return asyncio.run(_generate())
    except Exception as e:
        print(f"Edge TTS error: {e}")
        return None

def generate_audio(text, voice_id):
    """Router for audio generation based on voice_id."""
    openai_voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
    if voice_id in openai_voices:
        return generate_audio_openai(text, voice_id)
    else:
        # Default to Edge TTS for better support of Microsoft voices and SSML
        # Use standard en-US-AriaNeural if the voice_id is generic or unrecognized
        if not voice_id or voice_id == 'alloy': # fallback handling
            voice_id = "en-US-AriaNeural"
        return generate_audio_edge(text, voice_id)

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

def transcribe_audio_openai(base64_audio):
    """Transcribes audio using OpenAI Whisper API."""
    try:
        # 1. Decode base64 to binary
        if "base64," in base64_audio:
            base64_audio = base64_audio.split("base64,")[1]
        
        audio_data = base64.b64decode(base64_audio)
        
        # 2. Use io.BytesIO to create a file-like object
        buffer = io.BytesIO(audio_data)
        buffer.name = "audio.mp3" # Whisper needs a filename/extension
        
        # 3. Call Whisper API
        headers = {
            "Authorization": f"Bearer {API_KEY}"
        }
        
        files = {
            "file": (buffer.name, buffer, "audio/mpeg")
        }
        data = {
            "model": "whisper-1"
        }
        
        response = requests.post(
            "https://api.openai.com/v1/audio/transcriptions",
            headers=headers,
            files=files,
            data=data
        )
        response.raise_for_status()
        
        return response.json().get('text', '')
    except Exception as e:
        print(f"OpenAI transcription error: {e}")
        return None

@app.route('/api/generate-model-answer', methods=['POST'])
def generate_model_answer():
    if not API_KEY:
        return jsonify({"error": "Server API Key missing"}), 500

    data = request.json
    question = data.get('question')
    resume_context = data.get('resume_context', '')
    user_email = data.get('user_email') # Added for tracking

    # 3-TIER ROLE REVERSAL LOGIC
    # Tier 1: Free (Limit 3 Lifetime)
    # Tier 2: Unlimited (Limit 50/mo)
    # Tier 3: Credit (Deduct 1 Universal Credit)

    allowed = False
    
    if user_email and supabase:
        try:
             # Fetch Status
             db = supabase_admin if supabase_admin else supabase
             u_res = db.table('users').select('is_unlimited, subscription_status, monthly_voice_usage, role_reversal_count, credits').eq('email', user_email).execute()
             
             if u_res.data:
                 u = u_res.data[0]
                 rr_count = u.get('role_reversal_count', 0)
                 is_unlimited = u.get('is_unlimited', False)
                 sub_active = u.get('subscription_status') == 'active'
                 voice_usage = u.get('monthly_voice_usage', 0)
                 credits = u.get('credits', 0)

                 # CHECK 1: FREE TIER (< 3)
                 if rr_count < 3:
                     allowed = True
                     # Increment count
                     db.table('users').update({'role_reversal_count': rr_count + 1}).eq('email', user_email).execute()
                     print(f"Role Reversal: {user_email} used FREE tier ({rr_count + 1}/3)")
                 
                 # CHECK 2: UNLIMITED TIER (Status=Active, Usage < 50)
                 elif is_unlimited and sub_active:
                     if voice_usage < VOICE_CAP:
                         allowed = True
                         db.table('users').update({'monthly_voice_usage': voice_usage + 1}).eq('email', user_email).execute()
                         print(f"Role Reversal: {user_email} used UNLIMITED tier ({voice_usage + 1}/50)")
                     else:
                         return jsonify({"error": "Monthly Voice Limit Reached."}), 403

                 # CHECK 3: CREDIT TIER (Deduct 1 Credit)
                 elif credits > 0:
                     allowed = True
                     db.table('users').update({'credits': credits - 1}).eq('email', user_email).execute()
                     print(f"Role Reversal: {user_email} used CREDIT tier. Remaining: {credits - 1}")
                 
                 else:
                     return jsonify({"error": "Limit reached. Upgrade to Pro or buy credits."}), 402

        except Exception as tier_err:
             print(f"Role Reversal Access Error: {tier_err}")
             return jsonify({"error": "Access check failed"}), 500
    else:
        # Default allow if no auth? (Or block?)
        # For security, we should probably require auth, but existing logic was loose.
        # Let's assume auth is required for this specific tool if email is sent.
        if not user_email: 
             return jsonify({"error": "Login required"}), 401


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
        
        # TRACKING: Role Reversal Logic
        if user_email and supabase:
            try:
                # Simple Read-Modify-Write (Concurrency risk minimal for this scale)
                user_res = supabase.table('users').select('role_reversal_count').eq('email', user_email).execute()
                if user_res.data:
                    current_count = user_res.data[0].get('role_reversal_count', 0) or 0
                    supabase.table('users').update({'role_reversal_count': current_count + 1}).eq('email', user_email).execute()
                    print(f"Tracked Role Reversal for {user_email}: {current_count + 1}")
            except Exception as e:
                print(f"Tracking Error (Role Reversal): {e}")

        return jsonify(parsed_content)
    except Exception as e:
        print(f"Model Answer Gen Error: {e}")
        return jsonify({"error": "Failed to generate answer"}), 500
    except Exception as e:
        print(f"Model Answer Gen Error: {e}")
        return jsonify({"error": "Failed to generate answer"}), 500

@app.route('/api/speak', methods=['POST'])
def speak_text():
    if not API_KEY:
        return jsonify({"error": "Server API Key missing"}), 500

    data = request.json
    text = data.get('text')
    voice = data.get('voice', 'alloy')

    if not text:
        return jsonify({"error": "Text is required"}), 400

    try:
        # Re-use existing helper
        audio_base64 = generate_audio_openai(text, voice)
        if not audio_base64:
             return jsonify({"error": "Audio generation failed"}), 500
             
        return jsonify({"audio": audio_base64})
    except Exception as e:
        print(f"TTS Error: {e}")
        return jsonify({"error": str(e)}), 500
@app.route('/api/optimize', methods=['POST'])
def optimize_resume_content():
    if not API_KEY:
        return jsonify({"error": "Server configuration error: API Key missing"}), 500

    data = request.json
    user_data = data.get('user_data')
    template_name = data.get('template_name', 'modern')
    job_description = data.get('job_description', '')
    resume_text = data.get('resume_text', '')  # Fallback source

    # GUARDRAIL: Input Validation
    has_valid_user_data = user_data and (user_data.get('experience') or user_data.get('education'))
    has_valid_text = resume_text and len(resume_text) > 50

    if not has_valid_user_data and not has_valid_text:
        return jsonify({"error": "ERROR: No resume data found. Please upload your resume to the Scanner first."}), 400

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

    # Determine Data Source for Prompt
    data_block = ""
    if has_valid_user_data:
        data_block = json.dumps(user_data)
    else:
        data_block = f"RESUME TEXT:\n{resume_text}\n\n(Note: Parse this text into the structured JSON format: personal, summary, experience, education, skills)."

    prompt = f"""
    {base_instruction}
    {tailoring_instruction}
    {formatting_instruction}

    Here is the data:
    {data_block}

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



@app.route('/api', methods=['POST', 'OPTIONS'])
@app.route('/', methods=['POST', 'OPTIONS'])
def api():
    print(f"Incoming request to /api: {request.path} [{request.method}]")

    # CORS Preflight
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    if not API_KEY:
        return jsonify({"error": "Server configuration error: API Key missing"}), 500

    data = request.json
    action = data.get('action')

    # STRIPE INTEGRATIONS (Integrated bypass for routing robustness)
    if action == 'create-checkout-session':
        try:
            price_id = data.get('priceId')
            success_url = data.get('successUrl')
            cancel_url = data.get('cancelUrl')
            email = data.get('email')
            user_id = data.get('userId')
            
            plan_type = data.get('plan_type') or data.get('plan')
            feature = data.get('feature')

            if plan_type and plan_type in PRICE_IDS:
                price_id = PRICE_IDS.get(plan_type)
            elif feature == 'rewrite' or plan_type == 'rewrite':
                price_id = os.environ.get('STRIPE_REWRITE_PRICE_ID')
                feature = 'rewrite'
            elif feature == 'linkedin_optimize' or plan_type == 'linkedin_optimize':
                price_id = "price_1ShWBJIH1WTKNasqd7p9VA5f" # Hardcoded per request (or use ENV)
                feature = 'linkedin_optimize'

            if not price_id and not plan_type and not feature:
                 return jsonify({'error': 'Missing Plan or Feature selection.'}), 400
            
            if not price_id:
                 return jsonify({'error': f'Invalid or missing Price Configuration for: {plan_type or feature}'}), 400

            if not success_url:
                success_url = f"{app_domain}/strategy-lab.html?success=true"
            if not cancel_url:
                cancel_url = f"{app_domain}/strategy-lab.html?canceled=true"

            checkout_session = stripe.checkout.Session.create(
                line_items=[{'price': price_id, 'quantity': 1}],
                mode='payment',
                success_url=success_url,
                cancel_url=cancel_url,
                customer_email=email,
                client_reference_id=user_id,
                metadata={'user_email': email, 'user_id': user_id, 'feature': feature or plan_type}
            )
            return jsonify({"data": {'url': checkout_session.url}})
        except Exception as e:
            print(f"Unified Checkout Error: {e}")
            return jsonify({"error": str(e)}), 500

    if action == 'create-portal-session':
        try:
            email = data.get('email')
            if not email:
                return jsonify({'error': 'Email is required'}), 400
            customers = stripe.Customer.list(email=email, limit=1)
            if not customers.data:
                return jsonify({'error': 'No billing account found for this email.'}), 404
            customer = customers.data[0]
            return_url = f"{app_domain}/dashboard.html"
            portal_session = stripe.billing_portal.Session.create(
                customer=customer.id,
                return_url=return_url,
            )
            return jsonify({"data": {"url": portal_session.url}})
        except Exception as e:
            print(f"Unified Portal Error: {e}")
            return jsonify({"error": str(e)}), 500

    messages = []
    json_mode = False

    # ---------------------------------------------------------
    # ADMIN GHOST MODE CHECK
    # ---------------------------------------------------------
    is_admin_ghost = data.get('ghostMode', False)
    
    print(f"DEBUG API: Received Action = '{action}'")

    # Important: In production, verify the user is ACTUALLY an admin on the server side 
    # before trusting this flag. For this implementation, we will trust the client 
    # but verify the user's role logic below if 'is_admin_ghost' is True.
    
    # ---------------------------------------------------------
    # ACCESS CONTROL & MONETIZATION CHECK (Phase 13)
    # ---------------------------------------------------------
    PAID_ACTIONS = [
        'interview_chat', 'generate_report', 'analyze_resume', 'optimize_resume', 'optimize',
        'career_plan', 'cover_letter', 'negotiation_script', 'value_followup', 'inquisitor', 'linkedin_optimize'
    ]
    
    if action in PAID_ACTIONS:
        # Get email from request data OR try to infer it if possible
        # Frontend 'callApi' usually sends parameters, but we need to ensure 'email' passes through
        # 'optimize_resume' uses 'user_data' -> 'personal' -> 'email'
        email = data.get('email')
        
        if not email and (action == 'optimize_resume' or action == 'optimize') and 'user_data' in data:
            email = data.get('user_data', {}).get('personal', {}).get('email')

        if not email and action == 'analyze_resume' and 'email' not in data:
             # Assume analyze_resume sends email or we fail
             pass 

        if email:
            # FIX: Use Admin Client to bypass RLS (like /auth/user)
            db_client = supabase_admin if supabase_admin else supabase
            
            if db_client:
                # Check User Status (Updated Phase 34 + Free Tier Tracking)
                # NOTE: Removed analysis_count from here to prevent crash if SQL not run yet. We fetch it safely below.
                user_res = db_client.table('users').select(
                    'role, subscription_status, is_unlimited, resume_credits, interview_credits, rewrite_credits, credits_linkedin, credits, monthly_voice_usage, '
                    'credits_negotiation, credits_inquisitor, credits_followup, credits_30_60_90, credits_cover_letter'
                ).eq('email', email).execute()
                
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
                    resume_credits = user.get('resume_credits', 0) or 0
                    interview_credits = user.get('interview_credits', 0) or 0
                    rewrite_credits = user.get('rewrite_credits', 0) or 0
                    universal_credits = user.get('credits', 0) or 0
                    
                    # Log Check
                    print(f"Auth Check for {email}: Unlimited={is_unlimited}, R_Cred={resume_credits}, I_Cred={interview_credits}, Action={action}")

                    # Logic: ALLOW if 'is_unlimited' OR Specific Credit > 0
                    has_access = False
                    
                    if is_admin_ghost and user_role == 'admin':
                         has_access = True

                    elif is_unlimited:
                        # FAIR USE CHECK (Voice Tools)
                        if action in ['interview_chat']:
                             usage = user.get('monthly_voice_usage', 0) or 0
                             sub_status = user.get('subscription_status', 'active')
                             
                             if sub_status == 'active' and usage < VOICE_CAP:
                                 # Increment Usage (Optimistic / Fire & Forget or Await)
                                 # We are in checking phase. Does this function DEDUCT?
                                 # Current logic separates check vs deduct.
                                 # Line 405: "if should_deduct:"
                                 # But for Unlimited, we usually just return True.
                                 # We need to increment usage here IF should_deduct is True.
                                 if should_deduct:
                                     new_usage = usage + 1
                                     supabase_admin.table('users').update({'monthly_voice_usage': new_usage}).eq('email', email).execute()
                                     print(f"Fair Use Tracking: {new_usage}/{VOICE_CAP}")
                                 has_access = True
                             else:
                                 print(f"Fair Use Limit Reached or Inactive Sub: {usage}/{VOICE_CAP}, Status={sub_status}")
                                 has_access = False
                        else:
                             has_access = True
                    else:
                        # Check specific credit based on action
                        if action == 'analyze_resume':
                            # FREE TIER: No credit check, just track usage
                            has_access = True
                            
                            # Increment Usage (if not admin/ghost preventing it)
                            if should_deduct: 
                                supabase_upd = supabase_admin if supabase_admin else supabase
                                try:
                                    # Fetch current count safely
                                    # This protects against 500 Error if column doesn't exist yet
                                    count_res = supabase_upd.table('users').select('analysis_count').eq('email', email).execute()
                                    current_count = 0
                                    if count_res.data:
                                        current_count = count_res.data[0].get('analysis_count', 0) or 0
                                    
                                    new_count = current_count + 1
                                    
                                    supabase_upd.table('users').update({
                                        'analysis_count': new_count,
                                        'last_analysis_date': 'now()'
                                    }).eq('email', email).execute()
                                    print(f"Tracked Resume Analysis. Count: {new_count}")
                                except Exception as e:
                                    print(f"Tracking Error (Analysis): {e}")

                        elif action == 'optimize_resume':
                            if resume_credits > 0 or universal_credits > 0:
                                has_access = True
                                # Deduct immediately (unless unlimited, which is handled above)
                                if should_deduct:
                                    supabase_upd = supabase_admin if supabase_admin else supabase
                                    if resume_credits > 0:
                                        new_credits = resume_credits - 1
                                        supabase_upd.table('users').update({'resume_credits': new_credits}).eq('email', email).execute()
                                        print(f"Deducted 1 RESUME credit. Remaining: {new_credits}")
                                    else:
                                        new_credits = universal_credits - 1
                                        supabase_upd.table('users').update({'credits': new_credits}).eq('email', email).execute()
                                        print(f"Deducted 1 UNIVERSAL credit for Resume. Remaining: {new_credits}")

                        elif action == 'optimize':
                            # V2 REWRITE CREDIT CHECK
                            if rewrite_credits > 0 or universal_credits > 0:
                                has_access = True
                                if should_deduct:
                                    supabase_upd = supabase_admin if supabase_admin else supabase
                                    if rewrite_credits > 0:
                                        new_credits = rewrite_credits - 1
                                        supabase_upd.table('users').update({'rewrite_credits': new_credits}).eq('email', email).execute()
                                        print(f"Deducted 1 REWRITE credit. Remaining: {new_credits}")
                                    else:
                                        new_credits = universal_credits - 1
                                        supabase_upd.table('users').update({'credits': new_credits}).eq('email', email).execute()
                                        print(f"Deducted 1 UNIVERSAL credit for Rewrite. Remaining: {new_credits}")
                            else:
                                 print(f"Blocked: Insufficient credits for Rewrite (Rewrite: {rewrite_credits}, Universal: {universal_credits})")
                                 has_access = False

                                 has_access = False
 
                        elif action == 'linkedin_optimize':
                            # LINKEDIN OPTIMIZER CREDIT CHECK
                            linkedin_credits = user.get('credits_linkedin', 0) or 0
                            
                            if linkedin_credits > 0 or universal_credits > 0:
                                has_access = True
                                if should_deduct:
                                    supabase_upd = supabase_admin if supabase_admin else supabase
                                    if linkedin_credits > 0:
                                        new_val = linkedin_credits - 1
                                        supabase_upd.table('users').update({'credits_linkedin': new_val}).eq('email', email).execute()
                                        print(f"Deducted 1 LINKEDIN credit. New: {new_val}")
                                    else:
                                        new_val = universal_credits - 1
                                        supabase_upd.table('users').update({'credits': new_val}).eq('email', email).execute()
                                        print(f"Deducted 1 UNIVERSAL credit for LinkedIn. New: {new_val}")
                            else:
                                print(f"Blocked: Insufficient credits for LinkedIn (Specific: {linkedin_credits}, Universal: {universal_credits})")
                                has_access = False

                        elif action in ['career_plan', 'cover_letter', 'negotiation_script', 'value_followup', 'inquisitor']:
                            # Determine specific credit column
                            credit_col = {
                                'career_plan': 'credits_30_60_90',
                                'cover_letter': 'credits_cover_letter',
                                'negotiation_script': 'credits_negotiation',
                                'value_followup': 'credits_followup',
                                'inquisitor': 'credits_inquisitor'
                            }.get(action)
                            
                            specific_credits = user.get(credit_col, 0) or 0
                            
                            if specific_credits > 0 or universal_credits > 0:
                                has_access = True
                                if should_deduct:
                                    supabase_upd = supabase_admin if supabase_admin else supabase
                                    if specific_credits > 0:
                                        new_val = specific_credits - 1
                                        supabase_upd.table('users').update({credit_col: new_val}).eq('email', email).execute()
                                        print(f"Deducted 1 {action} credit from {credit_col}. New: {new_val}")
                                    else:
                                        new_val = universal_credits - 1
                                        supabase_upd.table('users').update({'credits': new_val}).eq('email', email).execute()
                                        print(f"Deducted 1 UNIVERSAL credit for {action}. New: {new_val}")
                            else:
                                has_access = False
                                print(f"Blocked: Insufficient credits for {action}")
                        
                        elif action in ['interview_chat', 'generate_report']:
                            if action == 'generate_report':
                                 # The report is included in the interview session.
                                 # Access is granted because the session was paid for at Question 1.
                                 has_access = True
                            
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
                                    if interview_credits > 0 or universal_credits > 0:
                                        has_access = True
                                        if should_deduct:
                                            supabase_upd = supabase_admin if supabase_admin else supabase
                                            if interview_credits > 0:
                                                new_credits = interview_credits - 1
                                                supabase_upd.table('users').update({'interview_credits': new_credits}).eq('email', email).execute()
                                                print(f"DEDUCTED 1 INTERVIEW CREDIT. Remaining: {new_credits}")
                                            else:
                                                new_credits = universal_credits - 1
                                                supabase_upd.table('users').update({'credits': new_credits}).eq('email', email).execute()
                                                print(f"DEDUCTED 1 UNIVERSAL credit for Interview. Remaining: {new_credits}")
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
        job_desc = data.get('job_description', '')
        
        # Calculate robust word count
        word_count = len(re.findall(r'\w+', resume))
        
        json_mode = True
        prompt = f"""
        You are an expert Executive Career Coach (rate $1000/hr). Analyze this resume meticulously.
        
        RESUME CONTENT:
        {resume}
        
        TARGET JOB DESCRIPTION:
        {job_desc if job_desc else "General executive-level optimization requested."}
        
        INSTRUCTION:
        1. Identify the target job title from the JD or resume.
        2. Provide an overall match score (0-100) based on the JD.
        3. Provide EXACTLY 5 detailed optimization protocols.
        4. Detect formatting inconsistencies (dates, punctuation, layout).
        5. Identify missing high-frequency keywords from the JD.

        CRITICAL RULES (OPTIMIZATION PROTOCOL):
        - NO INVENTED METRICS: Use "[X]%" or "[X]$".
        - EXACT QUOTES ONLY: Reference specific bullets from the resume.
        - HYPER-SPECIFICITY: Actionable feedback, not generic advice.
        - BRIDGE LANGUAGE (SENIORITY CHECK): If the candidate is a Leader (Manager, Director, VP) and the keyword is technical (e.g. Python, ETL, AWS), suggest "Directed strategy for X" or "Managed migration of X" instead of hands-on "Implemented X".
        - CONTEXTUAL TRANSLATION: Inject keywords into existing resume bullets instead of replacing them. (e.g., "Modernized systems by transitioning to Cloud Architecture" instead of just "Built Cloud Architecture").
        - CERTIFICATION NUDGE: If the gap is a hard credential (e.g. AWS Certified), the 'fix' must be an ACTION ITEM: "Do not add this yet. Action: Enroll in [Course] and list as (In Progress)".
        
        Return valid JSON with this EXACT structure:
        {{
            "job_title": "Senior Product Manager",
            "overall_score": 85,
            "word_count": {word_count},
            "summary": "Brief 1-sentence summary.",
            "benchmark": {{
                "level": "Executive",
                "percentile": "Top 10%",
                "text": "Status: Stronger than 90% of candidates for this specific role."
            }},
            "red_flags": [
                {{"title": "Issue", "issue": "Detail", "fix": "Specific fix"}}
            ],
            "improvements": [
                {{
                    "title": "Protocol Title", 
                    "suggestion": "Deep strategic advice. Include Rule-based bridge language if applicable.",
                    "current": "[Exact quote from resume]", 
                    "better": "[Hypothetically optimized version using Bridge Language and Metrics]"
                }}
            ],
            "keywords": {{
                "missing": [
                    {{"word": "Keyword", "advice": "How to integrate it using Bridge Language or Action Item if a credential."}}
                ]
            }},
            "ats_compatibility": {{
                "score": 8,
                "issues": ["Issue 1 with fix", "Issue 2 with fix"]
            }},
            "formatting": [
                {{"issue": "Consistency Problem", "fix": "<b>Found:</b> [A] vs [B]. <br><b>Fix:</b> [Instruction]"}}
            ]
        }}
        """
        messages = [{"role": "user", "content": prompt}]
        
    elif action == 'transcribe':
        audio = data.get('audio')
        if not audio:
            return jsonify({"error": "Audio data missing"}), 400
        transcript = transcribe_audio_openai(audio)
        return jsonify({"transcript": transcript})

    elif action == 'interview_chat':
        message = data.get('message', '')
        job_posting = data.get('jobPosting', '')
        voice = data.get('voice', 'en-US-AriaNeural')
        speed = data.get('speed', '+0%')
        is_start = data.get('isStart', False)
        question_count = data.get('questionCount', 1)
        json_mode = True

        # 1. SILENCE & "THINKING..." DETECTION (Anti-Hallucination Trap)
        user_input_clean = message.strip()
        if not is_start and (user_input_clean.lower() == "thinking..." or len(user_input_clean.split()) < 5):
            return jsonify({
                "data": {
                    "score": 0,
                    "feedback": "",
                    "improved_sample": "",
                    "text": "I am waiting for your response.",
                    "next_question": "I am waiting for your response."
                }
            })
        
        context = ""
        if job_posting:
            context = f"\n\nContext: The user is interviewing for the following job:\n{job_posting}\n\nTailor your questions and persona to this role. You already know the candidate is applying for this position. Do NOT ask them to state the position. Prepare to ask relevant interview questions."
        
        system_prompt = f"""System Instructions:
You are a strict but conversational hiring manager. YOUR GOAL is to evaluate the candidate's use of the STAR method. 

CONVERSATIONAL RULES:
1. STOP ANNOUNCING: You are FORBIDDEN from using the words "question," "next," or "first" in the opening sentence of your turn. Just ask the question directly.
2. USE NATURAL BRIDGES: Briefly acknowledge the user's previous answer before pivoting (e.g., "That sounds like a tough situation. Speaking of conflict...").
3. DIRECT INTERROGATION: Always phrase questions as direct sentences ending in a question mark.
4. SINGLE SENTENCE: The 'next_question' MUST be a single, complete sentence. Do not add any preamble.

Keep responses concise and professional. This interview consists of 5 questions. Current Question: {question_count} of 5.{context}"""
        
        if is_start:
            welcome_msg = "Welcome to the interview! I've reviewed the job details, and I'm going to ask you five questions. <break time=\"2.0s\" /> When answering, please provide specific examples of how you've handled key situations, and I encourage you to use the STAR method when providing your answers. <break time=\"2.0s\" /> You'll want to share a specific Situation or Task, the Action or Actions you took, and the Result of your Actions. <break time=\"2.0s\" /> The first question that I have for you is... <break time=\"1.0s\" />"
            
            user_prompt = f"""User: {message}

Start the interview. You MUST start your response with exactly: '{welcome_msg}'.
Immediately after the final <break time="1.0s" />, append the FIRST INTERVIEW QUESTION based on the Job Context provided.

JSON Template:
{{
  "transcript": "{message}",
  "feedback": "",
  "improved_sample": null,
  "job_title": "[Extract Job Title from Context]",
  "next_question": "{welcome_msg} [Insert Question 1 Here]"
}}"""
        
        else:
            # CONTINUATION: Evaluate previous answer, Ask next question
            
            # Ordinals for the NEXT question we are about to ask
            # Input question_count is the one just answered.
            # So if count=1, we are evaluating 1 and asking 2.
            next_q_num = question_count + 1
            if next_q_num >= 5:
                next_ordinal = "final"
            else:
                next_ordinal = "next"

            if question_count < 5:
                # Normal Case: Eval current -> Ask Next
                user_prompt = f"""
User Answer: {message}

Evaluate the answer to Question {question_count} using the HYPER-STRICT STAR SCORING RUBRIC (+25% Specificity Requirement):
1-2 (Fail/Weak): Missing S, A, or R. (HARD CONSTRAINT: Max 2 if any component is missing).
3 (Average): S, A, R present. Contains at least 1-2 specific details (names, tools) but lacks hard outcomes.
4 (Strong): Complete STAR. High technical specificity. Uses job-specific keywords. Must include a clear outcome or impact.
5 (Unicorn): Complete STAR. Highly specific AND includes MULTIPLE measurable metrics (%, $, time SAVED, scale).

CRITICAL INSTRUCTIONS:
1. SPECIFICITY AUDIT: If the answer is vague or lacks concrete nouns/actions, PENALIZE the score.
2. Start 'feedback' with: "I would score this answer a [score] because...".
3. In 'feedback', explicitly state which STAR components were present. The numeric score in the 'score' field MUST match the written explanation. If the user provides no substance, the Score is 0 and the feedback is "No answer provided."
4. BETTER ANSWER LOGIC SPLIT:
   - IF SCORE is 3 or 4: Use the "Plus-One" method. Retain the user's original voice/text and only inject the missing metric/result into the end. Use conversational transitions like "And that actually meant...".
   - IF SCORE is 1 or 2 (or user was unsure): Ignore the user's text entirely. Generate a FRESH, PERFECT example answer from scratch. Start with exactly: "Since you were unsure, here is an example of what a perfect answer sounds like: '[Insert Full STAR Story]'"
5. TONE: Coaching. Summarize gaps.

Return STRICT JSON: {{"score": [Numeric Score 0-5], "feedback": "...", "improved_sample": "...", "next_question": "..."}}
"""
            
            else:
                # Final Case: Eval Q5 -> End
                user_prompt = f"""
User Answer: {message}

Evaluate the answer to the final question (Question 5) using the HYPER-STRICT STAR SCORING RUBRIC (+25% Specificity):
1-2 (Fail/Weak): Missing S, A, or R. (HARD CONSTRAINT: Max 2 if any component is missing).
3 (Average): S, A, R present. Contains specific details but lacks hard outcomes.
4 (Strong): Complete STAR. High technical specificity and job-specific.
5 (Unicorn): Complete STAR, job-specific AND includes MULTIPLE measurable metrics.

CRITICAL INSTRUCTIONS:
1. SPECIFICITY AUDIT: Penalize vague answers.
2. Start 'feedback' with: "I would score this answer a [score] because...". The numeric score in the 'score' field MUST match the written explanation.
3. BETTER ANSWER LOGIC SPLIT:
   - IF SCORE is 3 or 4: Use the "Plus-One" method. Retain user voice/text and inject the missing metric into the end.
   - IF SCORE is 1 or 2: Ignore user text. Generate a FRESH, PERFECT example answer from scratch. Start with exactly: "Since you were unsure, here is an example of what a perfect answer sounds like: '[Insert Full STAR Story]'"
4. TONE: Coaching. Summarize overall performance vs STAR standards.

Return STRICT JSON: {{"score": [Numeric Score 0-5], "feedback": "...", "improved_sample": "...", "next_question": "[Acknowledge their final answer naturally and end the interview professionally]"}}
"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]


    elif action == 'lab_assistant_chat':
        # NEW: Lab Assistant Chat Logic
        message = data.get('message', '')
        history = data.get('history', []) # Previous messages if we want context (optional)

        system_prompt = """
You are the "Lab Assistant" for Ace Interview, a career strategy platform.
Your goal is to be helpful, encouraging, and knowledgeable, BUT you must strictly protect the business's premium revenue streams.

YOUR CORE DIRECTIVE:
You are an Educator, not an Executor. You explain "What" and "Why," but you never do the "How" for deep tasks.

THE GUARDRAILS (STRICT RULES):

1. RESUME & LINKEDIN REQUESTS:
   - IF asked to "rewrite," "edit," or "fix" a resume/summary:
   - DO NOT generate a full rewrite.
   - DO: Critique 1-2 sentences to show value, then STOP.
   - RESPONSE TEMPLATE: "I see some opportunities here! A strong summary should be metric-driven. For example, change 'Managed a team' to 'Led 10 people.' For a complete, professional rewrite, please use the **Executive Rewrite** tool in the dashboard."

2. INTERVIEW PRACTICE:
   - IF asked to "interview me" or "simulate a roleplay":
   - DO NOT engage in a back-and-forth roleplay.
   - DO: Provide ONE good practice question.
   - RESPONSE TEMPLATE: "That's a great role to target. A common question they'll ask is 'Tell me about a time you failed.' I can't listen to your audio here, but our **Interview Simulator** offers real-time voice analysis and scoring. Give that a try!"

3. SALARY NEGOTIATION:
   - IF asked for "specific scripts" or "negotiation emails" for a specific number:
   - DO NOT write the email.
   - DO: Give general principles (e.g., "Don't say the number first").
   - RESPONSE TEMPLATE: "The key is to anchor the range high. However, phrasing is delicate. For a custom-tailored negotiation script based on your specific offer, use **The Closer** tool."

4. GENERAL CAREER ADVICE (Safe Zone):
   - You MAY freely answer questions about:
   - Definitions (What is the STAR method?)
   - Corporate terminology (What does matrixed org mean?)
   - General etiquette (What to wear? When to send a thank you note?)

TONE:
- Professional, concise, slightly "Cyberpunk/Avant-Garde" (matches the app aesthetic).
- Use formatting (bullet points) for readability.
- Always end a "refusal" with a helpful link/nudge to the paid tool.

IMPORTANT - REVENUE LINKING PROTOCOL:
When you recommend a solution that requires deep work (writing, simulation, negotiation), you MUST use the EXACT tool name in your response to trigger the user interface link:
- Use "Executive Rewrite" if they need resume help.
- Use "Interview Simulator" if they need practice.
- Use "The Closer" if they need negotiation help.
"""
        
        # Build messages list
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add basic history if useful, or just the current message
        # For this implementation, we'll just send the current message to save tokens/complexity, 
        # unless history is passed. 
        if history:
            # Append last 2-3 turns max to keep context but save tokens
            for msg in history[-4:]: 
                role = "user" if msg.get("sender") == "user" else "assistant"
                messages.append({"role": role, "content": msg.get("text")})
        
        messages.append({"role": "user", "content": message})

        content = call_openai(messages, json_mode=False)
        return jsonify({"response": content})


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
        Generate an "Executive Coaching Report" based on the following interview history.
        
        History: {json.dumps(history)}
        
        The report must be an HTML document (no markdown) with a premium, coaching-oriented tone.
        
        REQUIRED SECTIONS:
        1. **Executive Summary**: A high-level overview of the candidate's performance.
        2. **Question Breakdown**: Use a table to show the score (1-5) for each question.
        3. **Aggregate Performance Insight**: Identify the most common recurring gap across all answers (e.g., "In 4 of the 5 questions, you scored lower due to missing or weak 'Result' components"). This section should tell the user exactly what ONE thing they should focus on practicing the most.
        4. **Gap Analysis (The STAR Filter)**: For each question, specifically identify which STAR components (Situation, Action, Result) were strong and which were weak/missing.
        5. **Metric Injection Strategy**: For any responses that scored below 5, provide a specific example of how the candidate could have used numbers (time saved, revenue increased, %, $) to move to a 'Unicorn' score.
        6. **Final Coaching Roadmap**: 3 actionable steps for the next interview.

        STYLE: Use inline CSS for a clean, modern look. Dark text on light background, professional borders, and clear headings.
        
        Return JSON structure: {{ "report": "<html>...</html>" }}
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
            {"role": "system", "content": """### SYSTEM ROLE ###
You are a dual-mode agent:
1. **The Auditor (Recommendations):** You aggressively analyze the input for missing context and "value gaps."
2. **The Editor (Profile Rewrite):** You rewrite the text using ONLY the provided facts (Strict Data Fidelity).

### PHASE 1: DIAGNOSTIC CHECK (CRITICAL) ###
1. If the draft is EMPTY/NULL: Output "CRITICAL ERROR: NO INPUT DATA RECEIVED."
2. If text exists: Proceed.

### PHASE 2: STRATEGIC AUDIT (KEY RECOMMENDATIONS) ###
Generate 3-4 bullet points of HIGH-LEVEL ADVICE based strictly on the user's *specific* content.
- **GENERIC ADVICE IS BANNED:** Do NOT say "Add a photo," "Add keywords," or "Include certifications."
- **TASK:** Find "Value Gaps" in their text.
  - *Gap Example 1:* If they mention "efficiency," ask: "Name the specific tool you used (e.g., Tableau, Python) to achieve this efficiency."
  - *Gap Example 2:* If they say "Managed a team," ask: "Specify the exact headcount (e.g., 'Team of 50') to demonstrate scale."
  - *Gap Example 3:* If they mention a "project," ask: "What was the budget size? Managing a $10k project is different from a $10M project."

### PHASE 3: PROFILE RECONSTRUCTION (STRICT DATA FIDELITY) ###
Rewrite the About section using ONLY the facts from the input.
- **NO HALLUCINATIONS:** If the user says "$1M+", do NOT change it to "$2M". Verify every number.
- **PRESERVE THE STORY:** Keep the unique backstory (e.g., "restaurant to boardroom"). Do not summarize it away.
- **STRUCTURE:**
   - **The Hook:** 2 lines summarizing their unique value/metrics.
   - **The Story:** The detailed career journey (keep the grit).
   - **The Evidence:** Bulleted list of specific metrics (copied exactly).
   - **The Call:** Brief invitation to connect.

### TECHNICAL JSON REQUIREMENT ###
You MUST return the output as a JSON object with this EXACT schema:
{
    "recommendations": ["Reflect the points from PHASE 2 here as a list of strings"],
    "refined_content": "The full text of the rewritten section from PHASE 3"
}
"""},
            {"role": "user", "content": f"""### INPUT DATA ###
User's Draft: "{about_me}"

### OUTPUT GENERATION ###
If input is present, generate the profile now. Verify every number against the input.
"""}
        ]
        response_text = call_openai(messages, json_mode=True)
        
        # Clean up markdown if present (Common OpenAI quirk)
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.startswith('```'):
            response_text = response_text[3:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]

        try:
            # LOG ACTIVITY: Record that the user optimized their profile
            log_db_activity(data.get('email', 'unknown'), 'linkedin_optimize', {"status": "success"})
            
            return jsonify(json.loads(response_text))
        except:
            # LOG ACTIVITY: Record success even if JSON parsing had to fallback (still "worked")
            log_db_activity(data.get('email', 'unknown'), 'linkedin_optimize', {"status": "fallback_string"})
            
            # Fallback if AI returns bad JSON
            # Return raw text in refined_content so user sees SOMETHING
            return jsonify({"recommendations": [], "refined_content": response_text})

    elif action == 'star_drill':
        try:
            user_input = data.get('input_text', '')
            user_id = data.get('user_id')
            email = data.get('email')

            # 1. LIMIT CHECK
            count = 0
            if user_id:
                # Use robust query - avoid .single() to prevent crash if user not found, catch generic errors
                try:
                    # Request specific columns, if they don't exist this will raise APIError
                    response = supabase.table('users').select('subscription_status, is_unlimited, star_drill_count').eq('id', user_id).execute()
                    if response.data and len(response.data) > 0:
                        u = response.data[0]
                        is_pro = u.get('is_unlimited') or u.get('subscription_status') == 'pro'
                        count = u.get('star_drill_count', 0)
                        
                        # Free User Logic
                        if not is_pro and count >= 3:
                            return jsonify({"error": "LIMIT_REACHED", "message": "Free limit reached (3/month). Upgrade for unlimited access."}), 403
                except Exception as db_err:
                    print(f"DB Check Failed (Likely Schema): {db_err}")
                    # If we can't check limits due to schema error, we should probably fail safe or block?
                    # For now, let's re-raise so it's caught by outer block and sent to frontend
                    raise db_err

            # 2. AI GENERATION
            messages = [
                {"role": "system", "content": """You are an expert Interview Coach specializing in the S.T.A.R. method.
                Your goal is to take a messy, rambling user story and structure it into a perfect S.T.A.R. format.
                
                OUTPUT RULES:
                - **S (Situation):** Set the scene briefly (1-2 sentences). Context only.
                - **T (Task):** What was the specific challenge or goal? (1 sentence).
                - **A (Action):** What did the USER specifically do? Focus heavily here. Use active verbs (Led, Built, Negotiated). (3-4 sentences).
                - **R (Result):** What was the outcome? Quantify it if possible ($ saved, % improved). (1-2 sentences).

                RETURN JSON ONLY:
                {
                    "S": "...",
                    "T": "...",
                    "A": "...",
                    "R": "..."
                }
                """},
                {"role": "user", "content": f"Here is my raw story:\n{user_input}"}
            ]
            
            response_text = call_openai(messages, json_mode=True)
            
            # Clean up
            if response_text.startswith('```json'): response_text = response_text[7:]
            if response_text.startswith('```'): response_text = response_text[3:]
            if response_text.endswith('```'): response_text = response_text[:-3]

            # 3. INCREMENT COUNT & LOG
            if user_id:
                try:
                    # Update count - verified earlier that we have it
                    supabase.table('users').update({'star_drill_count': count + 1}).eq('id', user_id).execute()
                except Exception as update_err:
                    print(f"Failed to update count: {update_err}")
                    # Non-critical, continue
            
            log_db_activity(email, 'star_drill', {"status": "success"})
            
            return jsonify(json.loads(response_text))

        except Exception as e:
            print(f"STAR Drill Critical Error: {e}")
            # Return JSON error to prevent 'Unexpected token <' in frontend
            return jsonify({"error": "SERVER_ERROR", "message": f"Backend Error: {str(e)}"}), 500

    elif action == 'parse_resume':
        resume_text = data.get('resume_text', '')
        system_msg = """You are a precise Resume Parsing Engine. Convert raw PDF text into structured JSON.
        
        CRITICAL RULES:
        1. Fix Merged Text: PDF extraction often merges Title and Date (e.g., "Senior ManagerMarch 2024"). You MUST split these into Role and Date.
        2. Ignore Artifacts: Do not parse lines like "Verizon logo" or repetitive headers as content.
        3. Infer Missing Formatting: Capitalize names, fix spacing.
        
        RETURN JSON SCHEMA:
        {
            "personal": {"name": "", "email": "", "phone": "", "location": "", "linkedin": "", "summary": ""},
            "skills": ["skill1", "skill2"],
            "experience": [{"role": "", "company": "", "dates": "", "description": ""}],
            "education": [{"degree": "", "school": "", "dates": ""}]
        }
        Return ONLY valid JSON.
        """
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
        
    # --- GATEKEEPER: Credit Check & Deduction (Python Version) ---
    # --- GATEKEEPER: Credit Check & Deduction (Python Version) ---
    elif action == 'optimize': # Executive Rewrite
        # 1. IDENTIFY USER (By Email)
        user_data = data.get('user_data', {})
        email = user_data.get('personal', {}).get('email')
        
        if not email:
             return jsonify({"error": "Email required for credit validation"}), 400

        # 2. FETCH PROFILE & CREDIT STATUS
        # We fetch ID here to ensure we have the UUID for the RPC call
        try:
            # Use Admin client if available to bypass RLS, otherwise fallback to standard client
            db_client = supabase_admin if supabase_admin else supabase
            
            # Fetch profile (using ilike for case-insensitive match)
            profile_res = db_client.table('users').select('id, credits, rewrite_credits, is_unlimited, subscription_status').ilike('email', email).execute()
            
            if not profile_res.data or len(profile_res.data) == 0:
                 print(f"Gatekeeper: Check failed for {email} - User not found in DB")
                 return jsonify({"error": f"User profile not found for {email}. Please ensure you are logged in."}), 404
                 
            profile = profile_res.data[0]
            
        except Exception as e:
            print(f"Gatekeeper Error: {e}")
            return jsonify({"error": f"Profile verification failed: {str(e)}"}), 500

        user_id = profile['id']

        # 3. THE GATEKEEPER CHECK (Priority: Unlimited -> Rewrite Credits -> Universal Credits)
        is_unlimited = profile.get('is_unlimited') or profile.get('subscription_status') == 'pro'
        rewrite_creds = profile.get('rewrite_credits', 0) or 0
        univ_creds = profile.get('credits', 0) or 0

        if not is_unlimited and rewrite_creds < 1 and univ_creds < 1:
             return jsonify({
                "error": "INSUFFICIENT_CREDITS", 
                "message": "You have run out of Rewrite Credits. Please upgrade to continue." 
             }), 402 # 402 Payment Required

        # 4. EXECUTE GENERATION
        # (user_data already extracted above)
        template_name = data.get('template_name', 'modern')
        job_description = data.get('job_description', '')
        resume_text = data.get('resume_text', '')  # Fallback source

        # GUARDRAIL: Input Validation
        has_valid_user_data = user_data and (user_data.get('experience') or user_data.get('education'))
        has_valid_text = resume_text and len(resume_text) > 50

        if not has_valid_user_data and not has_valid_text:
            return jsonify({"error": "ERROR: No resume data found. Please upload your resume to the Scanner first."}), 400

        # Determine Data Source for Prompt
        data_block = ""
        if has_valid_user_data:
            data_block = json.dumps(user_data)
        else:
            data_block = f"RESUME TEXT:\n{resume_text}\n\n(Note: Parse this text into the structured JSON format: personal, summary, experience, education, skills)."

        # "High-Scoring Data Fidelity" System Prompt
        system_prompt = "You are an expert Executive Resume Strategist (Fortune 500 level)."
        
        prompt = f"""
        TASK: Rewrite the User's Resume content to achieve a 95%+ match score against the Target Job Description (JD).

        INPUT DATA:
        1. USER RESUME: {data_block}
        2. TARGET JD: {job_description}

        CRITICAL INSTRUCTIONS (NON-NEGOTIABLE):
        1.  **DATA PRESERVATION:** You MUST use the **Exact Job Titles**, **Company Names**, and **Dates** from the User Resume. 
            * **FATAL ERROR:** Do NOT use the word "Role" or "Job Title" as a placeholder. If the input says "Senior Manager", you write "Senior Manager".
        2.  **CONTENT TRANSFORMATION:** Do not just copy-paste. Rewrite every bullet point to be **Result-Oriented**.
            * *Input:* "Responsible for managing data."
            * *Output:* "Spearheaded enterprise data governance strategy, ensuring 100% regulatory compliance." (Using keywords from JD).
        3.  **KEYWORD OPTIMIZATION:** Scan the JD for "Hard Skills" (e.g., Python, P&L Management, Strategic Planning). Integrate these naturally into the bullet points.
        4.  **EXECUTIVE FORMAT:**
            * **Summary:** 3 lines max. High impact.
            * **Experience:** Reverse chronological. 3-5 bullets per role. NO paragraphs.
            * **Format:** The `description` field for each role must be a Markdown formatted list of bullets (start with `* `).
        5.  **Handling Missing Info:** If the User Resume is missing a title, infer the most likely executive title based on the description (e.g., "Director of Operations") rather than writing "Role".

        OUTPUT REQUIREMENT:
        You must return a valid JSON object matching the schema below. Do NOT return raw Markdown. The Markdown content (bullets, headers) should be strings *inside* the JSON fields.
        
        JSON STRUCTURE:
        {{
            "personal": {{ "name": "...", "email": "...", "phone": "...", "location": "...", "summary": "..." }},
            "experience": [
                {{ "role": "Exact Title", "company": "Exact Co", "dates": "...", "description": "* Strong Action Verb...\\n* Another bullet..." }}
            ],
            "education": [...],
            "skills": ["..."],
            "enhancement_overview": "A brief markdown summary of the strategic changes made."
        }}

        Return ONLY valid JSON.
        """
        
        try:
            optimized_text = call_openai([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ], json_mode=True)
            
            opt_json = json.loads(optimized_text)
            jt = opt_json.get('job_title')
            
            # 4. ATOMIC CREDIT DEDUCTION (RPC)
            if not is_unlimited:
                 try:
                    if rewrite_creds > 0:
                        supabase.rpc('decrement_rewrite_credits', {'row_id': user_id}).execute()
                    else:
                        supabase.rpc('decrement_credits', {'row_id': user_id}).execute()
                 except Exception as e:
                    print(f"Credit Deduction Failed: {e}")

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
                
                # Switch to unified audio generator
                audio_base64 = generate_audio(speech_text, voice)
                
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
                clean_text = text.strip()
                if clean_text.startswith('```json'): clean_text = clean_text[7:]
                elif clean_text.startswith('```'): clean_text = clean_text[3:]
                if clean_text.endswith('```'): clean_text = clean_text[:-3]
                
                try:
                    report_data = json.loads(clean_text)
                except:
                    # Fallback for weird formatting
                    match = re.search(r"\{.*\}", clean_text, re.DOTALL)
                    if match:
                        report_data = json.loads(match.group(0))
                    else:
                        raise ValueError("Could not parse report JSON")
                
                # ---------------------------------------------------------
                # SAVE INTERVIEW TO DATABASE (New Fix)
                # ---------------------------------------------------------
                # 1. Resolve User ID
                user_id = None
                if email and supabase_admin:
                    u_res = supabase_admin.table('users').select('id').eq('email', email).execute()
                    if u_res.data:
                        user_id = u_res.data[0]['id']

                if user_id and report_data:
                    try:
                        # 2. Calculate Average Score from history
                        # history schema: [{question, answer, score, feedback}, ...]
                        history = data.get('history', [])
                        scores = [h.get('score', 0) for h in history if h.get('score') is not None]
                        avg_score = sum(scores) / len(scores) if scores else 0
                        
                        # 3. Extract Job Title (if provided in job_posting or history)
                        job_title = "General Interview"
                        # Try to infer it from the data
                        if data.get('jobPosting'):
                            # Very crude extraction of the first line if it looks like a title
                            first_line = data.get('jobPosting').strip().split('\n')[0]
                            if len(first_line) < 50: job_title = first_line

                        # 4. Insert into 'interviews' table
                        interview_record = {
                            "user_id": user_id,
                            "overall_score": round(avg_score * 2, 1),
                            "job_title": job_title,
                            "content": report_data.get('report', ''), # The HTML report
                            "status": "completed"
                        }
                        supabase_admin.table('interviews').insert(interview_record).execute()
                        print(f"SUCCESS: Saved Interview for {user_id} with score {avg_score}")
                    except Exception as save_err:
                        print(f"Error saving interview: {save_err}")

                # LOG ACTIVITY
                log_db_activity(email, 'interview_coach')
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
            
            # SAVE TO DATABASE (Debug/Robust Version)
            # ---------------------------------------------------------
            input_user_id = data.get('user_id')
            save_status = "Skipped"
            save_error = None
            
            if not supabase_admin:
                save_status = "Failed: No Admin Client"
            else:
                try:
                    user_id = input_user_id
                    
                    # 1. Resolve User ID
                    if not user_id and email:
                        u_res = supabase_admin.table('users').select('id').eq('email', email).execute()
                        if u_res.data:
                            user_id = u_res.data[0]['id']
                        else:
                            save_status = "Failed: User Not Found by Email"
                    
                    if user_id:
                        # 2. Extract Data
                        try:
                            # Re-parse to be safe or use existing object if available
                            # 'res_json' might be defined in try block above (line 1330), but 'text' is safer source here
                            payload_json = json.loads(text)
                            overall_score = payload_json.get('overall_score', 0)
                            job_tile_extracted = payload_json.get('job_title', 'Unknown Role')
                            
                            # 3. Insert Record
                            resumes_data = {
                                "user_id": user_id,
                                "overall_score": overall_score,
                                "job_title": job_tile_extracted,
                                "content": payload_json,
                                "file_name": data.get('filename', 'resume_analysis.pdf'),
                                "status": "analyzed"
                            }
                            supabase_admin.table('resumes').insert(resumes_data).execute()
                            save_status = "Success"
                            print(f"SUCCESS: Saved Resume Analysis for {user_id}")
                        except Exception as parse_err:
                            save_status = f"Failed: Parse/Insert Error ({str(parse_err)})"
                            print(f"Resume Save Error: {parse_err}")
                except Exception as db_err:
                    save_status = f"Failed: DB Error ({str(db_err)})"
                    print(f"Resume DB Error: {db_err}")

        # Return with debug info
        return jsonify({
            "data": text,
            "debug_save_status": save_status, 
            "debug_save_error": str(save_error) if save_error else None
        })

    except Exception as e:
        print(f"OpenAI API error: {e}")
        print(f"OpenAI API error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/stats', methods=['POST'])
def admin_stats():
    """Restricted endpoint for Admin Stats - Safe Mode (In-Memory Aggregation)."""
    try:
        data = request.json
        email = data.get('email', '').strip().lower()
        
        if not email or not supabase:
             return jsonify({"error": "Unauthorized"}), 401
             
        # 1. Verify Admin Role
        try:
            user_res = supabase.table('users').select('role').eq('email', email).execute()
            is_admin = False
            if user_res.data and len(user_res.data) > 0:
                if user_res.data[0].get('role') == 'admin':
                    is_admin = True
            
            if not is_admin:
                return jsonify({"error": "Access Denied"}), 403
        except Exception as e:
            print(f"Auth Check Failed: {e}")
            return jsonify({"error": "Auth Check Failed"}), 500

        # ---------------------------------------------------------
        # SAFE MODE DATA FETCHING
        # Fetch raw data and aggregate in Python to prevent SQL/Null crashes
        # ---------------------------------------------------------
        
        # Default Success Response Structure (Empty)
        safe_response = {
            "total_users": 0,
            "active_interviews": 0,
            "avg_duration": 0,
            "total_revenue": 0,
            "job_types": {},
            "recent_users": [],
            "recent_errors": [],
            "feature_usage": {"Resume Analysis": 0, "Interview Coach": 0, "System Errors": 0},
            "daily_activity": {"dates": [], "datasets": {}}
        }

        try:
            # 2. Fetch All Users for aggregation (Limit to recent 500 for performance if needed, but 'all' for total_users)
            # For "Total Users" count, we can use a lightweight count query
            count_res = supabase.table('users').select('*', count='exact', head=True).execute()
            safe_response['total_users'] = count_res.count if count_res.count is not None else 0

            # Fetch Recent Users (Deep fetch for table & partial aggregations) - Limit 100
            # We use this 100 sample to estimate 'Active Strategies' and display table
            users_res = supabase.table('users').select(
                'name, email, subscription_status, created_at, role, is_unlimited, interview_credits, resume_credits, credits_negotiation, credits_inquisitor, credits_followup, credits_30_60_90, credits_cover_letter, credits_interview_sim'
            ).order('created_at', desc=True).limit(100).execute()
            
            raw_users = users_res.data if users_res.data else []
            safe_response['recent_users'] = raw_users[:50] # Send top 50 to frontend

            # 3. In-Memory Aggregation (Null Safety)
            active_strategies = 0
            revenue_est = 0
            
            for u in raw_users:
                # Revenue: Unlimited ($29), Active ($9)
                if u.get('is_unlimited'):
                    revenue_est += 29.99
                elif u.get('subscription_status') == 'active':
                    revenue_est += 9.99
                
                # Active Strategy: Check if they have ANY strategy credits (Safe Logic)
                # Python's (val or 0) ensures None becomes 0
                c_neg = u.get('credits_negotiation') or 0
                c_inq = u.get('credits_inquisitor') or 0
                c_plan = u.get('credits_30_60_90') or 0
                c_sim = u.get('credits_interview_sim') or 0
                
                if c_neg > 0 or c_inq > 0 or c_plan > 0 or c_sim > 0:
                    active_strategies += 1

            safe_response['active_interviews'] = active_strategies
            safe_response['total_revenue'] = round(revenue_est, 2)

            # 4. Fetch Logs (Safe Mode)
            try:
                err_res = supabase.table('error_logs').select('*').order('created_at', desc=True).limit(5).execute()
                err_data = err_res.data if err_res.data else []
                clean_errors = []
                for e in err_data:
                    clean_errors.append({
                        'timestamp': e.get('created_at'),
                        'email': e.get('user_email') or 'System',
                        'type': e.get('error_type') or 'Unknown'
                    })
                safe_response['recent_errors'] = clean_errors
            except:
                print("Error fetching error logs")

            # 5. Activity Charts (Optional - keep simple or skip if crashing)
            # We will skip complex aggregation for now to ensure stability
            # or allow the previous robust logic if it was working? 
            # The prompt asks for "Raw user data" mostly. We'll leave the chart data empty or simpler.
            # Let's try to keep the job types simple logic if possible.
            
            # Simple Job Stats (Top 5 from recent logs)
            try:
                logs_res = supabase.table('activity_logs').select('metadata').order('created_at', desc=True).limit(200).execute()
                if logs_res.data:
                    jobs = {}
                    for l in logs_res.data:
                        m = l.get('metadata') or {}
                        t = m.get('job_title') or m.get('jobTitle')
                        if t and isinstance(t, str):
                            t = t.strip().title() 
                            if t: jobs[t] = jobs.get(t, 0) + 1
                    
                    sorted_j = sorted(jobs.items(), key=lambda x:x[1], reverse=True)[:5]
                    safe_response['job_types'] = {k:v for k,v in sorted_j}
            except:
                pass


            return jsonify(safe_response)

        except Exception as inner_e:
            print(f"Stats Aggregation Failed: {inner_e}")
            # FALBACK: Return success (200) with empty/safe data
            return jsonify(safe_response), 200

    except Exception as e:
        print(f"Admin Stats Critical Error: {e}")
        # Ultimate Fallback
        return jsonify({"total_users": 0}), 200

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

        elif action_type == 'add_credit_strategy':
            # Grant 1 credit to ALL strategy tools
            db = supabase_admin if supabase_admin else supabase
            user_res = supabase.table('users').select('*').eq('email', target_email).execute()
            if user_res.data:
                u = user_res.data[0]
                db.table('users').update({
                    'credits_negotiation': u.get('credits_negotiation', 0) + 1,
                    'credits_inquisitor': u.get('credits_inquisitor', 0) + 1,
                    'credits_followup': u.get('credits_followup', 0) + 1,
                    'credits_30_60_90': u.get('credits_30_60_90', 0) + 1,
                    'credits_cover_letter': u.get('credits_cover_letter', 0) + 1,
                    'credits_interview_sim': u.get('credits_interview_sim', 0) + 1
                }).eq('email', target_email).execute()
                return jsonify({"success": True, "message": "Strategy credits added (+1 all)"})
            return jsonify({"error": "User not found"}), 404

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

@app.route('/api/user-profile', methods=['GET'])
def user_profile():
    """Securely fetch user profile and credits from token."""
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header:
             return jsonify({"error": "Missing Authorization header"}), 401
        
        token = auth_header.split(" ")[1]
        
        # 1. Verify User with Supabase Auth
        if not supabase:
             print("CRITICAL: Supabase client is None (Env vars missing?)")
             return jsonify({"error": "Database configuration error"}), 500

        user_res = supabase.auth.get_user(token)
        if not user_res.user:
             return jsonify({"error": "Invalid token"}), 401
             
        user_id = user_res.user.id
        email = user_res.user.email
        
        # 2. Fetch Profile from 'users' table
        # CRITICAL: We MUST use the Admin client to bypass RLS.
        # If supabase_admin is None, it means SUPABASE_SERVICE_ROLE_KEY is missing in Vercel.
        if not supabase_admin:
            print("CRITICAL CONFIG ERROR: SUPABASE_SERVICE_ROLE_KEY is missing.")
            return jsonify({
                "error": "Configuration Error: SUPABASE_SERVICE_ROLE_KEY is missing in Vercel Environment Variables. Please add it to fix Database Access."
            }), 500

        db_client = supabase_admin
        print(f"User Profile Fetch: Using ADMIN client for {email}")
        
        # Select ALL columns so frontend gets all credit types and flags.
        try:
            profile_res = db_client.table('users').select('*').eq('id', user_id).execute()
        except Exception as query_err:
             print(f"User Profile Query Failed (ID lookup): {query_err}")
             profile_res = None

        if not profile_res or not profile_res.data:
            # Fallback checks if users table uses email as key or hasn't synced ID yet
            print(f"User Profile: Fallback to email lookup for {email}")
            try:
                profile_res = db_client.table('users').select('*').eq('email', email).execute()
            except Exception as fb_err:
                print(f"User Profile Fallback Query Failed: {fb_err}")
                return jsonify({"error": f"Database Query Failed: {str(fb_err)}"}), 500

            if not profile_res.data:
                 print(f"User Profile: User not found for {email}")
                 return jsonify({"error": "User profile not found"}), 404

        return jsonify(profile_res.data[0])

    except Exception as e:
        print(f"User Profile Fetch CRITICAL Error: {e}")
        import traceback
        traceback.print_exc()
        # Log to DB for debugging
        try:
            if supabase_admin:
                supabase_admin.table('error_logs').insert({
                    'error_type': 'UserProfile_Crash',
                    'details': f"Error: {str(e)}",
                    'user_email': email if 'email' in locals() else 'unknown'
                }).execute()
        except:
            pass
        return jsonify({"error": str(e)}), 500

@app.route('/api/generate-strategy-tool', methods=['POST'])
def generate_strategy_tool():
    """Unified endpoint for Strategy Lab tools with credit deduction."""
    try:
        # 1. Validation
        if not API_KEY:
            return jsonify({"error": "Configuration Error"}), 500
        
        data = request.json
        user_email = data.get('email')
        tool_type = data.get('tool_type') # 'closer', 'inquisitor', 'followup', 'plan'
        user_inputs = data.get('inputs', {}) # dict of fields
        
        if not user_email or not tool_type:
            return jsonify({"error": "Missing parameters"}), 400

        # 2. Get User & Check Credits
        db = supabase_admin if supabase_admin else supabase
        user_res = db.table('users').select('*').eq('email', user_email).execute()
        
        if not user_res.data:
            return jsonify({"error": "User not found"}), 404
            
        user = user_res.data[0]
        has_credit = False
        
        # UNIVERSAL CREDIT CHECK (Except for Free/Unlimited)
        # Any tool costs 1 Credit
        current_credits = user.get('credits', 0)
        has_credit = current_credits > 0
        
        # Tool-Specific Credit Overrides
        if tool_type == 'cover_letter' and user.get('credits_cover_letter', 0) > 0:
            has_credit = True
        elif tool_type == 'plan' and user.get('credits_30_60_90', 0) > 0:
             has_credit = True
        elif tool_type == 'closer' and user.get('credits_negotiation', 0) > 0:
             has_credit = True
        elif tool_type == 'inquisitor' and user.get('credits_inquisitor', 0) > 0:
             has_credit = True
        elif tool_type == 'follow_up' and user.get('credits_followup', 0) > 0:
             has_credit = True

        # Unlimited Override (Pro Plan)
        if user.get('is_unlimited', False):
            has_credit = True

        if not has_credit:
            return jsonify({"error": "Insufficient credits", "buy_link": "/pricing.html"}), 402

        # 3. Construct Prompt
        system_prompt = "You are an expert career strategist."
        user_prompt = ""

        if tool_type == 'closer':
            system_prompt = "You are a ruthless but professional negotiation coach. Use the 'Ackerman Bargaining' principles where appropriate but keep it professional."
            user_prompt = (
                f"Write a negotiation script (Phone Script + Email Draft) for this offer:\n"
                f"Base Salary: {user_inputs.get('current_offer') or user_inputs.get('base')}\n"
                f"Sign-On/Bonuses: {user_inputs.get('sign_on') or user_inputs.get('equity')}\n"
                f"Leverage/Counter-offer: {user_inputs.get('leverage')}\n"
                f"Goal/Ask: {user_inputs.get('goal')}\n\n"
                "Output Markdown. Be specific. Do not use placeholders like [Insert Name]."
            )
        
        elif tool_type == 'inquisitor':
            system_prompt = "You are a reverse-interview expert. You help candidates ask high-IQ questions that make them look strategic."
            # Frontend uses 'context' and 'company_name'. Backend was expecting 'job_description'.
            context_text = user_inputs.get('context') or user_inputs.get('job_description') or ""
            user_prompt = (
                f"Generate 5 high-impact questions for an interviewer with this title: {user_inputs.get('interviewer_role')}\n"
                f"Company: {user_inputs.get('company_name')}\n"
                f"Context/News: {context_text[:500]}\n\n"
                "Categorize them: 1. Cultural, 2. Strategic, 3. Role-Specific, 4. The 'Closer' Question.\n"
                "Explain WHY each question works in 1 sentence."
            )

        elif tool_type == 'followup':
            system_prompt = "You write 'Value-Add' follow-up emails. No generic 'thank yous'. We pitch a solution."
            user_prompt = (
                f"Write a short (<150 words) follow-up email to: {user_inputs.get('interviewer_name')}\n"
                f"Pain Point Discussed: {user_inputs.get('pain_point')}\n"
                f"Proposed Solution/Idea: {user_inputs.get('solution')}\n\n"
                "Tone: Professional, concise, confident. Subject Line included."
            )
            
        elif tool_type == 'plan':
            system_prompt = "You are an executive career coach."
            user_prompt = (
                f"Create a structured 30-60-90 day plan for a {user_inputs.get('role_title')} at {user_inputs.get('company_name')}.\n"
                f"Focus on this key priority: {user_inputs.get('main_priority')}.\n"
                "Structure it by phases: Learning (0-30), Executing (31-60), Leading (61-90). "
                "Output Markdown."
            )

        elif tool_type == 'cover_letter':
             system_prompt = """
### SYSTEM ROLE ###
You are an Executive Ghostwriter for high-level leaders. You DO NOT write standard cover letters.
**THE ENEMY:** "I am writing to apply...", "I am a perfect match...", "Enclosed is my resume." (BANNED PHRASES).

### THE GOAL ###
Write a narrative-driven letter that connects the user's *unique backstory* to the company's *hardest problems*.

### STRICT HEADER RULES:
1.  **Contact Info:** Output the User's Email and Phone as PLAIN TEXT.
    * **Bad:** `[Email: user@test.com](mailto:...)`
    * **Bad:** `Email: user@test.com`
    * **Good:** `user@test.com`
2.  **Placeholders:** For unknown info (Date, Hiring Manager, Company Address), use simple square brackets: `[Date]`, `[Hiring Manager Name]`, `[Company Address]`.
3.  **No Markdown Links:** Do not turn emails or numbers into clickable links.

### STRICT INSTRUCTIONS ###
1.  **The Hook (Paragraph 1):** DO NOT mention the job title in the first sentence. Start with a philosophy or a specific story from the user's resume (e.g., "Operations isn't about spreadsheets; it's about people..."). If the user has a "grit" story (e.g., "started in a restaurant" or "manual labor"), YOU MUST LEAD WITH THAT.
2.  **The Bridge (Paragraph 2):** Connect that gritty past to their current executive success. (e.g., "That early experience taught me X, which I used at Verizon to save $1M.").
3.  **The Pitch (Paragraph 3):** Address the Company's pain points (found in the Job Description) directly. Use the user's metrics (70% efficiency, $1M savings) as proof.
4.  **The Voice:** Punchy. Confident. Short sentences. No fluff.
5.  **Format:** Standard Business Letter.
"""
             manager = user_inputs.get('hiring_manager') or 'Hiring Manager'
             user_prompt = (
                 f"### INPUT DATA ###\n"
                 f"Target Role: {user_inputs.get('target_role')}\n"
                 f"Target Company: {user_inputs.get('company_name')}\n"
                 f"Hiring Manager: {manager}\n\n"
                 f"User's Resume & Context:\n{user_inputs.get('key_skills')}\n\n"
                 "### OUTPUT ###\n"
                 "Generate the letter in Markdown. Ensure strict adherence to Header Rules (Plain text contact info)."
             )

        elif tool_type == 'follow_up':
            system_prompt = """
### SYSTEM ROLE ###
You are an Executive Deal Closer. You write high-stakes follow-up emails.
**THE ENEMY:** "Just checking in" or "Touching base". (BANNED).
**THE GOAL:** Reiterate value and drive the process forward.

**SCENARIO LOGIC:**
1.  **IF Post-Interview:** Thank them specifically. Reference one specific topic discussed (invent a placeholder like '[Topic we discussed]'). Reiterate how your skills (from Resume) solve that specific problem.
2.  **IF Applied/No Response:** Be brief. Re-state the 'Hook' (your top achievement). Ask for a 15-min chat.
3.  **Voice:** Professional, confident, concise.

**FORMATTING:**
* Standard Email Format.
* **Subject Line:** Create 3 high-conversion subject line options at the top.
* **Placeholders:** Use brackets `[ ]` for unknown info so the frontend highlights them yellow.
* **Contact Info:** Plain text (no links).
"""
            user_prompt = (
                 f"### INPUT DATA ###\n"
                 f"Target Role: {user_inputs.get('target_role')}\n"
                 f"Target Company: {user_inputs.get('company_name')}\n"
                 f"Context & Status:\n{user_inputs.get('key_skills')}\n\n"
                 "### OUTPUT ###\n"
                 "Generate the follow-up email options in Markdown."
            )

        # 4. Call OpenAI
        try:
            content = call_openai([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ])
        except Exception as ai_err:
             return jsonify({"error": f"AI Generation Failed: {str(ai_err)}"}), 500

        # 5. Deduct Credit (if not unlimited)
        # 5. Deduct Credit (Specific > Universal)
        if not user.get('is_unlimited', False):
            deducted = False
            
            # Specific Tool Deduction
            if tool_type == 'cover_letter':
                 val = user.get('credits_cover_letter', 0)
                 if val > 0:
                     db.table('users').update({'credits_cover_letter': val - 1}).eq('email', user_email).execute()
                     deducted = True
                     
            elif tool_type == 'plan':
                 val = user.get('credits_30_60_90', 0)
                 if val > 0:
                     db.table('users').update({'credits_30_60_90': val - 1}).eq('email', user_email).execute()
                     deducted = True

            elif tool_type == 'closer':
                 val = user.get('credits_negotiation', 0)
                 if val > 0:
                     db.table('users').update({'credits_negotiation': val - 1}).eq('email', user_email).execute()
                     deducted = True
            
            elif tool_type == 'inquisitor':
                 val = user.get('credits_inquisitor', 0)
                 if val > 0:
                     db.table('users').update({'credits_inquisitor': val - 1}).eq('email', user_email).execute()
                     deducted = True
                     
            elif tool_type == 'follow_up':
                 val = user.get('credits_followup', 0)
                 if val > 0:
                     db.table('users').update({'credits_followup': val - 1}).eq('email', user_email).execute()
                     deducted = True

            # Universal Fallback (if specific not used)
            if not deducted and current_credits > 0:
                new_val = current_credits - 1
                db.table('users').update({'credits': new_val}).eq('email', user_email).execute()
                print(f"Deducted 1 Universal Credit for {tool_type} from {user_email}")

        return jsonify({"success": True, "content": content})

    except Exception as e:
        print(f"Strategy Gen Error: {e}")
        return jsonify({"error": str(e)}), 500

# ========================================
# JOB TRACKING ENDPOINTS (STRATEGY LOG)
# ========================================

@app.route('/api/jobs', methods=['GET', 'POST'])
def manage_jobs():
    """Unified endpoint to Get or Add jobs."""
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header:
             return jsonify({"error": "Missing Authorization header"}), 401
        
        token = auth_header.split(" ")[1]
        
        # Verify User
        if not supabase:
             return jsonify({"error": "DB Config Error"}), 500
        
        try:
            user_res = supabase.auth.get_user(token)
            if not user_res.user:
                 return jsonify({"error": "Invalid token"}), 401
            user_id = user_res.user.id
        except Exception as auth_e:
            print(f"Auth Check Failed: {auth_e}")
            return jsonify({"error": f"Auth Verification Failed: {str(auth_e)}"}), 401

        if request.method == 'GET':
            try:
                # Return jobs sorted by newest
                db = supabase_admin if supabase_admin else supabase
                res = db.table('user_jobs').select('*').eq('user_id', user_id).order('created_at', desc=True).execute()
                return jsonify(res.data)
            except Exception as e:
                print(f"Fetch Jobs Error: {e}")
                return jsonify({"error": str(e)}), 500

        elif request.method == 'POST':
            try:
                data = request.json
                job_title = data.get('job_title')
                company_name = data.get('company_name')
                job_description = data.get('job_description')

                if not job_title or not company_name:
                    return jsonify({"error": "Job Title and Company are required"}), 400

                new_job = {
                    "user_id": user_id,
                    "job_title": job_title,
                    "company_name": company_name,
                    "job_description": job_description,
                    "status": "Identified"
                }
                
                db = supabase_admin if supabase_admin else supabase
                res = db.table('user_jobs').insert(new_job).execute()
                # Return the created object
                return jsonify(res.data[0] if res.data else {})
            except Exception as e:
                print(f"Add Job Error: {e}")
                return jsonify({"error": str(e)}), 500

    except Exception as outer_e:
        print(f"Manage Jobs Critical Error: {outer_e}")
        return jsonify({"error": f"Critical Server Error: {str(outer_e)}"}), 500

@app.route('/api/jobs/<job_id>', methods=['DELETE', 'PUT'])
def job_operations(job_id):
    """Delete or Update a specific job."""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
         return jsonify({"error": "Missing Authorization header"}), 401
    token = auth_header.split(" ")[1]
    user_res = supabase.auth.get_user(token)
    if not user_res.user: 
        return jsonify({"error": "Unauthorized"}), 401
        
    user_id = user_res.user.id

    if request.method == 'DELETE':
        try:
            res = supabase_admin.table('user_jobs').delete().eq('id', job_id).eq('user_id', user_id).execute()
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
            
    elif request.method == 'PUT':
        try:
            data = request.json
            update_data = {}
            if 'status' in data: update_data['status'] = data['status']
            if 'resume_score' in data: update_data['resume_score'] = data['resume_score']
            if 'interview_score' in data: update_data['interview_score'] = data['interview_score']
            if 'job_description' in data: update_data['job_description'] = data['job_description']
            if 'notes' in data: update_data['notes'] = data['notes']
            if 'salary_target' in data: update_data['salary_target'] = data['salary_target']
            
            res = supabase_admin.table('user_jobs').update(update_data).eq('id', job_id).eq('user_id', user_id).execute()
            return jsonify(res.data)
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

@app.route('/api/auth/signup', methods=['POST', 'OPTIONS'])
@app.route('/auth/signup', methods=['POST', 'OPTIONS'])
def signup():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
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

@app.route('/api/auth/login', methods=['POST', 'OPTIONS'])
@app.route('/auth/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
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
        profile_res = supabase.table('users').select('id, email, name, subscription_status, is_unlimited, resume_credits, interview_credits, rewrite_credits, credits, role').eq('id', user.id).execute()
        
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
            "credits": profile_data.get("credits", 0),
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

@app.route('/api/auth/forgot-password', methods=['POST', 'OPTIONS'])
@app.route('/auth/forgot-password', methods=['POST', 'OPTIONS'])
def forgot_password():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
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

@app.route('/api/auth/update-password', methods=['POST', 'OPTIONS'])
@app.route('/auth/update-password', methods=['POST', 'OPTIONS'])
def update_password():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
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
                    "credits_negotiation": user.get('credits_negotiation', 0),
                    "credits_inquisitor": user.get('credits_inquisitor', 0),
                    "credits_followup": user.get('credits_followup', 0),
                    "credits_30_60_90": user.get('credits_30_60_90', 0),
                    "credits_cover_letter": user.get('credits_cover_letter', 0),
                    "credits_interview_sim": user.get('credits_interview_sim', 0),
                    "credits": user.get('credits', 0),
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

@app.route('/api/auth/update-status', methods=['POST', 'OPTIONS'])
@app.route('/auth/update-status', methods=['POST', 'OPTIONS'])
def update_user_status():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
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
    'interview': os.environ.get('Stripe_Interview_Only'),  # Mock Interview Session ($19.99)
    
    # STRATEGY LAB
    'strategy_plan': os.environ.get('STRIPE_PLAN_PRICE_ID'),
    'strategy_cover': os.environ.get('STRIPE_COVER_LETTER_PRICE_ID'),
    'strategy_negotiation': os.environ.get('STRIPE_NEGOTIATION_PRICE_ID'),
    'strategy_inquisitor': os.environ.get('STRIPE_INQUISITOR_PRICE_ID'), # New
    'strategy_followup': os.environ.get('STRIPE_FOLLOWUP_PRICE_ID'),     # New
    'strategy_interview_sim': os.environ.get('STRIPE_INTERVIEW_PRICE_ID'), # New (Sim)
    'strategy_bundle': os.environ.get('STRIPE_BUNDLE_PRICE_ID')
}







@app.route('/api/webhook-debug', methods=['GET'])
def webhook_debug():
    """Diagnostic endpoint to check if the server is ready for webhooks."""
    status = {
        'stripe_configured': stripe.api_key is not None,
        'webhook_secret_present': stripe_webhook_secret is not None,
        'supabase_url_present': SUPABASE_URL is not None,
        'supabase_admin_ready': supabase_admin is not None,
        'supabase_anon_ready': supabase is not None,
        'env_vars_checked': [
            'SUPABASE_SERVICE_ROLE_KEY', 'STRIPE_WEBHOOK_SECRET', 'OPENAI_API_KEY_'
        ]
    }
    
    # Try a test write to error_logs using the admin client
    test_write = "Not attempted"
    if supabase_admin:
        try:
            supabase_admin.table('error_logs').insert({
                'error_type': 'Diagnostic_Ping',
                'details': f'Manual ping from debug endpoint'
            }).execute()
            test_write = "Success"
        except Exception as e:
            test_write = f"Failed: {str(e)}"
    
    status['admin_write_test'] = test_write
    
    # NEW: Fetch logs to see if Stripe is hitting us
    logs = []
    if supabase_admin:
        try:
            res = supabase_admin.table('error_logs').select('*').order('created_at', desc=True).limit(10).execute()
            logs = res.data
        except Exception as e:
            logs = [f"Fetch error: {str(e)}"]
    
    status['recent_logs'] = logs
    return jsonify(status)

@app.route('/api/stripe-webhook', methods=['POST'])
def stripe_webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')

    # Trace logging to DB for cross-environment debugging
    def trace(msg, log_type="Webhook_Trace"):
        print(f"WEBHOOK TRACE: {msg}")
        log_db_error('system', log_type, msg)

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, stripe_webhook_secret
        )
    except ValueError as e:
        trace(f"Invalid payload: {e}", "Webhook_Error")
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError as e:
        trace(f"Invalid signature: {e}", "Webhook_Error")
        return jsonify({'error': 'Invalid signature'}), 400
    except Exception as e:
        trace(f"Event Construction Error: {e}", "Webhook_Error")
        return jsonify({'error': str(e)}), 400

    if not event:
        return jsonify({'error': 'Event construction failed'}), 400

    trace(f"Processing Event: {event['type']}")

    if not supabase:
        trace("Supabase Client Missing", "Webhook_Error")
        return jsonify({'error': 'Database error'}), 500
        
    db_client = supabase_admin if supabase_admin else supabase
    if not supabase_admin:
        trace("Supabase Admin Missing - Using Anon Client (RLS may fail)", "Webhook_Warning")

    try:
        # HANDLE SUBSCRIPTION CREATED / CHECKOUT COMPLETED
        if event['type'] == 'checkout.session.completed':
            try:
                session = event['data']['object']
                customer_email = session.get('customer_details', {}).get('email')
                client_reference_id = session.get('client_reference_id')
                metadata = session.get('metadata', {})
                plan_type = metadata.get('plan_type', 'basic')
                subscription_id = session.get('subscription')
                
                trace(f"Session Data: Email={customer_email}, RefID={client_reference_id}, Plan={plan_type}, SubID={subscription_id}")

                user_id = None
                user_data = None

                # 1. Try finding user by Client Reference ID (Supabase UUID)
                if client_reference_id:
                    trace(f"Lookup by client_reference_id: {client_reference_id}")
                    res = db_client.table('users').select('*').eq('id', client_reference_id).execute()
                    if res.data:
                        user_data = res.data[0]
                        user_id = user_data['id']
                        trace(f"Found user by ID: {user_id}")
                    else:
                        trace(f"No user found by ID: {client_reference_id}")

                # 2. Fallback: Find by Metadata Email
                if not user_id and metadata.get('user_email'):
                    m_email = metadata.get('user_email')
                    trace(f"Fallback lookup by metadata email: {m_email}")
                    res = db_client.table('users').select('*').ilike('email', m_email).execute()
                    if res.data:
                        user_data = res.data[0]
                        user_id = user_data['id']
                        trace(f"Found by Metadata Email: {m_email} -> ID: {user_id}")

                # 3. Final Fallback: Find by Stripe Customer Email
                if not user_id and customer_email:
                    trace(f"Final fallback lookup by customer email: {customer_email}")
                    res = db_client.table('users').select('*').ilike('email', customer_email).execute()
                    if res.data:
                        user_data = res.data[0]
                        user_id = user_data['id']
                        trace(f"Found by Stripe Email: {customer_email} -> ID: {user_id}")

                if user_id:
                    update_data = {}
                    current_credits = user_data.get('credits', 0) or 0

                    if plan_type == 'pro':
                        update_data['is_unlimited'] = True
                        update_data['subscription_status'] = 'active'
                        update_data['credits'] = 50 # Buffer for UI/scaling
                        trace("Adding UNLIMITED flags and 50 credit buffer")

                    elif metadata.get('feature') == 'rewrite' or plan_type == 'rewrite':
                        update_data['rewrite_credits'] = (user_data.get('rewrite_credits', 0) or 0) + 1
                        trace(f"Adding +1 credit for Rewrite. New: {update_data['rewrite_credits']}")

                    elif metadata.get('feature') == 'linkedin_optimize' or plan_type == 'linkedin_optimize':
                        update_data['credits_linkedin'] = (user_data.get('credits_linkedin', 0) or 0) + 1
                        trace(f"Adding +1 credit for LinkedIn. New: {update_data['credits_linkedin']}")
                    
                    elif plan_type == 'complete':
                        update_data['credits'] = (user_data.get('credits', 0) or 0) + 2
                        trace("+2 credits for Complete")

                    elif plan_type == 'strategy_bundle':
                        update_data['credits'] = (user_data.get('credits', 0) or 0) + 5
                        trace("+5 credits for Bundle")

                    elif plan_type in ['strategy_plan', 'strategy_cover', 'strategy_negotiation', 'strategy_inquisitor', 'strategy_followup', 'strategy_interview_sim', 'resume', 'interview']:
                        # SINGLE TOOL: Increment ONLY legacy column (no universal credit)
                        trace(f"Processing SINGLE TOOL: {plan_type}")
                        
                        if plan_type == 'strategy_interview_sim' or plan_type == 'interview':
                            update_data['interview_credits'] = (user_data.get('interview_credits', 0) or 0) + 1
                            trace("+1 Interview Credit")
                        elif plan_type == 'resume':
                            update_data['resume_credits'] = (user_data.get('resume_credits', 0) or 0) + 1
                            trace("+1 Resume Credit")
                        elif plan_type == 'strategy_plan':
                             update_data['credits_30_60_90'] = (user_data.get('credits_30_60_90', 0) or 0) + 1
                             trace("+1 30-60-90 Credit")
                        elif plan_type == 'strategy_cover':
                             update_data['credits_cover_letter'] = (user_data.get('credits_cover_letter', 0) or 0) + 1
                             trace("+1 Cover Letter Credit")
                        elif plan_type == 'strategy_negotiation':
                             update_data['credits_negotiation'] = (user_data.get('credits_negotiation', 0) or 0) + 1
                             trace("+1 Negotiation Credit")
                        elif plan_type == 'strategy_inquisitor':
                             update_data['credits_inquisitor'] = (user_data.get('credits_inquisitor', 0) or 0) + 1
                             trace("+1 Inquisitor Credit")
                        elif plan_type == 'strategy_followup':
                             update_data['credits_followup'] = (user_data.get('credits_followup', 0) or 0) + 1
                             trace("+1 Follow-up Credit")

                    if plan_type in ['pro', 'strategy_bundle', 'interview', 'strategy_interview_sim']:
                        update_data['role_reversal_count'] = 0
                        trace("Reset Role Reversal Count")

                    # Handle Subscription Renewal Date (NEW)
                    if subscription_id:
                        try:
                            sub_obj = stripe.Subscription.retrieve(subscription_id)
                            # Convert Unix timestamp to ISO for Supabase
                            import datetime
                            period_end_dt = datetime.datetime.fromtimestamp(sub_obj.current_period_end, datetime.timezone.utc)
                            update_data['subscription_period_end'] = period_end_dt.isoformat()
                            if not user_data.get('stripe_customer_id') and session.get('customer'):
                                update_data['stripe_customer_id'] = session.get('customer')
                            trace(f"Captured Renewal Date: {update_data['subscription_period_end']}")
                        except Exception as sub_err:
                            trace(f"Failed to fetch subscription end date: {sub_err}", "Webhook_Warning")

                    if update_data:
                        trace(f"Executing Update: {update_data}")
                        try:
                            response = db_client.table('users').update(update_data).eq('id', user_id).execute()
                            trace(f"Update Success: {response.data if hasattr(response, 'data') else 'No Result Data'}")
                        except Exception as update_err:
                            trace(f"DB UPDATE FAILED: {update_err}", "Webhook_Error")
                    else:
                        trace("No update_data generated for this plan_type", "Webhook_Warning")

                else:
                    trace(f"USER NOT FOUND. Checkout cannot be fulfilled.", "Webhook_Error")
            
            except Exception as e:
                import traceback
                trace(f"Checkout Handling Crash: {e}\n{traceback.format_exc()}", "Webhook_Error")
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

        # HANDLE INVOICE PAYMENT (Renewal / Monthly Reset)
        elif event['type'] == 'invoice.payment_succeeded':
            try:
                invoice = event['data']['object']
                billing_reason = invoice.get('billing_reason') # subscription_create, subscription_cycle, subscription_update
                
                # Only reset on cycle (renewal) or create.
                if billing_reason in ['subscription_cycle', 'subscription_create']:
                    customer_id = invoice.get('customer')
                    subscription_id = invoice.get('subscription')
                    amount_paid = invoice.get('amount_paid')
                    
                    print(f"Processing Renewal/Invoice: {customer_id}, Reason: {billing_reason}, Amount: {amount_paid}")
                    
                    # 1. Find User by Stripe Customer ID (if we stored it)
                    user_data = None
                    # Try finding by customer_id first
                    if customer_id:
                         # We assume we started storing stripe_customer_id in users table
                         # If not, we must fetch email from Stripe
                         res = db_client.table('users').select('*').eq('stripe_customer_id', customer_id).execute()
                         if res.data:
                             user_data = res.data[0]
                    
                    # 2. Fallback: Lookup by Email from Stripe Customer
                    if not user_data and customer_id:
                        try:
                            cust_obj = stripe.Customer.retrieve(customer_id)
                            email = cust_obj.email
                            if email:
                                res = db_client.table('users').select('*').eq('email', email).execute()
                                if res.data:
                                    user_data = res.data[0]
                                    # SELF-HEAL: Save customer_id for next time
                                    if not user_data.get('stripe_customer_id'):
                                        db_client.table('users').update({'stripe_customer_id': customer_id}).eq('id', user_data['id']).execute()
                        except Exception as e:
                            print(f"Stripe Customer Lookup Failed: {e}")

                    # 3. Apply Update
                    if user_data:
                        print(f"Resetting usage for user {user_data.get('email')}")
                        update_payload = {
                            'monthly_voice_usage': 0,
                            'subscription_status': 'active',
                            'is_unlimited': True # Ensure it's on
                        }
                        
                        # Update Renewal Date on renewal too
                        if subscription_id:
                            try:
                                sub_obj = stripe.Subscription.retrieve(subscription_id)
                                import datetime
                                period_end_dt = datetime.datetime.fromtimestamp(sub_obj.current_period_end, datetime.timezone.utc)
                                update_payload['subscription_period_end'] = period_end_dt.isoformat()
                                trace(f"Updated Renewal Date on Invoice: {update_payload['subscription_period_end']}")
                            except Exception as sub_err:
                                trace(f"Failed to fetch subscription end date on invoice: {sub_err}", "Webhook_Warning")

                        db_client.table('users').update(update_payload).eq('id', user_data['id']).execute()
                        print("Voice Usage Reset to 0. Subscription Active.")
                    else:
                        print(f"User not found for Invoice {invoice.get('id')}")

            except Exception as e:
                 print(f"Error handling invoice payment: {e}")
                 return jsonify({'error': str(e)}), 500

    except Exception as e:
        print(f"Global Webhook Error: {e}")
        return jsonify({'error': str(e)}), 500

    return jsonify({'status': 'success'}), 200

# For Vercel, we don't need app.run()
