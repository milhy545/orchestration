FROM python:3.12-slim

WORKDIR /app

RUN apt update && apt install -y git && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

EXPOSE 7002

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7002"]