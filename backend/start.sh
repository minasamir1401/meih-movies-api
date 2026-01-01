#!/bin/bash
set -e

echo "--- STARTING MULTI-SERVICE BOOT ---"

# Step 1: Start FlareSolverr
echo "[1/3] Launching FlareSolverr in background..."
export PYTHONPATH=$PYTHONPATH:/app/flaresolverr
export PORT=8191
export LOG_LEVEL=info

# Run FlareSolverr with its own directory as CWD
(cd /app/flaresolverr && python3 flaresolverr.py) &

# Step 2: Health Check for FlareSolverr
echo "[2/3] Waiting for FlareSolverr to bind to port 8191..."
MAX_RETRIES=30
COUNT=0
while ! curl -s http://localhost:8191/health > /dev/null; do
    sleep 1
    COUNT=$((COUNT+1))
    if [ $COUNT -ge $MAX_RETRIES ]; then
        echo "⚠️ FlareSolverr failed to start in time, continuing to FastAPI anyway..."
        break
    fi
done
echo "✅ FlareSolverr is ready!"

# Step 3: Start FastAPI
echo "[3/3] Launching FastAPI on port 7860..."
uvicorn main:app --host 0.0.0.0 --port 7860 --log-level info
