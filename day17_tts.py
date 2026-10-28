# day17_tts.py - Day 17: Bot speaks
import os, requests, tempfile, base64

# Option A: Groq PlayAI TTS (if available) - Fast & free
# Option B: Use gTTS for MVP - works on Render free tier

def text_to_speech_gtts(text: str) -> str:
    """
    Convert text to speech audio file, return path
    Using gTTS for Day 17 MVP - No API key needed
    For production, swap with Groq PlayAI or ElevenLabs
    """
    try:
        from gtts import gTTS
        # Clean text for TTS - remove *bold* markers, keep short
        clean_text = text.replace('*','').replace('•','').replace('-','')
        clean_text = clean_text[:300]  # Voice note max 30 sec = ~300 chars
        
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            temp_path = f.name
        
        tts = gTTS(text=clean_text, lang='en', slow=False)
        tts.save(temp_path)
        return temp_path
    except Exception as e:
        print(f"TTS error: {e}")
        return None

def text_to_speech_elevenlabs(text: str) -> str:
    """Production version with ElevenLabs - Better voice"""
    try:
        api_key = os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            return text_to_speech_gtts(text)
        
        url = "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM/convert"
        headers = {"xi-api-key": api_key, "Content-Type": "application/json"}
        data = {"text": text[:300], "model_id": "eleven_multilingual_v2"}
        
        r = requests.post(url, json=data, headers=headers, timeout=15)
        if r.status_code == 200:
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                f.write(r.content)
                return f.name
        return text_to_speech_gtts(text)
    except:
        return text_to_speech_gtts(text)

# Main function - auto picks best available
def generate_voice_reply(text: str) -> str:
    # Try ElevenLabs if key exists, else gTTS
    if os.getenv("ELEVENLABS_API_KEY"):
        return text_to_speech_elevenlabs(text)
    return text_to_speech_gtts(text)