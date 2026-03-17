FROM python:3.12-slim

WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Nainstalovat git jako první a ověřit instalaci
RUN apt-get update && apt-get install -y git --no-install-recommends && rm -rf /var/lib/apt/lists/* && git --version

COPY requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

COPY main.py .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
