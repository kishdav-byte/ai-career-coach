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

# Expose app
app = app