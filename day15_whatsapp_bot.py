# day15_whatsapp_bot.py - Day 15 Independent Bot
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from twilio.twiml.messaging_response import MessagingResponse
from langchain_groq import ChatGroq
from day15_memory import get_memory_context, update_student_profile
from day15_vector_kb import query_kb
import os, datetime as dt
from datetime import timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import json

app = FastAPI()
llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0.4)

def get_calendar_service():
    try:
        raw = os.getenv("GOOGLE_TOKEN")
        if not raw: return None
        info = json.loads(raw) if isinstance(raw, str) else raw
        creds = Credentials.from_authorized_user_info(info)
        return build("calendar", "v3", credentials=creds)
    except: return None

@app.get("/")
async def root():
    return {"day": 15, "feature": "Long-Term Memory + Vector RAG", "independent": True, "status": "Live"}

@app.post("/twilio")
async def twilio_webhook(request: Request):
    form = await request.form()
    msg = form.get("Body","").strip()
    from_num = form.get("From","wa-unknown")
    profile_name = form.get("ProfileName","Student")
    
    # Handle voice note transcription placeholder (Twilio sends MediaUrl)
    media_url = form.get("MediaUrl0","")
    if media_url and not msg:
        msg = "[Voice Note] - Student sent voice message about learning Agentic AI"
    
    # 1. Get memory context
    memory_ctx = get_memory_context(from_num)
    
    # 2. Query vector KB
    kb_ctx = query_kb(msg)
    
    # 3. Generate answer with memory + KB
    prompt = f"""
You are an Agentic AI Tutor on WhatsApp.

Student Memory: {memory_ctx}
Student Name from WhatsApp: {profile_name}
Current Question: {msg}

Relevant Knowledge Base:
{kb_ctx}

Instructions:
1. If new student, greet and ask name/level
2. Use memory to personalize - if they learned LangChain before, don't re-explain basics
3. Answer using KB context
4. Keep WhatsApp style: short, friendly, 2-3 paragraphs max
5. If they ask to book, say: Book via preply.in/MOHAMMAD6EN21972784102?ts=17923314 and mention you will check calendar
6. End with one follow-up question to keep learning

Note today's date is {dt.datetime.now().strftime('%Y-%m-%d')} IST.
"""
    try:
        response = await llm.ainvoke(prompt)
        answer = response.content
        
        # Update memory
        detected_level = None
        if "beginner" in msg.lower(): detected_level = "Beginner"
        if "intermediate" in msg.lower(): detected_level = "Intermediate"
        if "advanced" in msg.lower(): detected_level = "Advanced"
        
        topic = None
        for t in ["agentic","langgraph","langchain","rag","mcp","groq","supervisor"]:
            if t in msg.lower(): topic = t
        
        update_student_profile(from_num, name=profile_name, level=detected_level, topic=topic)
        
    except Exception as e:
        answer = f"Hey {profile_name}! I'm your Agentic AI tutor with memory. I remember our chats! Ask about LangGraph, RAG, etc. Book: preply.in/MOHAMMAD6EN21972784102?ts=17923314 (Error: {e})"

    resp = MessagingResponse()
    resp.message(answer[:1500])
    return PlainTextResponse(str(resp), media_type="application/xml")