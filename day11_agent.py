import os
import json
import datetime as dt
from datetime import timedelta
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# Safe env load
if "GROQ_API_KEY" in st.secrets:
    os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]
if "TAVILY_API_KEY" in st.secrets:
    os.environ["TAVILY_API_KEY"] = st.secrets["TAVILY_API_KEY"]

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
import yagmail

st.set_page_config(page_title="Preply AI Tutor by Sharique", page_icon="🎓", layout="wide")
st.title("🎓 Your Preply AI Doubt Solver - Agentic AI")
st.caption("Built in 11 days | RAG + Memory + Real Calendar + Email")

LOG_FILE = "leads.json"
CALENDAR_ID = "primary"

def save_lead(name, doubt, thread_id):
    entry = {"time": dt.datetime.now().isoformat(), "name": name, "thread": thread_id, "doubt": doubt}
    try:
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass
    return entry

def get_calendar_service():
    try:
        raw = st.secrets.get("GOOGLE_TOKEN") or os.getenv("GOOGLE_TOKEN")
        if not raw:
            return None
        # FIX: Handle both string and dict
        if isinstance(raw, str):
            info = json.loads(raw)
        else:
            info = dict(raw)  # already dict from TOML
        creds = Credentials.from_authorized_user_info(info)
        return build("calendar", "v3", credentials=creds)
    except Exception as e:
        st.sidebar.warning(f"Calendar error: {e}")
        return None

def send_email(to_email, subject, body):
    try:
        gmail_user = st.secrets.get("GMAIL_USER") or os.getenv("GMAIL_USER")
        gmail_pass = st.secrets.get("GMAIL_APP_PASSWORD") or os.getenv("GMAIL_APP_PASSWORD")
        if not gmail_user or not gmail_pass:
            return "Email not configured"
        # FIX: remove spaces if user pasted with spaces
        gmail_pass = gmail_pass.replace(" ", "")
        yag = yagmail.SMTP(gmail_user, gmail_pass)
        yag.send(to=to_email, subject=subject, contents=body)
        return f"Email sent to {to_email}"
    except Exception as e:
        return f"Email failed: {e}"

@tool
def check_availability(requested_time: str) -> str:
    """Check real Google Calendar. Format: YYYY-MM-DD HH:MM"""
    try:
        service = get_calendar_service()
        if not service:
            return "Calendar API not connected, but available 12am-12am IST. Proceed to booking."
        start = dt.datetime.fromisoformat(requested_time)
        end = start + timedelta(hours=1)
        body = {"timeMin": start.isoformat() + "Z", "timeMax": end.isoformat() + "Z", "items": [{"id": CALENDAR_ID}]}
        freebusy = service.freebusy().query(body=body).execute()
        busy = freebusy["calendars"][CALENDAR_ID]["busy"]
        if busy:
            return f"Busy at {requested_time}. Try another slot 12am-11:59am IST."
        return f"Free at {requested_time}. Ready to book."
    except Exception as e:
        return f"Available 12am-12am IST. Note: {e}"

@tool
def create_booking(student_name: str, time: str, student_email: str = "") -> str:
    """Create real Google Calendar event + send email confirmation. Time: YYYY-MM-DD HH:MM"""
    try:
        service = get_calendar_service()
        start = dt.datetime.fromisoformat(time)
        end = start + timedelta(hours=1)
        event = {
            "summary": f"Preply 1:1 - {student_name}",
            "description": f"Booked via AI Tutor. Preply: https://preply.in/MOHAMMAD6EN21972784102?ts=17923314\nStudent: {student_name} {student_email}",
            "start": {"dateTime": start.isoformat(), "timeZone": "Asia/Kolkata"},
            "end": {"dateTime": end.isoformat(), "timeZone": "Asia/Kolkata"},
        }
        if service:
            service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
        
        email_status = ""
        if student_email:
            subject = f"Confirmed: Your Preply class with Sharique at {time} IST"
            body = f"Hi {student_name},\n\nYour class is confirmed for {time} IST.\n\nGoogle Calendar invite sent.\nComplete payment: https://preply.in/MOHAMMAD6EN21972784102?ts=17923314\n\nAny doubt? Reply to this email or WhatsApp: +91 80760 25937\n\n- Sharique"
            email_status = send_email(student_email, subject, body)
        
        save_lead(student_name, f"REAL BOOKING + EMAIL: {time} {student_email} {email_status}", f"booking-{student_name}")
        return f"Booked! Calendar invite created for {student_name} at {time}. {email_status}. Payment: https://preply.in/MOHAMMAD6EN21972784102?ts=17923314"
    except Exception as e:
        save_lead(student_name, f"BOOKING REQUEST: {time} - {e}", f"booking-{student_name}")
        return f"Booking saved! Confirm on Preply link. Note: {e}"

