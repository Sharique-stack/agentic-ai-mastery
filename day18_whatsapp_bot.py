# day18_whatsapp_bot.py - Day 18 Independent Image Bot
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from twilio.twiml.messaging_response import MessagingResponse
from langchain_groq import ChatGroq
from day18_memory import get_memory_context, update_student_profile
from day18_image import generate_agentic_diagram
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
    return text.strip()[:900]

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
    except: return ""

KB = "Agentic AI=agents with tools+memory+planning. LangGraph=graph framework for multi-agent. RAG=Retrieve+Generate. MCP=connect LLMs to tools. Booking=preply.in/MOHAMMAD6EN21972784102"

def is_image_request(text: str) -> bool:
    keywords = ["show", "diagram", "image", "picture", "draw", "visual", "chart", "flow", "architecture", "dikhayo", "batao diagram"]
    return any(k in text.lower() for k in keywords)

@app.get("/")
async def root():
    return {"day": 18, "feature": "Image + Diagram Bot", "independent": True}

@app.post("/twilio")
async def twilio_webhook(request: Request):
    form = await request.form()
    body = form.get("Body","").strip()
    from_num = form.get("From","")
    profile_name = form.get("ProfileName","Student")
    media_url = form.get("MediaUrl0","")
    media_type = form.get("MediaContentType0","")
    
    user_text = body
    is_voice = False
    if media_url and "audio" in media_type:
        is_voice = True
        user_text = transcribe_voice(media_url) or body
    
    if not user_text: user_text = "Hello"
    
    memory_ctx = get_memory_context(from_num)
    wants_image = is_image_request(user_text)
    
    # Extract topic for image
    image_url = None
    if wants_image:
        # Use LLM to extract what diagram to draw
        extract_prompt = f"Extract diagram topic from: '{user_text}'. Return only 2-3 words like 'LangGraph', 'RAG architecture', 'MCP flow'. If generic, return '{user_text}'"
        try:
            topic_resp = await llm.ainvoke(extract_prompt)
            diagram_topic = topic_resp.content.strip()[:100]
        except:
            diagram_topic = user_text
        image_url = generate_agentic_diagram(diagram_topic)
    
    # Generate explanation
    prompt = f"""
You are Visual Tutor.

Memory: {memory_ctx}
Name: {profile_name}
Question: {user_text}
Wants Image: {wants_image}
KB: {KB}

RULES:
- NO tables | |
- Use *bold* not **bold**
- Short: 3 lines max + say "Check image above 👆"
- If wants image, explain in simple visual terms
- End with question
Today: {dt.datetime.now().strftime('%Y-%m-%d')}
"""
    try:
        resp = await llm.ainvoke(prompt)
        text_reply = whatsapp_cleaner(resp.content)
        topic = next((t for t in ["agentic","langgraph","rag","mcp","vector"] if t in user_text.lower()), None)
        update_student_profile(from_num, name=profile_name, topic=topic, is_image=wants_image, is_voice=is_voice)
    except Exception as e:
        text_reply = f"Hey {profile_name}! 🎨 Check the diagram! Ask what you want to see."[:400]

    twiml = MessagingResponse()
    
    if wants_image and image_url:
        # Send image FIRST, then text
        msg = twiml.message(f"🎨 Here's your *{user_text[:30]}* diagram!")
        msg.media(image_url)  # Twilio fetches public Pollinations URL
        # Second message with explanation
        twiml.message(text_reply)
    else:
        twiml.message(text_reply + ("\n\n_Try: 'Show LangGraph diagram' 🎨_" if not wants_image else ""))
    
    return PlainTextResponse(str(twiml), media_type="application/xml")