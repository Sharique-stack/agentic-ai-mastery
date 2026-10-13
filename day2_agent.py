import os
from dotenv import load_dotenv
load_dotenv()

from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain.agents import create_agent
from langchain_tavily import TavilySearch  # <-- NEW PACKAGE

# Debug: check keys loaded
print("Groq key loaded:", "yes" if os.getenv("GROQ_API_KEY") else "NO - .env broken")
print("Tavily key loaded:", "yes" if os.getenv("TAVILY_API_KEY") else "NO - .env broken")

llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0)

@tool
def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b

search_tool = TavilySearch(max_results=3)

agent = create_agent(model=llm, tools=[multiply, search_tool])

print("\n--- Test 1: Math ---")
r1 = agent.invoke({"messages": [{"role": "user", "content": "What is 15*12?"}]})
print(r1["messages"][-1].content)

print("\n--- Test 2: Web Search ---")
r2 = agent.invoke({"messages": [{"role": "user", "content": "Who won IPL 2025?"}]})
print(r2["messages"][-1].content)