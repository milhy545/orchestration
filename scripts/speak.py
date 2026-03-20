#!/usr/bin/env python3
"""
🎙️ Gemini Speak Script (Background Version)
Přečte text zprávy pomocí ElevenLabs a okamžitě ho přehraje na pozadí.
"""
import os
import sys
import re
import httpx
import subprocess
import shutil
from pathlib import Path

# --- Configuration ---
API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
VOICE_ID = "pNInz6obpg8n9YNoMsyS"  # Hlas "Brian"
MODEL_ID = "eleven_multilingual_v2"

def clean_markdown(text):
    """Odstraní markdown značky pro čistší poslech."""
    text = re.sub(r'```.*?```', '[kódový blok]', text, flags=re.DOTALL)
    text = re.sub(r'#+\s+', '', text)
    text = re.sub(r'\*\*', '', text)
    text = re.sub(r'-\s+', 'bod: ', text)
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
    return text

def play_audio(content):
    """Přehraje audio a neblokuje terminál."""
    temp_file = "/tmp/gemini_speak.mp3"
    with open(temp_file, "wb") as f:
        f.write(content)
    
    players = [
        ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", temp_file],
        ["mpv", "--no-video", temp_file],
        ["play", "-q", temp_file]
    ]
    
    for player_cmd in players:
        if shutil.which(player_cmd[0]):
            # Spuštění na pozadí pomocí Popen
            subprocess.Popen(player_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
    return False

def main():
    # 1. Zkusíme argument
    text = sys.argv[1] if len(sys.argv) > 1 else ""
    
    # 2. Pokud není argument, zkusíme proměnnou prostředí
    if not text:
        text = os.getenv("GEMINI_LAST_REPLY", "")
    
    # 3. Pokud stále nic, zkusíme vytáhnout poslední odpověď z historie Gemini CLI
    if not text:
        try:
            # gemini history --last 1 vrátí poslední odpověď
            result = subprocess.run(["gemini", "history", "--last", "1"], 
                                   capture_output=True, text=True, check=True)
            text = result.stdout.strip()
        except Exception:
            pass

    if not text:
        print("❌ Žádný text k přečtení (zkus: speak \"zpráva\")")
        return

    if not API_KEY:
        print("❌ ELEVENLABS_API_KEY není nastaven.")
        return

    clean_text = clean_markdown(text)
    
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
            play_audio(response.content)
    except Exception as e:
        pass # Na pozadí nechceme vypisovat chyby do rozepsaného příkazu

if __name__ == "__main__":
    main()
