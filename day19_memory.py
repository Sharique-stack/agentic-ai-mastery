# day19_memory.py - Day 19 Memory
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
        "images_sent": 0, "images_received": 0,
        "voice_in": 0, "preferred_mode": "text"
    })

def update_student_profile(phone: str, name=None, topic=None, sent_image=False, received_image=False, is_voice=False):
    mem = load_memory()
    p = get_student_profile(phone)
    if name: p["name"] = name
    if topic and topic not in p["topics_learned"]: p["topics_learned"].append(topic)
    if sent_image: p["images_sent"] += 1
    if received_image: p["images_received"] += 1
    if is_voice: p["voice_in"] += 1
    if received_image: p["preferred_mode"] = "visual"
    elif is_voice: p["preferred_mode"] = "voice"
    p["last_seen"] = datetime.now().isoformat()
    p["total_sessions"] += 1
    mem[phone] = p
    save_memory(mem)
    return p

def get_memory_context(phone: str) -> str:
    p = get_student_profile(phone)
    if p["total_sessions"] == 0: return "New student"
    return f"{p['name']} | Level: {p['level']} | Sent Img: {p['images_sent']} | Recv Img: {p['images_received']} | Voice: {p['voice_in']} | Pref: {p['preferred_mode']} | Learned: {','.join(p['topics_learned'][-3:])}"