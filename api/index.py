from flask import Flask, request, jsonify
import os
import json
import base64
# External libs will be lazy imported to prevent boot crashes
# from supabase import create_client, Client
# import stripe

app = Flask(__name__)

# 0. SANITY CHECK ROUTE (No Deps)
@app.route('/api/health')
def health_check():
    return jsonify({"status": "ok", "message": "Server is bootable"}), 200

# 1. SETUP SUPABASE
# 1. SETUP SUPABASE (Lazy Loader)
def get_supabase():
    from supabase import create_client, Client
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    return create_client(url, key)

# No top-level init
# try:
#     SUPABASE_URL = os.environ.get("SUPABASE_URL")
#     ...
# except Exception as e:
#     print(f"Supabase Init Error: {e}")

# 3. THE JOBS ROUTE (Secure Mode)
@app.route('/api/jobs', methods=['GET', 'POST'])
def manage_jobs():
    import traceback
    # 1. Extract Token
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"error": "Missing Authorization Header"}), 401
    
    try:
        token = auth_header.split(" ")[1]
    except IndexError:
        return jsonify({"error": "Invalid Token Format"}), 401

    # 2. Verify User (Gatekeeper)
    # Use the global client to verify the token is valid and get the ID.
    try:
        # Lazy Load Supabase
        supabase = get_supabase()
        user_response = supabase.auth.get_user(token)
        user_id = user_response.user.id
    except Exception as e:
        print(f"Auth Verification Failed: {e}")
        return jsonify({"error": "Unauthorized"}), 401
        
    # 3. Create RLS-Compatible Client
    # We create a new client and explicitly set the auth token for PostgREST.
    try:
        from supabase import create_client, Client
        SUPABASE_URL = os.environ.get("SUPABASE_URL")
        SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
        
        user_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        user_client.postgrest.auth(token)
    except Exception as e:
        print(f"Client Handshake Error: {e}")
        return jsonify({"error": f"Server Error: {str(e)}"}), 500

    # B. GET Request (Loading the Dashboard)
    if request.method == 'GET':
        try:
            # Query AS THE USER
            # Reverted to user_jobs. Map job_intel to notes for frontend compatibility.
            response = user_client.table('user_jobs').select(
                "id,job_title,company_name,status,job_description,job_intel,salary_target"
            ).eq('user_id', user_id).execute()

            clean_jobs = []
            for job in response.data:
                clean_jobs.append({
                    "id": job.get('id'),
                    "job_title": job.get('job_title', ''),     
                    "company_name": job.get('company_name', ''), 
                    "status": job.get('status', 'Engage'),
                    "job_description": job.get('job_description', ''),
                    "notes": job.get('job_intel', ''), # Map DB 'job_intel' -> API 'notes'
                    "salary_target": job.get('salary_target', '')
                })
            return jsonify(clean_jobs), 200
        except Exception as e:
            print(f"DB Error: {e}")
            return jsonify([]), 200

    # C. POST Request (Initiating Campaign)
    if request.method == 'POST':
        try:
            data = request.json
            new_job = {
                "user_id": user_id,
                "job_title": data.get('job_title', 'New Role'),
                "company_name": data.get('company_name', 'New Co'),
                "status": "Engage",
                "job_description": data.get('job_description', '')
                # job_intel starts empty or null
            }
            # Insert AS THE USER
            res = user_client.table('user_jobs').insert(new_job).execute()
            return jsonify(res.data), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500

# 4. UPDATE JOB (PUT) - Saving Dossier Intel
@app.route('/api/jobs/<job_id>', methods=['PUT'])
def update_job(job_id):
    # 1. Auth Setup (Reused Logic)
    auth_header = request.headers.get('Authorization')
    if not auth_header: return jsonify({"error": "No Token"}), 401
    
    try:
        from supabase import create_client, Client
        SUPABASE_URL = os.environ.get("SUPABASE_URL")
        SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
        
        token = auth_header.split(" ")[1]
        user_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        user_client.postgrest.auth(token)
        
        # Verify ownership implicitly via RLS
        data = request.json
        
        # Whitelist columns to update
        updates = {}
        if 'job_description' in data: updates['job_description'] = data['job_description']
        if 'notes' in data: updates['job_intel'] = data['notes'] # Map API 'notes' -> DB 'job_intel'
        if 'salary_target' in data: updates['salary_target'] = data['salary_target']
        if 'status' in data: updates['status'] = data['status']
        if 'job_title' in data: updates['job_title'] = data['job_title']
        
        if not updates:
            return jsonify({"status": "No changes"}), 200

        res = user_client.table('user_jobs').update(updates).eq('id', job_id).execute()
        return jsonify(res.data), 200

    except Exception as e:
        print(f"Update Error: {e}")
        return jsonify({"error": str(e)}), 500

# 5. GENERATE INTEL (POST) - AI Powered
@app.route('/api/generate-intel', methods=['POST'])
def generate_intel():
    # 1. Auth Check
    auth_header = request.headers.get('Authorization')
    if not auth_header: return jsonify({"error": "Unauthorized"}), 401

    try:
        from openai import OpenAI
        OPENAI_KEY = os.environ.get("OPENAI_API_KEY")
        if not OPENAI_KEY:
             return jsonify({"error": "Server Config Error: Missing AI Key"}), 500
        
        client = OpenAI(api_key=OPENAI_KEY)

        data = request.json
        jd_text = data.get('job_description', '')
        
        if len(jd_text) < 50:
            return jsonify({"error": "JD too short"}), 400

        # 3. Generate Intel
        prompt = (
            f"Analyze this Job Description and extract 3 critical insights for an executive candidate:\n"
            f"1. A Strategic Priority (What is the #1 big picture goal?)\n"
            f"2. A Key Competency (What specific skill is non-negotiable?)\n"
            f"3. A Cultural Clue (What is the vibe?)\n"
            f"Then, provide 1 specific 'Power Talking Point' the candidate can use.\n\n"
            f"JOB DESCRIPTION:\n{jd_text}\n\n"
            f"Format the output as a clean, concise list."
        )
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert executive career coach."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )

        ai_intel = response.choices[0].message.content
        
        return jsonify({"intel": ai_intel}), 200

    except Exception as e:
         print(f"AI Error: {e}")
         return jsonify({"error": str(e)}), 500

# 6. ANALYZE JD (POST)
@app.route('/api/analyze-jd', methods=['POST'])
def analyze_jd():
    try:
        data = request.json
        jd_text = data.get('job_description', '')
        
        if not jd_text or len(jd_text) < 10:
             return jsonify({"role": "Target Role", "company": "Target Company", "summary": "No context provided."}), 200

        # OpenAI Call
        from openai import OpenAI
        OPENAI_KEY = os.environ.get("OPENAI_API_KEY")
        if not OPENAI_KEY: return jsonify({"error": "Missing AI Key"}), 500
        
        client = OpenAI(api_key=OPENAI_KEY)
        
        prompt = (
            f"Analyze this Job Description:\n{jd_text}\n\n"
            f"Return a JSON object with these keys:\n"
            f"- role: Extract the EXACT job title verbatim from the text. Do not rename or generalize it (e.g. if it says 'Kitchen Leader', do not change it to 'Operations Leader'). Only if NO title is present, infer the closest standard title based on the overview.\n"
            f"- company: The specific company name\n"
            f"- summary: A 3-sentence summary of the main responsibilities"
        )

        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a data extraction assistant. Output valid JSON only."}, 
                {"role": "user", "content": prompt}
            ],
            response_format={ "type": "json_object" }
        )
        
        return jsonify(json.loads(completion.choices[0].message.content)), 200

    except Exception as e:
        print(f"Intel Error: {e}")
        return jsonify({"role": "Unknown Role", "company": "Unknown Company", "summary": "Analysis failed."}), 200

