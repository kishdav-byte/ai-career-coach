import os
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
env_path = os.path.join(BASE_DIR, '.env')
load_dotenv(env_path)

print(f"DEBUG: Loading .env from {env_path}")
print(f"DEBUG: OPENAI_API_KEY present: {'OPENAI_API_KEY' in os.environ}")
print(f"DEBUG: OPENAI_API_KEY_ present: {'OPENAI_API_KEY_' in os.environ}")

# Polyfill API Key if using underscore variant
if 'OPENAI_API_KEY' not in os.environ and 'OPENAI_API_KEY_' in os.environ:
    print("DEBUG: Polyfilling OPENAI_API_KEY from OPENAI_API_KEY_")
    os.environ['OPENAI_API_KEY'] = os.environ['OPENAI_API_KEY_']

from flask import send_from_directory, request
from api.index import app

print(f"DEBUG: BASE_DIR: {BASE_DIR}")
print(f"DEBUG: App Root Path (before): {app.root_path}")

# Patch app root path to match current directory (optional, but good practice)
app.root_path = BASE_DIR

print(f"DEBUG: App Root Path (after): {app.root_path}")

@app.route('/app')
def serve_app():
    print(f"DEBUG: Serving {BASE_DIR}/app.html")
    try:
        return send_from_directory(BASE_DIR, 'app.html')
    except Exception as e:
        print(f"ERROR: {e}")
        return str(e), 500

@app.route('/')
def serve_index():
    print(f"DEBUG: Serving {BASE_DIR}/index.html")
    return send_from_directory(BASE_DIR, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    # Try serving exact file from BASE_DIR
    if os.path.exists(os.path.join(BASE_DIR, path)):
        return send_from_directory(BASE_DIR, path)
    
    # Try serving HTML file (e.g. /login -> login.html)
    if os.path.exists(os.path.join(BASE_DIR, path + '.html')):
        return send_from_directory(BASE_DIR, path + '.html')

    print(f"DEBUG: 404 for {path}")
    return "File not found", 404

if __name__ == '__main__':
    print(f"🚀 Starting AI Career Coach locally at http://localhost:5001")
    app.run(port=5001, debug=True)
