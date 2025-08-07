#!/bin/bash
# ==============================================
# Production Startup Script - Accurate Tunnel Verification
# ==============================================

set -eo pipefail

# Configuration
LOG_DIR="/root/logs"
BACKEND_PORT=8081
COMFYUI_PORT=8187

# Initialize
mkdir -p "$LOG_DIR"
exec > >(tee -a "$LOG_DIR/startup.log") 2>&1

echo "=== Production Startup $(date) ==="
echo "Working directory: $(pwd)"
echo "Log directory: $LOG_DIR"

# --- Functions ---
safe_kill() {
    local pattern=$1
    local service=$2
    
    echo "Stopping $service..."
    pkill -f "$pattern" 2>/dev/null || true
    sleep 2
    
    if pgrep -f "$pattern" >/dev/null; then
        echo "Force killing $service..."
        pkill -9 -f "$pattern" 2>/dev/null || true
        sleep 1
    fi
}

check_service() {
    local url=$1
    local name=$2
    local max_attempts=30
    
    echo "Checking $name at $url..."
    for ((i=1; i<=max_attempts; i++)); do
        if curl -s --connect-timeout 3 "$url" >/dev/null; then
            echo "$name ready ✓"
            return 0
        fi
        echo "Attempt $i/$max_attempts failed, waiting 2s..."
        sleep 2
    done
    echo "ERROR: $name failed after $max_attempts attempts"
    return 1
}

# --- System Configuration ---
echo "--- System Configuration ---"
# GPU Isolation
export CUDA_VISIBLE_DEVICES=""
export HIP_VISIBLE_DEVICES=""
echo "GPU isolation: Disabled CUDA/HIP devices"

# Initialize PYTHONPATH if not set
export PYTHONPATH="${PYTHONPATH:-}:/workspace/Eden-AI/backend"

# --- Service Cleanup ---
echo "--- Service Cleanup ---"
safe_kill "uvicorn.*$BACKEND_PORT" "OpenWebUI Backend"
safe_kill "cloudflared.*eden-config" "Eden Tunnel"
safe_kill "cloudflared.*comfyui-config" "ComfyUI Tunnel"

# --- Backend Startup ---
echo "--- Starting OpenWebUI ---"
cd /workspace/Eden-AI

nohup uvicorn open_webui.main:app \
    --host 0.0.0.0 \
    --port $BACKEND_PORT \
    --workers 1 \
    --timeout-keep-alive 30 \
    --log-level info > "$LOG_DIR/openwebui.log" 2>&1 &

check_service "http://localhost:$BACKEND_PORT/health" "OpenWebUI Backend" || {
    echo "Last 10 log lines:"
    tail -n 10 "$LOG_DIR/openwebui.log"
    exit 1
}

# --- Tunnel Management ---
start_tunnel() {
    local config=$1
    local name=$2
    local log="$LOG_DIR/${name}-tunnel.log"
    
    echo "Starting $name tunnel..."
    nohup bash -c '
        echo "[$(date +%FT%TZ)] Starting tunnel..." >> "$2"
        while true; do
            if cloudflared tunnel --config "$3" run "$1" >> "$2" 2>&1; then
                echo "[$(date +%FT%TZ)] Tunnel exited cleanly" >> "$2"
            else
                echo "[$(date +%FT%TZ)] Tunnel crashed (exit $?)" >> "$2"
            fi
            sleep 5
        done
    ' _ "$name" "$log" "$config" &
}

echo "--- Tunnel Startup ---"
start_tunnel "/root/.cloudflared/eden-config.yml" "eden"
start_tunnel "/root/.cloudflared/comfyui-config.yml" "comfyui"

# --- Validation ---
echo "--- Service Validation ---"
sleep 10  # Allow tunnels to initialize

check_live() {
    local url=$1
    local name=$2
    echo -n "Checking $name... "
    
    if curl -Is --connect-timeout 3 "$url" >/dev/null 2>&1; then
        echo "Live ✓"
        return 0
    else
        echo "Down ✗"
        return 1
    fi
}

echo "Service Status:"
check_process() {
    if pgrep -f "$1" >/dev/null; then
        echo "  $2: Process Running ✓"
        return 0
    else
        echo "  $2: Process Missing ✗"
        return 1
    fi
}

check_process "uvicorn.*$BACKEND_PORT" "OpenWebUI"
check_process "cloudflared.*eden-config" "Eden Tunnel"
check_process "cloudflared.*comfyui-config" "ComfyUI Tunnel"

echo "Live Checks:"
check_live "http://localhost:$BACKEND_PORT/health" "Local Backend"
check_live "https://edenhub.io/health" "Eden Tunnel"
check_live "https://comfyui.edenhub.io" "ComfyUI Tunnel"

# --- Monitoring Instructions ---
echo "--- Monitoring Instructions ---"
cat <<EOF

=== Log Monitoring ===
Backend:    tail -f $LOG_DIR/openwebui.log
Eden:       tail -f $LOG_DIR/eden-tunnel.log
ComfyUI:    tail -f $LOG_DIR/comfyui-tunnel.log

=== Access URLs ===
OpenWebUI:  https://edenhub.io
            http://localhost:$BACKEND_PORT
ComfyUI:    https://comfyui.edenhub.io

=== Maintenance ===
To stop all services:
  pkill -f "uvicorn.*$BACKEND_PORT"
  pkill -f "cloudflared.*(eden-config|comfyui-config)"
EOF

# --- Continuous Monitoring (if interactive) ---
if [ -t 1 ]; then
    trap 'echo "=== Stopping all services ==="; safe_kill "uvicorn.*$BACKEND_PORT" "Backend"; safe_kill "cloudflared" "Tunnels"; exit 0' INT TERM
    
    echo ""
    echo "=== Entering monitoring mode ==="
    echo "Press Ctrl+C to stop all services"
    
    while true; do
        echo ""
        echo "[$(date +%FT%TZ)] System Status:"
        
        # Process checks
        check_process "uvicorn.*$BACKEND_PORT" "OpenWebUI"
        check_process "cloudflared.*eden-config" "Eden Tunnel"
        check_process "cloudflared.*comfyui-config" "ComfyUI Tunnel"
        
        # Live checks
        check_live "https://edenhub.io/health" "Eden Tunnel"
        check_live "https://comfyui.edenhub.io" "ComfyUI Tunnel"
        
        # Resource monitoring
        free -h | awk '/Mem/{printf "Memory: %.1f/%.1fGB\n", $3/1024, $2/1024}'
        df -h | awk '/\/$/{printf "Disk: %.1f/%.1fGB\n", $3, $2}'
        
        sleep 30
    done
fi