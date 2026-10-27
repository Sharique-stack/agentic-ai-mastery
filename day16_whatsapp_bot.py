# day16_whatsapp_bot.py - Day 16 Independent Voice Bot
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from twilio.twiml.messaging_response import MessagingResponse
from langchain_groq import ChatGroq
from day16_memory import get_memory_context, update_student_profile
from day16_voice import transcribe_voice
import os, re, datetime as dt, json
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()
llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0.3)

# WhatsApp cleaner (fixes your Day 14 table bug)
def whatsapp_cleaner(text: str) -> str:
    text = re.sub(r'\|.*\|', '', text)
    text = text.replace('---','')
    text = re.sub(r'\*\*(.*?)\*\*', r'*\1*', text)
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
    text = text.strip()
    if len(text) > 1000:
        text = text[:970] + "...\n\n*Type more for details*"
    return text

# Simple KB - Independent
KB_DOCS = """
Agentic AI = Autonomous agents with Tools + Memory + Planning.
LangGraph = Graph framework for multi-agent systems. Nodes=agents, Edges=flow. Supervisor pattern.
LangChain = Chaining LLMs with tools, prompts, memory.
RAG = Retrieve from docs then Generate answer. Steps: chunk->embed->store->retrieve->generate.
MCP = Model Context Protocol to connect LLMs to Drive, Slack, GitHub.
Groq = Fastest LLM inference 300+ tok/sec. Models: llama-3.3-70b, openai/gpt-oss-20b, whisper-large-v3.
Booking = preply.in/MOHAMMAD6EN21972784102?ts=17923314
"""

@app.get("/")
async def root():
    return {"day": 16, "feature": "Voice + Memory + Whisper", "independent": True, "model": "whisper-large-v3 + openai/gpt-oss-20b"}

@app.post("/twilio")
async def twilio_webhook(request: Request):
    form = await request.form()
    body = form.get("Body","").strip()
    from_num = form.get("From","wa-unknown")
    profile_name = form.get("ProfileName","Student")
    media_url = form.get("MediaUrl0","")
    media_type = form.get("MediaContentType0","")
    
    is_voice = False
    user_text = body
    
    # 1. VOICE HANDLING - Key Day 16 feature
    if media_url and ("audio" in media_type or "ogg" in media_type or "mpeg" in media_type):
        is_voice = True
        # Twilio auth from ENV for media download
        twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
        twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
        auth = (twilio_sid, twilio_token) if twilio_sid and twilio_token else None
        
        transcribed = transcribe_voice(media_url, auth)
        user_text = transcribed
        print(f"Voice transcribed: {transcribed}")
    
    if not user_text:
        user_text = "Hello"

    # 2. Memory
    memory_ctx = get_memory_context(from_num)
    
    # 3. Prompt - WhatsApp native, NO TABLES
    prompt = f"""
You are WhatsApp Voice Tutor. Student may have sent VOICE NOTE.

Memory: {memory_ctx}
Name: {profile_name}
Is Voice Message: {is_voice}
Transcribed Text: {user_text}

Knowledge Base: {KB_DOCS}

RULES:
- NEVER use tables | |
- Use *bold* for WhatsApp, not **bold**
- Short: 4 lines max
- If voice message, start with "Got your voice! 🎙️ You said: *{user_text[:80]}*"
- Personalize using memory
- Emojis: 🤖 💡 🎙️
- End with question
- Booking: preply.in/MOHAMMAD6EN21972784102?ts=17923314 if asked

Today: {dt.datetime.now().strftime('%Y-%m-%d')}
"""
    try:
        resp_ai = await llm.ainvoke(prompt)
        answer = whatsapp_cleaner(resp_ai.content)
        
        # Update memory
        level = None
        if "beginner" in user_text.lower(): level="Beginner"
        if "intermediate" in user_text.lower(): level="Intermediate"
        topic = next((t for t in ["agentic","langgraph","langchain","rag","mcp","groq"] if t in user_text.lower()), None)
        update_student_profile(from_num, name=profile_name, level=level, topic=topic, is_voice=is_voice)
        
    except Exception as e:
        answer = f"Hey {profile_name}! 🎙️ Got your {'voice' if is_voice else 'message'}! I'm your voice tutor with memory. Ask about LangGraph, RAG. Error: {e}"[:900]

    twiml = MessagingResponse()
    twiml.message(answer)
    return PlainTextResponse(str(twiml), media_type="application/xml")