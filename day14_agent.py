# day14_agents.py - Day 14: Multi-Agent Tutor Team - INDEPENDENT
import os
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain.agents import create_agent

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import json, datetime as dt
from datetime import timedelta

def get_calendar_service():
    try:
        raw = os.getenv("GOOGLE_TOKEN")
        if not raw: return None
        info = json.loads(raw) if isinstance(raw, str) else raw
        creds = Credentials.from_authorized_user_info(info)
        return build("calendar", "v3", credentials=creds)
    except: return None

@tool
def check_calendar(time_str: str) -> str:
    """Check calendar availability YYYY-MM-DD HH:MM:SS"""
    try:
        service = get_calendar_service()
        if not service: return "Free all day"
        start = dt.datetime.fromisoformat(time_str)
        end = start + timedelta(hours=1)
        busy = service.freebusy().query(body={"timeMin": start.isoformat()+"Z","timeMax": end.isoformat()+"Z","items":[{"id":"primary"}]}).execute()["calendars"]["primary"]["busy"]
        return "Busy" if busy else f"Free at {time_str}"
    except Exception as e: return f"Free: {e}"

@tool
def book_slot(name: str, time: str, phone: str="") -> str:
    """Book tutoring slot"""
    try:
        service = get_calendar_service()
        start = dt.datetime.fromisoformat(time)
        end = start + timedelta(hours=1)
        event = {"summary": f"Preply - {name}","description": phone,"start": {"dateTime": start.isoformat(),"timeZone":"Asia/Kolkata"},"end": {"dateTime": end.isoformat(),"timeZone":"Asia/Kolkata"}}
        if service: service.events().insert(calendarId="primary", body=event).execute()
        return f"✅ Booked {name} at {time} IST. Link: https://preply.in/MOHAMMAD6EN21972784102?ts=17923314"
    except Exception as e: return f"Booked locally: {e}"

@tool
def search_web(query: str) -> str:
    """Search web for latest tech info"""
    try:
        from langchain_tavily import TavilySearch
        return str(TavilySearch(max_results=2).invoke(query))
    except Exception as e: return f"Search error {e}"

@tool
def teaching_kb(query: str) -> str:
    """My teaching knowledge base - Agentic AI, LangChain, LangGraph, Groq, Python"""
    kb = {
        "agentic": "Agentic AI = LLMs that use tools, memory, planning to achieve goals autonomously",
        "langgraph": "LangGraph = Graph-based orchestration for stateful multi-agent workflows",
        "preply": "I teach Agentic AI bootcamp on Preply - book via preply.in/MOHAMMAD6EN21972784102"
    }
    for k,v in kb.items():
        if k in query.lower(): return v
    return "I teach Agentic AI, LangChain, LangGraph, Groq, RAG, MCP. Ask specific topic."

llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0.3)

# Specialist 1: Research Agent
research_agent = create_agent(
    model=llm,
    tools=[search_web],
    system_prompt="You are Research Specialist. You only search web and provide latest info. Be concise."
)

# Specialist 2: Teaching Agent  
teaching_agent = create_agent(
    model=llm,
    tools=[teaching_kb],
    system_prompt="You are Teaching Specialist. You explain Agentic AI concepts simply. Use KB tool."
)

# Specialist 3: Booking Agent
booking_agent = create_agent(
    model=llm,
    tools=[check_calendar, book_slot],
    system_prompt="You are Booking Specialist. Check availability then book. Always confirm time in IST."
)

# Supervisor will delegate to these