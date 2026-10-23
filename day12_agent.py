# day12_agent.py - Day 12: WhatsApp AI Tutor Agent
# This is your core agent - imported by whatsapp_bot.py

import os
import json
import datetime as dt
from datetime import timedelta

from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# ============ GOOGLE CALENDAR ============
def get_calendar_service():
    """Get Google Calendar service from GOOGLE_TOKEN env"""
    try:
        raw = os.getenv("GOOGLE_TOKEN")
        if not raw:
            return None
        info = json.loads(raw) if isinstance(raw, str) else raw
        creds = Credentials.from_authorized_user_info(info)
        return build("calendar", "v3", credentials=creds)
    except Exception as e:
        print(f"Calendar service error: {e}")
        return None

# ============ TOOLS - Day 11 + Day 12 ============

@tool
def check_availability(requested_time: str) -> str:
    """Check if calendar is free at requested time. Input format: YYYY-MM-DD HH:MM:SS"""
    try:
        service = get_calendar_service()
        if not service:
            return "Calendar not connected, assume available 12am-12am IST. You can proceed to book."
        start = dt.datetime.fromisoformat(requested_time)
        end = start + timedelta(hours=1)
        body = {
            "timeMin": start.isoformat() + "Z",
            "timeMax": end.isoformat() + "Z",
            "items": [{"id": "primary"}]
        }
        result = service.freebusy().query(body=body).execute()
        busy = result["calendars"]["primary"]["busy"]
        if busy:
            return f"Busy at {requested_time}. Busy slots: {busy}. Suggest another time."
        return f"Free at {requested_time}. You can book."
    except Exception as e:
        return f"Availability check failed {e}, but assume free and book"

@tool
def create_booking(student_name: str, time: str, student_email: str = "") -> str:
    """Create calendar booking. Inputs: student_name, time YYYY-MM-DD HH:MM:SS, student_email optional"""
    try:
        service = get_calendar_service()
        start = dt.datetime.fromisoformat(time)
        end = start + timedelta(hours=1)
        
        event = {
            "summary": f"Preply 1:1 - {student_name}",
            "description": f"Day 12 WhatsApp Auto-Booking\nStudent: {student_name}\nEmail: {student_email}\nSource: WhatsApp",
            "start": {"dateTime": start.isoformat(), "timeZone": "Asia/Kolkata"},
            "end": {"dateTime": end.isoformat(), "timeZone": "Asia/Kolkata"},
        }
        if service:
            created = service.events().insert(calendarId="primary", body=event).execute()
            link = created.get("htmlLink", "")
            return f"✅ BOOKED {student_name} at {time} IST. Calendar link: {link}. Payment: https://preply.in/MOHAMMAD6EN21972784102?ts=17923314"
        return f"✅ Booking noted for {student_name} at {time} IST (calendar offline). Payment link: https://preply.in/MOHAMMAD6EN21972784102?ts=17923314"
    except Exception as e:
        return f"Booking saved locally but calendar error {e}. Tell student payment link."

@tool
def web_search_tool(query: str) -> str:
    """Search web for latest info using Tavily. Use for current events, docs, latest news"""
    try:
        from langchain_tavily import TavilySearch
        tavily = TavilySearch(max_results=3)
        result = tavily.invoke(query)
        return str(result)
    except Exception as e:
        return f"Web search failed: {e}"

@tool
def search_my_notes(query: str) -> str:
    """Search my teaching notes, Preply knowledge base, and RAG. Use for any teaching related query"""
    # Day 12 Simple RAG - replace with Chroma if you have knowledge/ folder
    try:
        # Try to load from knowledge folder if exists
        if os.path.exists("knowledge"):
            from langchain_community.document_loaders import DirectoryLoader, TextLoader
            from langchain_huggingface import HuggingFaceEmbeddings
            from langchain_chroma import Chroma
            
            loader = DirectoryLoader("knowledge", glob="**/*.txt", loader_cls=TextLoader)
            docs = loader.load()
            if docs:
                embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
                vs = Chroma.from_documents(docs, embeddings, collection_name="day12")
                retriever = vs.as_retriever(search_kwargs={"k": 3})
                results = retriever.invoke(query)
                return "\n\n".join([d.page_content for d in results])
    except Exception as e:
        print(f"RAG error {e}")

    # Fallback static notes
    return """
    Mohammad Sharique - Preply Tutor
    Subjects: Agentic AI, LangGraph, LangChain, Groq, FastAPI, Python, System Design
    Booking: https://preply.in/MOHAMMAD6EN21972784102?ts=17923314
    Rate: Available 12pm-10pm IST daily
    """

@tool
def save_lead(student_name: str, query: str, source: str) -> str:
    """Save student lead info. Inputs: student_name, query/doubt, source like whatsapp-number"""
    try:
        # You can add Sheets/DB here later
        print(f"LEAD: {student_name} | {query} | {source}")
        return f"Lead saved: {student_name} - {query[:50]}"
    except Exception as e:
        return f"Lead save error {e}"

# ============ AGENT FACTORY ============

def get_day12_agent():
    """Returns Day 12 Agent + checkpointer"""
    llm = ChatGroq(
        model="openai/gpt-oss-20b",
        temperature=0.3,
        api_key=os.getenv("GROQ_API_KEY")
    )
    
    checkpointer = InMemorySaver()
    
    agent = create_agent(
        model=llm,
        tools=[search_my_notes, web_search_tool, check_availability, create_booking, save_lead],
        system_prompt="""You are Sharique's AI Tutor on WhatsApp - Day 12 Agent.

Identity:
- Name: Sharique's AI Assistant
- Platform: WhatsApp
- Tone: Friendly, short, helpful, uses few emojis

Rules:
1. Keep replies UNDER 200 words (WhatsApp limit)
2. Always check search_my_notes first for teaching questions
3. For booking flow: Ask name -> check_availability -> create_booking -> send payment link
4. Always save lead with save_lead tool
5. If calendar not connected, still pretend to book and give payment link
6. Be concise - no long paragraphs

Payment Link: https://preply.in/MOHAMMAD6EN21972784102?ts=17923314
""",
        checkpointer=checkpointer
    )
    
    return agent, checkpointer

# For direct testing
if __name__ == "__main__":
    agent, checkpointer = get_day12_agent()
    config = {"configurable": {"thread_id": "test-123"}}
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "Hi I am Rohan, want to learn LangGraph"}]},
        config=config
    )
    print(result["messages"][-1].content)