# day20_whatsapp_bot.py - Day 20 Bot + Analytics Dashboard
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, HTMLResponse, JSONResponse
from twilio.twiml.messaging_response import MessagingResponse
from langchain_groq import ChatGroq
from day20_memory import get_memory_context, update_student_profile
from day20_analytics import get_dashboard_stats, get_student_detail
import os, re, datetime as dt, requests, tempfile, urllib.parse, time, base64
from groq import Groq
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()
llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0.3)
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# --- Multimodal helpers (from Day 19) ---
def transcribe_audio(media_url, auth):
    try:
        r = requests.get(media_url, auth=auth, timeout=20)
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as f:
            f.write(r.content); path=f.name
        with open(path, "rb") as audio:
            tr = groq_client.audio.transcriptions.create(file=(path, audio.read()), model="whisper-large-v3", response_format="text")
        os.remove(path)
        return tr.strip() if isinstance(tr, str) else tr.text.strip()
    except: return ""

def analyze_image(media_url, auth, txt=""):
    try:
        r = requests.get(media_url, auth=auth, timeout=20)
        b64 = base64.b64encode(r.content).decode('utf-8')
        comp = groq_client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{"role":"user","content":[
                {"type":"text","text":f"Explain this student image. Context: {txt}. Under 120 words."},
                {"type":"image_url","image_url":{"url": f"data:image/jpeg;base64,{b64}"}}
            ]}],
            max_tokens=250
        )
        return comp.choices[0].message.content.strip()
    except: return "Image received"

def gen_diagram(topic: str):
    try:
        enhanced = f"educational diagram, white background, {topic}, clean labeled infographic"
        enc = urllib.parse.quote(enhanced)
        return f"https://image.pollinations.ai/prompt/{enc}?width=1024&height=768&model=flux&nologo=true&seed={int(time.time())}"
    except: return None

def cleaner(t): return re.sub(r'\*\*(.*?)\*\*', r'*\1*', re.sub(r'\|.*\|','',t)).strip()[:1000]

KB="Agentic AI=agents+tools+memory. LangGraph=multi-agent graph. RAG=retrieve+generate. MCP=connect LLM to tools. Booking=preply.in/MOHAMMAD6EN21972784102"

# --- Dashboard Routes ---
@app.get("/", response_class=HTMLResponse)
async def dashboard_home():
    stats = get_dashboard_stats()
    html = f"""
    <html><head><title>Day 20 Tutor Analytics</title>
    <meta name='viewport' content='width=device-width, initial-scale=1'>
    <style>
    body{{font-family:Inter,sans-serif;padding:20px;background:#f8fafc}}
    .card{{background:white;padding:20px;border-radius:12px;margin:10px 0;box-shadow:0 1px 3px rgba(0,0,0,0.1)}}
    .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px}}
    .num{{font-size:28px;font-weight:bold;color:#2563eb}}
    </style></head><body>
    <h1>📊 Day 20 - Tutor Analytics Dashboard</h1>
    <div class='grid'>
        <div class='card'><div>Total Students</div><div class='num'>{stats.get('total_students',0)}</div></div>
        <div class='card'><div>Total Sessions</div><div class='num'>{stats.get('total_sessions',0)}</div></div>
        <div class='card'><div>Active Today</div><div class='num'>{stats.get('active_today',0)}</div></div>
        <div class='card'><div>Images Sent</div><div class='num'>{stats.get('media_stats',{{}}).get('images_sent',0)}</div></div>
    </div>
    <div class='card'><h3>🎯 Modality Split</h3>
    Visual: {stats.get('modality',{{}}).get('visual',0)} ({stats.get('modality',{{}}).get('visual_pct',0)}%) | 
    Voice: {stats.get('modality',{{}}).get('voice',0)} | Text: {stats.get('modality',{{}}).get('text',0)}
    </div>
    <div class='card'><h3>🔥 Top Topics</h3>{'<br>'.join([f"{t['topic']}: {t['count']}" for t in stats.get('topics',[])]) or 'No topics yet'}</div>
    <div class='card'><h3>🏆 Top Students</h3>{'<br>'.join([f"{s['name']} - {s['sessions']} sessions ({s['pref']})" for s in stats.get('top_students',[])]) or 'No students'}</div>
    <div class='card'><a href='/stats'>View JSON API /stats</a> | <a href='/health'>Health</a></div>
    </body></html>
    """
    return HTMLResponse(html)

@app.get("/stats")
async def stats_json():
    return JSONResponse(get_dashboard_stats())

@app.get("/student/{phone}")
async def student_detail(phone: str):
    d = get_student_detail(phone)
    return JSONResponse(d or {"error":"not found"})

@app.get("/health")
async def health(): return {"day":20, "status":"ok"}

# --- WhatsApp Bot (same as Day 19) ---
@app.post("/twilio")
async def twilio_webhook(request: Request):
    form = await request.form()
    body = form.get("Body","").strip()
    from_num = form.get("From","")
    profile_name = form.get("ProfileName","Student")
    media_url = form.get("MediaUrl0","")
    media_type = form.get("MediaContentType0","")
    sid = os.getenv("TWILIO_ACCOUNT_SID"); token=os.getenv("TWILIO_AUTH_TOKEN")
    auth=(sid,token) if sid and token else None
    user_text=body; image_analysis=""; is_voice=False; recv_img=False; send_img=False
    if media_url:
        if "audio" in media_type:
            is_voice=True; user_text=transcribe_audio(media_url, auth) or body or "Voice"
        elif "image" in media_type:
            recv_img=True; image_analysis=analyze_image(media_url, auth, body); user_text=body or "Explain image"
    if not user_text: user_text="Hello"
    mem_ctx=get_memory_context(from_num)
    need_diagram = any(k in user_text.lower() for k in ["show","diagram","image","draw","visual","chart"])
    diagram_url=None
    if need_diagram:
        try:
            ext=await llm.ainvoke(f"Extract 3-word topic from: '{user_text}'"); topic=ext.content.strip()[:80]
        except: topic=user_text[:80]
        diagram_url=gen_diagram(topic)
    prompt=f"You are Tutor. Mem: {mem_ctx} Q: {user_text} ImgAnalysis: {image_analysis} WantsDiag: {need_diagram} KB:{KB} RULES: No tables, *bold* not **, 3 lines max, if img present acknowledge, end question. Today: {dt.datetime.now().strftime('%Y-%m-%d')}"
    try:
        resp=await llm.ainvoke(prompt); text_reply=cleaner(resp.content)
        top=next((t for t in ["agentic","langgraph","rag","mcp"] if t in user_text.lower()), None)
        update_student_profile(from_num, name=profile_name, topic=top, sent_image=bool(diagram_url), received_image=recv_img, is_voice=is_voice)
    except Exception as e:
        text_reply=f"Hey {profile_name}! Got it! {image_analysis[:100] if image_analysis else ''} Ask anything!"
    twiml=MessagingResponse()
    if need_diagram and diagram_url:
        m=twiml.message(f"🎨 *{user_text[:30]}*"); m.media(diagram_url); twiml.message(text_reply)
    else:
        twiml.message(text_reply + ("\n\n_Dashboard: /stats 📊_" if "stats" in user_text.lower() else ""))
    return PlainTextResponse(str(twiml), media_type="application/xml")