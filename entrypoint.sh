#!/bin/sh
set -e

mkdir -p /app/data

echo "============================================================"
echo "Starting Google Maps Scraper Go Engine on 127.0.0.1:8080..."
echo "Data folder: /app/data"
echo "============================================================"

# Launch Go engine in background and stream its logs
google-maps-scraper -web -data-folder /app/data -addr 127.0.0.1:8080 &
GO_PID=$!
echo "Go Engine launched with PID: $GO_PID"

# Wait for Go engine to respond
for i in $(seq 1 30); do
  if curl -s http://127.0.0.1:8080/api/v1/jobs > /dev/null 2>&1; then
    echo "✓ Go Engine is healthy and ready on 127.0.0.1:8080!"
    break
  fi
  echo "Waiting for Go Engine... ($i/30)"
  sleep 1
done

# Start Python Web UI
echo "Starting Leads Studio Web UI on port ${PORT:-5000}..."
exec python3 /app/web_ui.py
