# day14_whatsapp_bot.py - Day 14 Independent WhatsApp Bot
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from twilio.twiml.messaging_response import MessagingResponse
from day14_supervisor import run_supervisor_sync

app = FastAPI()

@app.get("/")
async def root():
    return {"day": 14, "pattern": "Supervisor Multi-Agent", "status": "Live", "independent": "No Day 13 dependency"}

@app.post("/twilio")
async def twilio_webhook(request: Request):
    form = await request.form()
    msg = form.get("Body","")
    from_num = form.get("From","")
    name = form.get("ProfileName","Student")
    
    try:
        answer = run_supervisor_sync(f"{name} says: {msg}", thread_id=f"wa-{from_num}")
    except Exception as e:
        answer = f"Team thinking... error {e}, but I teach Agentic AI. Book: preply.in/MOHAMMAD6EN21972784102?ts=17923314"
    
    resp = MessagingResponse()
    resp.message(answer[:1500])
    return PlainTextResponse(str(resp), media_type="application/xml")