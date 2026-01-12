import unittest
import html
import sys
import os
import asyncio
import requests
from unittest.mock import patch, MagicMock

# Add project root path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)
# Add src to path so 'import config' works inside helper.py
sys.path.append(os.path.join(project_root, 'src'))

# Mock Config BEFORE importing helper
with patch.dict('sys.modules', {'config': MagicMock()}):
    import config
    # Set dummy values
    config.TELEGRAM_TOKEN = "TEST_TOKEN"
    config.TELEGRAM_CHAT_ID = "12345"
    config.LOG_FILENAME = "test.log"
    
    # Import target module
    from src.utils.helper import kirim_tele, logger

class TestNotificationSafety(unittest.TestCase):
    
    def test_html_escape_logic(self):
        """1. Verify HTML Escaping Logic (for AI Reason)"""
        print("\n--- TEST: HTML Escaping ---")
        
        dirty_inputs = [
            ("Price < 500", "Price &lt; 500"),
            ("RSI > 70", "RSI &gt; 70"),
            ("Tag <b>Bold</b>", "Tag &lt;b&gt;Bold&lt;/b&gt;"),
            ("Normal Text", "Normal Text")
        ]
        
        for raw, expected in dirty_inputs:
            escaped = html.escape(raw)
            print(f"Input: '{raw}' -> Escaped: '{escaped}'")
            self.assertEqual(escaped, expected)

    @patch('src.utils.helper.asyncio.to_thread')
    @patch('requests.post')
    def test_kirim_tele_success(self, mock_post, mock_to_thread):
        """2. Verify kirim_tele handles 200 OK correctly"""
        print("\n--- TEST: Telegram Success (200) ---")
        print(f"DEBUG: Test sees requests.post as {requests.post}")
        
        # Setup Mock to_thread to run sync
        async def side_effect(func, *args):
            return func(*args)
        mock_to_thread.side_effect = side_effect
        
        # Setup Mock Response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Run async function
        asyncio.run(kirim_tele("Hello World"))
        
        # Verify call
        mock_post.assert_called_once()
        print("✅ Request sent and 200 OK handled.")

    @patch('src.utils.helper.asyncio.to_thread')
    @patch('requests.post')
    def test_kirim_tele_failure_logging(self, mock_post, mock_to_thread):
        """3. Verify kirim_tele LOGS error on 400 Bad Request"""
        print("\n--- TEST: Telegram Failure (400) ---")
        
        # Setup Mock to_thread to run sync
        async def side_effect(func, *args):
            return func(*args)
        mock_to_thread.side_effect = side_effect
        
        # Setup Mock Response
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request: Can't parse entities"
        mock_post.return_value = mock_response
        
        # We need to capture logger output
        with patch.object(logger, 'error') as mock_logger:
            asyncio.run(kirim_tele("Broken Message"))
            
            # Verify Logger was called
            mock_logger.assert_called()
            args, _ = mock_logger.call_args
            log_msg = args[0]
            
            print(f"Captured Log: {log_msg}")
            self.assertIn("Telegram Send Failed", log_msg)
            self.assertIn("Status 400", log_msg)

if __name__ == '__main__':
    unittest.main()
