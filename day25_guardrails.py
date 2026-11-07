# day25_guardrails.py - Input + Output guardrails
import re

# Blocked patterns - prompt injection / abuse
BLOCKED_PATTERNS = [
    r"ignore previous instructions",
    r"you are now",
    r"jailbreak",
    r"give me.*password",
    r"write.*malware",
    r"how to cheat.*exam",
]

TOXIC_WORDS = ["hate", "stupid idiot", "kill yourself"]

def check_input_guardrail(user_query: str) -> dict:
    q = user_query.lower()
    for pat in BLOCKED_PATTERNS:
        if re.search(pat, q):
            return {"allowed": False, "reason": f"Blocked: prompt-injection / unsafe request detected: {pat}"}
    for w in TOXIC_WORDS:
        if w in q:
            return {"allowed": False, "reason": "Blocked: toxic language"}
    if len(user_query) > 2000:
        return {"allowed": False, "reason": "Blocked: message too long"}
    return {"allowed": True, "reason": "ok"}

def check_output_guardrail(answer: str, rag_context: str = "") -> dict:
    # 1. Empty / too short
    if not answer or len(answer) < 20:
        return {"allowed": False, "reason": "Output too short / empty", "score": 0}

    # 2. Hallucination check - if RAG context exists, answer should overlap
    if rag_context:
        # Simple keyword overlap check
        context_words = set(rag_context.lower().split())
        answer_words = set(answer.lower().split())
        overlap = len(context_words & answer_words) / max(1, len(answer_words))
        if overlap < 0.05:
            return {"allowed": False, "reason": "Low faithfulness to RAG - possible hallucination", "score": round(overlap, 2)}

    # 3. No leaked system prompt
    if "GROQ_API_KEY" in answer or "system prompt" in answer.lower():
        return {"allowed": False, "reason": "Leaked system info", "score": 0}

    return {"allowed": True, "reason": "ok", "score": 1.0}