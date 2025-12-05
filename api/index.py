from flask import Flask, request, jsonify
import os
import requests
import json
from gtts import gTTS
import base64
import io
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# API Key from Environment Variable
API_KEY = os.environ.get('GEMINI_API_KEY')

def generate_audio_gtts(text, voice_id):
    """Generates audio using gTTS."""
    tld = 'us'
    if 'GB' in voice_id:
        tld = 'co.uk'
    
    try:
        tts = gTTS(text, lang='en', tld=tld)
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        return base64.b64encode(mp3_fp.read()).decode('utf-8')
    except Exception as e:
        print(f"gTTS error: {e}")
        return None

@app.route('/api/optimize', methods=['POST'])
def optimize_resume_content():
    if not API_KEY:
        return jsonify({"error": "Server configuration error: API Key missing"}), 500

    data = request.json
    user_data = data.get('user_data')
    template_name = data.get('template_name', 'modern')
    job_description = data.get('job_description', '')

    # Construct Prompt
    base_instruction = "Optimize the following resume content for a professional look. Improve clarity and impact."
    
    tailoring_instruction = ""
    if job_description:
        tailoring_instruction = f"\n\nTARGET JOB DESCRIPTION:\n{job_description}\n\nTAILORING INSTRUCTION: Tailor the resume content to align with the above Job Description. Use relevant keywords and phrasing from the JD. Emphasize matching skills. Do NOT invent new experience or skills."

    formatting_instruction = ""
    if template_name == 'condensed':
        formatting_instruction = "\n\nFORMATTING CRITICAL INSTRUCTION: Rewrite the 'Experience' descriptions as a list of concise, high-impact bullet points. Start each bullet with a hyphen (-). Do NOT use paragraphs. This formatting requirement overrides any other style instructions."
    else:
        formatting_instruction = "\n\nFORMATTING INSTRUCTION: Use professional paragraphs for the experience section. Do not use bullet points."

    prompt = f"""
    {base_instruction}
    {tailoring_instruction}
    {formatting_instruction}

    Here is the data:
    {json.dumps(user_data)}

    Return ONLY valid JSON with the exact same structure (personal, summary, experience, education, skills).
    Do not include markdown formatting (like ```json). Just the raw JSON string.
    """

    # Call Gemini API
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={API_KEY}"
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }

    try:
        response = requests.post(api_url, json=payload)
        response.raise_for_status()
        result = response.json()
        
        if 'candidates' in result and result['candidates']:
            text = result['candidates'][0]['content']['parts'][0]['text']
            # Clean up markdown if present
            if text.startswith('```json'):
                text = text[7:]
            if text.startswith('```'):
                text = text[3:]
            if text.endswith('```'):
                text = text[:-3]
            
            return jsonify(json.loads(text))
        else:
            return jsonify({"error": "Invalid response from Gemini", "raw": result}), 500
            
    except Exception as e:
        print(f"Error calling Gemini: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api', methods=['POST'])
def api():
    if not API_KEY:
        return jsonify({"error": "Server configuration error: API Key missing"}), 500

    data = request.json
    action = data.get('action')
    
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={API_KEY}"
    
    contents = []

    if action == 'analyze_resume':
        resume = data.get('resume', '')
        prompt = f"Analyze this resume and provide 3 strengths and 3 areas for improvement. Be specific.\n\nResume:\n{resume}"
        contents = [{"parts": [{"text": prompt}]}]
    elif action == 'interview_chat':
        message = data.get('message', '')
        job_posting = data.get('jobPosting', '')
        audio_data = data.get('audio', '') # Base64 audio string
        voice = data.get('voice', 'en-US-AriaNeural')
        speed = data.get('speed', '+0%')
        
        context = ""
        if job_posting:
            context = f"\n\nContext: The user is interviewing for the following job:\n{job_posting}\n\nTailor your questions and persona to this role. You already know the candidate is applying for this position. Do NOT ask them to state the position. Start with a relevant interview question."
        
        system_instruction = f"System Instruction: You are a strict hiring manager. Keep responses concise and professional.{context}"
        
        if audio_data:
            if "base64," in audio_data:
                audio_data = audio_data.split("base64,")[1]
                
            contents = [{
                "parts": [
                    {"text": f"{system_instruction}\n\nThe user has provided an audio answer. Please transcribe it exactly.\nCRITICAL INSTRUCTION: If the audio is silent, unclear, or contains no speech, set 'transcript' to '(No speech detected)', set 'feedback' to 'I didn\\'t catch that.', and set 'next_question' to 'Could you please repeat your answer?'.\nOtherwise, provide a critique, an IMPROVED VERSION of their answer, and the next question.\n\nReturn JSON: {{'transcript': '...', 'feedback': '...', 'improved_sample': '... (A more professional/impactful version of the user\\'s answer)', 'next_question': '...'}}"},
                    {
                        "inline_data": {
                            "mime_type": "audio/webm",
                            "data": audio_data
                        }
                    }
                ]
            }]
        else:
            contents = [{"parts": [{"text": f"{system_instruction}\n\nUser: {message}"}]}]

    elif action == 'career_plan':
        job_title = data.get('jobTitle', '')
        company = data.get('company', '')
        job_posting = data.get('jobPosting', '')
        
        prompt = f"""
        Create a 30-60-90 day plan for a {job_title} role at {company}.
        
        Job Posting / Description:
        {job_posting}
        
        Based on the job description (if provided), tailor the plan to specific responsibilities and requirements.
        
        Return ONLY valid JSON with the following structure:
        {{
            "day_30": ["bullet point 1", "bullet point 2", ...],
            "day_60": ["bullet point 1", "bullet point 2", ...],
            "day_90": ["bullet point 1", "bullet point 2", ...]
        }}
        Do not include markdown formatting. Just the raw JSON string.
        """
        contents = [{"parts": [{"text": prompt}]}]
    elif action == 'linkedin_optimize':
        about_me = data.get('aboutMe', '')
        prompt = f"Rewrite this LinkedIn 'About Me' section to be more SEO-friendly, professional, and engaging.\n\nOriginal:\n{about_me}"
        contents = [{"parts": [{"text": prompt}]}]
    elif action == 'cover_letter':
        job_desc = data.get('jobDesc', '')
        resume = data.get('resume', '')
        prompt = f"""
        Write a professional cover letter for this job description based on the provided resume.
        
        CRITICAL INSTRUCTIONS:
        1. Do NOT include the personal header (Name, Email, Phone, Location) at the top. This will be added programmatically.
        2. Start the letter immediately with the Date, followed by the Recipient Details (e.g., Hiring Manager, Company Name).
        3. Use the Name provided in the resume for the signature at the bottom.
        4. Tailor the content to the Job Description, highlighting relevant experience from the Resume.
        
        Job Description:
        {job_desc}
        
        Resume:
        {resume}
        """
        contents = [{"parts": [{"text": prompt}]}]
    else:
        return jsonify({"error": "Invalid action"}), 400

    payload = {
        "contents": contents
    }

    try:
        response = requests.post(api_url, json=payload)
        response.raise_for_status()
        result = response.json()
        
        if 'candidates' in result and result['candidates']:
            text = result['candidates'][0]['content']['parts'][0]['text']
            
            if action == 'interview_chat' and data.get('audio'):
                try:
                    if text.startswith('```json'): text = text[7:]
                    if text.startswith('```'): text = text[3:]
                    if text.endswith('```'): text = text[:-3]
                    
                    response_data = json.loads(text)
                    speech_text = f"{response_data.get('feedback', '')} Here is an improved version: {response_data.get('improved_sample', '')}. Now, are you ready for the next question? {response_data.get('next_question', '')}"
                    audio_base64 = generate_audio_gtts(speech_text, voice)
                    
                    if audio_base64:
                        response_data['audio'] = audio_base64
                    return jsonify({"data": response_data})
                    
                except Exception as e:
                    print(f"Error processing voice response: {e}")
                    return jsonify({"data": text})

            elif action == 'interview_chat':
                try:
                    audio_base64 = generate_audio_gtts(text, voice)
                    if audio_base64:
                        return jsonify({"data": {"text": text, "audio": audio_base64}})
                    else:
                         return jsonify({"data": text})
                except Exception as e:
                    return jsonify({"data": text})

            elif action == 'career_plan':
                try:
                    if text.startswith('```json'): text = text[7:]
                    if text.startswith('```'): text = text[3:]
                    if text.endswith('```'): text = text[:-3]
                    return jsonify({"data": json.loads(text)})
                except Exception as e:
                    return jsonify({"data": text})

            return jsonify({"data": text})

        else:
            return jsonify({"error": "Invalid response from Gemini", "raw": result})
            
    except Exception as e:
        return jsonify({"error": str(e)})

# For Vercel, we don't need app.run()
