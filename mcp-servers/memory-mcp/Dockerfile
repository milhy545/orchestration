FROM python:3.12-slim

WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

COPY main.py .

# Create volume mount point for memory database
RUN mkdir -p /tmp

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
