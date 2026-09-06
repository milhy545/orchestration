# Předávací protokol nasazení bezpečnostní brány Mega (Deployment Handoff)

Datum: 2026-09-06
Server: HAS (`root@192.168.0.58:2222`)
Pracovní strom: `/home/milhy777/Develop/orchestration-mega-security`
Adresář nasazení: `/home/mega-security-gateway-deploy`
Větev: `feat/mega-security-gateway`
Cílový commit: `46ba9e91ef58b81717a1a9c3594f3a6b5bd0030a` (`46ba9e9`)
Compose projekt: `mega-security-gateway`

---

## 1. Souhrn provedení

Bezpečnostní brána Mega Orchestratoru byla lokálně ověřena, odeslána na GitHub, bezpečně synchronizována do izolovaného adresáře nasazení na HAS, sestavena a spuštěna jako samostatný Docker Compose projekt. Všechny před- i po-nasazovací testy a validace proběhly úspěšně. Tailscale Funnel a Serve zůstávají zcela vypnuté (`No serve config`). Původní produkční stack orchestrace na portu 7000 zůstal nedotčen a je plně v provozu.

---

## 2. Důkazy z validace před nasazením

Všechny před-nasazovací testy byly spuštěny v čistém pracovním stromu `/home/milhy777/Develop/orchestration-mega-security`:

1. **Sada cílených jednotkových testů**:
   - Příkaz: `uv run --no-project --with pytest --with pytest-asyncio --with aiohttp pytest tests/unit/test_mega_gateway_security.py tests/unit/test_mega_security_cli.py`
   - Výsledek: 20 testů úspěšných za 0.58s (včetně idempotentního opakování DCR a čekajících párování).
2. **Kompilace do bajtkódu (`py_compile`)**:
   - Příkaz: `python3 -m py_compile mega_gateway/app.py mega_gateway/security.py tests/unit/test_mega_gateway_security.py tests/unit/test_mega_security_cli.py scripts/mega_security scripts/mega_funnel`
   - Výsledek: Návratový kód 0, žádné syntaktické ani kompilační chyby.
3. **Validace Docker Compose konfigurace**:
   - Příkaz: `MEGA_GATEWAY_PUBLIC_BASE_URL=https://home-automat-server.tailb42db0.ts.net MEGA_GATEWAY_CHATGPT_REGISTRATION_REDIRECT_HOSTS=chatgpt.com,chat.openai.com docker compose -f docker-compose.mega-gateway.yml config`
   - Výsledek: Návratový kód 0, striktně svázáno s `127.0.0.1:7080:7080`, externí síť `orchestration_mcp-network`.
4. **Detekce úniku citlivých údajů (`gitleaks`)**:
   - Příkaz: `gitleaks detect --log-opts="8c8a63b..HEAD" -v`
   - Výsledek: Naskenováno 9 commitů, 0 nalezených úniků.
5. **Kontrola bílých znaků (Whitespace)**:
   - Příkaz: `git diff --check 8c8a63b..HEAD`
   - Výsledek: Návratový kód 0, žádné chyby formátování.

---

## 3. Vzdálené odeslání (Git Push)

- Příkaz: `git push origin feat/mega-security-gateway`
- Rozsah: `749d906..46ba9e9`
- Stav: Úspěšně odesláno na GitHub (`milhy545/orchestration`).

---

## 4. Podrobnosti o nasazení na HAS

1. **Bezpečná synchronizace**:
   - Čistý pracovní strom byl synchronizován do `/home/mega-security-gateway-deploy` pomocí `rsync` se striktními výjimkami (`.env.mega-gateway`, `.git`, `.venv`, `claude-agent-env`, mezipaměti).
   - Oprávnění `0600` pro `/home/mega-security-gateway-deploy/.env.mega-gateway` byla striktně zachována.
   - Produkční adresář `/home/orchestration` zůstal zcela nedotčen.
2. **Svazky na hostiteli**:
   - Ověřena existence `/var/lib/mega-gateway` a `/run/mega-gateway` na HAS.
3. **Sestavení a spuštění**:
   - Příkaz: `cd /home/mega-security-gateway-deploy && docker compose -p mega-security-gateway --env-file .env.mega-gateway -f docker-compose.mega-gateway.yml up -d --build`
   - Název projektu: `mega-security-gateway`
   - Výsledek: Kontejner `mega-security-gateway-mega-security-gateway-1` vytvořen a spuštěn.

---

## 5. Důkazy z ověření po nasazení

1. **Stav kontejneru a zdraví**:
   - Stav: `Up (healthy)`
   - Healthcheck: `wget -qO- http://127.0.0.1:7080/health >/dev/null || exit 1`
2. **Vazba síťového portu**:
   - Příkaz: `netstat -tulpn | grep 7080`
   - Důkaz: `tcp 0 0 127.0.0.1:7080 0.0.0.0:* LISTEN 19865/docker-proxy`
   - Port je striktně svázán s `127.0.0.1`, zakázán na veřejných a LAN rozhraních.
