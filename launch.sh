#!/bin/bash
# GhostScan Launch Script

PROJECT_DIR="/home/ge/.gemini/antigravity/scratch/ghostscan"
BACKEND_LOG="$PROJECT_DIR/backend/api.log"

# Kill existing GhostScan processes
pkill -f "ghostscan/backend/api.py"

# Start unified backend
echo "Starting GhostScan Engine..."
nohup python3 "$PROJECT_DIR/backend/api.py" > "$BACKEND_LOG" 2>&1 &

# Wait for backend
sleep 2

# Launch App mode in Chrome
echo "Launching Interface..."
google-chrome --app="http://localhost:8002" --user-data-dir="/tmp/ghostscan_profile" &

echo "GhostScan is active."
