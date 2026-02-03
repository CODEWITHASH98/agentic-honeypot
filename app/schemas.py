from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class Message(BaseModel):
    sender: str = "unknown"
    content: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class SessionMetadata(BaseModel):
    source: str = "api"
    session_start: str = Field(default_factory=lambda: datetime.now().isoformat())

class ScamRequest(BaseModel):
    # Support multiple field names for compatibility
    conversation_id: Optional[str] = Field(default=None, alias="conversationId")
    session_id: Optional[str] = Field(default=None, alias="sessionId")
    messages: Optional[List[Message]] = None
    message: Optional[str] = None
    content: Optional[str] = None  # GUVI might use 'content'
    text: Optional[str] = None  # Or 'text'
    session_metadata: Optional[SessionMetadata] = None
    
    class Config:
        populate_by_name = True  # Allow both alias and field name
    
    def get_conversation_id(self) -> str:
        """Get conversation ID from various possible field names"""
        return self.conversation_id or self.session_id or f"conv-{datetime.now().timestamp()}"
    
    def get_latest_message(self) -> str:
        """Get the message content to analyze"""
        if self.message:
            return self.message
        if self.content:
            return self.content
        if self.text:
            return self.text
        if self.messages and len(self.messages) > 0:
            return self.messages[-1].content
        return ""

class DetectionResult(BaseModel):
    is_scam: bool
    confidence: float
    scam_type: Optional[str] = None
    detection_time_ms: int
    reasoning: Optional[str] = None

class AgentResponse(BaseModel):
    message: str
    persona_used: str
    strategy: str

class ExtractedIntelligence(BaseModel):
    upi_ids: List[str] = []
    bank_accounts: List[Dict[str, str]] = []
    phone_numbers: List[str] = []
    urls: List[Dict[str, Any]] = []
    extraction_completeness: float = 0.0

class ConversationMetrics(BaseModel):
    turn_count: int
    engagement_duration_seconds: int
    extraction_progress: float

class ScamResponse(BaseModel):
    conversation_id: str
    detection: DetectionResult
    agent_response: AgentResponse
    extracted_intelligence: ExtractedIntelligence
    conversation_metrics: ConversationMetrics
    metadata: Dict[str, Any]
