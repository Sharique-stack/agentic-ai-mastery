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

print("Day 4: Agent with Memory + RAG + Web Search\n")

# 1. Load knowledge base (from Day 3)
loader = DirectoryLoader("knowledge", glob="**/*.txt", loader_cls=TextLoader)
docs = loader.load()
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vectorstore = Chroma.from_documents(docs, embeddings, collection_name="day4")
retriever = vectorstore.as_retriever(search_kwargs={"k": 2})

# 2. Tools - all with docstrings!
@tool
def search_my_notes(query: str) -> str:
    """Search my personal knowledge base, Preply profile, and my notes. Always check this first."""
    results = retriever.invoke(query)
    if not results:
        return "No relevant info in my notes."
    return "\n\n".join([r.page_content for r in results])

@tool
def web_search_tool(query: str) -> str:
    """Search the internet for latest info, IPL, news, current events."""
    search = TavilySearch(max_results=2)
    return search.invoke(query)

@tool
def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b

# 3. Memory - This is the NEW part
checkpointer = InMemorySaver()

llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0)

agent = create_agent(
    model=llm,
    tools=[search_my_notes, web_search_tool, multiply],
    system_prompt="You are my Preply AI tutor. ALWAYS check search_my_notes first. Remember conversation history and use it to answer follow-up questions.",
    checkpointer=checkpointer  # <-- This gives memory
)

# 4. Chat with memory - must use same thread_id
config = {"configurable": {"thread_id": "student-123"}}

print("--- Chat Start (type 'exit' to stop) ---\n")

# Demo conversation that NEEDS memory
conversation = [
    "My name is Aman, I am learning RAG",
    "What is my Preply hourly rate?",
    "What did I say my name is?",
    "Explain RAG in simple words",
    "Give me an example of the previous concept"  # This needs memory of "RAG"
]

for q in conversation:
    print(f"You: {q}")
    result = agent.invoke(
        {"messages": [{"role": "user", "content": q}]},
        config=config
    )
    answer = result["messages"][-1].content
    print(f"Agent: {answer}\n")
    print("-" * 60 + "\n")

print("Now try interactive:")
while True:
    user_input = input("You: ")
    if user_input.lower() in ["exit", "quit"]:
        break
    result = agent.invoke(
        {"messages": [{"role": "user", "content": user_input}]},
        config=config
    )
    print(f"Agent: {result['messages'][-1].content}\n")