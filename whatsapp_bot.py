from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from twilio.twiml.messaging_response import MessagingResponse
from day12_agent import get_day12_agent

app = FastAPI()
agent, checkpointer = get_day12_agent()

@app.get("/")
async def root():
    return {"status": "Day 12 Agent Live"}

@app.post("/twilio")
async def twilio_hook(request: Request):
    form = await request.form()
    msg = form.get("Body","")
    from_num = form.get("From","")
    name = form.get("ProfileName","Student")
    
    config = {"configurable": {"thread_id": f"wa-{from_num}"}}
    result = agent.invoke(
        {"messages": [{"role": "user", "content": f"{name} ({from_num}) says: {msg}"}]},
        config=config
    )
    ans = result["messages"][-1].content
    
    resp = MessagingResponse()
    resp.message(ans[:1500])
    return PlainTextResponse(str(resp), media_type="application/xml")
@app.get("/dashboard")
async def dashboard():
    # Simple HTML dashboard (works on Render without Streamlit)
    import sqlite3
    conn = sqlite3.connect("leads.db")
    try:
        leads = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
        bookings = conn.execute("SELECT COUNT(*) FROM bookings").fetchone()[0]
        rows = conn.execute("SELECT student_name, query, timestamp FROM leads ORDER BY id DESC LIMIT 10").fetchall()
    except:
        leads, bookings, rows = 0,0,[]
    conn.close()
    
    html = f"""
    <html><body style="font-family:Arial;padding:20px">
    <h1>Day 13 Analytics</h1>
    <h2>{leads} Chats | {bookings} Bookings | {bookings/leads*100 if leads else 0:.1f}% Conv</h2>
    <ul>{"".join([f"<li><b>{r[0]}</b>: {r[1][:80]} - {r[2]}</li>" for r in rows])}</ul>
    <p><a href='/'>Home</a> | Full dashboard: Deploy day13_dashboard.py on Streamlit</p>
    </body></html>
    """
    from fastapi.responses import HTMLResponse
    return HTMLResponse(html)