#!/bin/bash
cd /workspace/Eden-AI

echo "Starting Eden-AI services..."
echo "Timestamp: $(date)"

# Kill any existing processes
echo "Stopping any existing services..."
pkill -f "uvicorn open_webui.main:app" 2>/dev/null || true
pkill -f "cloudflared" 2>/dev/null || true

# Remove Jupyter checkpoint files that break builds
echo "Cleaning up checkpoint files..."
find . -type d -name ".ipynb_checkpoints" -exec rm -rf {} + 2>/dev/null || true

# Start backend with nohup and log to file
echo "Starting backend server on port 8081..."
nohup bash -c 'cd backend && uvicorn open_webui.main:app --host 0.0.0.0 --port 8081' > backend.log 2>&1 &

# Wait a moment for backend to start
sleep 3

# Start Cloudflare tunnel
echo "Starting Cloudflare tunnel..."
nohup cloudflared tunnel --config ~/.cloudflared/edenhub-config.yml run edenhub > cloudflared.log 2>&1 &

echo ""
echo "✅ Services started in background!"
echo ""
echo "📋 Logs:"
echo "  Backend logs: tail -f backend.log"
echo "  Cloudflare logs: tail -f cloudflared.log"
echo ""
echo "🔍 Check status: ps aux | grep -E '(uvicorn|cloudflared)'"
echo ""
echo "🌐 Your site: https://edenhub.io"
