# day28_final_test.py - Run: python day28_final_test.py
import requests

BASE = "https://analytics-d976.onrender.com"
TESTS = [
    ("/", 200),
    ("/health", 200),
    ("/portfolio", 200),
    ("/eval", 200),
    ("/tools", 200),
    ("/interview", 200),
]

print("🧪 Day 28 Final Test...")
passed = 0
for path, expected in TESTS:
    try:
        r = requests.get(BASE + path, timeout=10)
        status = "✅ PASS" if r.status_code == expected else f"❌ FAIL {r.status_code}"
        if r.status_code == expected: passed += 1
        print(f"{status} {path}")
    except Exception as e:
        print(f"❌ FAIL {path} - {e}")

print(f"\nResult: {passed}/{len(TESTS)} passed")
if passed == len(TESTS):
    print("🚀 LAUNCH READY! Go to Day 29.")
else:
    print("🛠️ Fix failed endpoints before launch.")