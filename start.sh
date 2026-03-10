#!/bin/bash
set -e

echo "=== Starting AI Voice Agent ==="

# Start backend in background
echo "Starting FastAPI backend..."
python -m uvicorn backend:app --host 0.0.0.0 --port 8000 --workers=1 &
BACKEND_PID=$!
echo "Backend started with PID: $BACKEND_PID"

# Wait for backend to be ready
echo "Waiting for backend to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "Backend is ready!"
        break
    fi
    echo "Waiting... ($i/30)"
    sleep 1
done

# Start Streamlit in foreground
echo "Starting Streamlit frontend..."
exec streamlit run ui.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true
