# day19_multimodal.py - Day 19: Vision + Voice + Image Gen
import os, requests, tempfile, urllib.parse, time, base64
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def transcribe_audio(media_url: str, auth) -> str:
    try:
        r = requests.get(media_url, auth=auth, timeout=20)
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as f:
            f.write(r.content)
            path = f.name
        with open(path, "rb") as audio:
            tr = client.audio.transcriptions.create(
                file=(path, audio.read()),
                model="whisper-large-v3",
                response_format="text"
            )
        os.remove(path)
        return tr.strip() if isinstance(tr, str) else tr.text.strip()
    except Exception as e:
        print(f"Transcribe error: {e}")
        return ""

def analyze_image(media_url: str, auth, user_text: str = "") -> str:
    """
    Analyze student's image (notes, diagram, homework) using LLaVA vision via Groq
    """
    try:
        # Download image
        r = requests.get(media_url, auth=auth, timeout=20)
        # Convert to base64 for vision model
        b64 = base64.b64encode(r.content).decode('utf-8')
        
        # Groq vision model - Llama 4 Scout is multimodal
        completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"Student sent this image and says: '{user_text}'. Explain what is in image in simple terms, identify if it's notes/diagram/homework/code. Keep under 150 words, friendly tutor style."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
                    ]
                }
            ],
            max_tokens=300
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"Vision error: {e}")
        # Fallback without vision
        return "I received your image! [Vision analysis temporarily unavailable, but I can still help if you describe what's in it]"

def generate_diagram_image(topic: str) -> str:
    """Generate educational diagram - FREE Pollinations FLUX"""
    try:
        enhanced = f"educational diagram, white background, {topic}, clean, labeled, infographic, professional"
        encoded = urllib.parse.quote(enhanced)
        url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=768&model=flux&nologo=true&seed={int(time.time())}"
        return url
    except:
        return None