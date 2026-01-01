#!/bin/bash
set -e

echo "--- RENDER.COM DEPLOYMENT ---"

# Step 1: Start FlareSolverr
echo "[1/2] Launching FlareSolverr in background..."
export PYTHONPATH=$PYTHONPATH:/opt/render/project/src/flaresolverr
export PORT_FS=8191
export LOG_LEVEL=info

(cd /opt/render/project/src/flaresolverr && python3 flaresolverr.py) &

# Wait for FlareSolverr
echo "[2/2] Waiting for FlareSolverr..."
sleep 5

echo "✅ FlareSolverr ready!"
echo "--- Starting FastAPI on port $PORT ---"

# Render provides $PORT automatically
uvicorn main:app --host 0.0.0.0 --port ${PORT:-7860} --log-level info
