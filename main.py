import time
import asyncio
from dotenv import load_dotenv
load_dotenv()  # Load .env before other imports

from fastapi import FastAPI, HTTPException, Header, Request, Security, Depends, Body
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from app.schemas import ScamRequest, ScamResponse, ConversationMetrics, Message
from app.detection import detection_pipeline
from app.agent import agent_engine
from app.agent import agent_engine
from app.extraction import extraction_pipeline
from app.state_manager import state_manager
from app.callback.guvi_callback import guvi_callback
from app.config import settings

app = FastAPI(
    title="Agentic Honey-Pot API", 
    version="1.0.0",
    description="Scam detection and intelligence extraction API for hackathon evaluation"
)

# Security Scheme for Swagger UI
api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)

# CORS for external access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
@app.get("/healthz")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

@app.get("/")
async def root():
    return {"message": "Agentic Honey-Pot API", "docs": "/docs"}

@app.on_event("startup")
async def startup_event():
    print("Agentic Honey-Pot API starting up...")

@app.on_event("shutdown")
async def shutdown_event():
    await state_manager.close()
    await extraction_pipeline.close()

@app.post("/api/v1/scam-analysis", response_model=ScamResponse)
async def analyze_scam(
    request: Request,
    x_api_key: str = Security(api_key_header),
    body_doc: dict = Body(
        ...,
        example={
            "conversation_id": "test-123",
            "message": "You won a lottery! Send $100 fee now!"
        }
    )
):
    """
    Analyze a message for scam content, extract intelligence, and generate an autonomous agent response.
    
    Flow:
    1. Load/Create Session State
    2. Parallel Execution: 
       - Detection Pipeline (Rules -> Dataset -> URL -> LLM -> Validator)
       - Extraction Pipeline (Regex -> API Validators)
    3. Generate Agent Response (Persona-based)
    4. Check Exit Conditions -> Trigger GUVI Callback if needed
    5. Save Session & Return Response
    """
    start_time = time.time()
    
    # 1. Auth check
    if x_api_key != settings.API_SECRET_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    
    # Use body_doc directly (already parsed by FastAPI)
    body = body_doc
    
    # Extract fields with multiple possible names
    conv_id = (
        body.get("conversation_id") or 
        body.get("conversationId") or 
        body.get("session_id") or 
        body.get("sessionId") or 
        f"conv-{time.time()}"
    )
    
    # Extract message - can be string or dict
    raw_message = body.get("message") or body.get("content") or body.get("text") or ""
    
    # If message is a dict, extract the content
    if isinstance(raw_message, dict):
        message_content = (
            raw_message.get("content") or 
            raw_message.get("text") or 
            raw_message.get("message") or 
            raw_message.get("body") or
            ""
        )
    else:
        message_content = raw_message
    
    # Handle messages array if present
    messages = body.get("messages", [])
    if messages and isinstance(messages, list) and len(messages) > 0:
        last_msg = messages[-1]
        if isinstance(last_msg, dict):
            message_content = last_msg.get("content") or last_msg.get("text") or last_msg.get("message") or message_content
        elif isinstance(last_msg, str):
            message_content = last_msg
    
    # Ensure message_content is a string
    if not isinstance(message_content, str):
        message_content = str(message_content) if message_content else ""
    
    if not message_content:
        raise HTTPException(status_code=400, detail="No message content provided. Use 'message', 'content', or 'text' field.")

    # 2. Get/Create Session
    session_data = await state_manager.get_session(conv_id)
    if not session_data:
        session_data = {
            "history": [],
            "turn_count": 0,
            "metadata": body.get("session_metadata") or {"source": "api"},
            "extracted": {"upi_ids": [], "bank_accounts": [], "phone_numbers": [], "urls": []}
        }
    
    session_data["history"].append({"sender": "user", "content": message_content})
    
    # 4 & 5. Detection and Extraction (Parallel)
    detection_task = detection_pipeline.detect(message_content)
    extraction_task = extraction_pipeline.extract(message_content)
    
    detection_result, extraction_result = await asyncio.gather(detection_task, extraction_task)
    # Merge extraction results (deduplicated)
    for upi in extraction_result.upi_ids:
        if upi not in session_data["extracted"]["upi_ids"]:
            session_data["extracted"]["upi_ids"].append(upi)
    for acc in extraction_result.bank_accounts:
        if acc not in session_data["extracted"]["bank_accounts"]:
            session_data["extracted"]["bank_accounts"].append(acc)
    for phone in extraction_result.phone_numbers:
        if phone not in session_data["extracted"]["phone_numbers"]:
            session_data["extracted"]["phone_numbers"].append(phone)
    for url in extraction_result.urls:
        if url not in session_data["extracted"]["urls"]:
            session_data["extracted"]["urls"].append(url)

    # 6. Agent Response
    turn_count = session_data["turn_count"] + 1
    session_data["turn_count"] = turn_count
    
    # Reconstruct history objects for agent
    history_objs = [Message(**msg) for msg in session_data["history"]]
    
    agent_res = await agent_engine.generate_response(
        history_objs, 
        detection_result, 
        turn_count,
        extraction_result.extraction_completeness
    )
    
    # 7. Update History with Agent Response
    agent_msg = Message(
        sender="agent",
        content=agent_res.message,
        timestamp=str(time.time()) # simple timestamp
    )
    session_data["history"].append(agent_msg.dict())
    
    # 8. Check if conversation should end
    should_end = guvi_callback.should_send_callback(
        turn_count,
        extraction_result.extraction_completeness,
        agent_res.strategy
    )
    
    # 9. Send GUVI Callback if conversation ending
    # We only send if NOT already sent (you might want to track this in session_data)
    if should_end and not session_data.get("callback_sent"):
        session_data["callback_sent"] = True
        
        # Generate agent notes
        notes = f"{detection_result.scam_type or 'unknown'} scam detected. "
        notes += f"Engaged for {turn_count} turns. "
        notes += f"Extraction: {extraction_result.extraction_completeness:.0f}%. "
        notes += f"Reasoning: {detection_result.reasoning}"
        
        # Extract keywords from history
        all_text = " ".join([msg.content for msg in history_objs if msg.sender == "scammer"])
        keywords = list(set([w.lower() for w in all_text.split() if len(w) > 4]))[:10]
        
        extracted_data = session_data["extracted"].copy()
        extracted_data["keywords"] = keywords
        
        # Send callback (async, don't wait)
        asyncio.create_task(
            guvi_callback.send_final_result(
                session_id=request.conversation_id,
                scam_detected=detection_result.is_scam,
                total_messages=turn_count * 2,  # scammer + agent messages
                extracted_intelligence=extracted_data,
                agent_notes=notes
            )
        )
    
    # 10. Save Session
    await state_manager.save_session(conv_id, session_data)

    # 11. Metrics
    processing_time = (time.time() - start_time) * 1000
    
    try:
        session_start = session_data["metadata"].get("session_start", time.time())
        engagement_seconds = int(time.time() - float(session_start))
    except Exception:
        engagement_seconds = 0
    
    return ScamResponse(
        conversation_id=conv_id,
        detection=detection_result,
        agent_response=agent_res,
        extracted_intelligence=extraction_result,
        conversation_metrics=ConversationMetrics(
            turn_count=turn_count,
            engagement_duration_seconds=engagement_seconds,
            extraction_progress=extraction_result.extraction_completeness
        ),
        metadata={
            "processing_time_ms": int(processing_time),
            "model_version": "v1.0-multi-persona"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
