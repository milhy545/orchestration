FROM python:3.9-slim-buster

WORKDIR /app

# Nainstalovat git jako první a ověřit instalaci
RUN apt-get update && apt-get install -y git --no-install-recommends && rm -rf /var/lib/apt/lists/* && git --version

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]