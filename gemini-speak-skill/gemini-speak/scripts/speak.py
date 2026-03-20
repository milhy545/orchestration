#!/usr/bin/env python3
"""
🎙️ Gemini Speak Script
Přečte text zprávy pomocí ElevenLabs a okamžitě ho přehraje.
"""
import os
import sys
import re
import httpx
import subprocess
import shutil

# --- Configuration ---
# API KEY is loaded from the environment (passed by Gemini CLI or shell)
API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
VOICE_ID = "pNInz6obpg8n9YNoMsyS"  # Hlas "Brian"
MODEL_ID = "eleven_multilingual_v2"

def clean_markdown(text):
    """Odstraní markdown značky pro čistší poslech."""
    # Odstranění kódových bloků úplně (nečíst kód)
    text = re.sub(r'```.*?```', '[kódový blok]', text, flags=re.DOTALL)
    # Odstranění zbytků markdownu
    text = re.sub(r'#+\s+', '', text)
    text = re.sub(r'\*\*', '', text)
    text = re.sub(r'-\s+', 'bod: ', text)
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
    return text

def play_audio(content):
    """Pokusí se přehrát audio pomocí dostupného přehrávače."""
    temp_file = "/tmp/gemini_speak.mp3"
    with open(temp_file, "wb") as f:
        f.write(content)
    
    # Seznam preferovaných přehrávačů
    players = [
        ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", temp_file],
        ["mpv", "--no-video", temp_file],
        ["play", "-q", temp_file],  # SoX
        ["vlc", "--intf", "dummy", "--play-and-exit", temp_file]
    ]
    
    for player_cmd in players:
        if shutil.which(player_cmd[0]):
            try:
                subprocess.run(player_cmd, check=True)
                return True
            except Exception:
                continue
    return False

def main():
    # Text bereme buď z argumentu, nebo z proměnné prostředí GEMINI_LAST_REPLY
    text = sys.argv[1] if len(sys.argv) > 1 else os.getenv("GEMINI_LAST_REPLY", "")
    
    if not text:
        print("❌ Žádný text k přečtení.")
        return

    if not API_KEY:
        print("❌ ELEVENLABS_API_KEY není nastaven v prostředí.")
        return

    clean_text = clean_markdown(text)
    print(f"🗣️ Mluvím (ElevenLabs Brian)...")

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}/stream"
    headers = {"xi-api-key": API_KEY}
    data = {
        "text": clean_text,
        "model_id": MODEL_ID,
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
    }

    try:
        with httpx.Client() as client:
            response = client.post(url, json=data, timeout=60.0)
            response.raise_for_status()
            if not play_audio(response.content):
                print("❌ Nepodařilo se najít vhodný přehrávač (nainstaluj ffplay nebo mpv).")
    except Exception as e:
        print(f"❌ Chyba při spojení s ElevenLabs: {e}")

if __name__ == "__main__":
    main()
