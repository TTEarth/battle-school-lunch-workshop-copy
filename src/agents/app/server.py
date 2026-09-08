"""AG-UI 서버. 프론트엔드와 AG-UI 프로토콜로 통신한다.

실행: cd src/agents && python -m app.server (기본 :8002, 엔드포인트 /agent)
"""

from __future__ import annotations

from fastapi import FastAPI
from agent_framework.ag_ui import AgentFrameworkWorkflow, add_agent_framework_fastapi_endpoint

from .config import get_settings
from .workflow import build_workflow

app = FastAPI(title="급식 배틀 에이전트", version="1.0.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


_settings = get_settings()

# AG-UI 스레드마다 새 워크플로우 인스턴스를 만들어 실행 상태가 섞이지 않게 한다.
_agui_workflow = AgentFrameworkWorkflow(
    workflow_factory=lambda thread_id: build_workflow(_settings),
    name="lunch-battle-analysis",
    description="두 학교 중식 비교 평가 (Concurrent 멀티에이전트)",
)
add_agent_framework_fastapi_endpoint(app, _agui_workflow, "/agent")


def main() -> None:
    import uvicorn

    uvicorn.run(app, host=_settings.host, port=_settings.port)


if __name__ == "__main__":
    main()
