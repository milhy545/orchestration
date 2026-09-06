FROM alpine:3.20 AS downloader
RUN apk add --no-cache curl unzip
ARG VERSION=0.0.9
RUN ARCH=$(uname -m) && \
    if [ "$ARCH" = "x86_64" ]; then ARCH_TAG="linux-amd64"; \
    elif [ "$ARCH" = "aarch64" ]; then ARCH_TAG="linux-arm64"; \
    else echo "Unsupported architecture: $ARCH" && exit 1; fi && \
    curl -L -o client.zip "https://github.com/openai/tunnel-client/releases/download/v${VERSION}/${ARCH_TAG}.zip" && \
    unzip client.zip && \
    mv tunnel-client /usr/local/bin/tunnel-client && \
    chmod +x /usr/local/bin/tunnel-client

FROM alpine:3.20
RUN apk add --no-cache ca-certificates
COPY --from=downloader /usr/local/bin/tunnel-client /usr/local/bin/tunnel-client
ENTRYPOINT ["/usr/local/bin/tunnel-client"]
CMD ["run"]
