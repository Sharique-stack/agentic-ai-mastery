# day15_memory.py - Day 15: Student Memory (Independent)
import json, os
from datetime import datetime

MEMORY_FILE = "student_profiles.json"

def load_memory():
    if not os.path.exists(MEMORY_FILE): return {}
    try: return json.loads(open(MEMORY_FILE).read())
    except: return {}

def save_memory(data):
    open(MEMORY_FILE, 'w').write(json.dumps(data, indent=2))

def get_student_profile(phone: str):
    mem = load_memory()
    return mem.get(phone, {
        "phone": phone,
        "name": "Unknown",
        "level": "Beginner",
        "topics_learned": [],
        "last_seen": None,
        "total_sessions": 0,
        "interests": []
    })

def update_student_profile(phone: str, name=None, level=None, topic=None, interest=None):
    mem = load_memory()
    profile = get_student_profile(phone)
    if name: profile["name"] = name
    if level: profile["level"] = level
    if topic and topic not in profile["topics_learned"]:
        profile["topics_learned"].append(topic)
    if interest and interest not in profile["interests"]:
        profile["interests"].append(interest)
    profile["last_seen"] = datetime.now().isoformat()
    profile["total_sessions"] += 1
    mem[phone] = profile
    save_memory(mem)
    return profile

def get_memory_context(phone: str) -> str:
    p = get_student_profile(phone)
    if p["total_sessions"] == 0:
        return "New student, no history"
    return f"Student {p['name']} | Level: {p['level']} | Learned: {', '.join(p['topics_learned'][-5:])} | Interests: {', '.join(p['interests'])} | Sessions: {p['total_sessions']}"