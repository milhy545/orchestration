# Provozní návod pro Mega security gateway

Admin rozhraní gateway je Unix socket. Wrappery `scripts/mega_security` a
`scripts/mega_funnel` po každém připojení odešlou jeden JSON požadavek a přečtou
jednu JSON odpověď. Cesta je v `MEGA_GATEWAY_ADMIN_SOCKET`, výchozí hodnota je
`/run/mega-gateway/admin.sock`; pro údržbu a testy ji lze změnit přes `--socket`.

Nejdřív spusťte `scripts/mega_security status`. Další akce:

```text
pairing pending
pairing approve <pairing-id>
pairing reject <pairing-id>
profile list [profile-id]
profile grant <profile-id> <tool>
profile revoke <profile-id> <tool>
connections list
connections revoke <connection-id>
audit
backup-check
funnel-off
```

Každá změna se audituje v gateway a stále podléhá jejímu ověření a pravidlům.
ID dodává gateway; ID z jiného prostředí nehadejte ani znovu nepoužívejte.

`scripts/mega_funnel` je záměrně omezený:

```text
scripts/mega_funnel status   # výchozí, pouze čtení
scripts/mega_funnel off      # nouzové vypnutí
```

Spravuje pouze Funnel konfiguraci patřící této gateway. Nemá akci `on`,
nezpřístupňuje port 7000 a nikdy nespouští Docker Compose. Tyto skripty Funnel
neaktivují ani nenasazují.

Transportní kontrakt je `{"action": "...", "payload": {...}}` jako JSON objekt
ukončený novým řádkem. Úspěšná odpověď může být JSON objekt nebo
`{"ok": true, "data": ...}`. Zamítnutí používá `{"ok": false, "error":
"..."}`. Přesná pravidla akcí a pole odpovědi určuje implementace gateway.
