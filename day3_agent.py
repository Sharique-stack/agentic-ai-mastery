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

print("Loading knowledge base...")

# 1. Load your docs
loader = DirectoryLoader("knowledge", glob="**/*.txt", loader_cls=TextLoader)
docs = loader.load()
print(f"Loaded {len(docs)} docs")

# 2. Embed + Store (local, free)
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vectorstore = Chroma.from_documents(docs, embeddings, persist_directory="./chroma_db")
retriever = vectorstore.as_retriever(search_kwargs={"k": 2})

# 3. Tools
@tool
def search_my_notes(query: str) -> str:
    """Search my personal knowledge base, Preply profile, and my notes. Always use this first."""
    results = retriever.invoke(query)
    return "\n\n".join([r.page_content for r in results])

@tool
def web_search_tool(query: str) -> str:
    """Search the internet for latest information, news, cricket scores."""
    search = TavilySearch(max_results=2)
    return search.invoke(query)

@tool
def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b

# 4. Agent
llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0)

agent = create_agent(
    model=llm,
    tools=[search_my_notes, web_search_tool, multiply],
    system_prompt="ALWAYS check search_my_notes FIRST before using web_search_tool. If answer is in my notes, use that."
)

# Tests
tests = [
    "What is my Preply hourly rate and availability?",
    "What is RAG according to my notes?",
    "Who won IPL 2025?"  # This should trigger web search
]

for q in tests:
    print(f"\n--- Q: {q} ---")
    res = agent.invoke({"messages": [{"role": "user", "content": q}]})
    print(res["messages"][-1].content)