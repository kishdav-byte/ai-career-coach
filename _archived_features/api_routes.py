        # ARCHIVED ROUTE LOGIC
        # These features were removed from api/index.py
        
        elif action == 'career_plan':
            job_title = data.get('jobTitle', '')
            company = data.get('company', '')
            job_posting = data.get('jobPosting', '')

            messages = [
                {"role": "system", "content": "You are an expert career strategist."},
                {"role": "user", "content": f"""
        Create a 30-60-90 day plan for a {job_title} role at {company}.
        
        Job Description:
        {job_posting}
        
        Format the output as JSON with the following structure:
        {{
            "day_30": ["task 1", "task 2", "task 3"],
            "day_60": ["task 1", "task 2"],
            "day_90": ["task 1", "task 2"]
        }}
        """}
            ]
            response_text = call_openai(messages, json_mode=True)
            return jsonify({"data": response_text})

        elif action == 'linkedin_optimize':
            about_me = data.get('aboutMe', '')
            
            messages = [
                {"role": "system", "content": "You are a LinkedIn profile expert."},
                {"role": "user", "content": f"""
        Optimize the following 'About Me' section for LinkedIn. Make it more professional, engaging, and SEO-friendly.
        
        Current Text:
        {about_me}
        
        Format the output as JSON:
        {{
            "recommendations": ["rec 1", "rec 2"],
            "refined_sample": "full text of the rewritten section"
        }}
        """}
            ]
            response_text = call_openai(messages, json_mode=True)
            return jsonify({"data": response_text})

        elif action == 'cover_letter':
            job_desc = data.get('jobDesc', '')
            resume_text = data.get('resume', '')
            
            messages = [
                {"role": "system", "content": "You are an expert cover letter writer."},
                {"role": "user", "content": f"""
        Write a tailored cover letter based on the following:
        
        Job Description:
        {job_desc}
        
        My Resume:
        {resume_text}
        
        Output only the body of the cover letter.
        """}
            ]
            response_text = call_openai(messages)
            return jsonify({"data": response_text})
