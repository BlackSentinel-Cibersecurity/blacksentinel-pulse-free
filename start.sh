#!/bin/bash
# BlackSentinel Pulse - Start Script
# Starts both backend and frontend for development

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo "=========================================="
echo "   BLACKSENTINEL PULSE - Starting..."
echo "=========================================="
echo ""

# Kill any existing processes
pkill -f "uvicorn app.main" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true
sleep 1

# Start Backend
echo -e "${YELLOW}[1/2] Starting Backend (FastAPI)...${NC}"
cd "$BACKEND_DIR"

if [ ! -d "venv" ]; then
    echo -e "${RED}Virtual environment not found. Run: cd backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt${NC}"
    exit 1
fi

source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait for backend to be ready
echo "Waiting for backend..."
for i in $(seq 1 30); do
    if curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1; then
        echo -e "${GREEN}Backend ready on http://localhost:8000${NC}"
        break
    fi
    sleep 1
done

# Start Frontend
echo -e "${YELLOW}[2/2] Starting Frontend (Vite)...${NC}"
cd "$FRONTEND_DIR"

if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

npm run dev &
FRONTEND_PID=$!

sleep 3

echo ""
echo "=========================================="
echo -e "${GREEN}   BLACKSENTINEL PULSE is running!${NC}"
echo "=========================================="
echo ""
echo "   Frontend:  http://localhost:3000"
echo "   Backend:   http://localhost:8000"
echo "   API Docs:  http://localhost:8000/api/docs"
echo ""
echo "   Login:     admin / admin123"
echo ""
echo "   Press Ctrl+C to stop all services"
echo "=========================================="
echo ""

# Wait for Ctrl+C
trap "echo ''; echo 'Shutting down...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT TERM
wait
