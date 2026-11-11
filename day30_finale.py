# day30_finale.py - Your entire 30-day journey in 1 endpoint
from flask import Flask

app = Flask(__name__)

JOURNEY = [
    {"day": "1-5", "title": "Python + Groq + LLM Basics", "result": "First AI chat"},
    {"day": "6-10", "title": "Tools + Calculator + Memory", "result": "No hallucination math"},
    {"day": "11-15", "title": "RAG + Vector DB + Diagrams", "result": "Knows YOUR notes"},
    {"day": "16-20", "title": "MCP + Multi-Agent Supervisor", "result": "Routes like a team"},
    {"day": "21-25", "title": "WhatsApp + Docker + Render Deploy", "result": "Live for world"},
    {"day": "26-27", "title": "Eval + Portfolio + Interview Prep", "result": "HIREABLE"},
    {"day": "28", "title": "Polish + Launch Checklist", "result": "LAUNCH-READY"},
    {"day": "29", "title": "Feedback + Growth Loop", "result": "LOVED by users"},
    {"day": "30", "title": "GRAND FINALE", "result": "CAREER LAUNCHPAD"},
]

STATS = {
    "days": 30,
    "tools_built": 6,
    "agents": 4,
    "endpoints": 7,
    "lines_of_code": "2500+",
    "cost": "$0 (Groq Free Tier)",
    "live_url": "https://analytics-d976.onrender.com/",
    "stack": "Python, Groq, Flask, Twilio, Docker, Render, RAG, MCP"
}

@app.get("/journey")
def journey():
    return {"project": "WhatsApp AI Tutor", "journey": JOURNEY, "stats": STATS}

@app.get("/")
def home():
    return {
        "message": "🎓 I built this in 30 days. Day 1 I knew nothing about Agents. Day 30 I shipped this.",
        "journey": "/journey - See full 30 days",
        "portfolio": "/portfolio",
        "eval": "/eval - Accuracy, Latency, Cost",
        "feedback": "/feedback - What real users said",
        "interview": "/interview - Ask me anything about it",
        "live": "https://analytics-d976.onrender.com/"
    }