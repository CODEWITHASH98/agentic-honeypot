import httpx
import logging
from typing import Dict, Any, Optional

# Configure logging
logger = logging.getLogger(__name__)

class GuviCallback:
    """
    Handler for reporting final conversation results to the GUVI Hackathon API.
    
    Attributes:
        API_URL (str): The endpoint for submitting results.
    """
    
    API_URL = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"
    
    async def send_final_result(
        self, 
        session_id: str, 
        scam_detected: bool, 
        total_messages: int, 
        extracted_intelligence: Dict[str, Any],
        agent_notes: str
    ) -> bool:
        """
        Send the final report to GUVI.
        
        Payload format:
        {
            "sessionId": "string",
            "scamDetected": boolean,
            "totalMessagesExchanged": number,
            "extractedIntelligence": {
                "bankAccounts": [],
                "upiIds": [],
                "phishingLinks": [],
                "phoneNumbers": [],
                "suspiciousKeywords": []
            },
            "agentNotes": "string"
        }
        """
        
        # Format payload to match GUVI requirements (camelCase keys)
        # Prepare intelligence dictionary exactly as requested
        intelligence_dict = {
            "bankAccounts": [acc["account_number"] if isinstance(acc, dict) else acc for acc in extracted_intelligence.get("bank_accounts", [])],
            "upiIds": extracted_intelligence.get("upi_ids", []),
            "phishingLinks": [url["original"] if isinstance(url, dict) else url for url in extracted_intelligence.get("urls", [])],
            "phoneNumbers": extracted_intelligence.get("phone_numbers", []),
            "suspiciousKeywords": extracted_intelligence.get("keywords", [])
        }

        # Construct final payload
        payload = {
            "sessionId": session_id,
            "scamDetected": scam_detected,
            "totalMessagesExchanged": total_messages,
            "extractedIntelligence": intelligence_dict,
            "agentNotes": agent_notes
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(self.API_URL, json=payload)
                
                if response.status_code in (200, 201):
                    logger.info(f"[SUCCESS] GUVI Callback success for {session_id}")
                    return True
                else:
                    logger.error(f"[FAILURE] GUVI Callback failed ({response.status_code}): {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"[ERROR] GUVI Callback error: {e}")
            return False

    def should_send_callback(self, turn_count: int, extraction_completeness: float, current_strategy: str) -> bool:
        """
        Determine if the conversation is ending and we should trigger the callback.
        This is a helper to centralize the logic.
        """
        # Triggers: 
        # 1. Exit strategy reached
        # 2. Max turns reached (safety)
        # 3. High completeness (early success)
        
        if current_strategy == "exit":
            return True
            
        if turn_count >= 15:
            return True
            
        if extraction_completeness >= 90 and turn_count >= 8:
            return True
            
        return False

guvi_callback = GuviCallback()
