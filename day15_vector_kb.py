# day15_vector_kb.py - Day 15: Vector KB - Independent
from langchain_groq import ChatGroq
from langchain_core.documents import Document
import os

# Simple in-memory vector store - No external DB needed for Day 15
class SimpleVectorKB:
    def __init__(self):
        self.docs = [
            Document(page_content="Agentic AI = Autonomous agents that use LLMs + Tools + Memory + Planning to achieve goals without constant human input", metadata={"topic": "agentic"}),
            Document(page_content="LangGraph = Framework to build stateful, multi-actor applications with LLMs as graphs. Nodes are agents/tools, edges are transitions. Perfect for supervisor pattern", metadata={"topic": "langgraph"}),
            Document(page_content="LangChain = Framework for chaining LLMs with tools, memory, prompts. Components: Models, Prompts, Chains, Agents, Memory, Tools", metadata={"topic": "langchain"}),
            Document(page_content="RAG = Retrieval Augmented Generation. Steps: 1. Chunk docs 2. Embed 3. Store in vector DB 4. Retrieve relevant 5. Generate answer with context", metadata={"topic": "rag"}),
            Document(page_content="MCP = Model Context Protocol. Standard for connecting LLMs to external data sources like Drive, Slack, GitHub via servers", metadata={"topic": "mcp"}),
            Document(page_content="Groq = Ultra-fast LLM inference. Models: llama-3.3-70b, openai/gpt-oss-20b. Speed 300+ tokens/sec ideal for voice and real-time agents", metadata={"topic": "groq"}),
            Document(page_content="Supervisor Pattern = One manager agent routes tasks to specialist agents. Benefits: Modularity, Parallelism, Expertise. Supervisor decides: who, when", metadata={"topic": "supervisor"}),
            Document(page_content="Preply Teaching: I teach Agentic AI Bootcamp - 30 Days, hands-on LangChain, LangGraph, Groq, RAG, MCP, Deployment on Render. Book: preply.in/MOHAMMAD6EN21972784102?ts=17923314", metadata={"topic": "booking"}),
        ]
    
    def search(self, query: str, k=3):
        # Simple keyword search for Day 15 (No embeddings needed, keeps independent)
        query_lower = query.lower()
        scored = []
        for doc in self.docs:
            score = sum(1 for w in query_lower.split() if w in doc.page_content.lower())
            scored.append((score, doc))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [doc for score, doc in scored[:k] if score > 0] or self.docs[:2]

kb = SimpleVectorKB()

def query_kb(question: str) -> str:
    results = kb.search(question)
    context = "\n---\n".join([r.page_content for r in results])
    return context