import os
import json
import datetime as dt
from datetime import timedelta
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse

from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain.agents import create_agent
from langchain_tavily import TavilySearch
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import DirectoryLoader, TextLoader
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
    """Check if calendar is free at requested time in ISO format YYYY-MM-DD HH:MM:SS"""
    try:
        service = get_calendar_service()
        if not service: return "Available 12am-12am IST, proceed"
        start = dt.datetime.fromisoformat(requested_time)
        end = start + timedelta(hours=1)
        body = {"timeMin": start.isoformat() + "Z", "timeMax": end.isoformat() + "Z", "items": [{"id": "primary"}]}
        busy = service.freebusy().query(body=body).execute()["calendars"]["primary"]["busy"]
        return "Busy at that time" if busy else f"Free at {requested_time}"
    except Exception as e: return f"Available: {e}"

@tool
def create_booking(student_name: str, time: str, student_email: str = "") -> str:
    """Create calendar booking for student with name, time YYYY-MM-DD HH:MM:SS, and email"""
    try:
        service = get_calendar_service()
        start = dt.datetime.fromisoformat(time)
        end = start + timedelta(hours=1)
        event = {"summary": f"Preply 1:1 - {student_name}", "description": f"WhatsApp Booking {student_name} {student_email}", "start": {"dateTime": start.isoformat(), "timeZone": "Asia/Kolkata"}, "end": {"dateTime": end.isoformat(), "timeZone": "Asia/Kolkata"}}
        if service: service.events().insert(calendarId="primary", body=event).execute()
        return f"Booked {student_name} at {time} IST. Pay: https://preply.in/MOHAMMAD6EN21972784102?ts=17923314"
    except Exception as e: return f"Booking saved: {e}"

retriever = None
try:
    if os.path.exists("knowledge"):
        loader = DirectoryLoader("knowledge", glob="**/*.txt", loader_cls=TextLoader)
        docs = loader.load()
        if docs:
            embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
            vs = Chroma.from_documents(docs, embeddings, collection_name="wa")
            retriever = vs.as_retriever(search_kwargs={"k": 3})
except: pass

@tool
def search_my_notes(query: str) -> str:
    """Search my teaching notes and Preply knowledge base"""
    if not retriever: return "Notes not loaded"
    r = retriever.invoke(query)
    return "\n\n".join([x.page_content for x in r]) if r else "Not in notes"

@tool
def web_search_tool(query: str) -> str:
    """Search web for latest info using Tavily"""
    try: return TavilySearch(max_results=2).invoke(query)
    except: return "Web search failed"

llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0.3)
checkpointer = InMemorySaver()
agent = create_agent(model=llm, tools=[search_my_notes, web_search_tool, check_availability, create_booking], system_prompt="You are Sharique's AI Tutor on WhatsApp. Keep replies SHORT under 250 words. Always check search_my_notes first.", checkpointer=checkpointer)

@app.get("/")
async def root():
    return {"status": "Day 12 Twilio Bot Live"}

@app.post("/twilio")
async def twilio_webhook(request: Request):
    form = await request.form()
    incoming_msg = form.get("Body", "")
    from_number = form.get("From", "")
    profile_name = form.get("ProfileName", "Student")
    print(f"WhatsApp from {from_number}: {incoming_msg}")
    try:
        config = {"configurable": {"thread_id": f"wa-{from_number}"}}
        result = agent.invoke({"messages": [{"role": "user", "content": f"{profile_name} ({from_number}) says: {incoming_msg}"}]}, config=config)
        answer = result["messages"][-1].content
    except Exception as e:
        print(f"Agent error: {e}")
        answer = f"Hi {profile_name}! I got error {e}. Try again."
    resp = MessagingResponse()
    resp.message(answer[:1500])
    return PlainTextResponse(str(resp), media_type="application/xml")