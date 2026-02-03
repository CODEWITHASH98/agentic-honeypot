import os
import random
from typing import List, Optional
from app.schemas import AgentResponse, DetectionResult, Message
from app.personas import PERSONAS, select_persona, get_persona_context, Persona
from app.strategies import get_strategy_for_turn, should_exit_conversation, Strategy
from app.groq_client import groq_client

# Groq is now primary, OpenAI as fallback
client = groq_client

class AgentEngine:
    """
    Autonomous conversational agent that engages with scammers.
    
    Capabilities:
    - Persona Management: Selects appropriate persona (Elderly, Professional, etc.)
    - Strategy Execution: Manages conversation flow (Engagement -> Extraction -> Exit)
    - Response Generation: Uses LLM with fallback templates.
    """
    
    def __init__(self):
        self.fallback_responses = {
            "engagement": [
                "Oh really? I didn't know about this. Can you tell me more?",
                "That sounds interesting! How does this work exactly?",
                "Hmm, I'm not sure I understand. Could you explain again?",
                "Oh my! Is this really happening? What should I do?"
            ],
            "initial_extraction": [
                "Okay, so what do I need to do? Do I have to send money somewhere?",
                "I want to proceed. Where should I transfer the amount?",
                "My son usually helps me with this... but tell me, what account do I send to?",
                "Alright, I'm interested. What are the payment details?"
            ],
            "deep_extraction": [
                "I'm having some trouble with my bank app. Is there another way to pay?",
                "The link isn't working for me. Do you have a phone number I can call?",
                "Can you give me another UPI ID? This one isn't showing up.",
                "My internet is slow... can you send a different link?"
            ],
            "stalling": [
                "Let me check with my son first. Can you wait a bit?",
                "I need to go to the bank to get this done. Give me some time.",
                "Can you confirm the details again? I want to make sure I don't make mistakes.",
                "Just to be safe, can you tell me your company details?"
            ],
            "exit": [
                "Someone is at the door. I'll message you later!",
                "I need to go now, my daughter is calling. I'll continue this in 2 hours.",
                "Thank you for your help! I'll do this tomorrow when my grandson is here.",
                "I have to leave now. I'll get back to you soon!"
            ],
            "ignore": [
                "I think you have the wrong number.",
                "Sorry, I'm not interested.",
                "Please don't contact me again."
            ]
        }

    async def generate_response(
        self, 
        history: List[Message], 
        detection: DetectionResult, 
        turn_count: int,
        extraction_progress: float = 0.0
    ) -> AgentResponse:
        
        # If not a scam, ignore
        if not detection.is_scam:
            return AgentResponse(
                message=random.choice(self.fallback_responses["ignore"]),
                persona_used="none",
                strategy="ignore"
            )
        
        # Select persona based on scam type
        persona = select_persona(detection.scam_type or "unknown")
        
        # Get strategy based on turn
        strategy = get_strategy_for_turn(turn_count, extraction_progress)
        
        # Check if we should exit
        if history and should_exit_conversation(turn_count, extraction_progress, history[-1].content):
            strategy = get_strategy_for_turn(100, 100)  # Force exit strategy
        
        # Try LLM generation, fallback to templates
        try:
            if client:
                message = await self._generate_with_llm(history, persona, strategy, detection)
            else:
                message = self._generate_fallback(strategy.name)
        except Exception as e:
            print(f"LLM generation failed: {e}")
            message = self._generate_fallback(strategy.name)
        
        return AgentResponse(
            message=message,
            persona_used=persona.name,
            strategy=strategy.name
        )

    async def _generate_with_llm(
        self, 
        history: List[Message], 
        persona: Persona, 
        strategy: Strategy,
        detection: DetectionResult
    ) -> str:
        """Generate response using Groq LLM"""
        
        persona_context = get_persona_context(persona)
        
        # Format conversation history
        history_text = ""
        for msg in history[-6:]:  # Last 6 messages for context
            role = "Scammer" if msg.sender == "scammer" else "You"
            history_text += f"{role}: {msg.content}\n"
        
        system_prompt = f"""{persona_context}

CURRENT STRATEGY: {strategy.name}
Strategy Goal: {strategy.description}
Action to take: {strategy.action}

Detected scam type: {detection.scam_type}

Generate a natural response that:
1. Stays perfectly in character as {persona.name}
2. Follows the strategy: {strategy.action}
3. Sounds completely natural and human
4. Does NOT reveal you're detecting a scam or that you' re an AI
5. Keeps the conversation going to extract more information
6. Is concise (1-3 sentences max)

Respond ONLY with the message text, nothing else."""

        user_prompt = f"""Conversation so far:
{history_text}

Generate your next response as {persona.name}:"""

        response = await client.generate_agent_response(system_prompt, user_prompt, temperature=0.8)
        
        if response:
            return response
        else:
            # Fallback to template
            return self._generate_fallback(strategy.name)

    def _generate_fallback(self, strategy_name: str) -> str:
        """Generate fallback response when LLM is unavailable"""
        responses = self.fallback_responses.get(strategy_name, self.fallback_responses["engagement"])
        return random.choice(responses)

agent_engine = AgentEngine()