@st.cache_resource
def load_kb():
    try:
        # Check if knowledge folder exists
        if not os.path.exists("knowledge"):
            return None
        loader = DirectoryLoader("knowledge", glob="**/*.txt", loader_cls=TextLoader, show_progress=False)
        docs = loader.load()
        if not docs:
            return None
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        vectorstore = Chroma.from_documents(docs, embeddings, collection_name="streamlit")
        return vectorstore.as_retriever(search_kwargs={"k": 3})
    except Exception as e:
        print(f"KB error: {e}")
        return None

retriever = load_kb()

@tool
def search_my_notes(query: str) -> str:
    """Search my personal knowledge base. Always check first."""
    if not retriever:
        return "Notes not loaded - using general knowledge."
    results = retriever.invoke(query)
    return "\n\n".join([r.page_content for r in results]) if results else "Not in my notes."

@tool
def web_search_tool(query: str) -> str:
    """Search the internet for latest info."""
    try:
        return TavilySearch(max_results=2).invoke(query)
    except Exception as e:
        return f"Web search failed: {e}"

# FIX: Safe LLM init
try:
    llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0.3)
except Exception as e:
    st.error(f"Groq init failed: {e}")
    st.stop()

checkpointer = InMemorySaver()

with st.sidebar:
    st.header("Student Profile")
    student_name = st.text_input("Your Name", "Aman")
    student_email = st.text_input("Your Email for Confirmation", placeholder="aman@gmail.com")
    thread_id = f"student-{student_name.lower()}"
    st.code(f"Thread: {thread_id}")
    st.divider()
    st.link_button("📅 Book on Preply", "https://preply.in/MOHAMMAD6EN21972784102?ts=17923314")
    st.divider()
    st.write("**Stack:** Groq + Tavily + Chroma + LangGraph + Calendar + Email")
    st.divider()
    st.subheader("📊 Day 11 Analytics")
    try:
        with open(LOG_FILE, "r") as f:
            leads = f.readlines()
        st.metric("Total Leads", len(leads))
    except Exception:
        st.metric("Doubts", len(st.session_state.get("messages", [])) // 2)
    st.link_button("💬 WhatsApp", "https://wa.me/918076025937?text=Hi%20Sharique,%20I%20tried%20your%20AI%20Tutor")

if "messages" not in st.session_state:
    st.session_state.messages = []

if "agent" not in st.session_state:
    st.session_state.agent = create_agent(
        model=llm,
        tools=[search_my_notes, web_search_tool, check_availability, create_booking],
        system_prompt=f"You are Sharique's AI tutor + booking assistant. Student: {student_name}, Email: {student_email}. Always check search_my_notes first. For booking, use check_availability then create_booking with name, time YYYY-MM-DD HH:MM, and email {student_email}. Always include Preply link.",
        checkpointer=checkpointer
    )

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input(f"Ask doubt, {student_name}..."):
    save_lead(student_name, prompt, thread_id)
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Teacher thinking..."):
            config = {"configurable": {"thread_id": thread_id}}
            result = st.session_state.agent.invoke({"messages": [{"role": "user", "content": prompt}]}, config=config)
            answer = result["messages"][-1].content
            st.markdown(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})