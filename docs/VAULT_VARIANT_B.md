# Vault Variant B

`Vault Variant B` je dnes postavený kolem přenositelného modulu `vault-secrets-ui`, který používá deklarativní konfiguraci služeb a primárně formulářové zadávání jednotlivých klíčů.

## Co přidává

- `vault` na `${VAULT_PORT:-7070}`
- `vault-bootstrap` pro inicializaci politik a seed dat
- `vault-agent-common` pro render runtime `.env` snapshotů do `/vault/runtime/*.env` a secret files do `/vault/runtime/secrets/<service>/`
- `vault-secrets-ui` na `${VAULT_WEBUI_PORT:-10000}` s retro UI a key-first workflow

## Aktivní workflow

1. Vyberte cílovou službu.
2. Vyplňte dedikovaná pole pro klíče a konfigurační hodnoty.
3. Uložte změnu do Vaultu.
4. Restartujte dotčenou službu podle zobrazeného příkazu.
5. `Advanced JSON` použijte jen tehdy, když potřebujete uložit doplňkové klíče mimo formulář.

## Soubory

- `[services/vault-secrets-ui](/home/orchestration/services/vault-secrets-ui)`
- `[services/vault-secrets-ui/services.json](/home/orchestration/services/vault-secrets-ui/services.json)`
- `[scripts/vault-variant-b-smoke.sh](/home/orchestration/scripts/vault-variant-b-smoke.sh)`
- `docker-compose.vault.yml`

## Health checks

```bash
curl -s http://localhost:${VAULT_WEBUI_PORT:-10000}/health
curl -s http://localhost:${VAULT_PORT:-7070}/v1/sys/health
curl -s http://localhost:7000/health
./scripts/vault-ui-playwright-smoke.sh http://127.0.0.1:${VAULT_WEBUI_PORT:-10000}
```

Očekávaný výsledek:

- `vault-secrets-ui` vrací `status: healthy`
- health uvádí `token_file_present`
- health uvádí `vault_reachable`
- `mega-orchestrator` je stále dostupný na portu `7000`

## Konfigurace služeb

Aktivní seznam služeb a polí je v `[services/vault-secrets-ui/services.json](/home/orchestration/services/vault-secrets-ui/services.json)`.

Každá služba definuje:

- `id`
- `label`
- `vault_path`
- `env_file`
- `restart_target`
- `delivery_mode`
- `description`
- `fields`

Každé pole definuje:

- `name`
- `label`
- `target_env`
- `input_type`
- `secret`
- `advanced_only`
- `placeholder`
- `default`

`delivery_mode: "file"` je preferovaný režim pro secret-heavy služby. Renderer pak uloží raw secret do souboru pod `/vault/runtime/secrets/...` a do runtime `.env` zapíše jen `*_FILE` cestu, takže se secret nepropaguje do container env při startu přes Vault overlay.

## Přenositelnost

Modul lze přesunout do jiného projektu jako celek:

1. zkopírovat složku `[services/vault-secrets-ui](/home/orchestration/services/vault-secrets-ui)`
2. upravit `services.json`
3. nastavit `VAULT_ADDR` a `VAULT_TOKEN_FILE`
4. spustit `uvicorn app:app` nebo použít Dockerfile

## Historické varianty

- `2a03dc2`: starší obnovené retro UI
- `25dac15`: retro UI s runtime metadata a restart logikou
- `d892ff7`: bezpečnější health probe bez úniku detailů
- aktuální aktivní verze: přenositelný key-first modul s hidden advanced JSON režimem
