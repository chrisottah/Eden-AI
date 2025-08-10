#!/bin/bash

# Log files
LOG_DIR="./logs"
mkdir -p $LOG_DIR

# Start Cloudflare tunnel
nohup cloudflared tunnel --config /workspace/.cloudflared/your-tunnel-config.yml run your-tunnel-name > $LOG_DIR/cloudflared.log 2>&1 &

echo "Started Cloudflare tunnel (PID $!)"

# Start backend (adjust python environment path if needed)
nohup uvicorn backend.open_webui.main:app --host 0.0.0.0 --port 8081 > $LOG_DIR/backend.log 2>&1 &

echo "Started backend (PID $!)"

# Start frontend preview (assuming you want production preview)
nohup pnpm preview --host 0.0.0.0 --port 5173 > $LOG_DIR/frontend.log 2>&1 &

echo "Started frontend (PID $!)"

echo "All services started."
