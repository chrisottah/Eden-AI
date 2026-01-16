#!/bin/bash
cd /workspace/Eden-AI

echo "Starting Eden-AI services..."
echo "Timestamp: $(date)"

# Kill existing
pkill -f "uvicorn open_webui.main:app" 2>/dev/null || true
pkill -f "cloudflared" 2>/dev/null || true

# Remove Jupyter checkpoint files that break builds
echo "Cleaning up checkpoint files..."
find . -type d -name ".ipynb_checkpoints" -exec rm -rf {} + 2>/dev/null || true

# Set explicit paths for v0.7.2
export FRONTEND_BUILD_DIR="/workspace/Eden-AI/build"
export PYTHONPATH="/workspace/Eden-AI/backend:$PYTHONPATH"

# Create static folder and symlinks for branding
echo "Setting up branding assets..."
mkdir -p /workspace/Eden-AI/build/static

# Find and link splash
SPLASH_FILE=$(ls /workspace/Eden-AI/build/_app/immutable/assets/splash.*.png 2>/dev/null | head -1)
if [ -n "$SPLASH_FILE" ]; then
    ln -sf "$SPLASH_FILE" /workspace/Eden-AI/build/static/splash.png
    ln -sf "$SPLASH_FILE" /workspace/Eden-AI/build/static/splash-dark.png
    echo "✓ Splash symlinks created"
fi

# Copy favicon directly (remove old symlink first)
rm -f /workspace/Eden-AI/build/static/favicon.png
if [ -f "src/lib/assets/eden/favicon.png" ]; then
    cp src/lib/assets/eden/favicon.png /workspace/Eden-AI/build/static/favicon.png
    echo "✓ Favicon copied"
else
    echo "⚠ Warning: favicon not found at src/lib/assets/eden/favicon.png"
    if [ -n "$SPLASH_FILE" ]; then
        ln -sf "$SPLASH_FILE" /workspace/Eden-AI/build/static/favicon.png
        echo "✓ Using splash as favicon fallback"
    fi
fi

# Start backend
echo "Starting backend server on port 8081..."
nohup bash -c "cd backend && /venv/main/bin/uvicorn open_webui.main:app --host 0.0.0.0 --port 8081" > backend.log 2>&1 &

sleep 3

# Start Cloudflare tunnel
echo "Starting Cloudflare tunnel..."
nohup cloudflared tunnel --config /root/.cloudflared/eden-config.yml run > cloudflared.log 2>&1 &

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