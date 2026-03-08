# Perplexity HUB

Canonical research runtime for the orchestration stack.

## What It Does

- Uses Perplexity for live, cited retrieval.
- Optionally uses OpenAI to synthesize or normalize the retrieved result.
- Exposes one canonical API at `POST /hub/query`.

## Endpoints

- `GET /health`
- `GET /hub/providers`
- `POST /hub/query`

## Request Shape

```json
{
  "query": "latest redis security issue",
  "mode": "news",
  "model": "sonar-pro",
  "synthesis_provider": "openai"
}
```

Supported `mode` values:

- `news`
- `domain`
- `academic`
- `structured`

Additional fields:

- `domains`: required for `domain`
- `recency`: optional for `domain`
- `response_schema`: required for `structured`
- `synthesis_model`: optional when `synthesis_provider` is `openai`

## Secrets

- `PERPLEXITY_API_KEY` or `PERPLEXITY_API_KEY_FILE`
- `OPENAI_API_KEY` or `OPENAI_API_KEY_FILE`

`*_FILE` is the preferred runtime path for this service.

## Local Testing

```bash
/home/orchestration/.venv/bin/pytest --cov=/home/orchestration/mcp-servers/perplexity-hub --cov-report=term-missing /home/orchestration/mcp-servers/perplexity-hub/tests/test_main.py
```

## Debug Notes

- If `GET /health` reports `perplexity` or `openai` as `false`, the corresponding secret is not loaded.
- `422` means request validation failed.
- `502` means an upstream provider failed or returned an invalid payload.
