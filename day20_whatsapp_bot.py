# day20_whatsapp_bot.py - Day 20 SAFE version
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, HTMLResponse, JSONResponse
from twilio.twiml.messaging_response import MessagingResponse
import os, json, re, datetime as dt, requests, tempfile, urllib.parse, time, base64
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

# --- Safe imports ---
try:
    from langchain_groq import ChatGroq
    from groq import Groq
    from day20_memory import get_memory_context, update_student_profile
    from day20_analytics import get_dashboard_stats, get_student_detail
    HAS_GROQ = bool(os.getenv("GROQ_API_KEY"))
    if HAS_GROQ:
        llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.3)  # Stable model
        groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    else:
        llm = None
        groq_client = None
except Exception as e:
    print(f"Init warning: {e}")
    HAS_GROQ = False
    llm = None
    groq_client = None
    # Fallback import for analytics only
    try:
        from day20_analytics import get_dashboard_stats, get_student_detail
        from day20_memory import get_memory_context, update_student_profile
    except:
        pass

def transcribe_audio(media_url, auth):
    if not groq_client: return ""
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
    if not groq_client: return "Image received - vision needs GROQ_API_KEY"
    try:
        r = requests.get(media_url, auth=auth, timeout=20)
        b64 = base64.b64encode(r.content).decode('utf-8')
        comp = groq_client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{"role":"user","content":[
                {"type":"text","text":f"Explain this image: {txt}. Under 120 words."},
                {"type":"image_url","image_url":{"url": f"data:image/jpeg;base64,{b64}"}}
            ]}],
            max_tokens=250
        )
        return comp.choices[0].message.content.strip()
    except Exception as e:
        print(e); return "Image received"

def gen_diagram(topic: str):
    try:
        enhanced = f"educational diagram, white background, {topic}, clean labeled infographic"
        enc = urllib.parse.quote(enhanced)
        return f"https://image.pollinations.ai/prompt/{enc}?width=1024&height=768&model=flux&nologo=true&seed={int(time.time())}"
    except: return None

def cleaner(t): return re.sub(r'\*\*(.*?)\*\*', r'*\1*', re.sub(r'\|.*\|','',t)).strip()[:1000]

KB="Agentic AI=agents+tools+memory. LangGraph=multi-agent graph. RAG=retrieve+generate. MCP=connect LLM to tools."

@app.get("/", response_class=HTMLResponse)
async def dashboard_home():
    try:
        stats = get_dashboard_stats()
    except Exception as e:
        stats = {"total_students":0,"total_sessions":0,"active_today":0,"modality":{"visual":0,"voice":0,"text":0,"visual_pct":0},"topics":[],"media_stats":{"images_sent":0,"images_received":0,"voice_notes":0},"top_students":[]}
        print(f"Stats error: {e}")
    
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
    <p>Status: {'✅ Groq Connected' if HAS_GROQ else '⚠️ Add GROQ_API_KEY in Render ENV'}</p>
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
    <div class='card'><h3>🔥 Top Topics</h3>{'<br>'.join([f"{t['topic']}: {t['count']}" for t in stats.get('topics',[])]) or 'No topics yet - Send WhatsApp message first'}</div>
    <div class='card'><h3>🏆 Top Students</h3>{'<br>'.join([f"{s['name']} - {s['sessions']} sessions ({s['pref']})" for s in stats.get('top_students',[])]) or 'No students yet'}</div>
    <div class='card'><a href='/stats'>View JSON API /stats</a> | <a href='/health'>Health</a></div>
    </body></html>
    """
    return HTMLResponse(html)

@app.get("/stats")
async def stats_json():
    try:
        return JSONResponse(get_dashboard_stats())
    except Exception as e:
        return JSONResponse({"error": str(e), "total_students":0})

@app.get("/health")
async def health(): return {"day":20, "status":"ok", "groq_connected": HAS_GROQ}

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
    user_text=body; image_analysis=""; is_voice=False; recv_img=False
    if media_url:
        if "audio" in media_type:
            is_voice=True; user_text=transcribe_audio(media_url, auth) or body or "Voice"
        elif "image" in media_type:
            recv_img=True; image_analysis=analyze_image(media_url, auth, body); user_text=body or "Explain image"
    if not user_text: user_text="Hello"
    try:
        mem_ctx=get_memory_context(from_num)
    except: mem_ctx="New student"
    need_diagram = any(k in user_text.lower() for k in ["show","diagram","image","draw","visual","chart"])
    diagram_url=gen_diagram(user_text[:80]) if need_diagram else None
    
    if HAS_GROQ and llm:
        prompt=f"You are Tutor. Mem: {mem_ctx} Q: {user_text} Img: {image_analysis} WantsDiag: {need_diagram} KB:{KB} No tables, *bold* not **, 3 lines max, end question."
        try:
            resp=await llm.ainvoke(prompt); text_reply=cleaner(resp.content)
        except: text_reply=f"Hey {profile_name}! Got your message: {user_text[:100]}"
    else:
        text_reply=f"Hey {profile_name}! Bot works but add GROQ_API_KEY in Render for AI replies. You said: {user_text[:100]}"
    
    try:
        top=next((t for t in ["agentic","langgraph","rag","mcp"] if t in user_text.lower()), None)
        update_student_profile(from_num, name=profile_name, topic=top, sent_image=bool(diagram_url), received_image=recv_img, is_voice=is_voice)
    except: pass
    
    twiml=MessagingResponse()
    if need_diagram and diagram_url:
        m=twiml.message(f"🎨 *{user_text[:30]}*"); m.media(diagram_url); twiml.message(text_reply)
    else:
        twiml.message(text_reply)
    return PlainTextResponse(str(twiml), media_type="application/xml")