# Smart Deploy System v2.0

Unifikovaný nasazovací systém s **Centralizovaným zdrojem pravdy na HAS**.

## Základní pravidla
- **Master Data:** Všechny kanonické soubory jsou uloženy na `HAS:/home/orchestration/Smart-Deploy-System/unified-truth/`.
- **Sync Engine:** Automatická obousměrná synchronizace s vaším schválením.
- **Prioritní síť:** Lokální LAN (Port 2222) s Unifikovaným klíčem 2026.

## Hlavní funkce
1. **Zero-Touch Onboarding:** Noví agenti se automaticky nastaví z HAS.
2. **Sync Wizard:** Welcome Dashboard kontroluje a opravuje vaše kontextové soubory (`AGENTS.md`, `MEMORY.md`, `GEMINI.md`).
3. **Univerzální Instalátor:** Nasazování AI skillů nezávisle na typu agenta.

## Použití
Spusťte dashboard pro kontrolu stavu synchronizace:
```bash
welcome_dashboard
```

## Nastavení nového stroje
```bash
ssh HAS 'cat /home/orchestration/Smart-Deploy-System/bootstrap.sh' | bash
```
