# day22_memory.py
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
    return mem.get(phone, {"phone": phone, "name": "Unknown", "level": "Beginner", "topics_learned": [], "total_sessions": 0, "is_premium": False, "total_paid": 0, "images_sent": 0, "voice_in": 0, "preferred_mode": "text", "agent_interactions": 0})

def update_student_profile(phone: str, name=None, topic=None, sent_image=False, is_voice=False, received_image=False):
    mem = load_memory()
    p = get_student_profile(phone)
    if name: p["name"] = name
    if topic and topic not in p["topics_learned"]: p["topics_learned"].append(topic)
    if sent_image: p["images_sent"] = p.get("images_sent",0)+1
    if is_voice: p["voice_in"] = p.get("voice_in",0)+1
    if received_image: p["preferred_mode"] = "visual"
    elif is_voice and p.get("preferred_mode")!="visual": p["preferred_mode"] = "voice"
    p["last_seen"] = datetime.now().isoformat()
    p["total_sessions"] = p.get("total_sessions",0)+1
    p["agent_interactions"] = p.get("agent_interactions",0)+3
    mem[phone] = p
    save_memory(mem)
    return p

def get_memory_context(phone: str) -> str:
    p = get_student_profile(phone)
    return f"{p['name']} | Level: {p['level']} | Topics: {','.join(p['topics_learned'][-2:])} | Agent calls: {p.get('agent_interactions',0)}"