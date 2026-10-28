# day17_whatsapp_bot.py - Day 17 Independent Voice-to-Voice
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from twilio.twiml.messaging_response import MessagingResponse
from langchain_groq import ChatGroq
from day17_memory import get_memory_context, update_student_profile
from day17_tts import generate_voice_reply
from groq import Groq
import os, re, requests, tempfile, datetime as dt
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()
llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0.3)
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def whatsapp_cleaner(text: str) -> str:
    text = re.sub(r'\|.*\|', '', text)
    text = re.sub(r'\*\*(.*?)\*\*', r'*\1*', text)
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
    return text.strip()[:1000]

def transcribe_voice(media_url: str) -> str:
    try:
        sid = os.getenv("TWILIO_ACCOUNT_SID")
        token = os.getenv("TWILIO_AUTH_TOKEN")
        auth = (sid, token) if sid and token else None
        r = requests.get(media_url, auth=auth, timeout=15)
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as f:
            f.write(r.content)
            path = f.name
        with open(path, "rb") as audio:
            tr = groq_client.audio.transcriptions.create(file=(path, audio.read()), model="whisper-large-v3", response_format="text")
        os.remove(path)
        return tr.strip() if isinstance(tr, str) else tr.text.strip()
    except Exception as e:
        return f"[Voice] {e}"

KB = "Agentic AI = Agents with tools+memory+planning. LangGraph=Multi-agent graph framework. RAG=Retrieval Augmented Generation. MCP=Connect LLMs to external tools. Groq=Fast inference. Booking=preply.in/MOHAMMAD6EN21972784102"

@app.get("/")
async def root():
    return {"day": 17, "feature": "Voice-to-Voice TTS", "independent": True}

@app.post("/twilio")
async def twilio_webhook(request: Request):
    form = await request.form()
    body = form.get("Body","").strip()
    from_num = form.get("From","")
    profile_name = form.get("ProfileName","Student")
    media_url = form.get("MediaUrl0","")
    media_type = form.get("MediaContentType0","")
    
    is_voice_in = False
    user_text = body
    
    if media_url and "audio" in media_type:
        is_voice_in = True
        user_text = transcribe_voice(media_url)
    
    if not user_text: user_text = "Hello"
    
    memory_ctx = get_memory_context(from_num)
    
    prompt = f"""
You are Voice Tutor. Reply in 2 short sentences max (for voice note).

Memory: {memory_ctx}
Name: {profile_name}
Question: {user_text}
Is Voice Input: {is_voice_in}
KB: {KB}

RULES:
- NO tables, NO markdown tables
- Short: 2 sentences, under 250 chars (for TTS)
- Friendly, spoken style: "Hey Rahul, LangGraph is..."
- Use *bold* for text version
- End with quick question
Today: {dt.datetime.now().strftime('%Y-%m-%d')}
"""
    try:
        resp = await llm.ainvoke(prompt)
        text_reply = whatsapp_cleaner(resp.content)
        short_voice_text = text_reply[:280]  # For TTS
        
        # Generate voice file
        voice_path = generate_voice_reply(short_voice_text)
        
        # Decide: Send voice or text? If user sent voice, reply with voice
        level = "Beginner" if "beginner" in user_text.lower() else None
        topic = next((t for t in ["agentic","langgraph","rag","mcp"] if t in user_text.lower()), None)
        update_student_profile(from_num, name=profile_name, level=level, topic=topic, is_voice_in=is_voice_in, is_voice_out=True if is_voice_in else False)
        
    except Exception as e:
        text_reply = f"Hey {profile_name}! 🎙️ I heard you: {user_text[:60]}. Ask about LangGraph, RAG! Error: {e}"[:500]
        voice_path = None

    twiml_resp = MessagingResponse()
    
    # Day 17 Key: If voice input, send BOTH text + audio file URL
    # For Twilio, we need to host audio publicly. For MVP, send text with 🎙️ indicator
    # Full audio sending needs Twilio Media: resp.message().media(url)
    if voice_path and is_voice_in:
        # Upload to temp public URL logic would go here
        # For Render MVP, we send text + note that voice is generated
        # If you have AWS S3/Cloudinary, upload and use: msg.media(voice_url)
        twiml_resp.message(f"🎙️ Voice reply: {text_reply}\n\n_(Voice note generation ready - upload to S3 for media)_")
        # If you want actual voice note: 
        # msg = twiml_resp.message(f"🎙️ {text_reply}")
        # msg.media(f"https://your-cdn.com/{voice_filename}")
    else:
        twiml_resp.message(text_reply)
    
    return PlainTextResponse(str(twiml_resp), media_type="application/xml")

# For actual voice media serving:
@app.get("/audio/{filename}")
async def serve_audio(filename: str):
    from fastapi.responses import FileResponse
    import glob
    files = glob.glob(f"/tmp/*{filename}*")
    if files:
        return FileResponse(files[0], media_type="audio/mpeg")
    return {"error": "not found"}