# 🏗️ System Architecture

This document provides a comprehensive overview of the Agentic Honey-Pot system architecture, including UML diagrams and component explanations.

---

## 📊 High-Level Architecture

```mermaid
flowchart TB
    subgraph External["External Systems"]
        SCAMMER["Scammer"]
        GUVI["GUVI Evaluation API"]
    end
    
    subgraph API["FastAPI Application"]
        ENDPOINT["/api/v1/scam-analysis"]
        AUTH["API Key Auth"]
    end
    
    subgraph Core["Core Processing Pipeline"]
        DETECT["Detection Pipeline"]
        EXTRACT["Extraction Pipeline"]
        AGENT["Agent Engine"]
    end
    
    subgraph Detection["4-Tier Detection"]
        T1["Tier 1: Rules"]
        T2["Tier 2: Dataset"]
        T25["Tier 2.5: URL"]
        T3["Tier 3: LLM"]
        T4["Tier 4: Validator"]
    end
    
    subgraph State["State Management"]
        REDIS["Redis / Memory"]
    end
    
    SCAMMER -->|"Message"| ENDPOINT
    ENDPOINT --> AUTH
    AUTH --> DETECT
    AUTH --> EXTRACT
    
    DETECT --> T1 --> T2 --> T25 --> T3 --> T4
    
    T4 --> AGENT
    EXTRACT --> AGENT
    
    AGENT -->|"Response"| SCAMMER
    AGENT -->|"Final Report"| GUVI
    
    REDIS <-->|"Session State"| Core
```

---

## 🔄 API Request Sequence Diagram

```mermaid
sequenceDiagram
    participant S as Scammer
    participant API as FastAPI
    participant Auth as Auth Layer
    participant Det as Detection
    participant Ext as Extraction
    participant Agent as Agent Engine
    participant State as Redis
    participant GUVI as GUVI API
    
    S->>API: POST /api/v1/scam-analysis
    API->>Auth: Validate x-api-key
    
    alt Invalid Key
        Auth-->>S: 401 Unauthorized
    end
    
    API->>State: Get Session (conversation_id)
    State-->>API: Session Data / New Session
    
    par Parallel Processing
        API->>Det: detect(message)
        Det->>Det: Tier 1: Rule-based
        Det->>Det: Tier 2: Dataset Match
        Det->>Det: Tier 2.5: URL Check
        Det->>Det: Tier 3: LLM Analysis
        Det->>Det: Tier 4: Self-Validation
        Det-->>API: DetectionResult
    and
        API->>Ext: extract(message)
        Ext->>Ext: Regex Patterns
        Ext->>Ext: Validate & Enrich
        Ext-->>API: ExtractedIntelligence
    end
    
    API->>Agent: generate_response(history, detection, turn)
    Agent->>Agent: Select Persona
    Agent->>Agent: Get Strategy
    Agent->>Agent: Generate via LLM
    Agent-->>API: AgentResponse
    
    API->>State: Save Session
    
    alt Conversation Ending
        API->>GUVI: POST Final Result (async)
    end
    
    API-->>S: ScamResponse JSON
```

---

## 🧩 Class Diagram

```mermaid
classDiagram
    class DetectionPipeline {
        +url_validator: UrlValidator
        +detect(message: str) DetectionResult
        -_rule_based_detection(message: str) float
        -_classify_by_keywords(message: str) str
    }
    
    class AgentEngine {
        +fallback_responses: Dict
        +generate_response(history, detection, turn) AgentResponse
        -_generate_with_llm(history, persona, strategy) str
        -_generate_fallback(strategy_name: str) str
    }
    
    class ExtractionPipeline {
        +client: AsyncClient
        +extract(message: str) ExtractedIntelligence
        -_extract_with_regex(message: str) Dict
        -_validate_and_enrich(extracted: Dict) Dict
    }
    
    class GuviCallback {
        +API_URL: str
        +send_final_result(...) bool
        +should_send_callback(...) bool
    }
    
    class StateManager {
        +backend: RedisBackend | InMemoryBackend
        +get_session(id: str) Dict
        +save_session(id: str, data: Dict) void
    }
    
    class GroqClient {
        +client: AsyncGroq
        +analyze_scam(message: str) Dict
        +validate_detection(message: str, result: Dict) Dict
        +generate_agent_response(system, user) str
    }
    
    DetectionPipeline --> GroqClient : uses
    AgentEngine --> GroqClient : uses
    AgentEngine --> Persona : selects
    AgentEngine --> Strategy : follows
    
    class Persona {
        +name: str
        +traits: List~str~
        +vulnerabilities: List~str~
    }
    
    class Strategy {
        +name: str
        +description: str
        +action: str
        +target_extractions: List~str~
    }
```

---

## 📦 Component Overview

| Component | File | Responsibility |
|-----------|------|----------------|
| **API Layer** | `main.py` | Request handling, auth, orchestration |
| **Detection** | `app/detection.py` | 4-tier scam classification |
| **Extraction** | `app/extraction.py` | UPI, Bank, Phone, URL extraction |
| **Agent** | `app/agent.py` | Persona-based response generation |
| **Personas** | `app/personas.py` | Character definitions (Elderly, Youth, Pro) |
| **Strategies** | `app/strategies.py` | Conversation flow control |
| **LLM Client** | `app/groq_client.py` | Groq API wrapper |
| **State** | `app/state_manager.py` | Redis/Memory session storage |
| **Callback** | `app/callback/guvi_callback.py` | GUVI result submission |
| **URL Validator** | `app/url_validator.py` | Phishing link detection |
| **Dataset** | `app/dataset.py` | Known scam pattern matching |

---

## 🔐 Security Flow

```mermaid
flowchart LR
    REQ["Incoming Request"] --> HEADER{"x-api-key header?"}
    HEADER -->|"Missing"| REJECT["401 Unauthorized"]
    HEADER -->|"Present"| VALIDATE{"Key == API_SECRET_KEY?"}
    VALIDATE -->|"No"| REJECT
    VALIDATE -->|"Yes"| PROCESS["Process Request"]
```

---

## 📈 Data Flow

1. **Input**: Scammer message arrives via POST
2. **Auth**: API key validated
3. **State**: Session loaded/created from Redis
4. **Parallel**:
   - Detection runs 4 tiers
   - Extraction runs regex + validation
5. **Agent**: Generates contextual response
6. **Output**: JSON response returned
7. **Callback**: If ending, report to GUVI (async)
