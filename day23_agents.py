# day23_agents.py - Agents now use RAG
from day22_agents import researcher_agent, explainer_agent, quizzer_agent
from day23_rag import search_memory, add_to_memory
import asyncio

async def supervisor_with_memory(user_query: str, phone: str, level: str = "Beginner"):
    # Step 0: Recall past
    past_context = search_memory(phone, user_query, n=3)
    
    # Step 1: Research
    facts = await researcher_agent(user_query)
    
    # Step 2-3: Parallel with memory context
    enhanced_facts = f"{facts}\nPast context for this user:\n{past_context}"
    
    explain_task = explainer_agent(user_query, enhanced_facts, level)
    quiz_task = quizzer_agent(user_query, level)
    
    explanation, quiz = await asyncio.gather(explain_task, quiz_task)
    
    # Step 4: Save to memory
    add_to_memory(phone, user_query, f"{explanation[:200]} | {quiz[:100]}", level)
    
    return {
        "facts": facts,
        "past": past_context,
        "explanation": explanation,
        "quiz": quiz,
        "agents_used": 3,
        "memory_used": True
    }