# day21_whatsapp_bot.py - Day 21 Monetized
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, HTMLResponse, JSONResponse
from twilio.twiml.messaging_response import MessagingResponse
import os, re, datetime as dt, requests, tempfile, urllib.parse, time, base64
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

try:
    from langchain_groq import ChatGroq
    from groq import Groq
    from day21_memory import get_memory_context, update_student_profile, get_student_profile
    from day21_monetization import check_access, increment_usage, get_paywall_message, get_monetization_stats, mark_premium, BOOKING_LINK
    HAS_GROQ = bool(os.getenv("GROQ_API_KEY"))
    if HAS_GROQ:
        llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.3)
        groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    else:
        llm = None; groq_client = None
except Exception as e:
    print(f"Init: {e}")
    HAS_GROQ=False; llm=None; groq_client=None
    from day21_monetization import check_access, get_paywall_message, get_monetization_stats, BOOKING_LINK

# Helpers (same as Day 20)
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

def cleaner(t): return re.sub(r'\*\*(.*?)\*\*', r'*\1*', re.sub(r'\|.*\|','',t)).strip()[:1000]

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    try:
        stats = get_monetization_stats()
    except Exception as e:
        print(e); stats={"total_users":0,"premium_users":0,"free_users":0,"conversion_rate":0,"total_revenue":0,"active_today":0,"mrr":0,"top_payers":[]}
    
    html = f"""
    <html><head><title>Day 21 - Monetization</title><meta name='viewport' content='width=device-width, initial-scale=1'>
    <style>body{{font-family:Inter,sans-serif;padding:20px;background:#f8fafc}} .card{{background:white;padding:20px;border-radius:12px;margin:10px 0;box-shadow:0 1px 3px rgba(0,0,0,0.1)}} .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px}} .num{{font-size:28px;font-weight:bold;color:#2563eb}} .green{{color:#16a34a}} </style></head>
    <body>
    <h1>💰 Day 21 - Monetization Dashboard</h1>
    <div class='grid'>
        <div class='card'><div>Total Users</div><div class='num'>{stats.get('total_users',0)}</div></div>
        <div class='card'><div>Premium</div><div class='num green'>{stats.get('premium_users',0)}</div><small>{stats.get('conversion_rate',0)}% conv</small></div>
        <div class='card'><div>Total Revenue</div><div class='num green'>₹{stats.get('total_revenue',0)}</div><small>MRR: ₹{stats.get('mrr',0)}</small></div>
        <div class='card'><div>Active Today</div><div class='num'>{stats.get('active_today',0)}</div></div>
    </div>
    <div class='card'><h3>🎯 Model</h3> Free: 5/day | Premium: ₹299/month unlimited<br>Booking: <a href='{BOOKING_LINK}'>{BOOKING_LINK}</a></div>
    <div class='card'><h3>💳 Top Payers</h3>{'<br>'.join([f"{p.get('name')}: ₹{p.get('paid')}" for p in stats.get('top_payers',[])]) or 'No payers yet'}</div>
    <div class='card'><a href='/stats'>JSON /stats</a> | <a href='/health'>Health</a> | <a href='/revenue'>Revenue API</a></div>
    </body></html>
    """
    return HTMLResponse(html)

@app.get("/stats")
@app.get("/revenue")
async def revenue_api(): return JSONResponse(get_monetization_stats())

@app.get("/health")
async def health(): return {"day":21, "status":"ok"}

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
    
    # ADMIN: Mark paid
    if body.upper() in ["PAID", "PREMIUM"]:
        try:
            mark_premium(from_num)
            twiml=MessagingResponse()
            twiml.message(f"🎉 Welcome to Premium, {profile_name}! Unlimited access unlocked for 30 days. Ask anything! Booking: {BOOKING_LINK}")
            return PlainTextResponse(str(twiml), media_type="application/xml")
        except: pass
    
    # CHECK ACCESS
    try:
        can_access, remaining, is_premium = check_access(from_num)
    except:
        can_access, remaining, is_premium = True, 5, False
    
    if not can_access:
        twiml=MessagingResponse()
        twiml.message(get_paywall_message(0, profile_name))
        return PlainTextResponse(str(twiml), media_type="application/xml")
    
    # Process message
    user_text=body; image_analysis=""; is_voice=False; recv_img=False
    if media_url:
        if "audio" in media_type:
            is_voice=True; user_text=transcribe_audio(media_url, auth) or body or "Voice"
        elif "image" in media_type:
            recv_img=True; image_analysis=analyze_image(media_url, auth, body); user_text=body or "Explain image"
    if not user_text: user_text="Hello"
    
    try: mem_ctx=get_memory_context(from_num)
    except: mem_ctx=f"{profile_name} | {'PREMIUM' if is_premium else 'FREE'}"
    
    need_diagram = any(k in user_text.lower() for k in ["show","diagram","image","draw","visual","chart"])
    diagram_url=gen_diagram(user_text[:80]) if need_diagram else None
    
    if HAS_GROQ and llm:
        prompt=f"You are Tutor. Mem: {mem_ctx} Q: {user_text} Img: {image_analysis} Premium: {is_premium} Remaining: {remaining} No tables, *bold*, 3 lines max, end question."
        try: resp=await llm.ainvoke(prompt); text_reply=cleaner(resp.content)
        except: text_reply=f"Hey {profile_name}! Got: {user_text[:100]}"
    else:
        text_reply=f"Hey {profile_name}! You said: {user_text[:100]}"
    
    # Increment + save
    try:
        increment_usage(from_num)
        top=next((t for t in ["agentic","langgraph","rag","mcp"] if t in user_text.lower()), None)
        update_student_profile(from_num, name=profile_name, topic=top, sent_image=bool(diagram_url), is_voice=is_voice, received_image=recv_img)
    except: pass
    
    # Add quota footer for free users
    footer = ""
    if not is_premium:
        footer = f"\n\n_*{remaining-1} free left today. Premium: {BOOKING_LINK} 💳*_"
    
    twiml=MessagingResponse()
    if need_diagram and diagram_url:
        m=twiml.message(f"🎨 *{user_text[:30]}*"); m.media(diagram_url); twiml.message(text_reply + footer)
    else:
        twiml.message(text_reply + footer)
    return PlainTextResponse(str(twiml), media_type="application/xml")