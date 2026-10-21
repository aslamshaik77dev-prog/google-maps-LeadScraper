#!/bin/sh
set -e

# Start Go scraping engine in the background on port 8080
echo "Starting Google Maps Scraper Go Engine on :8080..."
google-maps-scraper -data-folder /data -addr :8080 &

# Wait for Go engine to start
for i in $(seq 1 30); do
  if curl -s http://localhost:8080/api/v1/jobs > /dev/null 2>&1; then
    echo "Go Engine is ready!"
    break
  fi
  sleep 1
done

# Start the Web UI dashboard on the Render-provided PORT (e.g. 10000)
echo "Starting Leads Studio Web UI on port ${PORT:-5000}..."
exec python3 /app/web_ui.py
