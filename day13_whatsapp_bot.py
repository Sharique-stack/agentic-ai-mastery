from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, HTMLResponse
from twilio.twiml.messaging_response import MessagingResponse
from day13_agent import get_day13_agent
import sqlite3

app = FastAPI()
agent, checkpointer = get_day13_agent()

@app.get("/")
async def root():
    return {"day": 13, "status": "Analytics Bot Live", "dashboard": "/dashboard"}

@app.get("/dashboard")
async def dashboard():
    conn = sqlite3.connect("leads.db")
    try:
        leads = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
        bookings = conn.execute("SELECT COUNT(*) FROM bookings").fetchone()[0]
        rows = conn.execute("SELECT student_name, query, timestamp FROM leads ORDER BY id DESC LIMIT 20").fetchall()
    except:
        leads, bookings, rows = 0, 0, []
    conn.close()
    html = f"""
    <html><body style="font-family:Arial;padding:20px;background:#f5f5f5">
    <h1>📊 Day 13 - WhatsApp Analytics</h1>
    <h2>{leads} Chats | {bookings} Bookings | {bookings/leads*100 if leads else 0:.1f}% Conversion</h2>
    <hr>
    <h3>Recent Chats</h3>
    <ul>{"".join([f"<li><b>{r[0]}</b>: {r[1][:100]} <i>({r[2]})</i></li>" for r in rows])}</ul>
    <p>Live DB: leads.db | <a href='/'>Home</a></p>
    </body></html>
    """
    return HTMLResponse(html)

@app.post("/twilio")
async def twilio_webhook(request: Request):
    form = await request.form()
    msg = form.get("Body","")
    from_num = form.get("From","")
    name = form.get("ProfileName","Student")
    config = {"configurable": {"thread_id": f"wa-{from_num}"}}
    result = agent.invoke({"messages": [{"role": "user", "content": f"{name} ({from_num}) says: {msg}"}]}, config=config)
    ans = result["messages"][-1].content
    resp = MessagingResponse()
    resp.message(ans[:1500])
    return PlainTextResponse(str(resp), media_type="application/xml")