FROM python:3.12-alpine

WORKDIR /app

RUN apk add --no-cache su-exec && addgroup -S gateway && adduser -S -G gateway gateway
COPY config/mega-gateway-requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY mega_gateway /app/mega_gateway
RUN mkdir -p /run/mega-gateway /data && chown -R gateway:gateway /run/mega-gateway /data

EXPOSE 7080
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 CMD wget -qO- http://127.0.0.1:7080/health >/dev/null || exit 1
CMD ["sh", "-c", "mkdir -p /run/mega-gateway /data && chown gateway:gateway /run/mega-gateway /data && exec su-exec gateway python -m mega_gateway"]
