import os
from dotenv import load_dotenv
load_dotenv()

from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain.agents import create_agent
from langchain_tavily import TavilySearch
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langgraph.checkpoint.memory import InMemorySaver

print("Day 5: Multi-Agent Tutor Team\n")

# Load KB (same as Day 3/4)
loader = DirectoryLoader("knowledge", glob="**/*.txt", loader_cls=TextLoader)
docs = loader.load()
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vectorstore = Chroma.from_documents(docs, embeddings, collection_name="day5")
retriever = vectorstore.as_retriever(search_kwargs={"k": 2})

@tool
def search_my_notes(query: str) -> str:
    """Search my notes, Preply profile, RAG notes. Always check first."""
    results = retriever.invoke(query)
    return "\n\n".join([r.page_content for r in results]) if results else "Not in notes."

@tool
def web_search_tool(query: str) -> str:
    """Search internet for latest info."""
    return TavilySearch(max_results=2).invoke(query)

llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0.3)

# 3 SPECIALIZED AGENTS
teacher_agent = create_agent(
    model=llm,
    tools=[search_my_notes],
    system_prompt="You are the TEACHER. Explain concepts simply using my notes. Use examples from my teaching style. Be friendly, concise. End with 'Do you want a quiz?'"
)

quiz_agent = create_agent(
    model=llm,
    tools=[],
    system_prompt="You are QUIZ MASTER. Create 2 short MCQs based on the last topic explained. Format: Q1, Options A-D, then Q2. Keep it fun, beginner level."
)

evaluator_agent = create_agent(
    model=llm,
    tools=[],
    system_prompt="You are EVALUATOR. User will give answers. Check them, give score /2, explain correct answers, encourage. If score 2/2 say 'Excellent!', else say 'Revise and try again'."
)

# SUPERVISOR / ORCHESTRATOR - Manual workflow for simplicity
checkpointer = InMemorySaver()
config = {"configurable": {"thread_id": "aman-preply"}}

def run_tutor_team():
    print("=== PREPLY MULTI-AGENT TUTOR STARTED ===\n")
    topic = input("Student, what do you want to learn today? (e.g., RAG): ")
    
    # Step 1: Teacher teaches
    print("\n[Teacher Agent Teaching...]\n")
    teach_res = teacher_agent.invoke({"messages": [{"role": "user", "content": f"Teach {topic} using my notes"}]})
    teaching = teach_res["messages"][-1].content
    print(f"TEACHER: {teaching}\n")
    
    # Step 2: Quiz Master creates quiz
    print("-" * 60)
    print("\n[Quiz Agent Creating Quiz...]\n")
    quiz_res = quiz_agent.invoke({"messages": [{"role": "user", "content": f"Create quiz for topic: {topic}. Context: {teaching}"}]})
    quiz = quiz_res["messages"][-1].content
    print(f"QUIZ MASTER: {quiz}\n")
    
    # Step 3: Student answers + Evaluator checks
    print("-" * 60)
    answers = input("\nYour answers (e.g., Q1 A, Q2 C): ")
    
    print("\n[Evaluator Agent Checking...]\n")
    eval_res = evaluator_agent.invoke({"messages": [{"role": "user", "content": f"Topic: {topic}. Quiz: {quiz}. Student answers: {answers}. Evaluate."}]})
    feedback = eval_res["messages"][-1].content
    print(f"EVALUATOR: {feedback}\n")
    
    print("\n=== SESSION COMPLETE ===")
    print("This is your Preply Doubt Solver v1!")

if __name__ == "__main__":
    run_tutor_team()