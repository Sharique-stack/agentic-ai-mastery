import os, json, datetime as dt
from datetime import timedelta
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from twilio.twiml.messaging_response import MessagingResponse

app = FastAPI()

def get_calendar_service():
    try:
        raw = os.getenv("GOOGLE_TOKEN")
        if not raw: return None
        info = json.loads(raw) if isinstance(raw, str) else raw
        creds = Credentials.from_authorized_user_info(info)
        return build("calendar", "v3", credentials=creds)
    except: return None

@tool
def check_availability(requested_time: str) -> str:
    """Check if calendar is free at requested time YYYY-MM-DD HH:MM:SS"""
    try:
        service = get_calendar_service()
        if not service: return "Available all day IST"
        start = dt.datetime.fromisoformat(requested_time)
        end = start + timedelta(hours=1)
        body = {"timeMin": start.isoformat()+"Z","timeMax": end.isoformat()+"Z","items":[{"id":"primary"}]}
        busy = service.freebusy().query(body=body).execute()["calendars"]["primary"]["busy"]
        return "Busy" if busy else f"Free at {requested_time}"
    except Exception as e: return f"Available: {e}"

@tool
def create_booking(student_name: str, time: str, student_email: str = "") -> str:
    """Create calendar booking with name, time YYYY-MM-DD HH:MM:SS, email"""
    try:
        service = get_calendar_service()
        start = dt.datetime.fromisoformat(time)
        end = start + timedelta(hours=1)
        event = {"summary":f"Preply 1:1 - {student_name}","description":f"WhatsApp {student_email}","start":{"dateTime":start.isoformat(),"timeZone":"Asia/Kolkata"},"end":{"dateTime":end.isoformat(),"timeZone":"Asia/Kolkata"}}
        if service: service.events().insert(calendarId="primary",body=event).execute()
        return f"Booked {student_name} at {time} IST. Pay: https://preply.in/MOHAMMAD6EN21972784102?ts=17923314"
    except Exception as e: return f"Saved: {e}"

@tool
def web_search_tool(query: str) -> str:
    """Search web for latest info"""
    try:
        from langchain_tavily import TavilySearch
        return str(TavilySearch(max_results=2).invoke(query))
    except Exception as e: return f"Search error {e}"

@tool
def search_my_notes(query: str) -> str:
    """Search my teaching notes"""
    return "Teaching Agentic AI, LangGraph, Groq. Use web_search for details."

llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0.3)
checkpointer = InMemorySaver()
agent = create_agent(model=llm, tools=[search_my_notes, web_search_tool, check_availability, create_booking], system_prompt="You are Sharique's AI Tutor on WhatsApp. Keep replies SHORT under 200 words.", checkpointer=checkpointer)

@app.get("/")
async def root(): return {"status":"Day 12 Twilio Bot Live - Port OK"}

@app.post("/twilio")
async def twilio_webhook(request: Request):
    form = await request.form()
    msg = form.get("Body","")
    from_num = form.get("From","")
    name = form.get("ProfileName","Student")
    print(f"WA {from_num}: {msg}")
    try:
        config = {"configurable":{"thread_id":f"wa-{from_num}"}}
        result = agent.invoke({"messages":[{"role":"user","content":f"{name} ({from_num}) says: {msg}"}]}, config=config)
        ans = result["messages"][-1].content
    except Exception as e:
        print(f"ERR {e}"); ans = f"Hi {name}! Error {e}, try again hi"
    resp = MessagingResponse(); resp.message(ans[:1500])
    return PlainTextResponse(str(resp), media_type="application/xml")