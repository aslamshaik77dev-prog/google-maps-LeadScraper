# syntax=docker/dockerfile:1

ARG GO_VERSION=1.24.1

# Build stage for Playwright dependencies
FROM golang:${GO_VERSION}-trixie AS playwright-deps
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/browsers
ENV PLAYWRIGHT_DRIVER_PATH=/opt/ms-playwright-go
ARG PLAYWRIGHT_GO_VERSION=v0.6100.0

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && go install github.com/mxschmitt/playwright-go/cmd/playwright@${PLAYWRIGHT_GO_VERSION} \
    && mkdir -p /opt/browsers \
    && playwright install chromium --with-deps

# Build stage
FROM golang:${GO_VERSION}-trixie AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -ldflags="-w -s" -o /usr/bin/google-maps-scraper

# Final stage
FROM debian:trixie-slim
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/browsers
ENV PLAYWRIGHT_DRIVER_PATH=/opt/ms-playwright-go

# Install runtime dependencies including python3 and curl
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    python3 \
    python3-pip \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libatspi2.0-0 \
    libx11-6 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir requests bottle --break-system-packages

COPY --from=playwright-deps /opt/browsers /opt/browsers
COPY --from=playwright-deps /opt/ms-playwright-go /opt/ms-playwright-go

RUN chmod -R 755 /opt/browsers \
    && chmod -R 755 /opt/ms-playwright-go

WORKDIR /app
COPY --from=builder /usr/bin/google-maps-scraper /usr/bin/
COPY ui /app/ui
COPY web_ui.py entrypoint.sh /app/

RUN chmod +x /app/entrypoint.sh

ENV PORT=10000
EXPOSE 10000

ENTRYPOINT ["/app/entrypoint.sh"]
