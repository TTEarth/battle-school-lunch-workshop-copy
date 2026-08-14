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

또는 원커맨드 스크립트:

```bash
# bash
NEIS_API_KEY=<키> ./scripts/run-app.sh          # Docker Compose
NEIS_API_KEY=<키> ./scripts/run-app.sh --local  # Docker 없이 로컬 실행

# PowerShell
$env:NEIS_API_KEY="<키>"; ./scripts/run-app.ps1         # Docker Compose
$env:NEIS_API_KEY="<키>"; ./scripts/run-app.ps1 -Local  # Docker 없이 로컬 실행
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

## Azure 배포 (azd)

Azure Developer CLI로 Container Apps에 배포합니다. 인프라는 `infra/` bicep, 서비스 정의는 루트 `azure.yaml`에 있습니다. 이미지 빌드는 ACR 원격 빌드를 사용하므로 로컬 Docker가 필요 없습니다.

```bash
azd auth login
azd env new <환경이름>
azd env set NEIS_API_KEY <발급받은 키>
azd up          # 프로비저닝(리소스 그룹/ACR/Container Apps) + 빌드 + 배포
```

- 배포 후 `FRONTEND_URI`/`BACKEND_URI`가 출력됩니다.
- 프론트엔드는 프로덕션에서 nginx가 정적 파일을 서빙하며 `/api`를 백엔드 Container App으로 프록시합니다(`Dockerfile.azure`, `nginx.conf.template`).
- 정리는 `azd down`.

## 테스트

```bash
# 백엔드 단위/통합 테스트
cd src/backend && python -m pytest

# 프론트엔드 통합 테스트
cd src/frontend && npm test

# E2E (프론트엔드 dev 서버 또는 Compose 기동 후)
cd src/e2e && npm install && npx playwright install chromium && npm test

# 실백엔드 관통 E2E (NEIS 대역 사용)
python src/e2e/neis_stub.py &                                   # :9310
NEIS_BASE_URL=http://localhost:9310 NEIS_API_KEY=stub uvicorn app.main:app  # src/backend에서
E2E_FULL=1 npm test                                             # src/e2e에서
```
