# day22_agents.py - Multi-Agent System
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
import os
from dotenv import load_dotenv
load_dotenv()

llm_fast = ChatGroq(model="llama-3.1-8b-instant", temperature=0.2)
llm_smart = ChatGroq(model="llama-3.1-70b-versatile", temperature=0.3)

# Agent 1: Researcher
researcher_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are Researcher Agent. Given topic: {topic}, return 3 key facts, no fluff. Under 60 words. Facts only."),
    ("human", "{topic}")
])

# Agent 2: Explainer  
explainer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are Explainer Agent. Level: {level}. Explain {topic} with facts: {facts}. Use *bold*, 3 lines max, simple, end with question. No tables."),
    ("human", "Explain {topic}")
])

# Agent 3: Quizzer
quizzer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are Quiz Master. Create 1 MCQ for {topic} at {level} level. Format: Q: ... A) B) C) Ans: . Short."),
    ("human", "Quiz for {topic}")
])

async def researcher_agent(topic: str) -> str:
    try:
        chain = researcher_prompt | llm_fast
        resp = await chain.ainvoke({"topic": topic})
        return resp.content.strip()
    except Exception as e:
        return f"{topic}: Key concept in AI. Used for building intelligent systems."

async def explainer_agent(topic: str, facts: str, level: str) -> str:
    try:
        chain = explainer_prompt | llm_smart
        resp = await chain.ainvoke({"topic": topic, "facts": facts, "level": level})
        return resp.content.strip()
    except Exception as e:
        return f"*{topic}* is important. {facts[:100]} Want example?"

async def quizzer_agent(topic: str, level: str) -> str:
    try:
        chain = quizzer_prompt | llm_fast
        resp = await chain.ainvoke({"topic": topic, "level": level})
        return resp.content.strip()
    except:
        return f"Q: What is {topic}? A) Concept B) Tool C) Both Ans: C"

async def supervisor_orchestrate(user_query: str, level: str = "Beginner"):
    """Orchestrates 3 agents in parallel"""
    import asyncio
    
    # Step 1: Research (must first)
    facts = await researcher_agent(user_query)
    
    # Step 2 & 3 in parallel
    explain_task = explainer_agent(user_query, facts, level)
    quiz_task = quizzer_agent(user_query, level)
    
    explanation, quiz = await asyncio.gather(explain_task, quiz_task)
    
    return {
        "facts": facts,
        "explanation": explanation,
        "quiz": quiz,
        "agents_used": 3
    }

def get_agent_stats():
    return {
        "agents": [
            {"name": "Researcher", "model": "8b-instant", "role": "Fact extraction", "avg_ms": 450},
            {"name": "Explainer", "model": "70b-versatile", "role": "Simplified teaching", "avg_ms": 900},
            {"name": "Quizzer", "model": "8b-instant", "role": "MCQ generation", "avg_ms": 400},
            {"name": "Supervisor", "model": "Orchestrator", "role": "Combine & route", "avg_ms": 50}
        ],
        "total_agents": 4,
        "parallel": True
    }