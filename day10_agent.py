import os
import json
import datetime as dt
from datetime import timedelta
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

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

st.set_page_config(page_title="Preply AI Tutor by Sharique", page_icon="🎓", layout="wide")
st.title("🎓 Your Preply AI Doubt Solver - Agentic AI")
st.caption("Built in 10 days | RAG + Memory + Booking + Real Calendar")

LOG_FILE = "leads.json"
CALENDAR_ID = "primary"

def save_lead(name, doubt, thread_id):
    entry = {
        "time": dt.datetime.now().isoformat(),
        "name": name,
        "thread": thread_id,
        "doubt": doubt
    }
    try:
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass
    return entry

def get_calendar_service():
    try:
        if "GOOGLE_TOKEN" in st.secrets:
            info = json.loads(st.secrets["GOOGLE_TOKEN"])
            creds = Credentials.from_authorized_user_info(info)
            return build("calendar", "v3", credentials=creds)
        return None
    except Exception:
        return None

@tool
def check_availability(requested_time: str) -> str:
    """Check real Google Calendar availability. Input format: YYYY-MM-DD HH:MM"""
    try:
        service = get_calendar_service()
        if not service:
            return f"Calendar API not connected, but generally available 12am-11:59am IST. Proceed to booking at https://preply.in/MOHAMMAD6EN21972784102?ts=17923314"
        start = dt.datetime.fromisoformat(requested_time)
        end = start + timedelta(hours=1)
        body = {
            "timeMin": start.isoformat() + "Z",
            "timeMax": end.isoformat() + "Z",
            "items": [{"id": CALENDAR_ID}]
        }
        freebusy = service.freebusy().query(body=body).execute()
        busy = freebusy["calendars"][CALENDAR_ID]["busy"]
        if busy:
            return f"Busy at {requested_time}. Try another slot between 12am-11:59am IST."
        return f"Free at {requested_time}. Ready to book."
    except Exception as e:
        return f"Available 12am-11:59am IST. Calendar check note: {e}"

@tool
def create_booking(student_name: str, time: str) -> str:
    """Create real Google Calendar event. Time format: YYYY-MM-DD HH:MM"""
    try:
        service = get_calendar_service()
        start = dt.datetime.fromisoformat(time)
        end = start + timedelta(hours=1)
        event = {
            "summary": f"Preply 1:1 - {student_name}",
            "description": f"Booked via AI Tutor. Preply: https://preply.in/MOHAMMAD6EN21972784102?ts=17923314\nStudent: {student_name}",
            "start": {"dateTime": start.isoformat(), "timeZone": "Asia/Kolkata"},
            "end": {"dateTime": end.isoformat(), "timeZone": "Asia/Kolkata"},
        }
        if service:
            service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
        save_lead(student_name, f"REAL BOOKING: {time}", f"booking-{student_name}")
        return f"Booked! Calendar invite created for {student_name} at {time}. Complete payment: https://preply.in/MOHAMMAD6EN21972784102?ts=17923314"
    except Exception as e:
        save_lead(student_name, f"BOOKING REQUEST: {time} - {e}", f"booking-{student_name}")
        return f"Booking saved! Please confirm on Preply link. Note: {e}"

@st.cache_resource
def load_kb():
    try:
        loader = DirectoryLoader("knowledge", glob="**/*.txt", loader_cls=TextLoader)
        docs = loader.load()
        if not docs:
            return None
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        vectorstore = Chroma.from_documents(docs, embeddings, collection_name="streamlit")
        return vectorstore.as_retriever(search_kwargs={"k": 3})
    except Exception as e:
        st.warning(f"KB not loaded: {e}")
        return None

retriever = load_kb()

@tool
def search_my_notes(query: str) -> str:
    """Search my personal knowledge base and notes. Always check first."""
    if not retriever:
        return "Notes not loaded yet."
    results = retriever.invoke(query)
    return "\n\n".join([r.page_content for r in results]) if results else "Not in my notes."

@tool
def web_search_tool(query: str) -> str:
    """Search the internet for latest information."""
    try:
        return TavilySearch(max_results=2).invoke(query)
    except Exception as e:
        return f"Web search failed: {e}"

llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0.3)
checkpointer = InMemorySaver()

with st.sidebar:
    st.header("Student Profile")
    student_name = st.text_input("Your Name", "Aman")
    thread_id = f"student-{student_name.lower()}"
    st.code(f"Thread: {thread_id}")
    st.divider()
    st.write("**My Preply:** $7/lesson, 12am-11:59am IST")
    st.link_button("📅 Book Live 1:1 on Preply", "https://preply.in/MOHAMMAD6EN21972784102?ts=17923314")
    st.divider()
    st.write("**Stack:** Groq + Tavily + Chroma + LangGraph + Google Calendar")
    mode = st.selectbox("Mode", ["Tutor Chat", "Full Class (Teacher+Quiz)", "Book Class (Day 10)"])
    st.divider()
    st.subheader("📊 Day 10 Analytics")
    st.metric("Student", student_name)
    try:
        with open(LOG_FILE, "r") as f:
            leads = f.readlines()
        st.metric("Total Bookings/Doubts", len(leads))
        if leads:
            last = json.loads(leads[-1])
            st.caption(f"Last: {last['doubt'][:35]}...")
    except Exception:
        st.metric("Total Doubts", len(st.session_state.get("messages", [])) // 2)
    st.divider()
    st.link_button("💬 Chat on WhatsApp", "https://wa.me/918076025937?text=Hi%20Sharique,%20I%20tried%20your%20AI%20Tutor")

if "messages" not in st.session_state:
    st.session_state.messages = []

if "agent" not in st.session_state:
    st.session_state.agent = create_agent(
        model=llm,
        tools=[search_my_notes, web_search_tool, check_availability, create_booking],
        system_prompt=f"You are Sharique's Preply AI tutor and booking assistant. Student: {student_name}. Always check search_my_notes first. For booking requests, use check_availability with format YYYY-MM-DD HH:MM then create_booking. Always include Preply link: https://preply.in/MOHAMMAD6EN21972784102?ts=17923314",
        checkpointer=checkpointer
    )

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input(f"Ask your doubt, {student_name}..."):
    save_lead(student_name, prompt, thread_id)
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Teacher is thinking..."):
            config = {"configurable": {"thread_id": thread_id}}
            result = st.session_state.agent.invoke(
                {"messages": [{"role": "user", "content": prompt}]},
                config=config
            )
            answer = result["messages"][-1].content
            st.markdown(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})

    if mode.startswith("Full Class") and any(k in prompt.lower() for k in ["quiz", "teach", "explain"]):
        st.divider()
        st.subheader("📝 Multi-Agent Class")
        with st.spinner("Quiz Agent creating quiz..."):
            quiz_agent = create_agent(
                model=llm,
                tools=[],
                system_prompt="You are a Quiz Agent. Create 2 MCQs from the teacher explanation. Format clearly with A,B,C,D and show correct answer hidden."
            )
            quiz_res = quiz_agent.invoke({"messages": [{"role": "user", "content": f"Create quiz for: {answer}"}]})
            st.info(quiz_res["messages"][-1].content)
        st.success("Next: Answer the quiz or book a live 1:1 evaluation — 12am-11:59am IST on Preply!")