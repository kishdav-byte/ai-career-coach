from flask import Flask, request, jsonify
from supabase import create_client, Client
import os
import json
import base64

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
            response = user_client.table('user_jobs').select(
                "id, job_title, company_name, status, job_description"
            ).eq('user_id', user_id).execute()

            clean_jobs = []
            for job in response.data:
                clean_jobs.append({
                    "id": job.get('id'),
                    "job_title": job.get('job_title', ''),     
                    "company_name": job.get('company_name', ''), 
                    "status": job.get('status', 'Identified'),
                    "job_description": job.get('job_description', '') 
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
                "status": "Identified",
                "job_description": data.get('job_description', '')
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
        if 'notes' in data: updates['notes'] = data['notes']
        if 'salary_target' in data: updates['salary_target'] = data['salary_target']
        
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
            f"- role: The specific job title\n"
            f"- company: The company name\n"
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


        # Build Context
        system_prompt = (
            "You are an expert Executive Interview Coach. Your goal is to conduct a realistic, "
            "high-stakes interview simulation. \n"
            f"CONTEXT:\nJob: {job_posting}\nCandidate Resume: {resume_text}\n"
            "BEHAVIOR:\n"
            "- Ask one hard, relevant question at a time.\n"
            "- If the user just answered, provide brief, critical feedback (score 1-5) on their answer before moving on.\n"
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
                "1. Introduce yourself as the hiring manager for the position mentioned in the Job context. "
                "2. Thank the candidate for spending the time with you. "
                "3. Advise that the interview will be broken down into two components: 'First, I'll ask you to give me a high level overview of your experience, then I will ask you to share specific examples of different situations that you have experienced.' "
                "4. Ask exactly: 'Let's start with your work history. Can you tell me about your previous roles and why this position is the right next step for you.'\n"
                "CRITICAL: This is the start of the interview. DO NOT provide any feedback or score. The user has not spoken yet. Just output the greeting as 'next_question'."
            )
            messages.append({
                "role": "user", 
                "content": greeting_instruction
            })
        elif question_count > 5:
             messages.append({
                 "role": "user",
                 "content": f"User Answer: {message}. This was the final question. Provide feedback and end the interview by saying 'Thank you for your time, that concludes our session.' as the next_question."
             })
        else:
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
            audio_response = client.audio.speech.create(
                model="tts-1-hd",
                voice=voice,
                input=ai_json['next_question']
            )
            # Encode
            audio_b64 = base64.b64encode(audio_response.content).decode('utf-8')
        
        return jsonify({
            "response": ai_json,
            "audio": audio_b64,
            "is_complete": False 
        }), 200

    except Exception as e:
        print(f"Feedback Error: {e}")
        return jsonify({"error": str(e)}), 500

# Expose app
app = app