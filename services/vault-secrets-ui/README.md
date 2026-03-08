# Vault Secrets UI

`vault-secrets-ui` je přenositelný Vault modul s retro webovým rozhraním zaměřeným primárně na zadávání jednotlivých klíčů místo editace celého JSON payloadu.

## Co obsahuje

- FastAPI aplikaci s endpointy `/`, `/health`, `/api/services`, `/api/secrets/{service}`
- deklarativní konfiguraci služeb v `services.json`
- generování runtime `.env` souborů
- podporu `delivery_mode: "file"` pro secret delivery bez raw hodnot v container env
- skrytý `Advanced JSON` režim pro výjimečné případy
- EN/CZ přepínač a 3 historické theme režimy

## Struktura

- `app.py`: tenký entrypoint pro Uvicorn
- `services.json`: přenosná definice služeb a formulářových polí
- `src/vault_secrets_ui/`: znovupoužitelný Python balíček
- `tests/`: unit, integration a E2E-style testy

## Lokální spuštění

```bash
cd services/vault-secrets-ui
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt pytest pytest-cov
PYTHONPATH=src uvicorn app:app --reload --port 10000
```

## Konfigurace

Používané proměnné prostředí:

- `VAULT_ADDR`
- `VAULT_TOKEN_FILE`

Služby se definují v `services.json`. Každá služba má:

- `id`
- `label`
- `vault_path`
- `env_file`
- `restart_target`
- `delivery_mode`
- `description`
- `fields`

Každé pole podporuje:

- `name`
- `label`
- `target_env`
- `input_type`
- `secret`
- `advanced_only`
- `placeholder`
- `default`

`delivery_mode` podporuje:

- `env`: starší režim, kdy se hodnoty zapisují přímo do runtime `.env`
- `file`: preferovaný režim pro secrety; renderer vytvoří secret file a do `.env` zapíše jen `*_FILE` cestu

Pro služby, které pracují s tajemstvími, je cílový stav `delivery_mode: "file"`, aby se raw klíče neobjevovaly v `docker inspect`.

## Přenos do jiného projektu

1. Zkopírujte složku `services/vault-secrets-ui`.
2. Upravte `services.json` podle cílových služeb.
3. Nastavte `VAULT_ADDR` a `VAULT_TOKEN_FILE`.
4. Spusťte `uvicorn app:app --host 0.0.0.0 --port 10000` nebo použijte přiložený Dockerfile.

## Docker

```bash
docker build -f services/vault-secrets-ui/Dockerfile -t vault-secrets-ui .
docker run --rm -p 10000:10000 \
  -e VAULT_ADDR=http://vault:8200 \
  -e VAULT_TOKEN_FILE=/vault/runtime/admin.token \
  -v /vault/runtime:/vault/runtime \
  vault-secrets-ui
```

## Testy

```bash
./.venv/bin/pytest services/vault-secrets-ui/tests \
  --cov=services/vault-secrets-ui/src/vault_secrets_ui \
  --cov-report=term-missing \
  --cov-fail-under=100
```

Browser smoke přes Playwright v kontejneru:

```bash
./scripts/vault-ui-playwright-smoke.sh http://127.0.0.1:10000
```

## Historie variant

- `2a03dc2`: starší obnovené retro UI
- `25dac15`: retro UI s runtime metadata a restart logikou
- `d892ff7`: bezpečnější health probe bez úniku detailů
- aktuální verze: key-first UI nad přenositelným balíčkem
