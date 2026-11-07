# day25_eval.py - Score every answer
import time, json, os
from datetime import datetime

EVAL_LOG = "eval_log.json"

def evaluate_answer(question: str, answer: str, tool_used: str, rag_context: str, start_time: float) -> dict:
    latency_ms = int((time.time() - start_time) * 1000)

    # Heuristic scores - fast, no extra LLM call
    # 1. Completeness (has explanation + example?)
    completeness = 1.0 if len(answer) > 200 and "example" in answer.lower() else 0.7
    # 2. Faithfulness (overlap with RAG)
    faithfulness = 0.9 if rag_context and any(w in answer.lower() for w in rag_context.lower().split()[:20]) else 0.6
    # 3. Tool success
    tool_success = 1.0 if tool_used != "error" else 0.0

    accuracy = round((completeness + faithfulness + tool_success) / 3 * 100, 1)

    # Cost estimate - Groq llama-3.1-8b-instant ~ $0.0001 / 1k tokens approx
    est_cost = round(len(question + answer) / 1000 * 0.0001, 5)

    record = {
        "time": datetime.now().isoformat(),
        "question": question[:100],
        "tool": tool_used,
        "accuracy": accuracy,
        "faithfulness": faithfulness,
        "latency_ms": latency_ms,
        "cost_usd": est_cost
    }

    # Append to log
    logs = []
    if os.path.exists(EVAL_LOG):
        try: logs = json.load(open(EVAL_LOG))
        except: logs = []
    logs.append(record)
    json.dump(logs[-200:], open(EVAL_LOG, "w"), indent=2)

    return record

def get_eval_stats():
    if not os.path.exists(EVAL_LOG):
        return {"total": 0, "avg_accuracy": 0, "avg_latency_ms": 0, "total_cost": 0}
    logs = json.load(open(EVAL_LOG))
    if not logs: return {"total": 0}
    return {
        "total": len(logs),
        "avg_accuracy": round(sum(x["accuracy"] for x in logs) / len(logs), 1),
        "avg_latency_ms": int(sum(x["latency_ms"] for x in logs) / len(logs)),
        "total_cost": round(sum(x["cost_usd"] for x in logs), 4),
        "tool_breakdown": {t: sum(1 for x in logs if x["tool"]==t) for t in set(x["tool"] for x in logs)}
    }