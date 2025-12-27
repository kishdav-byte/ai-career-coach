from flask import Flask, request, jsonify
from supabase import create_client, Client
import os

app = Flask(__name__)

# 1. SETUP SUPABASE
# We wrap this in try/except so import errors don't crash Vercel immediately
try:
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    print(f"Supabase Init Error: {e}")

# 2. DEFINE THE AUTH HELPER (This was likely missing!)
def get_user_id_from_token():
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None
    try:
        token = auth_header.split(" ")[1]
        user = supabase.auth.get_user(token)
        return user.user.id
    except Exception as e:
        print(f"Token Error: {e}")
        return None

# 3. THE JOBS ROUTE (Safe Mode)
@app.route('/api/jobs', methods=['GET', 'POST'])
def manage_jobs():
    # Auth Check
    try:
        user_id = get_user_id_from_token()
        if not user_id:
            return jsonify({"error": "Unauthorized"}), 401
    except Exception as e:
        print(f"Auth Crash: {e}")
        return jsonify({"error": "Auth Failed"}), 401

    if request.method == 'GET':
        try:
            # Explicit Column Select to prevent schema crashes
            response = supabase.table('user_jobs').select(
                "id, job_title, company_name, status, job_description"
            ).eq('user_id', user_id).execute()

            clean_jobs = []
            for job in response.data:
                clean_jobs.append({
                    "id": job.get('id'),
                    "role": job.get('job_title', 'Unknown Role'),
                    "company": job.get('company_name', 'Unknown Co'),
                    "status": job.get('status', 'Identified'),
                    "description": job.get('job_description', '')
                })
            return jsonify(clean_jobs), 200
        except Exception as e:
            print(f"DB Error: {e}")
            # Return empty list if DB fails (Keeps dashboard alive)
            return jsonify([]), 200

    # Handle POST
    if request.method == 'POST':
        try:
            data = request.json
            new_job = {
                "user_id": user_id,
                "job_title": data.get('role', 'New Role'),
                "company_name": data.get('company', 'New Co'),
                "status": "Identified",
                "job_description": data.get('description', '')
            }
            res = supabase.table('user_jobs').insert(new_job).execute()
            return jsonify(res.data), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500

# Expose app for Vercel
app = app
