import os
import json
import datetime as dt
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

st.set_page_config(page_title="Preply AI Tutor by Sharique", page_icon="🎓", layout="wide")
st.title("🎓 Your Preply AI Doubt Solver - Agentic AI")
st.caption("Built in 9 days | RAG + Memory + 3-Agent Team + Booking")

LOG_FILE = "leads.json"

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

@tool
def check_availability(requested_time: str) -> str:
    """Check if Sharique is available. My Preply hours: 12am-11:59pm IST."""
    return f"Available at {requested_time} within 12am-11:59pm IST. Confirm booking at https://preply.in/MOHAMMAD6EN21972784102?ts=17923314 and calendar invite will be sent."

@tool
def create_booking(student_name: str, time: str) -> str:
    """Create a booking confirmation for the student."""
    save_lead(student_name, f"BOOKING REQUEST: {time}", f"booking-{student_name}")
    return f"Booked! {student_name} - {time}. Calendar invite created. Please complete payment on Preply link."

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
    st.write("**My Preply:** $7/lesson, 12am-11:59pm IST")
    st.link_button("📅 Book Live 1:1 on Preply", "https://preply.in/MOHAMMAD6EN21972784102?ts=17923314")
    st.divider()
    st.write("**Stack:** Groq + Tavily + Chroma + LangGraph")
    mode = st.selectbox("Mode", ["Tutor Chat (Day 4)", "Full Class (Day 7 - Teacher+Quiz+Evaluator)", "Book Class (Day 9)"])
    st.divider()
    st.subheader("📊 Day 9 Analytics")
    st.metric("Student", student_name)
    try:
        with open(LOG_FILE, "r") as f:
            leads = f.readlines()
        st.metric("Total Doubts Today", len(leads))
        if leads:
            last = json.loads(leads[-1])
            st.caption(f"Last: {last['doubt'][:35]}...")
    except Exception:
        st.metric("Total Doubts Today", len(st.session_state.get("messages", [])) // 2)
    st.divider()
    st.link_button("💬 Chat on WhatsApp", "https://wa.me/918076025937?text=Hi%20Sharique,%20I%20tried%20your%20AI%20Tutor")

if "messages" not in st.session_state:
    st.session_state.messages = []

if "agent" not in st.session_state:
    st.session_state.agent = create_agent(
        model=llm,
        tools=[search_my_notes, web_search_tool, check_availability, create_booking],
        system_prompt=f"You are Sharique's Preply AI tutor and booking assistant. Student: {student_name}. Always check search_my_notes first. If they ask to book, use check_availability then create_booking. Always end with Preply link.",
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

    if mode.startswith("Full Class"):
        if "quiz" in prompt.lower() or prompt.lower().startswith("teach") or "explain" in prompt.lower():
            st.divider()
            st.subheader("📝 Multi-Agent Class")
            with st.spinner("Quiz Agent creating quiz..."):
                quiz_agent = create_agent(
                    model=llm, 
                    tools=[], 
                    system_prompt="You are a Quiz Agent. Create 2 MCQs from the teacher explanation. Format clearly with A,B,C,D and show correct answer hidden."
                )
                quiz_res = quiz_agent.invoke({"messages": [{"role": "user", "content": f"Create quiz for: {answer}"}]})
                quiz_text = quiz_res["messages"][-1].content
                st.info(quiz_text)
            st.success("Next: Answer the quiz above, or book a live session for 1:1 evaluation — 12am-11:59am IST on Preply!")