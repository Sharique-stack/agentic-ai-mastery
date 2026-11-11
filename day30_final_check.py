# Run: python day30_final_check.py
import requests
BASE = "https://analytics-d976.onrender.com"
checks = ["/", "/health", "/portfolio", "/eval", "/tools", "/interview", "/feedback", "/journey"]
print("🏁 Day 30 Final Check - 30 Days Complete!")
for p in checks:
    try:
        r = requests.get(BASE + p, timeout=10)
        print(f"{'✅' if r.status_code==200 else '❌'} {p} - {r.status_code}")
    except Exception as e:
        print(f"❌ {p} - {e}")
print("\n🎉 CONGRATULATIONS! You finished 30/30. You are not a beginner anymore.")
print("Share your journey. Someone on Day 1 needs to see this.")