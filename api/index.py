from flask import Flask, request, jsonify
from supabase import create_client, Client
import os

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

        # 2. Configure OpenAI
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

# Expose app
app = app