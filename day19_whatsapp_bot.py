# day19_whatsapp_bot.py - Day 19 Independent Multi-Modal Tutor
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from twilio.twiml.messaging_response import MessagingResponse
from langchain_groq import ChatGroq
from day19_memory import get_memory_context, update_student_profile
from day19_multimodal import transcribe_audio, analyze_image, generate_diagram_image
import os, re, datetime as dt
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()
llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0.3)

def cleaner(text: str) -> str:
    text = re.sub(r'\|.*\|', '', text)
    text = re.sub(r'\*\*(.*?)\*\*', r'*\1*', text)
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
    return text.strip()[:1000]

KB = "Agentic AI=agents with tools+memory. LangGraph=multi-agent graph framework. RAG=retrieve then generate. MCP=connect LLM to tools. Booking=preply.in/MOHAMMAD6EN21972784102"

def wants_diagram(text: str) -> bool:
    keys = ["show", "diagram", "image", "picture", "draw", "visual", "chart", "flow", "architecture", "dikhayo"]
    return any(k in text.lower() for k in keys)

@app.get("/")
async def root():
    return {"day": 19, "feature": "Multi-Modal Tutor", "handles": ["text", "voice", "image_in", "image_out"]}

@app.post("/twilio")
async def twilio_webhook(request: Request):
    form = await request.form()
    body = form.get("Body","").strip()
    from_num = form.get("From","")
    profile_name = form.get("ProfileName","Student")
    media_url = form.get("MediaUrl0","")
    media_type = form.get("MediaContentType0","")
    
    sid = os.getenv("TWILIO_ACCOUNT_SID")
    token = os.getenv("TWILIO_AUTH_TOKEN")
    auth = (sid, token) if sid and token else None

    user_text = body
    image_analysis = ""
    is_voice = False
    received_image = False
    sent_image = False

    # 1. Handle incoming modality
    if media_url:
        if "audio" in media_type:
            is_voice = True
            transcribed = transcribe_audio(media_url, auth) if auth else ""
            user_text = transcribed or body or "Voice message"
        elif "image" in media_type:
            received_image = True
            image_analysis = analyze_image(media_url, auth, body) if auth else "Image received"
            user_text = body or "Explain this image"
    
    if not user_text: user_text = "Hello"

    memory_ctx = get_memory_context(from_num)
    need_diagram = wants_diagram(user_text)

    # 2. Generate diagram if requested
    diagram_url = None
    if need_diagram:
        # Extract topic
        try:
            ext = await llm.ainvoke(f"Extract 3-word diagram topic from: '{user_text}'. Return only topic.")
            topic = ext.content.strip()[:80]
        except:
            topic = user_text[:80]
        diagram_url = generate_diagram_image(topic)

    # 3. Build prompt with multimodal context
    prompt = f"""
You are Multi-Modal Tutor for {profile_name}.

Memory: {memory_ctx}
User Input (Text): {user_text}
Image Analysis (if student sent image): {image_analysis}
Wants Diagram: {need_diagram}
KB: {KB}

RULES:
- NO tables | |
- *bold* not **bold**
- If image_analysis present, first acknowledge what you saw in their image, then answer
- If wants diagram, say "Check image 👆" + 2 line explanation
- Short: 3-4 lines max
- If student sent homework photo, help solve step by step but concise
- End with question
Today: {dt.datetime.now().strftime('%Y-%m-%d')}
"""
    try:
        resp = await llm.ainvoke(prompt)
        text_reply = cleaner(resp.content)
        topic = next((t for t in ["agentic","langgraph","rag","mcp","vector"] if t in user_text.lower()), None)
        update_student_profile(from_num, name=profile_name, topic=topic, sent_image=bool(diagram_url), received_image=received_image, is_voice=is_voice)
    except Exception as e:
        text_reply = f"Hey {profile_name}! Got your { 'voice' if is_voice else 'image' if received_image else 'message'}! {image_analysis[:200] if image_analysis else 'How can I help?'}"
        print(e)

    twiml = MessagingResponse()
    
    if need_diagram and diagram_url:
        sent_image = True
        msg = twiml.message(f"🎨 *{user_text[:35]}*")
        msg.media(diagram_url)
        twiml.message(text_reply)
    else:
        extra = ""
        if received_image and image_analysis:
            extra = f"\n\n_What I saw: {image_analysis[:150]}_"
        elif is_voice:
            extra = f"\n\n_🎙️ Transcribed: {user_text[:100]}_"
        
        twiml.message(text_reply + extra + ("\n\n_Try: Send notes photo or 'Show diagram' 🎨_" if not need_diagram and not received_image else ""))

    return PlainTextResponse(str(twiml), media_type="application/xml")