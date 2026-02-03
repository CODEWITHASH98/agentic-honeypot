import asyncio
import sys
import os
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.callback.guvi_callback import guvi_callback

async def test_callback_trigger():
    print("Testing Callback Logic...")
    
    # Mock httpx client
    with patch("httpx.AsyncClient") as mock_client:
        mock_post = MagicMock()
        mock_post.status_code = 200
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_post
        
        # Test Data
        session_id = "test-session-123"
        extracted_data = {
            "upi_ids": ["scammer@ybl"],
            "bank_accounts": ["1234567890"],
            "urls": ["http://phishing.com"],
            "phone_numbers": ["+919876543210"],
            "keywords": ["urgent", "pay"]
        }
        
        # 1. Test sending logic
        print("1. Sending callback payload...")
        success = await guvi_callback.send_final_result(
            session_id=session_id,
            scam_detected=True,
            total_messages=10,
            extracted_intelligence=extracted_data,
            agent_notes="Test notes"
        )
        
        assert success == True
        print("[SUCCESS] Callback sent successfully")
        
        # 2. Test Exit Logic
        print("2. Testing Exit Conditions...")
        
        # Scenario A: Early game (should not exit)
        assert guvi_callback.should_send_callback(turn_count=2, extraction_completeness=10, current_strategy="engagement") == False
        print("[SUCCESS] Correctly stayed in conversation (Turn 2)")
        
        # Scenario B: Manual Exit Strategy
        assert guvi_callback.should_send_callback(turn_count=5, extraction_completeness=50, current_strategy="exit") == True
        print("[SUCCESS] Correctly exited on 'exit' strategy")
        
        # Scenario C: Max Turns
        assert guvi_callback.should_send_callback(turn_count=16, extraction_completeness=50, current_strategy="stalling") == True
        print("[SUCCESS] Correctly exited on max turns")
        
        # Scenario D: High Extraction Success
        assert guvi_callback.should_send_callback(turn_count=9, extraction_completeness=95, current_strategy="deep_extraction") == True
        print("[SUCCESS] Correctly exited on high extraction success")

if __name__ == "__main__":
    asyncio.run(test_callback_trigger())
