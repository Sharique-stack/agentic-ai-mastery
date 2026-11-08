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

# WhatsApp AI Tutor - Multi-Agent RAG Tutor on WhatsApp 🤖

> Remembers, Acts, Self-Checks. Built in 30 Days. Live in Production.

**Live Demo:** https://analytics-d976.onrender.com/
**Try:** `/health` | `/portfolio` | `/eval` | `/tools`

![Day 26 Architecture](image_20261107_124305.webp)

## 🚀 What It Does

| Feature | Example | Tool |
| :--- | :--- | :--- |
| 🧮 Calculator | `What is 299 * 12?` → 3588 | `calculator` |
| 🌐 Live Search | `What is latest Groq model?` | `web_search` |
| 🎨 Diagram | `Draw RAG diagram` | `diagram` |
| 💻 Code Runner | `Run python print(2+2)` | `code_runner` |
| 🧠 Memory | `What did I learn about RAG?` | `memory_search` |

## 🧠 Architecture
