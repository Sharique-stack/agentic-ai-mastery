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