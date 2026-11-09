# day28_polish.py - Add to day22_whatsapp_bot.py before launch
import time
from collections import defaultdict

# --- Rate Limit: Max 20 msgs / min per user (prevent spam / cost blowup) ---
RATE_LIMIT = defaultdict(list)
def check_rate_limit(user_id: str, max_req=20, window=60):
    now = time.time()
    RATE_LIMIT[user_id] = [t for t in RATE_LIMIT[user_id] if now - t < window]
    if len(RATE_LIMIT[user_id]) >= max_req:
        return False
    RATE_LIMIT[user_id].append(now)
    return True

# --- Friendly Error Messages (never show traceback to user) ---
def friendly_error(e: Exception):
    print(f"[ERROR] {e}")  # Log for you
    return "⚠️ Oops, something went wrong. Try again in 30s or type 'help'. Team notified."

# --- Clean UI Helpers ---
def format_answer(answer: str, tool: str, latency_ms: int, accuracy: float):
    return f"""{answer}

---
🧰 Tool: {tool} | ⚡ {latency_ms}ms | ✅ Accuracy: {accuracy:.0%}
💡 Try: 'What did I learn?' | 'Draw RAG diagram' | 'Run python print(2+2)'"""

# --- Help Command ---
HELP_TEXT = """🤖 WhatsApp AI Tutor - Help

Try these:
🧮 What is 299 * 12?
🌐 What is latest Groq model?
🎨 Draw RAG diagram
💻 Run python print(2+2)
🧠 What did I learn about RAG?
📊 /health | /portfolio | /eval

Built in 30 Days | Day 28/30
Live: https://analytics-d976.onrender.com/
"""