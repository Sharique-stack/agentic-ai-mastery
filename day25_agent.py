# day25_agent.py - Wraps Day 24 agent
import time
from day24_agent import supervisor_with_tools
from day25_guardrails import check_input_guardrail, check_output_guardrail
from day25_eval import evaluate_answer

async def supervisor_with_guardrails(user_query: str, phone: str, level: str = "Beginner"):
    start = time.time()

    # STEP 0: Input Guardrail
    inp = check_input_guardrail(user_query)
    if not inp["allowed"]:
        return {
            "explanation": f"🛡️ I can't help with that. {inp['reason']}\nTry asking about RAG, Python, Math, etc.",
            "quiz": "What is RAG?",
            "tool_used": "guardrail_block",
            "tool_output": inp["reason"],
            "eval": {"accuracy": 0, "latency_ms": 0}
        }

    # STEP 1: Normal Day 24 Tool Agent
    result = await supervisor_with_tools(user_query, phone, level)

    # STEP 2: Output Guardrail
    out = check_output_guardrail(result["explanation"], rag_context=result.get("tool_output", ""))
    if not out["allowed"]:
        result["explanation"] = f"🛡️ I need to re-check that answer. {out['reason']}\nLet me give you a simpler, verified version:\n\nRAG = Retrieve relevant notes → Augment prompt → Generate answer with Groq."
        result["tool_used"] = "guardrail_fix"

    # STEP 3: Evaluate
    eval_data = evaluate_answer(user_query, result["explanation"], result["tool_used"], result.get("tool_output",""), start)
    result["eval"] = eval_data
    return result