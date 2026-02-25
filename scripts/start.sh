#!/bin/bash
# CrisisCore - Start all services

set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "🚨 Starting CrisisCore..."
echo ""

# Check for .env
if [ ! -f "$ROOT_DIR/backend/.env" ]; then
  echo "⚠️  No .env file found. Creating from example..."
  cp "$ROOT_DIR/backend/.env.example" "$ROOT_DIR/backend/.env"
  echo "❗ Please edit backend/.env and add your GEMINI_API_KEY"
  echo ""
fi

# Install backend deps if needed
if [ ! -d "$ROOT_DIR/backend/venv" ]; then
  echo "📦 Setting up Python virtual environment..."
  cd "$ROOT_DIR/backend"
  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
  echo ""
fi

# Install frontend deps if needed
if [ ! -d "$ROOT_DIR/frontend/node_modules" ]; then
  echo "📦 Installing frontend dependencies..."
  cd "$ROOT_DIR/frontend"
  npm install
  echo ""
fi

echo "🔧 Starting backend on http://localhost:8000..."
cd "$ROOT_DIR/backend"
source venv/bin/activate
uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!

sleep 2

echo "🎨 Starting frontend on http://localhost:5173..."
cd "$ROOT_DIR/frontend"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ CrisisCore is running!"
echo "   Backend:  http://localhost:8000"
echo "   Frontend: http://localhost:5173"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for both processes
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
