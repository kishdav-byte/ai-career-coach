import unittest
from unittest.mock import MagicMock, patch
import json
import sys
import os

# Add local path to import api.app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'api')))
from api.app import app

class TestLinkedInFailure(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    @patch('api.app.call_openai')
    @patch('api.app.supabase_admin')
    def test_linkedin_clean_json(self, mock_supa, mock_openai):
        """Test with perfect JSON response."""
        # 1. Mock DB (Credits exist)
        mock_supa.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            'role': 'user', 'credits_linkedin': 5, 'credits': 10
        }]
        
        # 2. Mock OpenAI (Clean JSON)
        mock_response = json.dumps({
            "recommendations": ["Fix typo", "Add metrics"],
            "refined_content": "This is the refined content."
        })
        mock_openai.return_value = mock_response

        # 3. Action
        payload = {
            'action': 'linkedin_optimize', 
            'email': 'test@example.com',
            'aboutMe': 'My rough draft.'
        }
        res = self.app.post('/api', json=payload)
        
        # 4. Result
        data = res.get_json()
        print(f"\n[Clean JSON] Response: {data}")
        self.assertEqual(data.get('refined_content'), "This is the refined content.")

    @patch('api.app.call_openai')
    @patch('api.app.supabase_admin')
    def test_linkedin_markdown_json(self, mock_supa, mock_openai):
        """Test with Markdown wrapped JSON (Common OpenAI quirk)."""
        mock_supa.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            'role': 'user', 'credits_linkedin': 5
        }]
        
        # Mock OpenAI (Markdown JSON)
        inner_json = json.dumps({
            "recommendations": ["Fix typo"],
            "refined_content": "Refined content from markdown."
        })
        mock_openai.return_value = f"```json\n{inner_json}\n```"

        payload = {'action': 'linkedin_optimize', 'email': 'test@example.com', 'aboutMe': 'Draft'}
        res = self.app.post('/api', json=payload)
        
        data = res.get_json()
        print(f"\n[Markdown JSON] Response: {data}")
        
        # This is where it likely fails currently (returns raw string in refined_content)
        if data.get('refined_content') == "Refined content from markdown.":
             print("[PASS] Handled Markdown correctly")
        else:
             print("[FAIL] Output is likely the raw string or empty")

if __name__ == '__main__':
    unittest.main()
