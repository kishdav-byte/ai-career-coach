from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return jsonify({
        "status": "alive",
        "env_check": {
            "stripe_key": "present" if os.environ.get('STRIPE_SECRET_KEY') else "missing",
            "supabase_url": "present" if os.environ.get('SUPABASE_URL') else "missing"
        }
    })
