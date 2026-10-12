import os
from dotenv import load_dotenv
load_dotenv()

from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain.agents import create_agent


os.environ["GROQ_API_KEY"] = "gsk_..."
llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0)

@tool
def get_data_science_definition(topic: str) -> str:
    """Get definition of any data science topic"""
    return f"{topic}: RAG = Retrieval Augmented Generation. Agent = LLM + Tools + Reasoning loop."

@tool
def multiply(a: int, b: int) -> int:
    """Multiply two numbers"""
    return a * b

agent = create_agent(llm, tools=[get_data_science_definition, multiply])

result = agent.invoke({
    "messages": [{"role": "user", "content": "What is RAG? And what is 24*7?"}]
})

print("\n--- FINAL ANSWER ---")
print(result["messages"][-1].content)