# day22_whatsapp_bot.py - Day 22 Multi-Agent
from unittest import result

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, HTMLResponse, JSONResponse
from twilio.twiml.messaging_response import MessagingResponse
import os, re, requests, tempfile, urllib.parse, time, base64, asyncio
from dotenv import load_dotenv
load_dotenv()
from day23_agents import supervisor_with_memory
from day23_rag import get_memory_stats
from day24_agent import supervisor_with_tools
from day24_tools import TOOLS

app = FastAPI()

try:
    from groq import Groq
    from day22_agents import supervisor_orchestrate, get_agent_stats
    from day22_memory import get_memory_context, update_student_profile
    from day21_monetization import check_access, increment_usage, get_paywall_message, get_monetization_stats, mark_premium, BOOKING_LINK
    from langchain_groq import ChatGroq
    HAS_GROQ = bool(os.getenv("GROQ_API_KEY"))
    groq_client = Groq(api_key=os.getenv("GROQ_API_KEY")) if HAS_GROQ else None
except Exception as e:
    print(f"Init: {e}")
    HAS_GROQ=False; groq_client=None
    def get_agent_stats(): return {"agents":[], "total_agents":0}
    def get_monetization_stats(): return {}
    def get_memory_context(p): return "New"

def transcribe_audio(url, auth):
    if not groq_client: return ""
    try:
        r=requests.get(url, auth=auth, timeout=20)
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as f:
            f.write(r.content); path=f.name
        with open(path,"rb") as audio:
            tr=groq_client.audio.transcriptions.create(file=(path, audio.read()), model="whisper-large-v3", response_format="text")
        os.remove(path)
        return tr.strip() if isinstance(tr,str) else tr.text.strip()
    except: return ""

def analyze_image(url, auth, txt=""):
    if not groq_client: return "Image received"
    try:
        r=requests.get(url, auth=auth, timeout=20)
        b64=base64.b64encode(r.content).decode('utf-8')
        comp=groq_client.chat.completions.create(model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{"role":"user","content":[{"type":"text","text":f"Explain: {txt}. Under 120w"},{"type":"image_url","image_url":{"url": f"data:image/jpeg;base64,{b64}"}}]}],
            max_tokens=250)
        return comp.choices[0].message.content.strip()
    except: return "Image received"

def gen_diagram(topic):
    try:
        enc=urllib.parse.quote(f"educational diagram, white background, {topic}, clean infographic")
        return f"https://image.pollinations.ai/prompt/{enc}?width=1024&height=768&model=flux&nologo=true&seed={int(time.time())}"
    except: return None

def cleaner(t): return re.sub(r'\*\*(.*?)\*\*', r'*\1*', re.sub(r'\|.*\|','',t)).strip()[:1200]

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    try:
        m_stats = get_monetization_stats()
        a_stats = get_agent_stats()
    except:
        m_stats = {"total_users":0,"premium_users":0,"total_revenue":0,"mrr":0}
        a_stats = {"agents":[], "total_agents":4}
    
    agents_html = "".join([f"<div class='card'><b>{a['name']}</b><br>Model: {a['model']}<br>Role: {a['role']}<br>~{a['avg_ms']}ms</div>" for a in a_stats.get("agents",[])])
    
    html = f"""
    <html><head><title>Day 22 - Multi-Agent</title><meta name='viewport' content='width=device-width, initial-scale=1'>
    <style>body{{font-family:Inter,sans-serif;padding:20px;background:#f8fafc}} .card{{background:white;padding:20px;border-radius:12px;margin:10px 0;box-shadow:0 1px 3px rgba(0,0,0,0.1)}} .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px}} .num{{font-size:28px;font-weight:bold;color:#2563eb}} </style></head>
    <body>
    <h1>🤖 Day 22 - Multi-Agent Tutor</h1>
    <div class='grid'>
        <div class='card'><div>Users</div><div class='num'>{m_stats.get('total_users',0)}</div></div>
        <div class='card'><div>Premium</div><div class='num'>{m_stats.get('premium_users',0)}</div></div>
        <div class='card'><div>Revenue</div><div class='num'>₹{m_stats.get('total_revenue',0)}</div></div>
        <div class='card'><div>Agents</div><div class='num'>{a_stats.get('total_agents',4)}</div></div>
    </div>
    <h3>🧠 Agents Running</h3>
    <div class='grid'>{agents_html or 'Loading agents...'}</div>
    <div class='card'><h3>Flow</h3>User → Supervisor → Researcher (facts) → [Explainer + Quizzer in parallel] → Combined Answer + Diagram</div>
    <div class='card'><a href='/stats'>Revenue</a> | <a href='/agents'>Agents JSON</a> | <a href='/health'>Health</a></div>
    </body></html>
    """
    return HTMLResponse(html)

