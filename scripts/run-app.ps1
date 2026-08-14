<#
.SYNOPSIS
급식 배틀 앱을 한 번에 실행합니다.

.DESCRIPTION
기본은 Docker Compose로 프론트엔드+백엔드를 함께 기동합니다.
-Local 스위치를 주면 Docker 없이 로컬 프로세스(uvicorn + vite dev)로 실행합니다.

.EXAMPLE
./scripts/run-app.ps1                # Docker Compose 실행
./scripts/run-app.ps1 -Local         # 로컬 dev 서버 실행
$env:NEIS_API_KEY="발급키"; ./scripts/run-app.ps1
#>
[CmdletBinding()]
param(
    [switch]$Local
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

if (-not $env:NEIS_API_KEY) {
    Write-Warning "NEIS_API_KEY 환경 변수가 비어 있습니다. 실제 급식 조회는 실패할 수 있습니다. (.env.example 참고)"
}

if (-not $Local) {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Error "docker를 찾을 수 없습니다. Docker를 설치하거나 -Local 스위치를 사용하세요."
    }
    Write-Host "Docker Compose로 앱을 기동합니다... (프론트: http://localhost:5173, 백엔드: http://localhost:8000)"
    docker compose up --build
    exit $LASTEXITCODE
}

Write-Host "로컬 모드로 실행합니다."

# 백엔드 의존성 설치 및 기동
Push-Location src\backend
python -m pip install --quiet fastapi "uvicorn[standard]" httpx
$backend = Start-Process python -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000" -PassThru -NoNewWindow
Pop-Location
Write-Host "백엔드 시작됨 (PID $($backend.Id)) - http://localhost:8000"

# 프론트엔드 의존성 설치 및 기동 (포그라운드)
Push-Location src\frontend
if (-not (Test-Path node_modules)) { npm install --no-audit --no-fund }
Write-Host "프론트엔드 시작 - http://localhost:5173 (Ctrl+C로 종료)"
try {
    npm run dev
}
finally {
    Pop-Location
    if (-not $backend.HasExited) {
        Stop-Process -Id $backend.Id -Force
        Write-Host "백엔드(PID $($backend.Id)) 종료됨"
    }
}
