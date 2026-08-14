# AGENTS.md

이 문서는 이 저장소에서 작업하는 AI 코딩 에이전트를 위한 운영 가이드입니다. 현재 저장소는 워크숍 템플릿 단계이며, 앱 구현물은 아직 포함되어 있지 않습니다. 따라서 아래 규칙은 `docs/04-implement-app.md` 이후 생성될 React/TypeScript 프론트엔드와 Python 백엔드 구조를 기준으로 유지·보완해야 합니다.

## 현재 저장소 상태

- 루트에는 워크숍 문서, GitHub 설정, `openapi.json`, `data/` 원본 자료만 있습니다.
- 실제 애플리케이션 코드는 아직 체크인되지 않았습니다.
- 이후 앱이 추가되면 이 문서를 즉시 업데이트해, 구현된 디렉터리 구조와 명령을 문서 내용과 일치시켜야 합니다.

## 예상 애플리케이션 구조

앱 구현이 완료되면 아래와 같은 루트 구조를 기준으로 관리합니다.

```text
.
|-- AGENTS.md
|-- frontend/
|-- backend/
|-- tests/
|-- compose.yml
|-- data/
|   `-- openapi.json 또는 루트 openapi.json을 참조하는 계약 문서
`-- .github/
```

- `frontend/`: React + TypeScript 애플리케이션
- `backend/`: Python API 애플리케이션
- `tests/`: E2E 또는 교차 계층 테스트
- `compose.yml` 또는 `docker-compose.yml`: 로컬 통합 실행 구성

구현이 실제로 다른 경로를 사용하면, 추측으로 유지하지 말고 실제 경로로 이 문서를 수정합니다.

## 기술 스택 기준

이 워크숍의 구현 단계와 CI 설정을 기준으로 다음 스택을 기본값으로 간주합니다.

| 영역 | 기본 기준 |
| --- | --- |
| 프론트엔드 | React, TypeScript, npm, Node.js 24 |
| 백엔드 | Python 3.12, `pyproject.toml` 기반 패키징, `pip install -e ".[dev]"` |
| 계약 | `openapi.json`에 정의된 NEIS Open API 계약 |
| 자동화 | GitHub Actions (`.github/workflows/ci.yml`) |
| 배포 | Azure Developer CLI (`azd`) |
| 컨테이너 | Docker Compose |

프론트엔드 UI 프레임워크, 상태관리, 테스트 러너, 포맷터, 린터는 실제 구현에 맞춰 명시적으로 적어야 합니다. 예: Fluent UI, Vitest, Playwright, ESLint, Prettier, Ruff, pytest.

## 필수 구현 원칙

### API 및 데이터 계약

- 프론트엔드는 **NEIS Open API를 직접 호출하지 않습니다**. 모든 외부 API 호출은 백엔드를 통해 중계합니다.
- 백엔드의 요청/응답 모델과 파라미터는 `openapi.json` 계약을 따라야 합니다.
- 계약을 확장하거나 변환하더라도, 원본 필드 의미를 임의로 바꾸지 않습니다.
- 샘플 데이터나 목 데이터를 추가할 때도 `openapi.json`의 필드 구조와 제약을 유지합니다.

### 비밀 정보 및 설정

- API 키, 토큰, 연결 문자열은 코드에 하드코딩하지 않습니다.
- `.env.example`에는 필요한 환경 변수 이름만 두고, 실제 값은 `.env` 또는 배포 환경 변수로 주입합니다.
- 로그, 테스트 fixture, 스크린샷, PR 본문에 비밀 정보를 남기지 않습니다.

### 생성 파일 및 원본 자료

- `openapi.json`은 생성 산출물로 취급합니다. 수동 수정이 필요하면 먼저 생성 원본과 생성 절차를 검토합니다.
- `data/` 아래의 원본 Excel 파일은 참조용 원본이므로 임의 수정하지 않습니다.
- GitHub Actions 또는 `azd`가 생성한 파일도 직접 덮어쓰기 전에 생성 규칙과 워크숍 문맥을 확인합니다.

## 작업 절차

### 의존성 설치

실제 구현 후에는 아래 명령을 우선 기준으로 사용합니다.

```bash
# frontend
cd frontend
npm ci

# backend
cd backend
python -m pip install -e ".[dev]"
```

패키지 관리자가 다르면 문서와 CI를 함께 갱신합니다. 예를 들어 `pnpm`이나 `uv`를 도입했다면 명령, 캐시, 락파일 기준을 모두 맞춰야 합니다.

### 로컬 개발

```bash
# frontend dev server
cd frontend
npm run dev

# backend dev server
cd backend
python -m uvicorn app.main:app --reload
```

