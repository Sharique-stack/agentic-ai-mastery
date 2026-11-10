# Add to day22_whatsapp_bot.py
@app.get("/feedback")
def feedback_api():
    from day29_feedback import get_feedback_stats
    stats = get_feedback_stats()
    return {
        "project": "WhatsApp AI Tutor - Community Feedback",
        "day": "29/30",
        "stats": stats,
        "message": "Real users > My opinions. This is what they said.",
        "try_it": "WhatsApp: Send 'feedback 5 Loved it!'",
        "live": "https://analytics-d976.onrender.com/"
    }