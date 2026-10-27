# day16_voice.py - Day 16: Voice to Text
import os, requests, tempfile
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def transcribe_voice(media_url: str, twilio_auth=None) -> str:
    """
    Download WhatsApp voice note from Twilio MediaUrl and transcribe via Groq Whisper
    """
    try:
        # Download audio (Twilio MediaUrl needs auth)
        auth = twilio_auth  # (Account SID, Auth Token) if needed
        if auth:
            r = requests.get(media_url, auth=auth, timeout=20)
        else:
            r = requests.get(media_url, timeout=20)
        
        if r.status_code != 200:
            return "[Voice Note - could not download]"

        # Save temp ogg file (WhatsApp voice = ogg/opus)
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as f:
            f.write(r.content)
            temp_path = f.name

        # Transcribe via Groq Whisper - Super fast
        with open(temp_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                file=(temp_path, audio_file.read()),
                model="whisper-large-v3",
                language="en",  # auto detects hi/en mix too
                response_format="text"
            )
        
        os.remove(temp_path)
        text = transcription.strip() if isinstance(transcription, str) else transcription.text.strip()
        return text if text else "[Voice Note - empty]"
    
    except Exception as e:
        print(f"Voice transcribe error: {e}")
        return f"[Voice Note error: {str(e)[:100]}]"