3. **Interní Docker konektivita k backendu**:
   - Konektivita k `http://mega-orchestrator:7000/mcp` přes síť `orchestration_mcp-network` byla ověřena přímo zevnitř kontejneru brány.
   - Produkční Mega Orchestrator na portu 7000 zůstává online a v pořádku (healthy).
4. **Oprávnění Unix admin socketu**:
   - Soubor: `/run/mega-gateway/admin.sock`
   - Oprávnění: `0600` (`srw-------`)
5. **Funkčnost lokálního administrátorského CLI**:
   - Příkaz: `/home/mega-security-gateway-deploy/scripts/mega_security status`
   - Výstup:
     ```json
     {
       "allowed_tools": [
         "get_context",
         "list_memories",
         "memory_stats",
         "registry_get_server",
         "registry_search",
         "search_memories",
         "skills_list"
       ],
       "profiles": [
         "chatgpt",
         "gemini-spark"
       ],
       "service": "mega-security-gateway"
     }
     ```
6. **Neautorizovaná výzva na `/mcp`**:
   - Příkaz: `curl -s -i -X POST http://127.0.0.1:7080/mcp`
   - HTTP Status: `401 Unauthorized`
   - Hlavička: `WWW-Authenticate: Bearer resource_metadata="https://home-automat-server.tailb42db0.ts.net/.well-known/oauth-protected-resource", error="invalid_token"`
   - Tělo: `{"error": "invalid_token", "error_description": "Bearer access token required"}`
7. **Integrita OAuth metadat a issueru**:
   - Příkazy:
     - `curl -s http://127.0.0.1:7080/.well-known/oauth-protected-resource`
     - `curl -s http://127.0.0.1:7080/.well-known/oauth-authorization-server`
   - Ověřeno, že nakonfigurovaný HTTPS původ `https://home-automat-server.tailb42db0.ts.net` je striktně použit pro všechny endpointy a metadata issueru i při injektování nepřátelských hlaviček `Host` nebo `X-Forwarded-*`.

---

## 6. Stav Tailscale Funnel / Serve

- `tailscale serve status`: `No serve config`
- `tailscale funnel status`: `No serve config`
- `./scripts/mega_funnel status`: `{}`
- Nouzový vypínací skript: `./scripts/mega_funnel off` (neexistuje žádná akce `on`).
- Funnel zůstává kompletně vypnutý.

---

## 7. Zbytková rizika a známá omezení

- **Zbytkové riziko P2 (Vyčerpání rezervací DCR / Párování)**:
  Neautentizovaný volající může vyčerpat všechny dostupné sloty dynamické registrace klientů (DCR) nebo rezervace čekajících párování v rámci klouzavého 10minutového limitu. Ačkoliv tento limit úspěšně chrání před zahlcením databáze a paměti, nezaručuje férovost mezi jednotlivými klienty. Jde o známý architektonický kompromis pro kompatibilitu s anonymní registrací ChatGPT bez důvěry v podvrhnutelné IP hlavičky klientů.
- **Neprovedené E2E testování**:
  Žádný reálný end-to-end OAuth průchod se skutečnými klientskými účty OpenAI ChatGPT nebo Google Gemini nebyl proveden, v souladu se striktní instrukcí nepředstírat neprovedené testy jako úspěšné.

---

## 8. Postup pro Rollback (POUZE pro `mega-security-gateway`)

Pokud bude vyžadován rollback bezpečnostní brány, proveďte výhradně následující příkazy. **NIKDY** nespouštějte `docker compose down` v adresáři `/home/orchestration`.

```bash
# 1. Zastavení a odstranění kontejneru bezpečnostní brány
cd /home/mega-security-gateway-deploy
docker compose -p mega-security-gateway --env-file .env.mega-gateway -f docker-compose.mega-gateway.yml down

# 2. (Volitelné) Odstranění Docker obrazu brány
docker rmi mega-security-gateway-mega-security-gateway

# 3. Vyčištění runtime socketu, je-li vyžadováno
rm -f /run/mega-gateway/admin.sock

# 4. Ujištění se, že Tailscale Funnel je kompletně vypnutý
./scripts/mega_funnel off
```

---

## 9. Další kroky pro lidského operátora

1. Zahajte OAuth připojení z ChatGPT nebo Gemini custom aplikace vůči URL:
   `https://home-automat-server.tailb42db0.ts.net/mcp`
2. Zjistěte nově vygenerované čekající ID párování (pairing ID) lokálně na HAS:
   ```bash
   cd /home/mega-security-gateway-deploy
   ./scripts/mega_security pairing pending
   ```
3. Schvalte párování lokálně přes administrátorské CLI:
   ```bash
   ./scripts/mega_security pairing approve <pairing_id>
   ```
