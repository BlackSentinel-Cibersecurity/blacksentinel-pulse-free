#!/bin/bash
# BlackSentinel Pulse - One-Command Setup
# Installs everything and starts the system

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo ""
echo -e "${CYAN}=========================================="
echo "   BLACKSENTINEL PULSE - Setup"
echo "==========================================${NC}"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 not found. Install: brew install python@3.11 (macOS) or apt install python3 (Linux)${NC}"
    exit 1
fi

# Check Node
if ! command -v node &> /dev/null; then
    echo -e "${RED}Node.js not found. Install: brew install node (macOS) or apt install nodejs (Linux)${NC}"
    exit 1
fi

echo -e "${YELLOW}[1/5] Setting up backend...${NC}"
cd "$SCRIPT_DIR/backend"

if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Created virtual environment"
fi

source venv/bin/activate
pip install -r requirements.txt -q
echo -e "${GREEN}Backend dependencies installed${NC}"

echo -e "${YELLOW}[2/5] Seeding database...${NC}"
python seed.py 2>&1 | grep -v "SAWarning\|DeprecationWarning\|sys:0"
echo -e "${GREEN}Database seeded${NC}"

echo -e "${YELLOW}[3/5] Setting up frontend...${NC}"
cd "$SCRIPT_DIR/frontend"
npm install --silent 2>/dev/null
echo -e "${GREEN}Frontend dependencies installed${NC}"

echo -e "${YELLOW}[4/5] Building frontend...${NC}"
npm run build --silent 2>/dev/null
echo -e "${GREEN}Frontend built${NC}"

echo -e "${YELLOW}[5/5] Starting services...${NC}"
cd "$SCRIPT_DIR"

# Start backend
cd "$SCRIPT_DIR/backend"
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait for backend
for i in $(seq 1 30); do
    if curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1; then
        break
    fi
    sleep 1
done

# Start frontend dev server
cd "$SCRIPT_DIR/frontend"
npm run dev &
FRONTEND_PID=$!

sleep 3

echo ""
echo -e "${CYAN}=========================================="
echo -e "${GREEN}   BLACKSENTINEL PULSE is running!${NC}"
echo -e "${CYAN}==========================================${NC}"
echo ""
echo "   Frontend:  http://localhost:3000"
echo "   Backend:   http://localhost:8000"
echo "   API Docs:  http://localhost:8000/api/docs"
echo ""
echo "   Login:     admin / admin123"
echo ""
echo "   Press Ctrl+C to stop"
echo -e "${CYAN}==========================================${NC}"
echo ""

trap "echo ''; echo 'Shutting down...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT TERM
wait
