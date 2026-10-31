# day20_memory.py - Day 20 Memory with analytics fields
import json, os
from datetime import datetime

FILE = "student_profiles.json"

def load_memory():
    if not os.path.exists(FILE): return {}
    try: return json.loads(open(FILE).read())
    except: return {}

def save_memory(data):
    open(FILE, 'w').write(json.dumps(data, indent=2))

def get_student_profile(phone: str):
    mem = load_memory()
    return mem.get(phone, {
        "phone": phone, "name": "Unknown", "level": "Beginner",
        "topics_learned": [], "total_sessions": 0,
        "images_sent": 0, "images_received": 0, "images_requested": 0,
        "voice_in": 0, "voice_out": 0, "preferred_mode": "text",
        "first_seen": datetime.now().isoformat()
    })

def update_student_profile(phone: str, name=None, topic=None, sent_image=False, received_image=False, is_voice=False):
    mem = load_memory()
    p = get_student_profile(phone)
    if name: p["name"] = name
    if topic and topic not in p["topics_learned"]: p["topics_learned"].append(topic)
    if sent_image: p["images_sent"] = p.get("images_sent",0)+1; p["images_requested"] = p.get("images_requested",0)+1
    if received_image: p["images_received"] = p.get("images_received",0)+1
    if is_voice: p["voice_in"] = p.get("voice_in",0)+1
    if received_image: p["preferred_mode"] = "visual"
    elif is_voice and p.get("preferred_mode")!="visual": p["preferred_mode"] = "voice"
    p["last_seen"] = datetime.now().isoformat()
    p["total_sessions"] = p.get("total_sessions",0)+1
    mem[phone] = p
    save_memory(mem)
    return p

def get_memory_context(phone: str) -> str:
    p = get_student_profile(phone)
    if p["total_sessions"]==0: return "New student"
    return f"{p['name']} | Lvl: {p['level']} | Sess: {p['total_sessions']} | Pref: {p['preferred_mode']} | Learned: {','.join(p['topics_learned'][-2:])}"