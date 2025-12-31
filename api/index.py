from flask import Flask, request, jsonify
from supabase import create_client, Client
import os
import json
import base64
import stripe

app = Flask(__name__)

# 1. SETUP SUPABASE
try:
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    print(f"Supabase Init Error: {e}")

# 3. THE JOBS ROUTE (Secure Mode)
@app.route('/api/jobs', methods=['GET', 'POST'])
def manage_jobs():
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
        user_response = supabase.auth.get_user(token)
        user_id = user_response.user.id
    except Exception as e:
        print(f"Auth Verification Failed: {e}")
        return jsonify({"error": "Unauthorized"}), 401
        
    # 3. Create RLS-Compatible Client
    # We create a new client and explicitly set the auth token for PostgREST.
    try:
        user_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        user_client.postgrest.auth(token)
    except Exception as e:
        print(f"Client Handshake Error: {e}")
        return jsonify({"error": "Server Error"}), 500

    # B. GET Request (Loading the Dashboard)
    if request.method == 'GET':
        try:
            # Query AS THE USER
            # Reverted to user_jobs. Map job_intel to notes for frontend compatibility.
            response = user_client.table('user_jobs').select(
                "id, job_title, company_name, status, job_description, job_intel, salary_target"
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
        data = request.json
        jd_text = data.get('job_description', '')
        
        if len(jd_text) < 50:
            return jsonify({"error": "JD too short"}), 400

        # 2. Configure OpenAI (Triggering Redeploy)
        from openai import OpenAI
        OPENAI_KEY = os.environ.get("OPENAI_API_KEY")
        if not OPENAI_KEY:
             return jsonify({"error": "Server Config Error: Missing AI Key"}), 500
        
        client = OpenAI(api_key=OPENAI_KEY)

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
        
        result = json.loads(completion.choices[0].message.content)
        return jsonify(result), 200

    except Exception as e:
        print(f"Analyze JD Error: {e}")
        return jsonify({"role": "Unknown Role", "company": "Unknown Company", "summary": "Analysis failed."}), 200

# 7. GET FEEDBACK / INTERVIEW LOOP (POST)
@app.route('/api/get-feedback', methods=['POST'])
def get_feedback():
    try:
        data = request.json
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
        message = data.get('message', '')
        history = data.get('history', [])
        job_posting = data.get('jobPosting', '')
        resume_text = data.get('resumeText', '')
        is_start = data.get('isStart', False)
        question_count = data.get('questionCount', 1)
        role_title = data.get('roleTitle', '')

        # DYNAMIC RUBRIC Logic
        # Question 2 evaluates the answer to Q1 (Background/Intro). 
        # Questions 3+ evaluate STAR answers.
        
        if question_count == 2:
            rubric_text = (
                "SCORING RUBRIC (BACKGROUND QUESTION):\n"
                "- Score 1-2: User's background is irrelevant or poorly communicated.\n"
                "- Score 3-4: Experience is relevant but lacks executive presence or clear connection.\n"
                "- Score 5: Strong executive summary. Clearly links past experience to this specific role's requirements.\n"
            )
        else:
            rubric_text = (
                "SCORING RUBRIC (STAR METHOD):\n"
                "- Score 1-2: User fails to provide a specific Situation, Action, or Result.\n"
                "- Score 3-4: User provides S-A-R but lacks specific metrics or could be better organized.\n"
                "- Score 5 (Unicorn): Perfect delivery. Relevant Situation, specific Action/Strategy, and measurable Result ($/%).\n"
            )
        
        # Build Context
        # We explicitly set the "Target Role" using the passed title to avoid AI guessing.
        system_prompt = (
            "You are an expert Executive Interview Coach. Your goal is to conduct a realistic, "
            "high-stakes interview simulation. \n"
            f"CONTEXT:\nTarget Role: {role_title}\nJob Description: {job_posting}\nCandidate Resume: {resume_text}\n"
            "BEHAVIOR:\n"
            f"{rubric_text}"
            "BEHAVIOR:\n"
            "- Ask one hard, relevant question at a time.\n"
            "- Provide brief, constructive feedback based on the rubric above.\n"
            "- Keep questions concise but challenging.\n"
            f"- This is Question {question_count} of 5.\n"
            "- Output JSON format: { \"feedback\": \"...\", \"score\": X, \"next_question\": \"...\" }"
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
                "1. Introduce yourself simply as 'the Hiring Manager' for the position mentioned in the Job context. Do NOT use a specific name. "
                "2. Thank the candidate for spending the time with you. "
                "3. Advise that the interview will be broken down into two components: 'First, I'll ask you to give me a high level overview of your experience, then I will ask you to share specific examples of different situations that you have experienced.' "
                "4. Ask exactly: 'Let's start with your work history. Can you tell me about your previous roles and why this position is the right next step for you.'\n"
                "CRITICAL: This is the start of the interview. DO NOT provide any feedback or score. The user has not spoken yet. Just output the greeting as 'next_question'."
            )
            messages.append({
                "role": "user", 
                "content": greeting_instruction
            })
        elif question_count == 2:
            messages.append({
                "role": "user",
                "content": (
                    f"User Answer: {message}. \n"
                    "Step 1: Thank the user for sharing that.\n"
                    "Step 2: Transition to the STAR component. Say exactly: 'The next part of the interview will focus on situations that you have experienced. I'll ask you the question, and what I want you to provide is a Specific Situation or Task, the actions you took, and the results of your actions.'\n"
                    "Step 3: Ask the first STAR question."
                )
            })
        elif question_count in [3, 4]:
             messages.append({
                "role": "user",
                "content": (
                    f"User Answer: {message}. \n"
                    "Step 1: Provide brief feedback (score).\n"
                    "Step 2: Say exactly: 'Thank you. The next question that I have for you is'\n"
                    "Step 3: Ask the next interview question."
                )
             })
        elif question_count == 5:
             messages.append({
                "role": "user",
                "content": (
                    f"User Answer: {message}. \n"
                    "Step 1: Provide brief feedback (score).\n"
                    "Step 2: Say exactly: 'The final question I have for you is'\n"
                    "Step 3: Ask the final interview question."
                )
             })
        elif question_count > 5:
             messages.append({
                 "role": "user",
                 "content": f"User Answer: {message}. This was the final question. Provide feedback and end the interview by saying 'Those were all of the questions that I have for you, thank you for your time.' as the next_question."
             })
        else:
            # Fallback for any other state (shouldn't be hit if logic is perfect, but safe)
            messages.append({"role": "user", "content": message})

        # 1. Text Generation
        chat_completion = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            response_format={ "type": "json_object" }
        )
        
        ai_response_text = chat_completion.choices[0].message.content
        ai_json = json.loads(ai_response_text) 
        
        # 2. Audio Generation (Omit if empty text)
        audio_b64 = None
        if ai_json.get('next_question'):
            voice = data.get('voice', 'alloy')

            # SPEAK FEEDBACK + QUESTION
            speech_text = ai_json['next_question']
            if ai_json.get('feedback'):
                 speech_text = f"Feedback: {ai_json['feedback']} \n\n {ai_json['next_question']}"

            audio_response = client.audio.speech.create(
                model="tts-1-hd",
                voice=voice,
                input=speech_text
            )
            # Encode
            audio_b64 = base64.b64encode(audio_response.content).decode('utf-8')
        
        return jsonify({
            "response": ai_json,
            "audio": audio_b64,
            "is_complete": question_count > 5
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
            
            system_prompt = f"""
            You are the neural core of the Strategy Lab. You provide cold, clinical, yet highly effective career advice.
            
            CURRENT MISSION CONTEXT:
            {mission_context}
            
            OPERATIONAL DIRECTIVES:
            1. NEVER be dismissive. If you lack direct knowledge of a company, perform "Strategic Extrapolation."
            2. Analyze the Job Description and Role title provided in the context to infer company culture, priorities, and pain points.
            3. Provide a "calculated profile" of the company based on its industry and the type of talent they are hiring.
            4. If the user asks about a specific company and you don't have it in your training data, do not tell them to "research on their own." Instead, provide a framework of exactly WHAT they should look for and WHY it matters for their specific role.
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
            role = inputs.get('interviewer_role', 'Interviewer')
            company = inputs.get('company_name', 'Company')
            context = inputs.get('context', '')
            
            prompt = f"""
            Generate 5 High-Impact Reverse Interview Questions for a candidate interviewing with a {role} at {company}.
            
            CONTEXT:
            {context}
            
            GOAL:
            The goal is to flip the dynamic, show deep strategic insight, and uncover red flags or golden opportunities.
            
            OUTPUT FORMAT (Markdown):
            For each question:
            ### 1. The [Name of Strategy] Question
            **"The Script..."**
            *Why this works:* Explanation of the psychology.
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