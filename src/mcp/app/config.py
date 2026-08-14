"""MCP 서버 설정. 환경 변수로 외부 API 접근 및 서버 바인딩 설정을 주입한다."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    neis_base_url: str
    neis_api_key: str
    request_timeout: float
    host: str
    port: int


def get_settings() -> Settings:
    return Settings(
        neis_base_url=os.environ.get("NEIS_BASE_URL", "https://open.neis.go.kr"),
        neis_api_key=os.environ.get("NEIS_API_KEY", ""),
        request_timeout=float(os.environ.get("NEIS_TIMEOUT_SECONDS", "10")),
        host=os.environ.get("MCP_HOST", "0.0.0.0"),
        port=int(os.environ.get("MCP_PORT", "8001")),
    )
