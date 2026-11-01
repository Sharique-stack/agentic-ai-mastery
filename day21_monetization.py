# day21_monetization.py - Day 21: Monetization Engine
import json, os
from datetime import datetime, date

FILE = "student_profiles.json"
LIMIT_FILE = "daily_usage.json"

FREE_LIMIT = 5  # Free messages per day
BOOKING_LINK = "https://preply.in/MOHAMMAD6EN21972784102"
UPI_LINK = "upi://pay?pa=mohammad@upi&pn=Tutor&am=299&cu=INR&tn=Premium+Tutor+Monthly"

def load_usage():
    if not os.path.exists(LIMIT_FILE): return {}
    try: return json.loads(open(LIMIT_FILE).read())
    except: return {}

def save_usage(data):
    open(LIMIT_FILE, 'w').write(json.dumps(data, indent=2))

def load_profiles():
    if not os.path.exists(FILE): return {}
    try: return json.loads(open(FILE).read())
    except: return {}

def save_profiles(data):
    open(FILE, 'w').write(json.dumps(data, indent=2))

def check_access(phone: str):
    """Returns: (can_access: bool, remaining: int, is_premium: bool)"""
    profiles = load_profiles()
    profile = profiles.get(phone, {})
    
    # Premium = unlimited
    if profile.get("is_premium"):
        expiry_str = profile.get("premium_expiry")
        if expiry_str:
            try:
                expiry = datetime.fromisoformat(expiry_str).date()
                if expiry >= date.today():
                    return True, 999, True
                else:
                    # Expired
                    profile["is_premium"] = False
                    save_profiles(profiles)
            except: pass
        else:
            return True, 999, True

    # Free user - check daily limit
    usage = load_usage()
    today = date.today().isoformat()
    phone_usage = usage.get(phone, {})
    
    if phone_usage.get("date") != today:
        # New day - reset
        phone_usage = {"date": today, "count": 0}
    
    count = phone_usage.get("count", 0)
    remaining = FREE_LIMIT - count
    
    if count < FREE_LIMIT:
        return True, remaining, False
    else:
        return False, 0, False

def increment_usage(phone: str):
    usage = load_usage()
    today = date.today().isoformat()
    phone_usage = usage.get(phone, {})
    if phone_usage.get("date") != today:
        phone_usage = {"date": today, "count": 0}
    phone_usage["count"] = phone_usage.get("count", 0) + 1
    phone_usage["date"] = today
    usage[phone] = phone_usage
    save_usage(usage)
    return phone_usage["count"]

def get_paywall_message(remaining=0, name="Student"):
    return f"""Hey {name}! 🚀

You've used your *{FREE_LIMIT} free messages* today.

*Premium Benefits (₹299/month):*
✅ Unlimited questions 24/7
✅ Image + Voice analysis
✅ Diagram generation
✅ Personalized study plans

*Get Premium:*
1️⃣ Book 1-1 Session: {BOOKING_LINK}
2️⃣ UPI Pay: {UPI_LINK}
3️⃣ Reply "PAID" after payment

Or wait till tomorrow for free quota reset! What do you want to learn today?"""

def mark_premium(phone: str, days=30):
    profiles = load_profiles()
    p = profiles.get(phone, {})
    p["is_premium"] = True
    p["premium_since"] = datetime.now().isoformat()
    p["premium_expiry"] = (datetime.now() + datetime.timedelta(days=days)).date().isoformat()
    p["total_paid"] = p.get("total_paid",0) + 299
    profiles[phone] = p
    save_profiles(profiles)
    return p

def get_monetization_stats():
    profiles = load_profiles()
    usage = load_usage()
    total = len(profiles)
    premium = sum(1 for p in profiles.values() if p.get("is_premium"))
    total_revenue = sum(p.get("total_paid",0) for p in profiles.values())
    
    # Conversion rate
    conv_rate = round(premium/total*100, 1) if total else 0
    
    # Active today
    today = date.today().isoformat()
    active_today = sum(1 for u in usage.values() if u.get("date")==today)
    
    # Top payers
    top = sorted(profiles.values(), key=lambda x: x.get("total_paid",0), reverse=True)[:5]
    
    return {
        "total_users": total,
        "premium_users": premium,
        "free_users": total - premium,
        "conversion_rate": conv_rate,
        "total_revenue": total_revenue,
        "active_today": active_today,
        "mrr": premium * 299,  # Monthly recurring
        "top_payers": [{"name": p.get("name"), "paid": p.get("total_paid",0)} for p in top]
    }