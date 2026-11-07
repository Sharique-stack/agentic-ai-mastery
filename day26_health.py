# day26_health.py
import time, os, json
from datetime import datetime

START_TIME = time.time()

def get_health():
    uptime_sec = int(time.time() - START_TIME)
    # Check critical env vars
    checks = {
        "groq_key": bool(os.getenv("GROQ_API_KEY")),
        "twilio": True, # Twilio is stateless webhook
        "eval_log": os.path.exists("eval_log.json"),
        "memory": os.path.exists("eval_log.json"),
    }
    all_ok = all(checks.values())
    return {
        "status": "healthy" if all_ok else "degraded",
        "uptime_sec": uptime_sec,
        "uptime_human": f"{uptime_sec//3600}h {(uptime_sec%3600)//60}m",
        "timestamp": datetime.now().isoformat(),
        "checks": checks,
        "version": "v1.0-day26"
    }