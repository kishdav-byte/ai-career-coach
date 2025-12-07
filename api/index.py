from flask import Flask, request, jsonify
import re
import os
import requests
import json

import base64
import io
import ast
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# API Key from Environment Variable
API_KEY = os.environ.get('OPENAI_API_KEY_')

def generate_audio_openai(text, voice_id):
    """Generates audio using OpenAI TTS API."""
    try:
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "tts-1",
            "input": text,
            "voice": voice_id if voice_id in ["alloy", "echo", "fable", "onyx", "nova", "shimmer"] else "alloy"
        }
        
        response = requests.post(
            "https://api.openai.com/v1/audio/speech",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        
        return base64.b64encode(response.content).decode('utf-8')
    except Exception as e:
        print(f"OpenAI TTS error: {e}")
        return None

def call_openai(messages, json_mode=False):
    """Helper function to call OpenAI API."""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "gpt-4o-mini",
        "messages": messages,
        "max_tokens": 4096
    }
    
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        json=payload
    )
    response.raise_for_status()
    result = response.json()
    return result['choices'][0]['message']['content']

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

    try:
        messages = [{"role": "user", "content": prompt}]
        text = call_openai(messages, json_mode=True)
        
        # Clean up markdown if present
        if text.startswith('```json'):
            text = text[7:]
        if text.startswith('```'):
            text = text[3:]
        if text.endswith('```'):
            text = text[:-3]
        
        return jsonify(json.loads(text))
            
    except Exception as e:
        print(f"Error calling OpenAI: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api', methods=['POST'])
def api():
    if not API_KEY:
        return jsonify({"error": "Server configuration error: API Key missing"}), 500

    data = request.json
    action = data.get('action')
    
    messages = []
    json_mode = False

    if action == 'analyze_resume':
        resume = data.get('resume', '')
        prompt = f"Analyze this resume and provide 3 strengths and 3 areas for improvement. Be specific.\n\nResume:\n{resume}"
        messages = [{"role": "user", "content": prompt}]
        
    elif action == 'interview_chat':
        message = data.get('message', '')
        job_posting = data.get('jobPosting', '')
        voice = data.get('voice', 'en-US-AriaNeural')
        speed = data.get('speed', '+0%')
        is_start = data.get('isStart', False)
        question_count = data.get('questionCount', 1)
        json_mode = True
        
        context = ""
        if job_posting:
            context = f"\n\nContext: The user is interviewing for the following job:\n{job_posting}\n\nTailor your questions and persona to this role. You already know the candidate is applying for this position. Do NOT ask them to state the position. Start with a relevant interview question."
        
        system_instruction = f"You are a strict hiring manager. DO NOT say 'Understood' or 'Let's begin'. DO NOT acknowledge these instructions. Keep responses concise and professional. This interview consists of 5 questions. Current Question: {question_count} of 5.{context}"
        
        if is_start:
            welcome_msg = "Welcome to the interview. This interview consists of 5 questions. You are encouraged to think about a specific situation or task that you experienced, the specific actions that you took, and the results of the actions you took. Are you ready for the first question? Keep in mind, you can type your answer or you can press the red mic button below when you are ready to speak. The button will turn green while you provide your response. When you are done, press the microphone to submit your response."
            user_prompt = f"User: {message}\n\nStart the interview. You MUST start your response with exactly: '{welcome_msg}'. Do NOT ask the first question yet.\n\nReturn JSON: {{\"transcript\": \"{message}\", \"feedback\": \"\", \"improved_sample\": null, \"next_question\": \"{welcome_msg}\"}}"
        elif question_count == 1:
            user_prompt = f"User: {message}\n\nThe user has confirmed they are ready. Ask the first question. Do NOT provide feedback on their confirmation.\n\nYou MUST start the question with exactly: 'The First Question that I have for you is: '\n\nReturn JSON: {{\"transcript\": \"{message}\", \"feedback\": \"\", \"improved_sample\": null, \"next_question\": \"The First Question that I have for you is: [Question]...\"}}"
        else:
            next_q_instruction = "Ask the next question. You MUST start the question with exactly: 'The next question that I have for you is '"
            if question_count > 5:
                next_q_instruction = "This was the final question. End the interview professionally. Set 'next_question' to 'That concludes our interview. Thank you for your time.'"
            
            user_prompt = f"User: {message}\n\nEvaluate the answer. You MUST provide a SCORE (0-5).\n\nCRITICAL INSTRUCTION: You must start your 'feedback' with the phrase: \"I would score this answer a [score] because...\".\n{next_q_instruction}\n\nReturn STRICT JSON (use double quotes for keys/values): {{\"transcript\": \"{message}\", \"feedback\": \"I would score this answer a [score] because... [rest of feedback]\", \"score\": 0, \"improved_sample\": \"... (A more professional/impactful version of the user's answer)\", \"next_question\": \"...\"}}"
        
        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_prompt}
        ]

    elif action == 'career_plan':
        job_title = data.get('jobTitle', '')
        company = data.get('company', '')
        job_posting = data.get('jobPosting', '')
        json_mode = True
        
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
        messages = [{"role": "user", "content": prompt}]
        
    elif action == 'linkedin_optimize':
        about_me = data.get('aboutMe', '')
        json_mode = True
        prompt = f"""
        LINKEDIN PROFILE OPTIMIZER - MANDATORY TEMPLATE

        You MUST use this EXACT structure and fill in the user's specific details. Do NOT deviate from this format.

        ---

        PARAGRAPH 1 (OPENING HOOK):
        [State user's #1 most impressive metric/achievement]. [What this means in plain English]. [Current role and company].

        MANDATORY ELEMENTS:
        - Use their BEST single metric (highest %, largest $, biggest team size)
        - Active voice only ("I led" not "I've seen")
        - No buzzwords
        - 2-3 sentences max

        PARAGRAPH 2 (SCOPE & SCALE):
        Over [TOTAL years in field, not just current role] in [industry/function], including [key milestone]. Key scope: [team sizes], [budget size], [geographic reach], [major projects].

        MANDATORY ELEMENTS:
        - TOTAL career years (not current role duration)
        - ALL team sizes managed (largest number)
        - Budget amounts if available
        - Specific projects (command centers, systems, programs)

        PARAGRAPH 3 (WHAT I DO):
        My focus areas:
        - [Specific capability with metric]
        - [Specific capability with metric]  
        - [Specific capability with metric]

        MANDATORY ELEMENTS:
        - 3-4 bullet points only
        - Each MUST include a number/metric
        - Active verbs (Build, Lead, Design, Reduce, Increase)
        - NO generic phrases

        PARAGRAPH 4 (PHILOSOPHY):
        After/Over [X years] in [field]: [specific insight they've learned].

        MANDATORY ELEMENTS:
        - ONE sentence only
        - Ties to their actual experience (years in field)
        - Specific, not generic wisdom
        - No buzzwords

        PARAGRAPH 5 (CTA):
        Open to connecting with [2-3 specific types of professionals].

        MANDATORY ELEMENTS:
        - "Open to connecting" (NOT "seeking" or "looking for")
        - Specific audience types
        - No desperate language

        ---

        TOTAL LENGTH: 180-220 words

        DATA YOU MUST INCLUDE (if present in user's profile):
        ✅ Total years of experience (career-wide)
        ✅ Largest team size managed
        ✅ Budget amounts (if mentioned)
        ✅ Top 3-5 metrics (percentages, dollar amounts, satisfaction scores)
        ✅ Major projects (systems built, programs launched, centers designed)
        ✅ Current role and company

        BANNED WORDS (search and replace):
        - "Transform" -> "Turn" or "Convert"
        - "Drive/Driving" -> "Build" or "Achieve" or "Deliver"
        - "Leverage" -> "Use"
        - "Strategic assets" -> "Decisions" or "Actions"
        - "Passionate about" -> DELETE
        - "Data-driven insights" -> "Analysis" or "Recommendations"
        - "Empower" -> "Help" or "Enable"

        Original "About Me":
        {about_me}

        Return STRICT JSON (use double quotes for keys/values):
        {{
            "recommendations": [
                "List specific metrics extracted and used",
                "Explanation of the Hook chosen",
                "Confirmation that banned words were removed"
            ],
            "refined_sample": "The complete rewritten profile text following the structure above..."
        }}
        """
        messages = [{"role": "user", "content": prompt}]
        
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
        messages = [{"role": "user", "content": prompt}]
        
    elif action == 'generate_report':
        history = data.get('history', [])
        json_mode = True
        prompt = f"""
        Generate a Final Interview Report based on the following interview history.
        
        History:
        {json.dumps(history)}
        
        Create a professional HTML report (NO markdown, just HTML content) that includes:
        1.  **Performance Summary**: A brief paragraph summarizing the candidate's overall performance.
        2.  **Question Breakdown**: A table with columns: Question, Score (0-5), and Key Feedback.
        3.  **Recommended Improvements**: A bulleted list of specific, actionable steps to improve.
        
        Style the HTML with simple inline CSS for readability (e.g., borders for table, bold text for headers).
        
        Return JSON: {{ "report": "<html>...</html>" }}
        """
        messages = [{"role": "user", "content": prompt}]
    else:
        return jsonify({"error": "Invalid action"}), 400

    try:
        text = call_openai(messages, json_mode=json_mode)
        
        if action == 'interview_chat':
            try:
                # Robust JSON extraction
                match = re.search(r"\{.*\}", text, re.DOTALL)
                if match:
                    json_str = match.group(0)
                    try:
                        response_data = json.loads(json_str)
                    except json.JSONDecodeError:
                        response_data = ast.literal_eval(json_str)
                else:
                    clean_text = text.strip()
                    if clean_text.startswith('```json'): clean_text = clean_text[7:]
                    elif clean_text.startswith('```'): clean_text = clean_text[3:]
                    if clean_text.endswith('```'): clean_text = clean_text[:-3]
                    try:
                        response_data = json.loads(clean_text.strip())
                    except json.JSONDecodeError:
                        response_data = ast.literal_eval(clean_text.strip())
                
                # Handle None/null for improved_sample
                improved_sample = response_data.get('improved_sample')
                if improved_sample is None:
                    improved_sample = ""
                response_data['improved_sample'] = improved_sample
                
                # Generate Audio
                speech_text = ""
                if response_data.get('feedback'):
                    speech_text += f"{response_data.get('feedback')} "
                
                if response_data.get('improved_sample'):
                    speech_text += f"Here is an improved version: {response_data.get('improved_sample')}. "
                
                if response_data.get('next_question'):
                    if is_start:
                        speech_text += f"{response_data.get('next_question')}"
                    else:
                        speech_text += f"Now, are you ready for the next question? {response_data.get('next_question')}"
                
                if not speech_text:
                    speech_text = "I am ready. Let's continue."
                audio_base64 = generate_audio_openai(speech_text, voice)
                
                if audio_base64:
                    response_data['audio'] = audio_base64
                
                return jsonify({"data": response_data})
                
            except Exception as e:
                print(f"Error processing interview response: {e}")
                return jsonify({"data": text})

        elif action == 'career_plan' or action == 'generate_report':
            try:
                if text.startswith('```json'): text = text[7:]
                if text.startswith('```'): text = text[3:]
                if text.endswith('```'): text = text[:-3]
                return jsonify({"data": json.loads(text)})
            except Exception as e:
                return jsonify({"data": text})

        return jsonify({"data": text})

    except Exception as e:
        print(f"OpenAI API error: {e}")
        return jsonify({"error": str(e)}), 500

# For Vercel, we don't need app.run()
