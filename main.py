import time
import asyncio
from dotenv import load_dotenv
load_dotenv()  # Load .env before other imports

from fastapi import FastAPI, HTTPException, Header, Request, Security, Depends, Body
from fastapi.responses import HTMLResponse
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
    description="Scam detection and intelligence extraction API for hackathon evaluation",
    redirect_slashes=False  # Prevent 307 redirects that lose POST body
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

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agentic Honey-Pot API</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            min-height: 100vh;
            color: #fff;
            padding: 40px 20px;
        }
        .container { max-width: 900px; margin: 0 auto; }
        h1 {
            font-size: 2.5rem;
            background: linear-gradient(90deg, #00d4ff, #7b2cbf);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        .subtitle { color: #94a3b8; font-size: 1.1rem; margin-bottom: 30px; }
        .buttons { display: flex; gap: 15px; margin-bottom: 40px; flex-wrap: wrap; }
        .btn {
            padding: 12px 24px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 600;
            transition: all 0.3s ease;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        .btn-primary {
            background: linear-gradient(90deg, #00d4ff, #7b2cbf);
            color: #fff;
        }
        .btn-github {
            background: #24292e;
            color: #fff;
            border: 1px solid #444;
        }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 10px 30px rgba(0,212,255,0.3); }
        .card {
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 25px;
            margin-bottom: 20px;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .card h2 { color: #00d4ff; margin-bottom: 15px; font-size: 1.3rem; }
        .feature-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }
        .feature {
            background: rgba(0,212,255,0.1);
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }
        .feature .icon { font-size: 2rem; margin-bottom: 8px; }
        .feature h3 { font-size: 1rem; margin-bottom: 5px; }
        .feature p { font-size: 0.85rem; color: #94a3b8; }
        pre {
            background: #1e1e1e;
            padding: 15px;
            border-radius: 8px;
            overflow-x: auto;
            font-size: 0.85rem;
        }
        code { color: #00d4ff; }
        .mermaid { background: #fff; border-radius: 8px; padding: 15px; margin-top: 15px; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.1); }
        th { color: #00d4ff; }
        .badge { display: inline-block; padding: 4px 10px; border-radius: 20px; font-size: 0.75rem; margin-right: 5px; }
        .badge-green { background: #10b981; }
        .badge-blue { background: #3b82f6; }
        .footer { text-align: center; margin-top: 40px; color: #64748b; font-size: 0.9rem; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🍯 Agentic Honey-Pot API</h1>
        <p class="subtitle">AI-Powered Scam Detection & Autonomous Engagement System</p>
        
        <div class="buttons">
            <a href="/docs" class="btn btn-primary">📚 API Documentation</a>
            <a href="/architecture" class="btn btn-primary">🏗️ Architecture</a>
            <a href="https://github.com/CODEWITHASH98/agentic-honeypot" target="_blank" class="btn btn-github">
                <svg height="20" width="20" viewBox="0 0 16 16" fill="currentColor">
                    <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/>
                </svg>
                View on GitHub
            </a>
        </div>

        <div class="card">
            <h2>🎯 Key Features</h2>
            <div class="feature-grid">
                <div class="feature">
                    <div class="icon">🔍</div>
                    <h3>4-Tier Detection</h3>
                    <p>Rules → Dataset → URL → LLM → Validator</p>
                </div>
                <div class="feature">
                    <div class="icon">🤖</div>
                    <h3>Autonomous Agent</h3>
                    <p>Persona-based engagement</p>
                </div>
                <div class="feature">
                    <div class="icon">📊</div>
                    <h3>Intel Extraction</h3>
                    <p>UPI, Bank, Phone, URLs</p>
                </div>
                <div class="feature">
                    <div class="icon">⚡</div>
                    <h3>&lt;2s Latency</h3>
                    <p>Parallel async processing</p>
                </div>
            </div>
        </div>

        <div class="card">
            <h2>🏗️ Architecture</h2>
            <table>
                <tr><th>Component</th><th>Technology</th><th>Purpose</th></tr>
                <tr><td>API Framework</td><td>FastAPI</td><td>Async request handling</td></tr>
                <tr><td>LLM</td><td>Groq (Llama 3.3 70B)</td><td>Scam analysis & responses</td></tr>
                <tr><td>State</td><td>Redis / In-Memory</td><td>Session management</td></tr>
                <tr><td>Detection</td><td>4-Tier Pipeline</td><td>Multi-layer classification</td></tr>
            </table>
        </div>

        <div class="card">
            <h2>📡 Quick Start</h2>
            <pre><code>curl -X POST "https://agentic-honeypot-25xp.onrender.com/api/v1/scam-analysis" \\
  -H "Content-Type: application/json" \\
  -H "x-api-key: YOUR_API_KEY" \\
  -d '{"message": "You won a lottery!"}'</code></pre>
        </div>

        <div class="card">
            <h2>📋 Endpoints</h2>
            <table>
                <tr><th>Method</th><th>Path</th><th>Description</th></tr>
                <tr><td><span class="badge badge-green">GET</span></td><td>/healthz</td><td>Health check</td></tr>
                <tr><td><span class="badge badge-blue">POST</span></td><td>/api/v1/scam-analysis</td><td>Analyze scam message</td></tr>
                <tr><td><span class="badge badge-green">GET</span></td><td>/docs</td><td>Swagger UI</td></tr>
            </table>
        </div>

        <div class="footer">
            <p>Built for GUVI Hackathon 2026 | <a href="https://github.com/CODEWITHASH98/agentic-honeypot" style="color:#00d4ff;">GitHub</a></p>
        </div>
    </div>
</body>
</html>
    """

@app.get("/architecture", response_class=HTMLResponse)
async def architecture_page():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Architecture - Agentic Honey-Pot</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            min-height: 100vh;
            color: #fff;
            padding: 40px 20px;
        }
        .container { max-width: 1000px; margin: 0 auto; }
        h1 { color: #00d4ff; margin-bottom: 20px; }
        h2 { color: #00d4ff; margin: 30px 0 15px; font-size: 1.4rem; }
        .card {
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 25px;
            margin-bottom: 20px;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .mermaid { background: #fff; border-radius: 8px; padding: 20px; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.1); }
        th { color: #00d4ff; }
        .btn {
            display: inline-block;
            padding: 10px 20px;
            background: #00d4ff;
            color: #000;
            text-decoration: none;
            border-radius: 8px;
            margin-right: 10px;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="btn">← Back to Home</a>
        <a href="https://github.com/CODEWITHASH98/agentic-honeypot" class="btn" target="_blank">GitHub</a>
        
        <h1>🏗️ System Architecture</h1>
        
        <div class="card">
            <h2>High-Level Architecture</h2>
            <div class="mermaid">
flowchart TB
    subgraph External["External Systems"]
        SCAMMER["Scammer"]
        GUVI["GUVI API"]
    end
    subgraph API["FastAPI"]
        ENDPOINT["/api/v1/scam-analysis"]
        AUTH["API Key Auth"]
    end
    subgraph Core["Core Pipeline"]
        DETECT["Detection"]
        EXTRACT["Extraction"]
        AGENT["Agent"]
    end
    SCAMMER -->|Message| ENDPOINT
    ENDPOINT --> AUTH --> DETECT
    AUTH --> EXTRACT
    DETECT --> AGENT
    EXTRACT --> AGENT
    AGENT -->|Response| SCAMMER
    AGENT -->|Report| GUVI
            </div>
        </div>

        <div class="card">
            <h2>Detection Pipeline</h2>
            <table>
                <tr><th>Tier</th><th>Name</th><th>Description</th></tr>
                <tr><td>1</td><td>Rules</td><td>Keyword & pattern matching</td></tr>
                <tr><td>2</td><td>Dataset</td><td>Known scam hash lookup</td></tr>
                <tr><td>2.5</td><td>URL</td><td>Phishing domain detection</td></tr>
                <tr><td>3</td><td>LLM</td><td>Groq Llama 3.3 analysis</td></tr>
                <tr><td>4</td><td>Validator</td><td>Self-correction consensus</td></tr>
            </table>
        </div>

        <div class="card">
            <h2>Agent Personas</h2>
            <table>
                <tr><th>Persona</th><th>Traits</th><th>Best For</th></tr>
                <tr><td>👴 Elderly Confused</td><td>Trusting, slow</td><td>Financial scams</td></tr>
                <tr><td>🧑 Young Eager</td><td>Enthusiastic, naive</td><td>Job scams</td></tr>
                <tr><td>👨‍💼 Cautious Pro</td><td>Skeptical</td><td>Tech support scams</td></tr>
            </table>
        </div>

        <div class="card">
            <h2>Component Overview</h2>
            <table>
                <tr><th>Component</th><th>File</th><th>Purpose</th></tr>
                <tr><td>API</td><td>main.py</td><td>Request handling</td></tr>
                <tr><td>Detection</td><td>detection.py</td><td>4-Tier pipeline</td></tr>
                <tr><td>Agent</td><td>agent.py</td><td>Response generation</td></tr>
                <tr><td>Extraction</td><td>extraction.py</td><td>Intel extraction</td></tr>
                <tr><td>Callback</td><td>guvi_callback.py</td><td>GUVI reporting</td></tr>
            </table>
        </div>
    </div>
    <script>mermaid.initialize({startOnLoad:true, theme:'default'});</script>
</body>
</html>
    """

@app.on_event("startup")
async def startup_event():
    print("Agentic Honey-Pot API starting up...")

@app.on_event("shutdown")
async def shutdown_event():
    await state_manager.close()
    await extraction_pipeline.close()

@app.post("/api/v1/scam-analysis", response_model=ScamResponse)
@app.post("/api/v1/scam-analysis/", response_model=ScamResponse, include_in_schema=False)
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