위 명령은 템플릿 기준 예시입니다. 실제 엔트리포인트가 `src/main.tsx`, `main.py`, `app.py`, `backend/src/...` 등으로 달라지면 실행 명령을 정확히 교체합니다.

### 빌드, 포맷, 린트, 타입 검사

최소한 아래 범주의 명령이 구현되어 있어야 합니다.

```bash
# frontend
cd frontend
npm run build
npm run lint
npm run typecheck
npm run format

# backend
cd backend
python -m pytest
python -m ruff check .
python -m ruff format --check .
python -m mypy .
```

- 스크립트 이름은 실제 `package.json`과 `pyproject.toml` 기준으로 맞춥니다.
- 존재하지 않는 명령을 문서에 적지 않습니다.
- 새 도구를 도입했다면 CI와 로컬 명령을 함께 정렬합니다.

### Docker Compose

Compose 파일이 있으면 아래 명령을 기준으로 유지합니다.

```bash
docker compose up --build
docker compose down
docker compose config
```

- 파일명이 `compose.yml`, `compose.yaml`, `docker-compose.yml`, `docker-compose.yaml` 중 무엇인지 문서에 명시합니다.
- 프론트엔드와 백엔드, 필요한 경우 데이터 저장소까지 함께 부팅되도록 구성합니다.

## 테스트 가이드

앱 구현 후 아래 세 범주의 테스트 위치와 실행 명령을 반드시 문서화합니다.

| 테스트 종류 | 기본 위치 | 예시 명령 |
| --- | --- | --- |
| 프론트엔드 통합 테스트 | `frontend/src/**/*.test.ts(x)` 또는 `frontend/tests/` | `npm test` |
| 백엔드 단위/통합 테스트 | `backend/tests/` | `pytest` |
| E2E 테스트 | 루트 `tests/e2e/` 또는 `frontend/e2e/` | `npx playwright test` |

테스트 작성 원칙:

- 프론트엔드 테스트는 UI 동작과 API 계약 소비 방식을 검증하고, NEIS 실서버 직접 호출에 의존하지 않습니다.
- 백엔드 테스트는 NEIS 연동 경계에서 HTTP mocking 또는 fixture를 사용해 재현 가능하게 유지합니다.
- E2E 테스트는 사용자 시나리오 중심으로 작성하고, 불안정한 시간 의존성·외부 네트워크 의존성을 피합니다.
- 테스트 추가 시 happy path뿐 아니라 오류 응답, 빈 데이터, 날짜 범위 예외 같은 경계 조건을 포함합니다.

## CI 및 배포 규칙

- `.github/workflows/ci.yml`은 현재 `frontend/package-lock.json`, `backend/pyproject.toml`, Compose 파일 존재 여부를 기준으로 동작합니다.
- 실제 앱 구조가 준비되면 CI가 더 이상 placeholder가 아니도록 빌드, 테스트, 타입 검사 단계로 강화해야 합니다.
- Azure 배포를 추가하면 `azd up`과 GitHub Actions 배포 워크플로우 간 설정이 충돌하지 않게 유지합니다.

## 커밋 및 PR 규칙

- 한 이슈 또는 한 논리 단위만 포함하는 작은 변경으로 작업합니다.
- 코드 변경 시 관련 문서와 테스트를 같이 업데이트합니다.
- 모든 PR 본문은 예외 없이 `.github/PULL_REQUEST_TEMPLATE.md`를 복사해 각 섹션을 채운 형태로 작성합니다.
- PR 설명은 반드시 `.github/PULL_REQUEST_TEMPLATE.md`를 따르며, 섹션을 임의로 삭제하거나 무시하지 않습니다.
- PR의 Validation 섹션에는 실제로 실행한 명령만 적습니다.
- 생성된 스냅샷이나 대용량 산출물은 필요성과 재현 방법이 있을 때만 커밋합니다.

## 에이전트 작업 규칙

- 구현 코드가 없는 상태에서는 존재하지 않는 디렉터리, 명령, 도구를 완료된 것처럼 문서화하지 않습니다.
- 구현 후 이 문서를 수정할 때는 먼저 실제 파일 구조와 스크립트를 확인한 뒤 반영합니다.
- 프론트엔드, 백엔드, 테스트, Compose, CI 문서 중 하나를 바꾸면 다른 섹션과 모순이 없는지 함께 점검합니다.
- 워크숍 문서(`docs/`)의 흐름을 깨지 않는 범위에서만 보완하고, 단계별 안내와 충돌하는 독자 규칙을 추가하지 않습니다.