# ------------------------------------------------------------------------------
# HELPER: Sanitization Pre-Processor (v5.0)
# ------------------------------------------------------------------------------
def sanitize_input(text):
    if not text: return None
    import re
    # 1. Strip Brackets [] or <> (System tags)
    clean = re.sub(r'\[.*?\]', '', text)
    clean = re.sub(r'<.*?>', '', clean)
    
    # 2. Remove System Artifacts/Prompt Injections
    artifacts = [
        "thoughtful use of diagrams", "generate image", "ignore previous instructions",
        "system prompt", "internal score"
    ]
    for art in artifacts:
        clean = re.sub(f'(?i){art}', '', clean)
        
    clean = clean.strip()
    return clean if clean else "Null Input"

# ------------------------------------------------------------------------------
# ROUTE: Get AI Feedback & Next Question
# ------------------------------------------------------------------------------
@app.route('/api/get-feedback', methods=['POST'])
def get_feedback():
    try:
        data = request.json
        # v5.0 SANITIZATION
        raw_message = data.get('message', '')
        message = sanitize_input(raw_message)
        
        if message == "Null Input":
             return jsonify({
                "response": {
                    "feedback": "Please provide a valid text response.", 
                    "internal_score": 0, 
                    "next_question": "Could you please rephrase your answer?"
                },
                "audio": None,
                "is_complete": False
            }), 200

        history = data.get('history', [])
        action = data.get('action') 

        # OpenAI Config
        from openai import OpenAI
        OPENAI_KEY = os.environ.get("OPENAI_API_KEY")
        if not OPENAI_KEY: return jsonify({"error": "Missing AI Key"}), 500
        client = OpenAI(api_key=OPENAI_KEY)

        # --- A. TRANSCRIPTION PATH ---
        if action == 'transcribe':
            import tempfile
            audio_b64 = data.get('audio', '')
            # Robust decode: handle data URI scheme if present
            if ',' in audio_b64:
                audio_b64 = audio_b64.split(',')[1]
            
            audio_bytes = base64.b64decode(audio_b64)
            
            with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as temp_audio:
                temp_audio.write(audio_bytes)
                temp_path = temp_audio.name
            
            try:
                with open(temp_path, "rb") as audio_file:
                    transcription = client.audio.transcriptions.create(
                        model="whisper-1", 
                        file=audio_file
                    )
                return jsonify({"transcript": transcription.text}), 200
            finally:
                if os.path.exists(temp_path): os.remove(temp_path)

        # --- B. FEEDBACK PATH (Existing) ---
        # message = data.get('message', '') # This is now sanitized above
        history = data.get('history', [])
        job_posting = data.get('jobPosting', '')
        resume_text = data.get('resumeText', '')
        is_start = data.get('isStart', False)
        question_count = data.get('questionCount', 1)
        role_title = data.get('roleTitle', '')

        # DYNAMIC RUBRIC Logic
        # Question 2 evaluates the answer to Q1 (Background/Intro). 
        # Questions 3+ evaluate STAR answers.
        
        # Prepare variables
        interviewer_intel = str(data.get('interviewer_intel') or '')
        role_title = str(data.get('job_title') or 'Candidate')
        
        # ---------------------------------------------------------
        # ACE INTERVIEW MASTER PROTOCOL v6.0 (Hardliner & Anchoring)
        # ---------------------------------------------------------
        
        # [PHASE 1: INITIALIZATION & ARCHETYPE]
        # Set Seniority Scale
        seniority_level = "Tactical Execution (Junior/Mid)"
        if any(x in role_title.upper() for x in ["SENIOR", "LEAD", "MANAGER"]):
            seniority_level = "Strategic Ownership"
        if any(x in role_title.upper() for x in ["DIRECTOR", "VP", "HEAD", "CHIEF", "C-LEVEL", "EXECUTIVE"]):
            seniority_level = "Vision, Culture, & ROI Dominance"

        # Set Archetype
        context_text = (role_title + " " + interviewer_intel).upper()
        persona_role = "The Ace Evaluator (Standard Corporate)"
        archetype_rubric = "Core Value: Structure & Competence. Reward STAR structure."

        if any(x in context_text for x in ["HOSPITALITY", "SAFETY", "GUEST", "PATIENT", "MEDICAL", "SCHOOL", "NURSE", "DOCTOR", "CLINIC"]):
            persona_role = "The Guardian (Safety & Culture First)"
            archetype_rubric = (
                "Core Value: Protection of People.\n"
                "Kill Switch: Sacrificing safety for speed/money is an IMMEDIATE FAIL (Score 1)."
            )
        elif any(x in context_text for x in ["BANK", "AUDIT", "COMPLIANCE", "ACCOUNTANT", "RISK", "LEGAL", "CFO", "ATTORNEY"]):
            persona_role = "The Steward (Accuracy & Risk Management)"
            archetype_rubric = (
                "Core Value: Accuracy, Stability, Compliance.\n"
                "Kill Switch: Guessing or 'Moving Fast' without controls is an IMMEDIATE FAIL (Score 1)."
            )
        elif any(x in context_text for x in ["STARTUP", "GROWTH", "VC", "SPEED", "PRODUCT", "TECH", "SAAS", "SALES", "MARKETING"]):
            persona_role = "The Growth Operator (Speed & ROI)"
            archetype_rubric = (
                "Core Value: Speed, Action, Revenue.\n"
                "Kill Switch: Citing 'policy' as an excuse for inaction is a FAIL."
            )

        # [PHASE 3: THE "FAIR JUDGE" SCORING LOGIC] (v7.0)
        rubric_text = (
            f"### ARCHETYPE: {persona_role}\n{archetype_rubric}\n\n"
            "### LOGIC GATES (Automatic Penalties)\n"
            "1. Gap Logic Detector: IF Candidate describes Situation + Result but skips the Action -> MAX SCORE: 2.\n"
            "2. Black Box Constraint: IF Action is vague ('I led', 'I handled') without mechanics -> MAX SCORE: 3.\n"
            "3. Kill Switches: Toxic, Reckless, or Pyrrhic behavior -> MAX SCORE: 1.\n"
            "4. Magic Wand Penalty: IF answer describes feelings/energy without mechanics -> MAX SCORE: 2.\n\n"
            "### THE FAIR JUDGE RUBRIC (Score Accurately, Not Harshly)\n"
            "- 5 (Exceptional): Specific Metric (%, $) AND Innovative Strategy. (< 10% of candidates).\n"
            "- 4 (Strong): Perfect STAR structure + Specific Nouns/Tools + Positive Result.\n"
            "- 3 (Competent): Answered the prompt relevantly. Followed STAR. Result was okay. (DEFAULT SCORE).\n"
            "- 2 (Weak): 'Gap Logic' (Skipped Action), vague buzzwords, or off-topic.\n"
            "- 1 (Fail): Non-Answer, Toxic, or < 15 words.\n\n"
            "### PHASE 4: THE 'MISSED OPPORTUNITY' ENGINE\n"
            "IF {{Internal_Score}} < 4:\n"
            "Scan Candidate Resume. If a better example exists, generate a brief coaching tip in the metadata.\n"
        )
        
        # Build System Prompt (v7.0)
        system_prompt = (
            f"Role: You are {persona_role}, a PhD-level Behavioral Analyst and 'Fair Judge'.\n"
            f"Objective: Conduct a high-stakes, structured interview. Score accurately but silently.\n"
            f"SENIORITY: {seniority_level}\n"
            f"CONTEXT:\nTarget Role: {role_title}\nJob Description: {job_posting}\nCandidate Resume: {resume_text}\n"
            f"Intel: {interviewer_intel}\n\n"
            f"{rubric_text}\n\n"
            "[PHASE 2: THE INTERVIEW LOOP & SANITIZATION]\n"
            "- Execute exactly 6 questions. Perform a [STATE RESET] between questions.\n"
            "- SANITIZATION: Strip artifacts ([], <>, 'generate image'). IF Null -> Do not score.\n"
            f"- Current Status: This is Question {question_count} of 6.\n\n"
            "[PHASE 3: THE 'CONTEXT-AWARE JUDGE' SCORING LOGIC]\n"
            "Assess every answer on a strict 1-5 Scale.\n\n"
            "CRITICAL OUTPUT FORMAT (STRICT JSON ENFORCEMENT):\n"
            "You are forbidden from outputting conversational text. You must output a single, valid JSON object containing exactly these three fields:\n\n"
            "{\n"
            '  "feedback": "[String: Polite, encouraging feedback only. NO scores. NO numbers.]",\n'
            '  "internal_score": [Integer: 1-5],\n'
            '  "next_question": "[String: The transition and the next interview question.]"\n'
            "}\n\n"
            "SCORING RULES (The 'Fair Judge'):\n"
            "1. SCORE 5: Specific Metrics (%, $) AND Strategy.\n"
            "2. SCORE 4: Strong STAR format + Tools + Result.\n"
            "3. SCORE 3: Competent answer. Relevant to prompt. (DEFAULT).\n"
            "4. SCORE 2: Weak action, vague, OR Gap Logic (Missing Action/Result).\n"
            "5. SCORE 1: Toxic, harmful, or <15 words ONLY. (1 is RESERVED for failures, NOT for missing details).\n\n"
            "Step A: Determine Rubric Type\n"
            "Type A (Background - Q1 Only):\n"
            "  - Definition: A high-level professional summary.\n"
            "  - Constraint: DO NOT ask for specific examples or metrics here.\n"
            "  - Scoring:\n"
            "    * If they share a relevant summary of their career -> Score = 3 (Default to 3 for any relevant Bio).\n"
            "    * If the user gives details relating to recent accomplishments that are relevant to the role -> Score 4 or 5.\n"
            "    * If the user does not provide relevant experience -> Score 2.\n\n"
            "Type B (Behavioral - Q2-Q6):\n"
            "  - Definition: A specific story using STAR.\n"
            "  - Scoring: Apply Gap Logic.\n"
            "  - Gap Logic Rule: IF missing Action OR Result -> Max Score 2 (NOT 1).\n"
            "  - Remember: Score 1 is ONLY for toxic/harmful/empty answers.\n\n"
            "SAFETY CHECK:\n"
            'Before outputting, verify that "feedback" and "next_question" contain ZERO integers or rating references (e.g., "5/5").\n'
            "CRITICAL Q6 CONSTRAINT: If this is Question 6 (final question), do NOT output ANY text after the JSON object. The interview ends here.\n"

            "- IF Score 4-5: Validate strength. 'That is a strong example because...'\n"
            "- IF Score 3: Validate but nudge. 'You described the situation, but I need more mechanics...'\n"
            "- IF Score 1-2: Move on neutrally or ask for clarification.\n"
        )
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add limited history to save context window
        for interaction in history[-3:]: 
            if 'question' in interaction: messages.append({"role": "assistant", "content": interaction['question']})
            if 'answer' in interaction: messages.append({"role": "user", "content": interaction['answer']})
        
        # Current Input Strategy
        if is_start:
            # FORCE GREETING LOGIC
            greeting_instruction = (
                "Start the interview. "
                "1. Say exactly: 'Hello, and welcome. Thank you for joining me today. I am the Hiring Manager for the position.' "
                "2. Set the stage: 'To give you an overview of our session: First, I'll ask for a high level overview of your background, and then we will dive into specific situational examples.' "
                "3. Ask Question 1: 'Let's get started. Walk me through your background and why you are the right fit for this role?'\n"
                "CRITICAL: DO NOT provide feedback yet. Output greeting as 'next_question'."
            )
            messages.append({"role": "user", "content": greeting_instruction})

        elif question_count == 2:
            messages.append({
                "role": "user",
                "content": (
                    f"User Answer: {message}. \n"
                    "Step 1: Thank them (Put this in 'feedback' field).\n"
                    "Step 2: Explain STAR Method: 'For the next questions, please use the STAR method: Situation, Task, Action, Result.' (Add to 'feedback' field).\n"
                    "Step 3: Ask the first Behavioral Question (Conflict, Failure, or Strategy). (Put ONLY the Question in 'next_question' field)."
                )
            })

        elif question_count in [3, 4, 5]:
             messages.append({
                "role": "user",
                "content": (
                    f"User Answer: {message}. \n"
                    "Step 1: Score (1-5) and provide brief feedback. (Put ONLY this critique in 'feedback' field).\n"
                    "Step 2: Say exactly: 'The next question that I have for you is...' (Put this in 'next_question' field).\n"
                    "Step 3: Ask the next behavioral question. (Append to 'next_question' field)."
                )
             })

        elif question_count == 6:
             messages.append({
                "role": "user",
                "content": (
                    f"User Answer: {message}. \n"
                    "Step 1: Score and Feedback. (Put ONLY critique in 'feedback' field).\n"
                    "Step 2: Say exactly: 'The final question I have for you is...' (Put this in 'next_question' field).\n"
                    "Step 3: Ask the Final Question (The Closer). (Append to 'next_question' field)."
                )
             })

        elif question_count > 6:
             # FINAL REPORT LOGIC (MASTER PROTOCOL v2.1)
             # 1. Build Full Transcript WITH LIVE SCORES (Binding)
             full_transcript = "INTERVIEW_TRANSCRIPT WITH SILENT METADATA:\n"
             session_metadata = "SESSION_METADATA (SILENT SCORES):\n"
             for idx, h in enumerate(history):
                 q = h.get('question', '')
                 a = h.get('answer', '')
                 
                 # v7.0 FIX: Improved Purge (< 20 words + System Triggers)
                 # Aggressively filter greetings/start commands to prevent indexing shift.
                 if len(q) < 15 or len(a.split()) < 20 or a.strip().lower() in ["start", "ready", "hello", "begin", "hi"]: continue 

                 # BINDING: Include the ACTUAL feedback/score the user received live
                 live_fb = h.get('feedback', 'No feedback recorded')
                 
                 # v5.0 SILENT SCORE RETRIEVAL
                 # Check for 'internal_score' first (v5), then 'score' (v4 legacy), then parse feedback (v3)
                 silent_score = h.get('internal_score') or h.get('score') or 0
                 
                 full_transcript += f"Turn {idx+1}:\nQ: {q}\nA: {a}\nLIVE_FEEDBACK: {live_fb}\n\n"
                 session_metadata += f"Turn {idx+1} Score: {silent_score}\n"
             
             # CRITICAL FIX: Append the FINAL Answer (which is not in history yet)
             full_transcript += f"Turn {len(history)+1} (FINAL QUESTION):\nQ: {lastAiQuestion if 'lastAiQuestion' in locals() else 'Final Question'}\nA: {message}\n\n"
             # Final turn score is yet to be determined by the Auditor, so no metadata for it yet.

             # 2. DEFINITIVE GOVERNANCE PROMPT (v7.0 - THE AUDITOR)
             final_report_system_prompt = (
                 "### TASK: GENERATE ACE INTERVIEW REPORT (v7.0 - THE AUDITOR)\n"
                 "You are 'The Ace Auditor'. Review the transcript and generate the final HTML report.\n\n"
                 "### INPUT DATA:\n"
                 "1. Interview_Transcript (The text conversations)\n"
                 "2. Session_Metadata (The hidden SILENT SCORES assigned during live session)\n\n"
                 "### PHASE 5: THE AUDITOR (FINAL REPORT)\n"
                 "Instruction: Compile the final report using Topic Anchoring and Silent Retrieval.\n\n"
                 "### STEP 1: THE GREETING PURGE\n"
                 "Rule: Ignore any turn that contains 'Start', 'Hello', 'Ready', or is < 20 words. Do not map these to Question Slots.\n\n"
                 "### STEP 2: TOPIC MAPPING (The Anchor)\n"
                 "Scan the remaining answers and map them to the best fit:\n"
                 "- Slot Q1: Find answer matching 'Background/Fit/History'.\n"
                 "- Slot Q2: Find answer matching 'Conflict/Challenge'.\n"
                 "- Slot Q3: Find answer matching 'Change/Adaptability'.\n"
                 "- Slot Q4: Find answer matching 'Strategy/Decision'.\n"
                 "- Slot Q5: Find answer matching 'Motivation/Performance/Automation'.\n"
                 "- Slot Q6: Find answer matching 'Culture/Turnaround'.\n"
                 "Fallback: If a topic doesn't align perfectly, map the remaining answers in Chronological Order.\n\n"
                 "### STEP 3: SMART HEADERS\n"
                 "For each question, generate a 3-5 word summary of the candidate's actual content.\n"
                 "Example: If they discuss Python automation, use 'Q5: Python Automation', NOT 'Q5: Motivation'.\n\n"
                 "### STEP 4: SCORING CONSTRAINTS (CRITICAL)\n"
                 "When reviewing the Silent Scores from Session Metadata:\n"
                 "- IF a score is 0, Null, or None -> Set Score = 1.\n"
                 "- TRUST the Silent Scores UNLESS they violate these rules:\n"
                 "  * Score 1 is RESERVED for toxic/harmful/empty answers ONLY.\n"
                 "  * IF an answer has clear content (20+ words) but missing Action/Result -> MAX Score should be 2 (NOT 1).\n"
                 "  * IF Silent Score = 1 but answer is substantial -> OVERRIDE to Score = 2.\n\n"
                 "### STEP 5: CALCULATE OVERALL SCORE (CRITICAL MATH)\n"
                 "Formula: Overall_Score = (Q1_Score + Q2_Score + Q3_Score + Q4_Score + Q5_Score + Q6_Score) / 6\n"
                 "IMPORTANT: Use proper division. Round to 1 decimal place.\n"
                 "Example: (1+4+2+4+5+1)/6 = 17/6 = 2.8 (NOT 2.5)\n\n"
                 "### STEP 6: OUTPUT JSON FORMAT (STRICT)\n"
                 "You must output a single JSON object. NO conversational text before or after the JSON.\n"
                 "Required keys:\n"
                 "- \"formatted_report\": The full HTML string.\n"
                 "- \"average_score\": The calculated average.\n"
                 "- \"q6_feedback_spoken\": Closing remark.\n"
                 "- \"verdict_text\": 'RECOMMEND' or 'NO HIRE'.\n\n"
                 "### HTML TEMPLATE (formatted_report)\n"
                 "<div class=\"ace-report\">\n"
                 "  <h1>Interview Scorecard</h1>\n"
                 "  <div class=\"summary\">\n"
                 "    <h2>Overall Score: {{Calculated_Average}}/5</h2>\n"
                 "    <h3 class=\"{{Verdict_Color}}\">Verdict: {{Verdict}}</h3>\n"
                 "  </div>\n\n"
                 "  <div class=\"deep-dive\">\n"
                 "    <div class=\"question-block\">\n"
                 "      <h4>{{Q1_SMART_HEADER}}</h4>\n"
                 "      <p><strong>Score:</strong> {{Internal_Score_Q1}}/5</p>\n"
                 "      <p><strong>Analysis:</strong> {{Reasoning}}</p>\n"
                 "    </div>\n"
                 "    <div class=\"question-block\">\n"
                 "      <h4>{{Q2_SMART_HEADER}}</h4>\n"
                 "      <p><strong>Score:</strong> {{Internal_Score_Q2}}/5</p>\n"
                 "      <p><strong>Analysis:</strong> {{Reasoning}}</p>\n"
                 "    </div>\n"
                 "    <div class=\"question-block\">\n"
                 "      <h4>{{Q3_SMART_HEADER}}</h4>\n"
                 "      <p><strong>Score:</strong> {{Internal_Score_Q3}}/5</p>\n"
                 "      <p><strong>Analysis:</strong> {{Reasoning}}</p>\n"
                 "    </div>\n"
                 "    <div class=\"question-block\">\n"
                 "      <h4>{{Q4_SMART_HEADER}}</h4>\n"
                 "      <p><strong>Score:</strong> {{Internal_Score_Q4}}/5</p>\n"
                 "      <p><strong>Analysis:</strong> {{Reasoning}}</p>\n"
                 "    </div>\n"
                 "    <div class=\"question-block\">\n"
                 "      <h4>{{Q5_SMART_HEADER}}</h4>\n"
                 "      <p><strong>Score:</strong> {{Internal_Score_Q5}}/5</p>\n"
                 "      <p><strong>Analysis:</strong> {{Reasoning}}</p>\n"
                 "    </div>\n"
                 "    <div class=\"question-block\">\n"
                 "      <h4>{{Q6_SMART_HEADER}}</h4>\n"
                 "      <p><strong>Score:</strong> {{Internal_Score_Q6}}/5</p>\n"
                 "      <p><strong>Analysis:</strong> {{Reasoning}}</p>\n"
                 "      <p style=\"color:#2563eb; font-style:italic;\">\n"
                 "        <strong>💡 ACE Coaching:</strong> {{Resume_Gap_Tip_If_Any}}\n"
                 "      </p>\n"
                 "    </div>\n"
                 "  </div>\n"
                 "</div>\n"
             )


             messages = [
                 {"role": "system", "content": final_report_system_prompt},
                 {"role": "user", "content": f"TRANSCRIPT:\n{full_transcript}\n\nSESSION_METADATA:\n{session_metadata}\n\nRESUME:\n{resume_text}\n\nGenerate Final Report JSON."}
             ]
        else:
            messages.append({"role": "user", "content": message})

        # 1. Text Generation
        print(f"DEBUG: Generating Final Report for count {question_count}...")
        try:
             # OPTIMIZATION: Use gpt-4o-mini for faster report generation (prevents Vercel timeout)
             chat_completion = client.chat.completions.create(
                 model="gpt-4o-mini",
                 messages=messages,
                 response_format={ "type": "json_object" }
             )
             
             ai_response_text = chat_completion.choices[0].message.content
             print(f"DEBUG: AI Response: {ai_response_text[:100]}...")
             
             try:
                  ai_json = json.loads(ai_response_text)
                  
                  # v7.2 REGEX SAFETY NET: Scrub leaked scores from BOTH fields
                  import re
                  score_pattern = r'\b(Score|Rating):\s*\d+/\d+\b'
                  
                  if "feedback" in ai_json:
                      feedback = ai_json["feedback"]
                      feedback = re.sub(score_pattern, '', feedback, flags=re.IGNORECASE)
                      feedback = re.sub(r'\b\d+/\d+\b', '', feedback)  # Catch standalone "1/5"
                      feedback = re.sub(r'\s+', ' ', feedback).strip()
                      ai_json["feedback"] = feedback
                  
                  if "next_question" in ai_json:
                      next_q = ai_json["next_question"]
                      next_q = re.sub(score_pattern, '', next_q, flags=re.IGNORECASE)
                      next_q = re.sub(r'\b\d+/\d+\b', '', next_q)
                      next_q = re.sub(r'\s+', ' ', next_q).strip()
                      ai_json["next_question"] = next_q
                      
             except Exception as json_err:
                  print(f"DEBUG JSON Error: {json_err}")
                  ai_json = { "feedback": ai_response_text, "next_question": "End of Interview (JSON Error).", "formatted_report": f"<h1>Error Generating Report</h1><p>{str(json_err)}</p>" }

             # REPORT FORMATTING BRIDGE
             if "formatted_report" in ai_json:
                  # v7.3 BACKEND MATH ENFORCEMENT & SCORE OVERRIDE
                  # Extract all scores from history and calculate correct average
                  all_scores = []
                  for h in history:
                      score = h.get('internal_score') or h.get('score') or 0
                      if score > 0:  # Only count valid scores
                          all_scores.append(score)
                  
                  # Calculate Python-enforced average (AI math is unreliable)
                  if len(all_scores) >= 6:
                      correct_average = round(sum(all_scores) / len(all_scores), 1)
                      print(f"DEBUG: Backend calculated average: {correct_average} (AI reported: {ai_json.get('average_score')})")
                      
                      # OVERRIDE AI's incorrect math
                      ai_json["average_score"] = correct_average
                      
                      # Update verdict based on correct average
                      if correct_average >= 3.5:
                          ai_json["verdict_text"] = "RECOMMEND"
                      else:
                          ai_json["verdict_text"] = "NO HIRE"
                  
                  # SEPARATION FIX: Feedback is the SPOKEN feedback, report is passed separately
                  ai_json["formatted_report"] = ai_json["formatted_report"] # Keep the reference
                  ai_json["feedback"] = ai_json.get("q6_feedback_spoken", "Interview Complete.")
                  ai_json["next_question"] = "" # No next text needed in UI

             # SCORE COMPLIANCE (v6.1)
             # Only apply mechanics if NOT START and Q2+
             if question_count > 1 and not is_start:
                 # 1. Word Count Penalty (<20 words -> Score 1)
                 if len(message.split()) < 20:
                     print(f"PENALTY: Answer too short ({len(message.split())} words). Forcing Score 1.")
                     ai_json["internal_score"] = 1
                     ai_json["score"] = 1
                     ai_json["feedback"] = ai_json.get("feedback", "") + " (System Note: Response was too brief to score higher.)"

                 # 2. Force Minimum Score 1 (No Zeros)
                 current_int_score = ai_json.get("internal_score") or ai_json.get("score")
                 if current_int_score is None or float(current_int_score) < 1:
                      ai_json["internal_score"] = 1
                      ai_json["score"] = 1

             # 2. Audio Generation (Omit if empty text)
             audio_b64 = None
             if ai_json.get('next_question') or (question_count > 6): # Allow audio logic to run for end
                 voice = data.get('voice', 'alloy')

                 # SPEAK LOGIC
                 speech_text = ai_json.get('next_question', '')
                 
                 # FINAL REPORT AUDIO OVERRIDE
                 if question_count > 6 and "average_score" in ai_json:
                     q6_fb = ai_json.get("q6_feedback_spoken", "That concludes the interview.")
                     speech_text = f"Feedback: {q6_fb} That concludes the interview. Thank you for your time."
                 
                 # STANDARD FEEDBACK AUDIO
                 elif ai_json.get('feedback'):
                      speech_text = f"Feedback: {ai_json['feedback']} \n\n {ai_json['next_question']}"

                 # GUARD: Prevent Empty String Crash (OpenAI 400)
                 if not speech_text or not speech_text.strip():
                     speech_text = "Analysis complete. Thank you."

                 audio_response = client.audio.speech.create(
                     model="tts-1-hd",
                     voice=voice,
                     input=speech_text
                 )
                 import base64
                 audio_b64 = base64.b64encode(audio_response.content).decode('utf-8')
        
        except Exception as e:
             import traceback
             print(f"CRITICAL REPORT ERROR: {traceback.format_exc()}")
             return jsonify({"error": f"Report Gen Error: {str(e)}", "details": traceback.format_exc()}), 500
        # MATH ENFORCER v2: Calculate Actual Average
        try:
            # 1. Extract Scores from History
            extracted_scores = []
            import re
            
            # A. From History (Q1-Q5)
            for turn in history:
                # Look for "Score: 3/5" or "Score: 3" in previous feedbacks
                feedback = turn.get('formatted_feedback') or turn.get('feedback', '')
                match = re.search(r'Score:\s*(\d+(\.\d+)?)', feedback, re.IGNORECASE)
                if match:
                    extracted_scores.append(float(match.group(1)))
            
            # B. From Q6 (Current Response)
            # We asked AI to output q6_score in JSON
            q6_score = ai_json.get("q6_score", 0)
            if q6_score:
                extracted_scores.append(float(q6_score))
            
            # C. Calculate
            if extracted_scores:
                real_avg = sum(extracted_scores) / len(extracted_scores)
                ai_json["average_score"] = round(real_avg, 1)
                print(f"Verified Score: {ai_json['average_score']} (from {extracted_scores})")
            else:
                # Fallback to AI's guess
                raw_score = str(ai_json.get("average_score", "0"))
                clean_score = raw_score.split('/')[0].strip()
                ai_json["average_score"] = float(clean_score)

        except Exception as e:
            print(f"Score Math Error: {e}")
            ai_json["average_score"] = 0.0

        ai_json["average_score"] = ai_json["average_score"] # Ensure it sticks
        
        # Encode (Ensure audio_b64 is set)
        # Note: audio_b64 is already set in the Try block above.
        # If Try failed, audio_b64 is None.
        
        return jsonify({
            "response": ai_json,
            "audio": audio_b64,
            "is_complete": question_count > 6,
            "average_score": ai_json.get("average_score", 0.0)
        }), 200

    except Exception as e:
        print(f"Feedback Error: {e}")
        return jsonify({"error": str(e)}), 500

