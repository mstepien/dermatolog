#!/bin/bash
echo "Stopping any existing uvicorn processes..."
pkill -f uvicorn || true

echo "Starting application server..."
# Using nohup and python -m uvicorn to ensure correct python path and persistence
nohup /Users/mstepien/Documents/dev2/py/fasts/venv/bin/python3.10 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > server.log 2>&1 &

echo "Waiting for server to be ready..."
# Simple loop to check if port 8000 is open (using curl or netcat logic via python)
for i in {1..30}; do
    if curl -s http://localhost:8000/api/health >/dev/null; then
        echo "Server is UP!"
        exit 0
    fi
    echo "Waiting for server... ($i/30)"
    sleep 1
done

echo "Server failed to start. Check server.log:"
tail -n 20 server.log
exit 1
