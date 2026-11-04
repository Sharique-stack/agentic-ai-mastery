# day24_tools.py - All tools agent can call
import math, json, os, requests
from datetime import datetime

TOOLS = {
    "calculator": "Use for any math: 45*12, sqrt(144), (1200-299)/299",
    "web_search": "Use for latest/current info, news, prices",
    "diagram_generator": "Use when user asks for diagram/flowchart/visual",
    "code_runner": "Use when user asks to run python code",
    "memory_search": "Use when user asks what did I learn / past"
}

def tool_calculator(expression: str) -> str:
    try:
        # Safe eval - only math
        allowed = {"sqrt": math.sqrt, "pow": pow, "abs": abs, "round": round}
        result = eval(expression, {"__builtins__": {}}, allowed)
        return f"🧮 Calculator: {expression} = {result}"
    except Exception as e:
        return f"Calculator error: {e}"

def tool_web_search(query: str) -> str:
    # Using DuckDuckGo instant answer - free, no key
    try:
        r = requests.get(f"https://api.duckduckgo.com/?q={query}&format=json", timeout=5)
        data = r.json()
        abstract = data.get("AbstractText") or data.get("RelatedTopics", [{}])[0].get("Text", "")
        return f"🌐 Web: {abstract[:300] if abstract else 'No live result, using LLM knowledge'}"
    except:
        return "🌐 Web search unavailable, using training knowledge"

def tool_diagram_generator(topic: str) -> str:
    return f"🎨 Diagram requested for: {topic}\nUse /diagram endpoint to generate image\nFlow: {topic} -> Retrieve -> Augment -> Generate"

def tool_code_runner(code: str) -> str:
    try:
        # Safe: only print / math
        output = {}
        exec(f"result = {code}", {}, output)
        return f"💻 Code run: {code} = {output.get('result')}"
    except Exception as e:
        return f"Code error: {e}"

def tool_memory_search(phone: str, query: str) -> str:
    from day23_rag import search_memory
    return search_memory(phone, query)

# MCP-style dispatcher - agent calls this
def call_tool(tool_name: str, args: dict, phone: str = "") -> str:
    if tool_name == "calculator":
        return tool_calculator(args.get("expression", ""))
    if tool_name == "web_search":
        return tool_web_search(args.get("query", ""))
    if tool_name == "diagram_generator":
        return tool_diagram_generator(args.get("topic", ""))
    if tool_name == "code_runner":
        return tool_code_runner(args.get("code", ""))
    if tool_name == "memory_search":
        return tool_memory_search(phone, args.get("query", ""))
    return f"Unknown tool: {tool_name}"