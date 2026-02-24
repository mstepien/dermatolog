#!/bin/bash

#kill <PID> && source venv/bin/activate && nohup uvicorn main:app --host 127.0.0.1 --port 8080 > server.log 2>&1 &

# Find the PID of the running uvicorn process
PID=$(ps aux | grep "uvicorn app.main:app" | grep -v grep | awk '{print $2}')

if [ -n "$PID" ]; then
    echo "Stopping existing application(s) (PIDs: $PID)..."
    echo "$PID" | xargs kill
    sleep 2 # Wait for it to shut down
else
    echo "No running application found."
fi
