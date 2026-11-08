# day27_interview.py - If recruiter asks, you answer like this
INTERVIEW_QA = {
    "Why Groq and not OpenAI?": "Groq llama-3.1-8b-instant is fast (<1s latency), cheap ($0.0001/1k tokens), great for real-time WhatsApp. I optimized for latency + cost.",
    "How do you prevent hallucination?": "Two ways: 1) RAG - answer must overlap with retrieved context. 2) Tools - Math via calculator tool, not LLM. 3) Output Guardrail - if faithfulness < 0.05, auto-fix.",
    "What is MCP?": "Model Context Protocol - standard way for LLM to call tools. I implemented MCP-style function-calling: TOOLS dict with name, description, function. Supervisor picks tool based on query.",
    "How does memory work?": "I log every Q&A in eval_log.json + memory store. On new query, I search past topics. If user asks 'What did I learn?', I retrieve it. Simple but effective.",
    "How do you handle prompt injection?": "Input guardrail with regex blocklist: 'ignore previous instructions', 'you are now', etc. + output guardrail to block leaked keys. Returns blocked message, logs it.",
    "Why Docker + Gunicorn?": "Docker = runs anywhere, same env. Gunicorn = 2 workers handle concurrent WhatsApp webhooks. Healthcheck /health tells Render if app is alive for auto-restart.",
    "What would you improve next?": "1) Vector DB (Pinecone/Chroma) for real RAG. 2) Redis for memory. 3) LangGraph for multi-agent orchestration. 4) User auth + per-user memory."
}

def get_answer(q: str):
    return INTERVIEW_QA.get(q, "I built it end-to-end, let me walk you through the code.")