# 8. GENERAL API ROUTE (Report Generation)
@app.route('/api', methods=['POST'])
def general_api():
    try:
        data = request.json
        action = data.get('action') 
        
        # OpenAI Config
        from openai import OpenAI
        OPENAI_KEY = os.environ.get("OPENAI_API_KEY")
        if not OPENAI_KEY: return jsonify({"error": "Missing AI Key"}), 500
        client = OpenAI(api_key=OPENAI_KEY)

        if action == 'generate_report':
            history = data.get('history', [])
            job_posting = data.get('jobPosting', '')

            prompt = f"""
            Generate a Final Executive Coaching Report based on this interview history.
            
            HISTORY:
            {json.dumps(history)}

            JOB CONTEXT:
            {job_posting}

            CRITICAL TASKS:
            1. Calculate an AVERAGE SCORE based on the scores found in the history (0-5 scale).
            2. Identify 3 Key Strengths.
            3. Identify 3 Specific Areas for Improvement.
            
            OUTPUT FORMAT:
            Return a JSON object with this structure:
            {{
                "report": "<html>...</html>",
                "average_score": 4.5
            }}
            
            HTML REQUIREMENTS:
            - Use a modern, dark-mode compatible style (Tailwind-like classes or inline styles).
            - Include a big "Overall Score" badge (e.g., 4.2/5).
            - Use bullet points for strengths/weaknesses.
            - Keep it professional and encouraging.
            """

            completion = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                response_format={ "type": "json_object" }
            )
            
            result = json.loads(completion.choices[0].message.content)
            
            # --- PYTHON MATH ENFORCER ---
            # Don't trust the AI's math. Calculate it from the history.
            try:
                extracted_scores = []
                import re
                for turn in history:
                    feedback = turn.get('feedback', '')
                    # Look for "Score: 3/5" or "Score: 3"
                    match = re.search(r'Score:\s*(\d+(\.\d+)?)', feedback, re.IGNORECASE)
                    if match:
                        extracted_scores.append(float(match.group(1)))
                
                if extracted_scores:
                    # Calculate precise average
                    avg = sum(extracted_scores) / len(extracted_scores)
                    # Round to 1 decimal place (e.g. 3.8)
                    result['average_score'] = round(avg, 1)
                    print(f"Server-Side Calc: Found {len(extracted_scores)} scores. Avg: {result['average_score']}")
                else:
                    if 'average_score' not in result:
                        result['average_score'] = 0
            except Exception as e:
                print(f"Math Enforcer Error: {e}")
                # Fallback to AI's guess if python logic fails
                if 'average_score' not in result:
                    result['average_score'] = 0

            return jsonify({"data": result}), 200
            
        elif action == 'parse_resume':
            resume_text = data.get('resume_text', '')
            
            prompt = f"""
            Extract structured data from this resume text.
            Resume Text:
            {resume_text[:4000]} (truncated)

            Output JSON structure:
            {{
                "personal": {{ "name": "...", "email": "...", "phone": "..." }},
                "experience": [
                    {{ "role": "...", "company": "...", "dates": "...", "description": "..." }}
                ],
                "education": [
                     {{ "degree": "...", "school": "...", "dates": "..." }}
                ]
            }}
            """

            completion = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a resume parser. Output only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={ "type": "json_object" }
            )
            
            return jsonify({"data": completion.choices[0].message.content}), 200

        elif action == 'analyze_resume':
            resume_text = data.get('resume', '')
            jd_text = data.get('job_description', '')
            
            prompt = f"""
            Analyze this resume against the following job description.
            RESUME:
            {resume_text[:4000]}
            
            JOB DESCRIPTION:
            {jd_text[:2000]}

            Output JSON structure exactly:
            {{
                "overall_score": 0-100 (integer),
                "ats_compatibility": {{ "score": 0-10 (integer) }},
                "keywords": {{
                    "missing": [
                        {{ "word": "high-priority keyword from JD missing in resume" }},
                        {{ "word": "..." }}
                    ]
                }},
                "formatting": [
                    {{ "issue": "Specific formatting concern", "fix": "How to fix it" }}
                ],
                "improvements": [
                    {{ 
                        "title": "Improvement Category", 
                        "suggestion": "Detailed strategy", 
                        "current": "Snippet from resume showing the issue", 
                        "better": "Better version of that snippet" 
                    }}
                ],
                "word_count": {len(resume_text.split())}
            }}
            """

            completion = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a professional resume auditor. Output valid JSON only. Be extremely specific in the improvements section."},
                    {"role": "user", "content": prompt}
                ],
                response_format={ "type": "json_object" }
            )
            return jsonify({"data": completion.choices[0].message.content}), 200

        elif action == 'optimize':
            user_data = data.get('user_data', {})
            # Fix Key Mismatch: Frontend sends 'resume_text' and 'job_description'
            resume_text = data.get('resume_text', '')
            jd_text = data.get('job_description', '')
            strategy = data.get('strategy', 'Professional and Results-Driven')

            prompt = f"""
            Optimize this resume for the target job using the specified strategy.
            
            USER IDENTITY (DO NOT HALLUCINATE):
            Name: {user_data.get('personal', {}).get('name', 'N/A')}
            Email: {user_data.get('personal', {}).get('email', 'N/A')}
            Phone: {user_data.get('personal', {}).get('phone', 'N/A')}
            Location: {user_data.get('personal', {}).get('location', 'N/A')}

            ORIGINAL RESUME CONTENT:
            {resume_text[:4000]}

            TARGET JOB:
            {jd_text[:2000]}

            STRATEGY:
            {strategy}

            INSTRUCTIONS:
            1. Rewrite the 'Summary' and 'Experience' sections to align with the JD while maintaining absolute truthfulness to the ORIGINAL RESUME content.
            2. USE THE PROVIDED IDENTITY (Name, Email, etc.). NEVER invent dummy data like "John Doe".
            
            Output JSON structure exactly:
            {{
                "personal": {{
                    "name": "{user_data.get('personal', {}).get('name', 'N/A')}",
                    "email": "{user_data.get('personal', {}).get('email', 'N/A')}",
                    "phone": "{user_data.get('personal', {}).get('phone', 'N/A')}",
                    "location": "{user_data.get('personal', {}).get('location', 'N/A')}",
                    "summary": "NEW OPTIMIZED SUMMARY"
                }},
                "experience": [
                    {{ "role": "...", "company": "...", "dates": "...", "description": "NEW OPTIMIZED BULLETS" }}
                ],
                "skills": ["keyword1", "keyword2", "..."],
                "enhancement_overview": "A brief explanation of the strategic changes made (Markdown allowed)."
            }}
            """

            completion = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    { "role": "system", "content": "You are an expert executive resume writer. Use provided user data ONLY. No hallucinations." },
                    { "role": "user", "content": prompt }
                ],
                response_format={ "type": "json_object" }
            )
            return jsonify({ "data": completion.choices[0].message.content }), 200

        elif action == 'cover_letter':
            resume_text = data.get('resume', '')
            jd_text = data.get('jobDesc', '')
            user_data = data.get('user_data', {})
            p = user_data.get('personal', {})
            
            prompt = f"""
            Write a highly tailored, professional cover letter based on the provided resume and job description.
            
            USER IDENTITY (USE THESE - DO NOT USE PLACEHOLDERS FOR THESE):
            Name: {p.get('name', 'N/A')}
            Email: {p.get('email', 'N/A')}
            Phone: {p.get('phone', 'N/A')}
            Location: {p.get('location', 'N/A')}

            RESUME CONTENT:
            {resume_text[:4000]}
            
            JOB DESCRIPTION:
            {jd_text[:2000]}

            INSTRUCTIONS:
            1. Use a modern, professional tone.
            2. Highlighting specific achievements from the RESUME CONTENT that align with the JOB DESCRIPTION.
            3. Use the USER IDENTITY provided for the header and signature. DO NOT use placeholders like [Your Name] or [Your Phone] if information is provided above.
            4. Keep it concise (under 400 words).
            5. Use placeholders like [Date], [Hiring Manager Name], [Company Name], etc. ONLY if they are not clear from the JD or User Identity.
            6. Output in Markdown format.
            """

            completion = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    { "role": "system", "content": "You are an expert executive cover letter writer. Use provided identity and resume. No placeholders for user info." },
                    { "role": "user", "content": prompt }
                ]
            )
            return jsonify({ "data": completion.choices[0].message.content }), 200

        elif action == 'linkedin_optimize':
            about_me = data.get('aboutMe', '')
            
            prompt = f"""
            Analyze and optimize this LinkedIn 'About' section for a high-performance professional.
            
            ABOUT SECTION:
            {about_me[:4000]}

            INSTRUCTIONS:
            1. Provide 3-5 specific recommendations for improvement.
            2. Provide a refined, "Sample" version of the About section that is compelling and results-driven.
            3. Output JSON structure exactly:
            {{
                "recommendations": ["Recommendation 1", "Recommendation 2", ...],
                "refined_content": "The full revised text..."
            }}
            """

            completion = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    { "role": "system", "content": "You are a LinkedIn branding expert. Output valid JSON only." },
                    { "role": "user", "content": prompt }
                ],
                response_format={ "type": "json_object" }
            )
            return jsonify(json.loads(completion.choices[0].message.content)), 200

        elif action == 'lab_assistant_chat':
            user_message = data.get('message', '')
            mission_context = data.get('context', '')
            
            # 1. Fetch User Jobs for Context
            active_jobs_context = "No active jobs found."
            try:
                auth_header = request.headers.get('Authorization')
                if auth_header:
                    token = auth_header.split(" ")[1]
                    user_response = supabase.auth.get_user(token)
                    user_id = user_response.user.id
                    
                    user_client = create_client(SUPABASE_URL, SUPABASE_KEY)
                    user_client.postgrest.auth(token)
                    jobs_res = user_client.table('user_jobs').select('company, role, status').eq('user_id', user_id).execute()
                    if jobs_res.data:
                        active_jobs_context = "\n".join([f"- {j['role']} @ {j['company']} ({j['status']})" for j in jobs_res.data])
            except Exception as e:
                print(f"Job Context Error: {e}")

            # SPECIAL HANDLING: Initial Opening Generation
            if user_message == "GENERATE_OPENING_GREETING":
                opening_prompt = f"""
                You are a sophisticated AI Career Strategist.
                CONTEXT:
                {mission_context}

                TASK:
                Generate a 2-sentence personalized greeting.
                1. Acknowledge the user's current status found in CONTEXT.
                   - IF CONTEXT contains specific Role/Company, mention them.
                   - IF CONTEXT is generic (e.g. "General Strategy"), simply welcome the user to the Strategy Lab.
                   - DO NOT use placeholders like "[Job Title]" or "[Company Name]".
                2. OFFER to research current news and announcements for that company (if specific company exists).
                3. Ask how you can help.

                EXAMPLE (Specific):
                "I see you are in the Interviewing phase for the Product Manager role at Google. I can attempt to research current news for them if you'd like. Please tell me how I can help you today."
                
                EXAMPLE (Generic):
                "Welcome to the Strategy Lab. I am ready to assist with your career planning or negotiation strategy. How can I help you advance your position today?"
                """
                completion = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": opening_prompt}]
                )
                return jsonify({"response": completion.choices[0].message.content}), 200

            system_prompt = f"""
            You are the neural core of the Strategy Lab. You provide cold, clinical, yet highly effective career advice.
            
            CURRENT MISSION CONTEXT:
            {mission_context}

            ACTIVE USER JOBS:
            {active_jobs_context}
            
            OPERATIONAL DIRECTIVES:
            1. **JOB AWARENESS**: Review the 'ACTIVE USER JOBS'. If the user's query is key-less (e.g. "Draft an email"), ASK the user which job they are referring to before proceeding.
            2. **COMPANY SCANNING**: If the user asks to "scan" a company, you may simulate a strategic analysis of current trends, potential pain points, and new launches relevant to that industry.
            3. **TRUTH PROTOCOL (REFINED)**:
               - **General Knowledge**: You MAY use your internal training data to provide general company culture, funding history (up to your knowledge cutoff), and public strategic reputation.
               - **Real-Time Data**: DO NOT claim to know *real-time* stock prices or private internal memos. If asked for this, provide a general framework but strictly state you don't have live access.
               - **No Hallucinations**: Do not invent specific financial numbers or news events.
            4. **AMBIGUITY RESOLUTION**: If a company name is common (e.g. "Loop", "Apex"), look at the Context (Role/JD) to infer the correct entity.
               - IF uncertain, provide a "Disambiguation List" (e.g. "Did you mean Loop Returns (SaaS), Loop Industries (Plastics), or Loop Insurance?").
               - PRIORITIZE the entity that matches the User's industry/role.
            5. **OPENING**: Start by acknowledging the user's specific context or asking which of their active jobs they are focusing on today.
            5. Maintain a high-leverage, executive tone.
            
            REVENUE LINKING PROTOCOL (CRITICAL):
            When relevant, you MUST naturally mention one of the following tools in your response to trigger a conversion chip:
            - Mention "Executive Rewrite" if the user needs resume optimization.
            - Mention "Interview Simulator" if the user needs to practice for behaviorals or technicals.
            - Mention "The Closer" if the user is discussing salary or contract negotiation.

            INSTRUCTIONS:
            1. Provide actionable, high-leverage advice.
            2. Use Markdown for formatting.
            3. Keep responses punchy and professional.
            """

            completion = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    { "role": "system", "content": system_prompt },
                    { "role": "user", "content": user_message }
                ]
            )
            return jsonify({ "response": completion.choices[0].message.content }), 200

        elif action == 'star_coach_init':
            resume_text = data.get('resume_text', '')
            job_description = data.get('job_description', '')
            role_title = data.get('role_title', 'Target Role')
            # NEW: Accept history to avoid repeats
            story_history = data.get('story_history', []) # List of {title, situation}
            
            history_context = ""
            if story_history:
                history_context = "PREVIOUSLY COVERED TOPICS (DO NOT ASK ABOUT THESE):\n"
                for h in story_history:
                     history_context += f"- {h.get('title', 'Story')}: {h.get('situation', '')[:100]}...\n"

            prompt = f"""
            You are an expert Behavioral Interview Coach.

            USER CONTEXT:
            - Target Role: {role_title}
            - Job Description (Excerpt): {job_description[:1000]}
            - User Resume (Excerpt): {resume_text[:2000]}
            
            {history_context}

            TASK:
            1. Analyze the User Resume to find a specific role and accomplishment that is relevant to the Target Role's requirements.
            2. Formulate a behavioral interview question that explicitly references this past experience to prompt a specific story.
            3. IGNORE topics listed in "PREVIOUSLY COVERED TOPICS". Find a NEW angle.

            FORMAT:
            "I see on your resume that you [mention specific accomplishment/responsibility] when you were a [Role] at [Company]. This is very relevant to [Target Company]'s need for [Skill]. 

            Can you walk me through that situation? What was the specific challenge?"

            Output JSON:
            {{
                "question": "The question text..."
            }}
            """

            completion = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    { "role": "system", "content": "You are a tough but fair Interview Coach. Output valid JSON." },
                    { "role": "user", "content": prompt }
                ],
                response_format={ "type": "json_object" }
            )
            return jsonify(json.loads(completion.choices[0].message.content)), 200

        elif action == 'star_coach_step':
            history = data.get('history', [])
            latest_input = data.get('latest_input', '')
            
            # Format history for LLM
            messages = [{ "role": "system", "content": "You are an Interview Coach helping the user refine a STAR story. Your goal is to get a COMPLETE story (Situation, Task, Action, Result) from them. If the story is vague, ask 1 clarifying question. If it is complete enough, extraction the STAR data." }]
            
            for msg in history:
                messages.append(msg)
            
            messages.append({"role": "user", "content": latest_input})

            # Append instruction for next step
            messages.append({
                "role": "user", 
                "content": """
                Analyze the user's latest response in the context of the story so far.
                
                3. KILL SWITCHES (Immediate MAX Score: 1):
                - Triggers: Ethical breach, reckless risk, 'saving the day' alone (Hero Complex), ignoring data.
                - Verdict: 'DO NOT RECOMMEND'.
                4. MAGIC WAND PENALTY (Feeling vs Action):
                - IF answer describes feelings ('I shifted energy', 'I made them feel safe') BUT misses mechanics ('I held a meeting'):
                - PENALTY: This is a 'Magic Wand' answer. MAX SCORE: 2.
                - Reason: 'Vague/Emotional Response'.
                DECISION LOGIC:
                1. IF the story is missing key details (e.g. vague Action, no Result, unclear Task), output status "clarify" and ask ONE follow-up question.
                2. IF the story is solid and complete, output status "complete" and extract the S.T.A.R. data.

                Output JSON Structure:
                {
                    "status": "clarify" OR "complete",
                    "question": "Your follow-up question..." (ONLY IF status=clarify),
                    "star_data": { "S": "...", "T": "...", "A": "...", "R": "..." } (ONLY IF status=complete)
                }
                """
            })

            completion = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                response_format={ "type": "json_object" }
            )
            return jsonify(json.loads(completion.choices[0].message.content)), 200

        elif action == 'star_drill':
            input_text = data.get('input_text', '')
            user_id = data.get('user_id')

            if not input_text or len(input_text) < 10:
                return jsonify({"error": "Story too short"}), 400

            prompt = f"""
            Take this raw, unstructured interview story and restructure it into the perfect S.T.A.R. format.
            
            RAW STORY:
            {input_text}

            INSTRUCTIONS:
            1. TITLE: Generate a professional 3-5 word title for this story (e.g. "Cost Reduction Initiative" or "Conflict Resolution").
            2. SITUATION (S): Briefly set the context. Who, when, where? 
            3. TASK (T): What was the specific challenge or goal?
            4. ACTION (A): What specific steps did YOU take? (Emphasize "I", not "We"). This should be the bulk of the answer.
            5. RESULT (R): What was the outcome? Use numbers/metrics if possible.
            
            Output JSON structure exactly:
            {{
                "Title": "...",
                "S": "...",
                "T": "...",
                "A": "...",
                "R": "..."
            }}
            """

            completion = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    { "role": "system", "content": "You are an expert interview coach. Structure raw stories into perfect STAR format. Output valid JSON." },
                    { "role": "user", "content": prompt }
                ],
                response_format={ "type": "json_object" }
            )
            
            result = json.loads(completion.choices[0].message.content)
            
            # SAVE TO DB
            if user_id:
                try:
                    # Authenticate as user to respect RLS
                    auth_header = request.headers.get('Authorization')
                    if auth_header:
                        token = auth_header.split(" ")[1]
                        user_client = create_client(SUPABASE_URL, SUPABASE_KEY)
                        user_client.postgrest.auth(token)
                        
                        user_client.table('star_stories').insert({
                            "user_id": user_id,
                            "input_text": input_text,
                            "title": result.get('Title', 'New STAR Story'),
                            "situation": result.get('S'),
                            "task": result.get('T'),
                            "action": result.get('A'),
                            "result": result.get('R')
                        }).execute()
                except Exception as e:
                    print(f"STAR Save Error: {e}")
                    # Non-blocking error, return result anyway

            return jsonify(result), 200

        elif action == 'get_star_stories':
            user_id = data.get('user_id')
            if not user_id: return jsonify({"error": "No User ID"}), 400
            
            try:
                # Authenticate as user
                auth_header = request.headers.get('Authorization')
                if auth_header:
                    token = auth_header.split(" ")[1]
                    user_client = create_client(SUPABASE_URL, SUPABASE_KEY)
                    user_client.postgrest.auth(token)
                    
                    response = user_client.table('star_stories').select("*").eq('user_id', user_id).order('created_at', desc=True).execute()
                    return jsonify({"stories": response.data}), 200
                else:
                    return jsonify({"error": "No Token"}), 401
            except Exception as e:
                print(f"Fetch Stories Error: {e}")
                return jsonify({"error": str(e)}), 500

        return jsonify({"error": f"Invalid Action: {action} (v2)"}), 400

    except Exception as e:
        print(f"General API Error: {e}")
        print(f"General API Error: {e}")
        return jsonify({"error": str(e)}), 500

