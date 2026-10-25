# day14_supervisor.py - Day 14 Supervisor - Independent
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from day14_agents import research_agent, teaching_agent, booking_agent

llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0.3)

SUPERVISOR_PROMPT = """
You are Supervisor of Tutor Team. You have 3 specialists:
1. research_agent - for latest info, news, web search
2. teaching_agent - for explaining Agentic AI, LangChain, etc
3. booking_agent - for checking calendar and booking

User query: {query}

Decide which specialist(s) to call. You can call multiple.
- If query about "latest", "news", "what is new" -> research_agent
- If query about "explain", "teach", "what is LangGraph" -> teaching_agent  
- If query about "book", "slot", "tomorrow 6pm" -> booking_agent
- If mixed, call in sequence and combine answer.

Return final concise WhatsApp-style answer (under 200 words) with booking link if relevant.
"""

async def run_supervisor_team(user_query: str, thread_id: str = "default"):
    config = {"configurable": {"thread_id": thread_id}}
    
    # Simple routing logic (Day 14 - rule based supervisor)
    q = user_query.lower()
    results = []
    
    if any(w in q for w in ["latest","news","search","current","2025","2026","trending"]):
        r = await research_agent.ainvoke({"messages": [HumanMessage(content=user_query)]}, config=config)
        results.append(f"Research: {r['messages'][-1].content}")
    
    if any(w in q for w in ["explain","what is","teach","how does","langchain","langgraph","agentic","rag"]):
        r = await teaching_agent.ainvoke({"messages": [HumanMessage(content=user_query)]}, config=config)
        results.append(f"Teaching: {r['messages'][-1].content}")
    
    if any(w in q for w in ["book","slot","appointment","tomorrow","today","pm","am",":"]):
        r = await booking_agent.ainvoke({"messages": [HumanMessage(content=user_query)]}, config=config)
        results.append(f"Booking: {r['messages'][-1].content}")
    
    # If no specialist matched, default to teaching
    if not results:
        r = await teaching_agent.ainvoke({"messages": [HumanMessage(content=user_query)]}, config=config)
        results.append(r['messages'][-1].content)
    
    # Supervisor synthesis
    final_prompt = SUPERVISOR_PROMPT.format(query=user_query) + f"\n\nSpecialist outputs:\n" + "\n".join(results)
    final = await llm.ainvoke(final_prompt)
    return final.content

def run_supervisor_sync(user_query: str, thread_id: str="default"):
    import asyncio
    return asyncio.run(run_supervisor_team(user_query, thread_id))