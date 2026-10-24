# day13_agent.py - Day 13: Analytics Agent (Separate from Day 12)
# Keeps Day 12 safe, adds SQLite analytics
import os
import json
import sqlite3
import datetime as dt
from datetime import timedelta, datetime

from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# ============ DAY 13: AUTO-CREATE DB ============
def init_db():
    conn = sqlite3.connect("leads.db")
    conn.execute("""
    CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_name TEXT,
        phone TEXT,
        query TEXT,
        timestamp TEXT,
        booked INTEGER DEFAULT 0
    )
    """)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_name TEXT,
        phone TEXT,
        time TEXT,
        timestamp TEXT
    )
    """)
    conn.commit()
    conn.close()

init_db()

def get_calendar_service():
    try:
        raw = os.getenv("GOOGLE_TOKEN")
        if not raw: return None
        info = json.loads(raw) if isinstance(raw, str) else raw
        creds = Credentials.from_authorized_user_info(info)
        return build("calendar", "v3", credentials=creds)
    except: return None

# ============ TOOLS (Same as Day 12 + DB save) ============
@tool
def check_availability(requested_time: str) -> str:
    """Check if calendar is free at requested time. Input format: YYYY-MM-DD HH:MM:SS"""
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
        # Day 13: Save to analytics
        conn = sqlite3.connect("leads.db")
        conn.execute("INSERT INTO bookings (student_name, phone, time, timestamp) VALUES (?,?,?,?)",
                     (student_name, student_email, time, datetime.now().isoformat()))
        conn.commit()
        conn.close()

        service = get_calendar_service()
        start = dt.datetime.fromisoformat(time)
        end = start + timedelta(hours=1)
        event = {"summary": f"Preply 1:1 - {student_name}","description": f"WhatsApp {student_email}","start": {"dateTime": start.isoformat(),"timeZone":"Asia/Kolkata"},"end": {"dateTime": end.isoformat(),"timeZone":"Asia/Kolkata"}}
        if service: service.events().insert(calendarId="primary", body=event).execute()
        return f"✅ Booked {student_name} at {time} IST. Pay: https://preply.in/MOHAMMAD6EN21972784102?ts=17923314"
    except Exception as e: return f"Saved: {e}"

@tool
def web_search_tool(query: str) -> str:
    """Search web for latest info using Tavily"""
    try:
        from langchain_tavily import TavilySearch
        return str(TavilySearch(max_results=2).invoke(query))
    except Exception as e: return f"Search error {e}"

@tool
def search_my_notes(query: str) -> str:
    """Search my teaching notes and Preply knowledge base"""
    return "Teaching: Agentic AI, LangGraph, LangChain, Groq, Preply."

@tool
def save_lead(student_name: str, query: str, source: str) -> str:
    """Save student lead info with name, query, source like whatsapp-number. Call for every message."""
    try:
        conn = sqlite3.connect("leads.db")
        conn.execute("INSERT INTO leads (student_name, phone, query, timestamp) VALUES (?,?,?,?)",
                     (student_name, source, query, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        return f"Lead saved {student_name}"
    except Exception as e: return f"Lead error {e}"

@tool
def get_analytics_summary(query: str) -> str:
    """Get analytics summary of leads and bookings. Use when user asks dashboard/stats/analytics"""
    try:
        conn = sqlite3.connect("leads.db")
        total_leads = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
        total_bookings = conn.execute("SELECT COUNT(*) FROM bookings").fetchone()[0]
        recent = conn.execute("SELECT student_name, query FROM leads ORDER BY id DESC LIMIT 5").fetchall()
        conn.close()
        return f"Analytics: {total_leads} chats, {total_bookings} bookings. Recent: {recent}"
    except Exception as e:
        return f"Analytics error {e}, DB empty"

def get_day13_agent():
    llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0.3)
    checkpointer = InMemorySaver()
    agent = create_agent(
        model=llm,
        tools=[search_my_notes, web_search_tool, check_availability, create_booking, save_lead, get_analytics_summary],
        system_prompt="You are Sharique's Day 13 Analytics Tutor on WhatsApp. SHORT replies. For every message call save_lead. You also have get_analytics_summary tool for stats.",
        checkpointer=checkpointer
    )
    return agent, checkpointer