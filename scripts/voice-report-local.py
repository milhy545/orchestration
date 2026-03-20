#!/usr/bin/env python3
"""
🎙️ FORAI Voice Report Generator (Local Edition)
Usage: uv run scripts/voice-report-local.py <report_file.md>
"""
import os
import sys
import re
import httpx
from pathlib import Path

# --- Configuration ---
# Doporučuji dát klíč sem nebo do shellu: export ELEVENLABS_API_KEY="tvůj_klíč"
API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
VOICE_ID = "pNInz6obpg8n9YNoMsyS"  # Hlas "Brian" - skvělý pro reporty
MODEL_ID = "eleven_multilingual_v2"

def clean_markdown(text):
    """Odstraní markdown značky pro čistší poslech."""
    text = re.sub(r'#+\s+', '', text)  # Nadpisy
    text = re.sub(r'\*\*', '', text)   # Tučné písmo
    text = re.sub(r'-\s+', 'bod: ', text) # Odrážky nahradí slovem bod
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text) # Odkazy
    text = re.sub(r'`{3}.*?`{3}', '[kódový blok přeskočen]', text, flags=re.DOTALL) # Kód
    return text

def generate_audio(file_path):
    if not API_KEY:
        print("❌ Chyba: Chybí ELEVENLABS_API_KEY. Nastav ho v shellu: export ELEVENLABS_API_KEY='...'")
        return

    path = Path(file_path)
    if not path.exists():
        print(f"❌ Soubor {file_path} nebyl nalezen.")
        return

    print(f"📖 Čtu report: {file_path}")
    raw_text = path.read_text(encoding='utf-8')
    clean_text = clean_markdown(raw_text)

    output_file = path.with_suffix('.mp3')
    
    print(f"🗣️ Odesílám do ElevenLabs (Hlas: Brian)...")
    
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": API_KEY
    }
    data = {
        "text": clean_text,
        "model_id": MODEL_ID,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }

    try:
        with httpx.Client() as client:
            response = client.post(url, json=data, timeout=60.0)
            response.raise_for_status()
            
            with open(output_file, 'wb') as f:
                f.write(response.content)
            
            print(f"✅ HOTOVO! Report uložen lokálně jako: {output_file}")
            print(f"🎵 Můžeš si ho hned pustit.")
            
    except Exception as e:
        print(f"❌ Chyba při generování: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Použití: uv run voice-report-local.py <soubor.md>")
    else:
        generate_audio(sys.argv[1])
