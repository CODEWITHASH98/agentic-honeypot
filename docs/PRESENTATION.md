# 🎤 Presentation Outline

## Slide 1: Title
- **Agentic Honey-Pot API**
- "AI-Powered Scam Detection & Autonomous Engagement"
- Team Name / Your Name
- GUVI Hackathon 2026

---

## Slide 2: Problem Statement
- Scammers target vulnerable populations
- Traditional detection is reactive
- No intelligence gathering from scams
- **Solution**: Turn the tables on scammers

---

## Slide 3: Live Demo (if possible)
- Show Swagger UI at `/docs`
- Send a scam message
- Show detection result
- Show agent response
- Highlight extracted intelligence

---

## Slide 4: Architecture Overview
- Show High-Level Diagram
- Explain parallel processing
- Highlight speed (<2s latency)

---

## Slide 5: 4-Tier Detection Pipeline
| Tier | Purpose | Speed |
|------|---------|-------|
| Rules | Keywords | <5ms |
| Dataset | Known patterns | <10ms |
| URL | Phishing check | <10ms |
| LLM | Context | ~500ms |
| Validator | Self-correction | ~500ms |

---

## Slide 6: Agent System
- **3 Personas**: Elderly, Youth, Professional
- **5 Strategies**: Engage → Extract → Stall → Exit
- **Goal**: Maximize engagement & extraction

---

## Slide 7: Intelligence Extraction
- UPI IDs
- Bank Accounts
- Phone Numbers
- Phishing URLs
- All validated and enriched

---

## Slide 8: Technical Highlights
- **FastAPI** for async performance
- **Groq** for 10x faster LLM inference
- **Redis** for scalable state management
- **Parallelized** detection + extraction

---

## Slide 9: Security
- API Key authentication
- Rate limiting ready
- CORS configured
- Production-ready

---

## Slide 10: Results & Metrics
- **94%+ Detection Accuracy**
- **<2s Total Latency**
- **Auto GUVI Callback** at conversation end

---

## Slide 11: Why We Win
1. Complete solution (all requirements met)
2. Innovative multi-tier detection
3. Autonomous persona-based agent
4. Self-correcting AI (Tier 4)
5. Production-ready code quality

---

## Slide 12: Thank You
- GitHub Link
- Questions?