# 9. USER PROFILE (GET)
@app.route('/api/user-profile', methods=['GET'])
def get_user_profile():
    auth_header = request.headers.get('Authorization')
    if not auth_header: return jsonify({"error": "No Token"}), 401
    
    try:
        token = auth_header.split(" ")[1]
        user_response = supabase.auth.get_user(token)
        user_id = user_response.user.id
        
        # Use RLS client to query public.users
        user_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        user_client.postgrest.auth(token)
        
        # Fetch detailed profile from public table
        res = user_client.table('users').select('*').eq('id', user_id).single().execute()
        
        if not res.data:
            # Fallback if no public profile yet (should exist via trigger, but safe to handle)
            return jsonify({
                "id": user_id,
                "email": user_response.user.email,
                "credits": 0,
                "is_unlimited": False
            }), 200
            
        return jsonify(res.data), 200

    except Exception as e:
        print(f"Profile Fetch Error: {e}")
        return jsonify({"error": str(e)}), 500

# 10. CREATE CHECKOUT SESSION (POST)
@app.route('/api/create-checkout-session', methods=['POST'])
def create_checkout_session():
    auth_header = request.headers.get('Authorization')
    if not auth_header: return jsonify({"error": "No Token"}), 401

    try:
        data = request.json
        plan_type = data.get('plan_type')
        success_url = data.get('successUrl', 'https://tryaceinterview.com/dashboard.html')
        cancel_url = success_url # Just go back
        
        stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
        if not stripe.api_key: return jsonify({"error": "Server Missing Stripe Key"}), 500
        
        # PRICE MAPPING
        price_id = None
        if plan_type == 'strategy_inquisitor':
            price_id = 'price_1SePpZIH1WTKNasqLuNq4sSZ'
        elif plan_type == 'strategy_followup':
            price_id = 'price_1SeQHYIH1WTKNasqpFyl2ef0'
        # elif plan_type == 'strategy_closer': price_id = '...'
        
        if not price_id:
            return jsonify({"error": "Invalid Plan Type"}), 400

        checkout_session = stripe.checkout.Session.create(
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "user_id": data.get('userId'), # Pass user ID for webhook fulfillment
                "plan_type": plan_type
            }
        )
        
        return jsonify({"url": checkout_session.url}), 200

    except Exception as e:
        print(f"Checkout Error: {e}")
        return jsonify({"error": str(e)}), 500

