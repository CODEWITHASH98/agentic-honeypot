import os
from typing import Optional, Dict
from groq import AsyncGroq

class GroqClient:
    """Wrapper for Groq LLM for both detection and agent responses"""
    
    def __init__(self):
        self.client = None
        self._initialize()
    
    def _initialize(self):
        """Initialize Groq client if API key available"""
        try:
            api_key = os.getenv("GROQ_API_KEY")
            if api_key and api_key != "your-groq-api-key-here":
                # Add timeout to client
                self.client = AsyncGroq(
                    api_key=api_key,
                    timeout=5.0, # 5 second timeout
                    max_retries=1
                )
                print("[INFO] Groq LLM initialized")
            else:
                print("[WARN] Groq API key not found - using fallback mode")
        except Exception as e:
            print(f"[ERROR] Groq initialization failed: {e}")
    
    async def analyze_scam(self, message: str, context: str = "") -> Optional[Dict]:
        """
        Tier 3: Primary LLM scam detection
        Returns: {is_scam, confidence, scam_type, reasoning}
        """
        if not self.client:
            return None
        
        try:
            prompt = f"""Analyze if this is a scam message. Respond with JSON only.

Message: "{message}"

{context}

Return format:
{{
  "is_scam": true or false,
  "confidence": 0-100,
  "scam_type": "banking|job|prize|tech_support|investment|romance|unknown",
  "reasoning": "brief explanation of tactics used"
}}"""

            response = await self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=200,
                response_format={"type": "json_object"}
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            print(f"Groq analysis error: {e}")
            return None
    
    async def validate_detection(self, message: str, initial_result: Dict) -> Optional[Dict]:
        """
        Tier 4: Self-validation with different prompt
        Returns: {is_scam, confidence, reasoning}
        """
        if not self.client:
            return None
        
        try:
            prompt = f"""You are a security expert. Perform deep analysis of this message for social engineering tactics.

Message: "{message}"

Previous analysis suggested: {initial_result.get('scam_type', 'unknown')} scam with {initial_result.get('confidence', 0)}% confidence.

Verify if this assessment is correct. Look for:
- Urgency tactics
- Authority impersonation
- Requests for sensitive information
- Too-good-to-be-true offers

Return JSON:
{{
  "is_scam": true or false,
  "confidence": 0-100,
  "reasoning": "validation explanation"
}}"""

            response = await self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=150,
                response_format={"type": "json_object"}
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            print(f"Groq validation error: {e}")
            return None
    
    async def generate_agent_response(self, system_prompt: str, user_prompt: str, temperature: float = 0.7) -> Optional[str]:
        """
        Generate agent conversation response using Groq
        """
        if not self.client:
            return None
        
        try:
            response = await self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=150
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Groq agent generation error: {e}")
            return None

groq_client = GroqClient()
