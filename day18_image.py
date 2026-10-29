# day18_image.py - Day 18: Generate diagrams/images (FREE, no API key)
import os, requests, tempfile, urllib.parse, time

def generate_diagram(prompt: str) -> str:
    """
    Generate educational diagram using Pollinations (FLUX model) - FREE, no key, public URL
    Twilio can directly use this URL as media
    """
    try:
        # Enhance prompt for educational diagram
        enhanced = f"educational diagram, clean white background, {prompt}, professional, labeled, simple, infographic style, vector"
        # Pollinations - FREE image gen, returns direct image URL
        encoded = urllib.parse.quote(enhanced)
        # Using FLUX model via Pollinations
        image_url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=768&model=flux&nologo=true&seed={int(time.time())}"
        
        # Verify it exists (quick HEAD request)
        # Don't download, just return URL - Twilio will fetch it
        return image_url
    except Exception as e:
        print(f"Image gen error: {e}")
        return None

def generate_agentic_diagram(topic: str) -> str:
    """Pre-made prompts for common topics - better quality"""
    prompts = {
        "langgraph": "LangGraph multi-agent system flowchart, supervisor agent at top, worker agents below, nodes and edges, arrows showing workflow",
        "rag": "RAG architecture diagram, user query, embedding, vector database retrieval, LLM generation steps",
        "agentic ai": "Agentic AI loop diagram, LLM brain, tools, memory, planning cycle",
        "mcp": "Model Context Protocol diagram, LLM connected to Gmail, Slack, GitHub via MCP server",
        "vector db": "Vector database embedding diagram, documents chunked, converted to vectors, stored"
    }
    topic_lower = topic.lower()
    for key, pre_prompt in prompts.items():
        if key in topic_lower:
            return generate_diagram(pre_prompt)
    
    # Custom
    return generate_diagram(topic)

# Test
if __name__ == "__main__":
    url = generate_agentic_diagram("LangGraph supervisor pattern")
    print(url)q