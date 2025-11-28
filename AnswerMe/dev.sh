#!/bin/bash

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🚀 AnswerMe Development Setup${NC}"

# Check dependencies
command -v docker >/dev/null 2>&1 || { echo -e "${RED}Docker required but not installed.${NC}"; exit 1; }
command -v node >/dev/null 2>&1 || { echo -e "${RED}Node.js required but not installed.${NC}"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo -e "${RED}Python3 required but not installed.${NC}"; exit 1; }

cd "$(dirname "$0")"

# Start PostgreSQL
echo -e "${YELLOW}📦 Starting PostgreSQL...${NC}"
docker compose up -d postgres
sleep 3

# Backend setup
echo -e "${YELLOW}🐍 Setting up backend...${NC}"
cd backend

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -q -r requirements.txt

if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Edit backend/.env with your settings${NC}"
fi

# Frontend setup
echo -e "${YELLOW}⚛️  Setting up frontend...${NC}"
cd ../frontend

if [ ! -d "node_modules" ]; then
    npm install
fi

if [ ! -f ".env.local" ]; then
    cp .env.local.example .env.local
fi

cd ..

# Run both services
echo -e "${GREEN}✅ Starting services...${NC}"
echo -e "Backend:  http://localhost:8000"
echo -e "Frontend: http://localhost:3005"
echo -e "API Docs: http://localhost:8000/docs"
echo ""

# Start backend and frontend in parallel
cd backend && source venv/bin/activate && uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!

cd frontend && npm run dev &
FRONTEND_PID=$!

# Cleanup on exit
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; docker-compose stop postgres" EXIT

wait
