import httpx
import asyncio
from typing import Dict, List

class GUVICallback:
    """Handles final callback to GUVI evaluation server"""
    
    def __init__(self):
        self.callback_url = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"
        self.timeout = 10.0
    
    async def send_final_result(
        self,
        session_id: str,
        scam_detected: bool,
        total_messages: int,
        extracted_intelligence: Dict,
        agent_notes: str
    ) -> bool:
        """
        Send final conversation results to GUVI
        
        Args:
            session_id: The unique session ID from GUVI request
            scam_detected: Whether scam was detected
            total_messages: Total turn count (scammer + agent)
            extracted_intelligence: Dict with upi_ids, bank_accounts, etc.
            agent_notes: Summary of scammer tactics
        
        Returns:
            True if callback succeeded, False otherwise
        """
        payload = {
            "sessionId": session_id,
            "scamDetected": scam_detected,
            "totalMessagesExchanged": total_messages,
            "extractedIntelligence": {
                "bankAccounts": extracted_intelligence.get("bank_accounts", []),
                "upiIds": extracted_intelligence.get("upi_ids", []),
                "phishingLinks": extracted_intelligence.get("urls", []),
                "phoneNumbers": extracted_intelligence.get("phone_numbers", []),
                "suspiciousKeywords": extracted_intelligence.get("keywords", [])
            },
            "agentNotes": agent_notes
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.callback_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    print(f"✓ GUVI callback sent successfully for session {session_id}")
                    return True
                else:
                    print(f"⚠ GUVI callback failed: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            print(f"✗ GUVI callback error for session {session_id}: {e}")
            # Retry logic
            return await self._retry_callback(payload, retries=2)
    
    async def _retry_callback(self, payload: Dict, retries: int) -> bool:
        """Retry callback on failure"""
        for attempt in range(retries):
            await asyncio.sleep(1)  # Wait before retry
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        self.callback_url,
                        json=payload,
                        headers={"Content-Type": "application/json"}
                    )
                    if response.status_code == 200:
                        print(f"✓ GUVI callback succeeded on retry {attempt + 1}")
                        return True
            except:
                continue
        
        print(f"✗ GUVI callback failed after {retries} retries")
        return False
    
    def should_send_callback(self, turn_count: int, extraction_completeness: float, strategy: str) -> bool:
        """
        Determine if conversation should end and callback sent
        
        Exit conditions:
        1. Turn count >= 10 (enough engagement)
        2. Extraction >= 80% (got most intel)
        3. Strategy is 'exit' (agent decided to end)
        4. Turn count >= 15 (max duration reached)
        """
        if turn_count >= 15:  # Max turns
            return True
        if turn_count >= 10 and extraction_completeness >= 80:  # Goal achieved
            return True
        if strategy == "exit":  # Agent forcing exit
            return True
        
        return False

guvi_callback = GUVICallback()