# 11. GENERATE STRATEGY TOOL (POST)
@app.route('/api/generate-strategy-tool', methods=['POST'])
def generate_strategy_tool():
    auth_header = request.headers.get('Authorization')
    if not auth_header: return jsonify({"error": "Unauthorized"}), 401

    try:
        data = request.json
        tool_type = data.get('tool_type')
        inputs = data.get('inputs', {})
        
        from openai import OpenAI
        OPENAI_KEY = os.environ.get("OPENAI_API_KEY")
        if not OPENAI_KEY: return jsonify({"error": "Missing AI Key"}), 500
        client = OpenAI(api_key=OPENAI_KEY)

        prompt = ""
        
        if tool_type == 'inquisitor':
            interviewer_role = inputs.get('interviewer_role', 'Interviewer')
            company = inputs.get('company_name', 'Company')
            context = inputs.get('context', '')
            jd = inputs.get('jd', '')
            user_target_role = inputs.get('user_role', 'Candidate')
            
            prompt = f"""
            You are a Strategic Interview Consultant. Generate 5 High-Impact Reverse Interview Questions for a candidate ({user_target_role}) interviewing with a {interviewer_role} at {company}.
            
            INPUT DATA:
            - **Company Context**: {context}
            - **Job Description (JD)**: {jd[:3000]}
            
            INSTRUCTIONS:
            1. **SIMULATED SEARCH**: Use your internal knowledge base to "search" for {company}'s recent market position, products, or pain points. Combine this with the provided Context.
            2. **JD ANALYSIS**: Scan the JD for heavy emphasis areas (e.g. "scaling," "modernizing," "speed") and formulate a question that proves the candidate understands this unspoken priority.
            3. **ROLE ALIGNMENT**: Tailor the complexity. If the candidate is a VP, ask about strategy/P&L. If Engineer, ask about technical debt/velocity.
            
            GOAL:
            The goal is to flip the dynamic, show deep strategic insight, and uncover red flags or golden opportunities.
            
            OUTPUT FORMAT (Markdown):
            For each question:
            ### 1. The [Name of Strategy] Question
            **"The Script..."**
            *Why this works:* Explanation of the psychology + data used (e.g. "This leverages the fact that they just raised Series B...").
            """

        elif tool_type == 'closer':
            offer = inputs.get('current_offer', '0')
            bonus = inputs.get('sign_on', '0')
            leverage = inputs.get('leverage', 'None')
            goal = inputs.get('goal', 'Improve offer')
            
            prompt = f"""
            Write a Salary Negotiation Script.
            
            CURRENT OFFER: ${offer} (Base) + ${bonus} (Sign-on)
            LEVERAGE/CONTEXT: {leverage}
            GOAL: {goal}
            
            OUTPUT FORMAT (Markdown):
            1. **Strategic Analysis**: Brief assessment of leverage (2-3 sentences).
            2. **The Script (Email Version)**: A polished email draft.
            3. **The Script (Phone Version)**: Bullet points for a live conversation.
            """

        elif tool_type == 'followup':
            recipient = inputs.get('recipient_name', 'Hiring Manager')
            scenario = inputs.get('scenario', 'post_interview')
            context = inputs.get('context', '')
            
            prompt = f"""
            Write a Strategy Follow-Up Email/Message.
            
            RECIPIENT: {recipient}
            SCENARIO: {scenario}
            VALUE CONTEXT: {context}
            
            OUTPUT FORMAT (Markdown):
            **Subject Line Options:**
            1. ...
            2. ...
            
            **The Email Draft:**
            [Content]
            
            **Why this works:** Brief explanation.
            """
            
        else:
             return jsonify({"error": "Invalid Tool Type"}), 400

        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a world-class Executive Career Strategist."},
                {"role": "user", "content": prompt}
            ]
        )
        
        return jsonify({"content": completion.choices[0].message.content}), 200

    except Exception as e:
        print(f"Strategy Gen Error: {e}")
        return jsonify({"error": str(e)}), 500

# Expose app
app = app