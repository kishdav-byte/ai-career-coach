import unittest
from unittest.mock import MagicMock, patch
import json
import sys
import os

# Add local path to import api.app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'api')))
from api.app import app

class TestLinkedInCredits(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    @patch('api.app.supabase_admin')
    def test_linkedin_access_specific_first(self, mock_supa):
        """Test that credits_linkedin are used before universal credits."""
        # 1. Setup User with BOTH types of credits
        mock_user_data = {
            'role': 'user', 'subscription_status': 'free', 'is_unlimited': False,
            'credits_linkedin': 5, 'credits': 10
        }
        
        # Mock API Key Check
        with patch('api.app.API_KEY', 'valid_key'):
            # Mock DB Select
            mock_supa.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [mock_user_data]
            
            # Mock Call OpenAI (to skip actual generation)
            with patch('api.app.call_openai', return_value='{}'):
                
                # ACTION: Call Optimize
                payload = {
                    'action': 'linkedin_optimize', 
                    'user_data': {'personal': {'email': 'test@example.com'}},
                    'email': 'test@example.com' # Simulate passing email
                }
                self.app.post('/api', json=payload)
                
                # ASSERT: Check what was updated
                # We expect 'credits_linkedin' to be updated to 4
                mock_supa.table.return_value.update.assert_called_with({'credits_linkedin': 4})
                print("\n[PASS] Specific Priority: Deducted from credits_linkedin (5->4)")

    @patch('api.app.supabase_admin')
    def test_linkedin_fallback(self, mock_supa):
        """Test that universal credits are used if specific credits are 0."""
        # 1. Setup User with ONLY Universal credits
        mock_user_data = {
            'role': 'user', 'subscription_status': 'free', 'is_unlimited': False,
            'credits_linkedin': 0, 'credits': 10
        }
        
        with patch('api.app.API_KEY', 'valid_key'):
            mock_supa.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [mock_user_data]
            with patch('api.app.call_openai', return_value='{}'):
                
                payload = {
                    'action': 'linkedin_optimize', 
                    'email': 'test@example.com'
                }
                self.app.post('/api', json=payload)
                
                # ASSERT: Check what was updated
                # We expect 'credits' to be updated to 9
                mock_supa.table.return_value.update.assert_called_with({'credits': 9})
                print("\n[PASS] Fallback: Deducted from universal credits (10->9)")

if __name__ == '__main__':
    unittest.main()
