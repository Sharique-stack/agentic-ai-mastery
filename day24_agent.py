# day24_agent.py - Tool-using supervisor
import json, re
from day24_tools import TOOLS, call_tool
from day23_agents import supervisor_with_memory
from groq import Groq
import os

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

async def supervisor_with_tools(user_query: str, phone: str, level: str = "Beginner"):
    # Step 0: Let LLM decide tool
    tool_prompt = f"""
    You are a router. Available tools: {json.dumps(TOOLS, indent=2)}
    User query: "{user_query}"
    Return ONLY JSON: {{"tool": "calculator|web_search|diagram_generator|code_runner|memory_search|none", "args": {{}}}}
    Examples:
    "What is 299*12?" -> {{"tool": "calculator", "args": {{"expression": "299*12"}}}}
    "What is latest Groq model?" -> {{"tool": "web_search", "args": {{"query": "latest Groq model"}}}}
    "What did I learn yesterday?" -> {{"tool": "memory_search", "args": {{"query": "yesterday"}}}}
    "Draw RAG diagram" -> {{"tool": "diagram_generator", "args": {{"topic": "RAG"}}}}
    "Run 2+2" -> {{"tool": "code_runner", "args": {{"code": "2+2"}}}}
    """
    try:
        res = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": tool_prompt}],
            temperature=0
        )
        decision = json.loads(re.search(r'\{.*\}', res.choices[0].message.content, re.S).group())
        tool_name = decision.get("tool", "none")
    except:
        tool_name, decision = "none", {}

    tool_output = ""
    if tool_name != "none":
        tool_output = call_tool(tool_name, decision.get("args", {}), phone)

    # Step 1: Normal multi-agent with tool context
    result = await supervisor_with_memory(f"{user_query}\nTool result: {tool_output}", phone, level)
    result["tool_used"] = tool_name
    result["tool_output"] = tool_output
    return result