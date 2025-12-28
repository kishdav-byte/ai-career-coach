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

# 2. AUTHENTICATED CLIENT HELPER (Identity Handoff)
# This creates a new Supabase client SPECIFIC to this request using the User's Token.
def get_authenticated_client():
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        # If no token, return the default client (which will fail RLS, as expected)
        return supabase
    
    try:
        # Extract the actual token "Bearer <token>"
        token = auth_header.split(" ")[1]
        
        # Create a new client that masquerades as the user
        client = create_client(
            SUPABASE_URL, 
            SUPABASE_KEY, 
            options={'headers': {'Authorization': f'Bearer {token}'}}
        )
        return client
    except Exception as e:
        print(f"Auth Handshake Error: {e}")
        return supabase

# 3. THE JOBS ROUTE (Secure Mode)
@app.route('/api/jobs', methods=['GET', 'POST'])
def manage_jobs():
    # 1. Get the Client that acts AS THE USER
    user_client = get_authenticated_client()

    # 2. Get User ID (Double Check validation)
    try:
        # We ask Supabase "Who am I?" using the forwarded token
        user_response = user_client.auth.get_user()
        user_id = user_response.user.id
    except Exception as e:
        print(f"Identity Verification Failed: {e}")
        return jsonify({"error": "Unauthorized"}), 401

    # B. GET Request (Loading the Dashboard)
    if request.method == 'GET':
        try:
            # Now we query AS THE USER. RLS will pass!
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