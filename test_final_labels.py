#!/usr/bin/env python3
import os, sys
sys.path.insert(0, '/Users/davidkish/Desktop/AI Career Coach')
from api.index import app
from scoring_option_b import calculate_rubric_score_option_b
import api.index as api_module

api_module.calculate_rubric_score = calculate_rubric_score_option_b

client = app.test_client()
history = []

print("Testing score labels in final report...")

# Quick interview
turns = [
    {'turn': 1, 'msg': 'READY', 'is_start': True},
    {'turn': 2, 'msg': 'MBA, $35M EBITDA growth'},
    {'turn': 3, 'msg': 'I facilitated sessions resulting in $35M EBITDA growth'},
    {'turn': 4, 'msg': 'I managed AI projects and delivered on time'},
    {'turn': 5, 'msg': 'I implemented compliance for 300+ systems with 100% compliance'},
    {'turn': 6, 'msg': 'I presented a roadmap showing $35M value'},
    {'turn': 7, 'msg': '22% revenue increase was the North Star metric'},
]

for test in turns:
    res = client.post('/api/get-feedback', json={
        'message': test['msg'],
        'isStart': test.get('is_start', False),
        'questionCount': test['turn'],
        'history': history,
        'jobPosting': 'Senior Manager',
        'resumeText': 'MBA',
        'job_title': 'Senior Manager'
    })
    if res.status_code == 200:
        data = res.get_json()
        ai_json = data.get('response', {})
        history.append({
            'question': ai_json.get('next_question', ''),
            'answer': test['msg'],
            'feedback': ai_json.get('feedback', ''),
            'internal_score': ai_json.get('internal_score', 0)
        })

# Generate final report
print("\nGenerating final report...")
res = client.post('/api/get-feedback', json={
    'message': 'Thank you',
    'isStart': False,
    'questionCount': 8,
    'history': history,
    'jobPosting': 'Senior Manager',
    'resumeText': 'MBA',
    'job_title': 'Senior Manager'
})

if res.status_code == 200:
    data = res.get_json()
    ai_json = data.get('response', {})
    
    if 'formatted_report' in ai_json:
        report = ai_json['formatted_report']
        score = ai_json.get('average_score', 0)
        
        import re
        # Extract score and label
        match = re.search(r'text-4xl[^>]*>([^<]+)<.*?text-indigo-300[^>]*>([^<]+)<', report, re.DOTALL)
        
        if match:
            score_display = match.group(1).strip()
            label = match.group(2).strip()
            
            print("\n" + "="*60)
            print("FINAL REPORT - USER SEES:")
            print("="*60)
            print(f"Score: {score_display}")
            print(f"Label: {label}")
            print("="*60)
            
            if label in ['Well Done', 'Average', 'Needs Work']:
                print(f"\n🎉 SUCCESS! User-friendly labels working!")
                print(f"   Numeric score: {score}/4.0")
                print(f"   User-friendly: {label}")
            else:
                print(f"\n⚠️  Unexpected label: {label}")
        else:
            print("❌ Could not extract score display from report")
    else:
        print("❌ No formatted_report in response")
else:
    print(f"❌ Request failed with status {res.status_code}")
