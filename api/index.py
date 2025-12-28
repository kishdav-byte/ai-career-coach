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

# 2. AUTH HELPER (This fixes the Security!)
# It extracts the token from the header so we know who the user is.
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

# 3. THE JOBS ROUTE
@app.route('/api/jobs', methods=['GET', 'POST'])
def manage_jobs():
    # A. Security Check
    user_id = get_user_id_from_token()
    if not user_id:
        # If we can't identify the user, block the request
        return jsonify({"error": "Unauthorized"}), 401

    # B. GET Request (Loading the Dashboard/Interview)
    if request.method == 'GET':
        try:
            response = supabase.table('user_jobs').select(
                "id, job_title, company_name, status, job_description"
            ).eq('user_id', user_id).execute()

            # Fix: Return the EXACT keys the frontend expects
            clean_jobs = []
            for job in response.data:
                clean_jobs.append({
                    "id": job.get('id'),
                    "job_title": job.get('job_title', ''),     # Fixed mapping
                    "company_name": job.get('company_name', ''), # Fixed mapping
                    "status": job.get('status', 'Identified'),
                    "job_description": job.get('job_description', '') # Fixed mapping
                })
            return jsonify(clean_jobs), 200
        except Exception as e:
            return jsonify([]), 200

    # C. POST Request (Initiating Campaign)
    if request.method == 'POST':
        try:
            data = request.json
            new_job = {
                "user_id": user_id,
                # Fix: Look for the keys your Frontend is ACTUALLY sending
                "job_title": data.get('job_title', 'New Role'),
                "company_name": data.get('company_name', 'New Co'),
                "status": "Identified",
                "job_description": data.get('job_description', '')
            }
            res = supabase.table('user_jobs').insert(new_job).execute()
            return jsonify(res.data), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500

# Expose app
app = app