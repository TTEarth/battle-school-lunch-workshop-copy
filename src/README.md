# 급식 배틀 앱 (src)

PRD.md / TRD.md 기준으로 구현된 학교 급식 조회 웹 애플리케이션입니다.

## 구조

```
src/
  openapi.json    # 내부(프론트-백엔드) API 계약
  backend/        # FastAPI 백엔드 (NEIS 중계, 중식 필터, 검증, 정규화)
  frontend/       # React(Vite) 프론트엔드 (3단계 UI)
  e2e/            # Playwright E2E 테스트
```

- 외부 NEIS 계약: 저장소 루트 `openapi.json`
- 프론트엔드는 NEIS를 직접 호출하지 않고 내부 API(`/api/*`)만 사용합니다.

## 실행 (Docker Compose)

저장소 루트에서:

```bash
NEIS_API_KEY=<발급받은 키> docker compose up --build
```

- 프론트엔드: http://localhost:5173
- 백엔드: http://localhost:8000 (문서: /docs)

## 로컬 개발

```bash
# 백엔드
cd src/backend
pip install fastapi "uvicorn[standard]" httpx pytest
uvicorn app.main:app --reload

# 프론트엔드
cd src/frontend
npm install
npm run dev
```

환경 변수는 루트 `.env.example` 참고 (`NEIS_API_KEY` 등).

## 테스트

```bash
# 백엔드 단위/통합 테스트
cd src/backend && python -m pytest

# 프론트엔드 통합 테스트
cd src/frontend && npm test

# E2E (프론트엔드 dev 서버 또는 Compose 기동 후)
cd src/e2e && npm install && npx playwright install chromium && npm test
```