@app.get("/agents")
async def agents_api(): return JSONResponse(get_agent_stats())

@app.get("/stats")
async def stats_api(): return JSONResponse(get_monetization_stats())

@app.get("/health")
async def health(): return {"day":22, "status":"ok", "agents":4}

@app.get("/memory/{phone}")
async def memory_api(phone: str, q: str = "AI"):
    from day23_rag import search_memory
    return {"phone": phone, "query": q, "results": search_memory(phone, q)}


# New endpoint for dashboard:
@app.get("/tools")
async def tools_api():
    return {"tools": list(TOOLS.keys()), "total": len(TOOLS), "mcp_style": "function-calling", "status": "active"}
@app.post("/twilio")
async def twilio_webhook(request: Request):
    form = await request.form()
    body = form.get("Body","").strip()
    from_num = form.get("From","")
    profile_name = form.get("ProfileName","Student")
    media_url = form.get("MediaUrl0","")
    media_type = form.get("MediaContentType0","")
    sid=os.getenv("TWILIO_ACCOUNT_SID"); token=os.getenv("TWILIO_AUTH_TOKEN")
    auth=(sid,token) if sid and token else None

    if body.upper() in ["PAID","PREMIUM"]:
        try:
            mark_premium(from_num)
            twiml=MessagingResponse(); twiml.message(f"🎉 Premium unlocked, {profile_name}!")
            return PlainTextResponse(str(twiml), media_type="application/xml")
        except: pass

    try:
        can_access, remaining, is_premium = check_access(from_num)
    except:
        can_access, remaining, is_premium = True, 5, False

    if not can_access:
        twiml=MessagingResponse(); twiml.message(get_paywall_message(0, profile_name))
        return PlainTextResponse(str(twiml), media_type="application/xml")

    user_text=body; image_analysis=""; is_voice=False; recv_img=False
    if media_url:
        if "audio" in media_type:
            is_voice=True; user_text=transcribe_audio(media_url, auth) or body or "Voice"
        elif "image" in media_type:
            recv_img=True; image_analysis=analyze_image(media_url, auth, body); user_text=body or "Explain image"
    if not user_text: user_text="Hello"

    try: mem_ctx=get_memory_context(from_num)
    except: mem_ctx=profile_name
    
    # MULTI-AGENT ORCHESTRATION
    try:
        if HAS_GROQ:
            level = "Beginner"
            if "advanced" in user_text.lower(): level="Advanced"
            result = await supervisor_with_tools(user_text, from_num, level)
            reply = f"{result['explanation']}\n\n🛠️ Tool: {result['tool_used']} → {result['tool_output'][:150]}\n\n📝 {result['quiz']}"
            facts = result['facts']
        else:
            text_reply = f"Hey {profile_name}! Multi-agent needs GROQ_API_KEY. You said: {user_text[:100]}"
    except Exception as e:
        print(e)
        text_reply = f"Hey {profile_name}! Got: {user_text[:100]}. What level are you?"

    need_diagram = any(k in user_text.lower() for k in ["show","diagram","image","draw","visual","chart"])
    diagram_url=gen_diagram(user_text[:80]) if need_diagram else None

    try:
        increment_usage(from_num)
        top=next((t for t in ["agentic","langgraph","rag","mcp","agent"] if t in user_text.lower()), None)
        update_student_profile(from_num, name=profile_name, topic=top, sent_image=bool(diagram_url), is_voice=is_voice, received_image=recv_img)
    except: pass

    footer = "" if is_premium else f"\n\n_*{remaining-1} free left. Premium: {BOOKING_LINK}*_"
    
    twiml=MessagingResponse()
    if need_diagram and diagram_url:
        m=twiml.message(f"🎨 *{user_text[:30]}* - 3 Agents worked on this"); m.media(diagram_url); twiml.message(text_reply + footer)
    else:
        twiml.message(text_reply + footer)
    return PlainTextResponse(str(twiml), media_type="application/xml")

from fastapi import Request, Response

@app.post("/whatsapp")
async def whatsapp(request: Request):
    form = await request.form()
    msg = form.get("Body", "")
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response><Message>You said: {msg} - bot is working!</Message></Response>"""
    return Response(content=xml, media_type="text/xml")