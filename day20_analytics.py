# day20_analytics.py - Day 20: Student Analytics
import json, os
from datetime import datetime, timedelta
from collections import Counter

FILE = "student_profiles.json"

def load_all():
    if not os.path.exists(FILE): return {}
    try: return json.loads(open(FILE).read())
    except: return {}

def get_dashboard_stats():
    data = load_all()
    if not data:
        return {"total_students": 0, "message": "No data yet"}

    total = len(data)
    total_sessions = sum(p.get("total_sessions",0) for p in data.values())
    
    # Modality
    visual = sum(1 for p in data.values() if p.get("preferred_mode")=="visual")
    voice = sum(1 for p in data.values() if p.get("preferred_mode")=="voice")
    text = total - visual - voice
    
    # Topics
    all_topics = []
    for p in data.values():
        all_topics.extend(p.get("topics_learned",[]))
    topic_counts = Counter(all_topics).most_common(5)
    
    # Activity
    images_sent = sum(p.get("images_sent",0) + p.get("images_requested",0) for p in data.values())
    images_received = sum(p.get("images_received",0) for p in data.values())
    voice_in = sum(p.get("voice_in",0) for p in data.values())
    
    # Active today
    today = datetime.now().date()
    active_today = 0
    for p in data.values():
        try:
            last = datetime.fromisoformat(p.get("last_seen","")).date()
            if last == today: active_today += 1
        except: pass
    
    # Top students
    top = sorted(data.values(), key=lambda x: x.get("total_sessions",0), reverse=True)[:5]
    top_list = [{"name": p.get("name"), "sessions": p.get("total_sessions"), "pref": p.get("preferred_mode")} for p in top]

    return {
        "total_students": total,
        "total_sessions": total_sessions,
        "active_today": active_today,
        "modality": {"visual": visual, "voice": voice, "text": text, "visual_pct": round(visual/total*100) if total else 0},
        "topics": [{"topic": t, "count": c} for t,c in topic_counts],
        "media_stats": {"images_sent": images_sent, "images_received": images_received, "voice_notes": voice_in},
        "top_students": top_list,
        "generated_at": datetime.now().isoformat()
    }

def get_student_detail(phone: str):
    data = load_all()
    return data.get(phone, None)