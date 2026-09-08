"""에이전트 앱 설정. 환경 변수로 MCP 서버, LLM 백엔드, 서버 포트를 주입한다."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    mcp_url: str
    llm_backend: str  # "copilot"(GitHub Copilot SDK) | "github-models"(OpenAI 호환 폴백)
    github_token: str
    github_models_base_url: str
    github_models_model: str
    copilot_model: str
    host: str
    port: int


def get_settings() -> Settings:
    return Settings(
        mcp_url=os.environ.get("MCP_URL", "http://localhost:8001/mcp"),
        llm_backend=os.environ.get("AGENT_LLM_BACKEND", "copilot"),
        github_token=os.environ.get("GITHUB_TOKEN", ""),
        github_models_base_url=os.environ.get(
            "GITHUB_MODELS_BASE_URL", "https://models.github.ai/inference"
        ),
        github_models_model=os.environ.get("GITHUB_MODELS_MODEL", "openai/gpt-4.1-mini"),
        copilot_model=os.environ.get("GITHUB_COPILOT_MODEL", ""),
        host=os.environ.get("AGENT_HOST", "0.0.0.0"),
        port=int(os.environ.get("AGENT_PORT", "8002")),
    )
