#!/bin/bash
cd /workspace/Eden-AI

echo "Starting Eden-AI services..."
echo "Timestamp: $(date)"

# Kill any existing processes
echo "Stopping any existing services..."
pkill -f "uvicorn open_webui.main:app" 2>/dev/null || true
pkill -f "cloudflared" 2>/dev/null || true

# Build the frontend
echo "Building frontend..."
pnpm build

# Start backend with nohup and log to file
echo "Starting backend server on port 8081..."
nohup bash -c 'cd backend && uvicorn open_webui.main:app --host 0.0.0.0 --port 8081' > backend.log 2>&1 &

# Start Cloudflare tunnel
echo "Starting Cloudflare tunnel..."
nohup cloudflared tunnel --config ~/.cloudflared/edenhub-config.yml run edenhub-tunnel > cloudflared.log 2>&1 &

echo "Services started in background!"
echo "Backend logs: backend.log"
echo "Cloudflare logs: cloudflare.log"
echo "Check status with: ps aux | grep -E '(uvicorn|cloudflared)'"
echo "View logs with: tail -f backend.log or tail -f cloudflare.log"