# Day 12 - WhatsApp AI Tutor Bot 💬🤖

Live: https://preply-whatsapp-bot.onrender.com/
Webhook: https://preply-whatsapp-bot.onrender.com/twilio

Architecture: WhatsApp → Twilio → FastAPI → LangGraph Agent (Groq + Tools) → Google Calendar → Reply

Tools:
- check_availability
- create_booking
- search_my_notes
- web_search_tool
- save_lead

Deploy:
Build: pip install -r requirements.txt
Start: python -m uvicorn whatsapp_bot:app --host 0.0.0.0 --port 10000
Env: GROQ_API_KEY, TAVILY_API_KEY, GOOGLE_TOKEN