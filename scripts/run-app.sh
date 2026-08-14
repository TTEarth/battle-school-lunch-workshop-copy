#!/usr/bin/env bash
# 급식 배틀 앱을 한 번에 실행합니다.
#
# 기본: Docker Compose로 프론트엔드+백엔드 기동
# --local: Docker 없이 로컬 프로세스(uvicorn + vite dev)로 실행
#
# 사용 예:
#   ./scripts/run-app.sh
#   ./scripts/run-app.sh --local
#   NEIS_API_KEY=발급키 ./scripts/run-app.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

if [[ -z "${NEIS_API_KEY:-}" ]]; then
  echo "경고: NEIS_API_KEY 환경 변수가 비어 있습니다. 실제 급식 조회는 실패할 수 있습니다. (.env.example 참고)" >&2
fi

if [[ "${1:-}" != "--local" ]]; then
  if ! command -v docker >/dev/null 2>&1; then
    echo "오류: docker를 찾을 수 없습니다. Docker를 설치하거나 --local 옵션을 사용하세요." >&2
    exit 1
  fi
  echo "Docker Compose로 앱을 기동합니다... (프론트: http://localhost:5173, 백엔드: http://localhost:8000)"
  exec docker compose up --build
fi

echo "로컬 모드로 실행합니다."

# 백엔드 의존성 설치 및 기동
pushd src/backend >/dev/null
python -m pip install --quiet fastapi "uvicorn[standard]" httpx
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
popd >/dev/null
echo "백엔드 시작됨 (PID $BACKEND_PID) - http://localhost:8000"

cleanup() {
  if kill -0 "$BACKEND_PID" 2>/dev/null; then
    kill "$BACKEND_PID" 2>/dev/null || true
    echo "백엔드(PID $BACKEND_PID) 종료됨"
  fi
}
trap cleanup EXIT

# 프론트엔드 의존성 설치 및 기동 (포그라운드)
cd src/frontend
if [[ ! -d node_modules ]]; then
  npm install --no-audit --no-fund
fi
echo "프론트엔드 시작 - http://localhost:5173 (Ctrl+C로 종료)"
npm run dev
