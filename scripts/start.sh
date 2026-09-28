#!/usr/bin/env bash
set -euo pipefail

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}Starting Rivet...${NC}"

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( dirname "$SCRIPT_DIR" )"

if ! command -v uv >/dev/null 2>&1; then
  echo -e "${RED}Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh${NC}"
  exit 1
fi

if [ ! -f "$PROJECT_ROOT/app/server/.env" ]; then
  cp "$PROJECT_ROOT/app/server/.env.sample" "$PROJECT_ROOT/app/server/.env"
  echo "Wrote app/server/.env from sample (demo worker, no keys)."
fi

cleanup() {
  echo -e "\n${BLUE}Shutting down services...${NC}"
  pids="$(jobs -p || true)"
  if [ -n "$pids" ]; then
    kill $pids 2>/dev/null || true
  fi
  wait || true
  echo -e "${GREEN}Services stopped.${NC}"
  exit 0
}
trap cleanup EXIT INT TERM

echo -e "${GREEN}Starting backend...${NC}"
cd "$PROJECT_ROOT/app/server"
uv sync --all-extras
uv run python server.py &
BACKEND_PID=$!

echo "Waiting for backend..."
for _ in 1 2 3 4 5 6 7 8 9 10; do
  if kill -0 "$BACKEND_PID" 2>/dev/null && curl -sf http://127.0.0.1:8000/health >/dev/null 2>&1; then
    break
  fi
  sleep 0.5
done

if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
  echo -e "${RED}Backend failed to start.${NC}"
  exit 1
fi

echo -e "${GREEN}Starting frontend...${NC}"
cd "$PROJECT_ROOT/app/client"
if [ ! -d node_modules ]; then
  npm install
fi
npm run dev &
FRONTEND_PID=$!
sleep 2

if ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
  echo -e "${RED}Frontend failed to start.${NC}"
  exit 1
fi

echo -e "${GREEN}Rivet is up.${NC}"
echo -e "${BLUE}Console:  http://localhost:5173${NC}"
echo -e "${BLUE}API:      http://127.0.0.1:8000${NC}"
echo -e "${BLUE}OpenAPI:  http://127.0.0.1:8000/docs${NC}"
echo ""
echo "Press Ctrl+C to stop."
wait
