from flask import Flask, request, jsonify
import os

app = Flask(__name__)

@app.route('/api/test')
def test():
    return jsonify({"status": "API is working!", "path": request.path})

@app.route('/api/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
def catch_all(path):
    return jsonify({
        "error": "Route not found in test handler",
        "path": f"/api/{path}",
        "method": request.method
    }), 404

# Vercel handler
handler = app
