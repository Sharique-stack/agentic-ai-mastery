# day26_portfolio.py - Your 30-day journey as API
PORTFOLIO = {
    "name": "WhatsApp AI Tutor",
    "tagline": "Multi-Agent RAG Tutor on WhatsApp - Remembers, Acts, Self-Checks",
    "live": "https://analytics-d976.onrender.com/",
    "stack": ["Python", "Flask", "Groq", "Twilio", "RAG", "MCP", "Docker", "Render"],
    "journey": [
        {"day": 20, "title": "Tutor Analytics Dashboard", "desc": "Total Students, Sessions, Top Topics"},
        {"day": 22, "title": "WhatsApp Bot", "desc": "Twilio Sandbox + Flask /whatsapp webhook"},
        {"day": 23, "title": "Memory", "desc": "Agent remembers past topics + weak areas"},
        {"day": 24, "title": "Tool Use + MCP", "desc": "Calculator, Web Search, Diagram, Code Runner"},
        {"day": 25, "title": "Evaluation + Guardrails", "desc": "94.2% Accuracy, Blocks injection, Cost tracking"},
        {"day": 26, "title": "Production + Portfolio", "desc": "Docker, Health Check, /health, /portfolio"},
    ],
    "features": [
        "🧮 Calculator tool - no hallucinated math",
        "🌐 Live Web Search - current info",
        "🎨 Diagram Generator",
        "💻 Code Runner",
        "🧠 Persistent Memory",
        "🛡️ Guardrails + Evaluation"
    ],
    "try_it": [
        "WhatsApp: What is 299 * 12?",
        "WhatsApp: What did I learn about RAG?",
        "WhatsApp: Draw RAG diagram",
        "WhatsApp: What is latest Groq model?"
    ],
    "github": "YOUR_GITHUB_LINK_HERE",
    "linkedin": "YOUR_LINKEDIN_HERE"
}

def get_portfolio():
    return PORTFOLIO