# day29_feedback.py - Add to day22_whatsapp_bot.py
import json, time
from datetime import datetime

FEEDBACK_FILE = "feedback_log.json"

def save_feedback(user_id: str, message: str, rating: int = 0, category: str = "general"):
    """Save every feedback - this is gold for interviews."""
    entry = {
        "user_id": user_id,
        "message": message,
        "rating": rating,  # 1-5 stars
        "category": category,  # bug, feature, ui, praise
        "timestamp": datetime.now().isoformat()
    }
    try:
        data = json.load(open(FEEDBACK_FILE))
    except:
        data = []
    data.append(entry)
    json.dump(data, open(FEEDBACK_FILE, "w"), indent=2)
    return entry

def get_feedback_stats():
    try:
        data = json.load(open(FEEDBACK_FILE))
    except:
        return {"total": 0, "avg_rating": 0, "top_issues": []}
    if not data: return {"total": 0, "avg_rating": 0, "top_issues": []}
    ratings = [d["rating"] for d in data if d["rating"] > 0]
    avg = sum(ratings) / len(ratings) if ratings else 0
    # Count categories
    cats = {}
    for d in data:
        cats[d["category"]] = cats.get(d["category"], 0) + 1
    return {
        "total": len(data),
        "avg_rating": round(avg, 2),
        "categories": cats,
        "latest": data[-3:]
    }

# --- Feedback Commands for WhatsApp ---
FEEDBACK_PROMPT = """⭐ Love it? Hate it? Tell me!

Reply like this:
`feedback 5 Loved the calculator, super fast!`
`feedback 2 Memory didn't work for me`

Your feedback shapes Day 30!
"""

# In webhook:
# if msg.startswith("feedback"): parse rating + text -> save_feedback()
# if msg == "feedback": reply FEEDBACK_PROMPT