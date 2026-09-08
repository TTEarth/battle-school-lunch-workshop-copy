"""DevUI 실행 진입점. 멀티에이전트 워크플로우를 시각적으로 확인한다.

실행: cd src/agents && python -m app.devui  (기본 http://localhost:8090)
"""

from __future__ import annotations

import os

from agent_framework.devui import serve

from .config import get_settings
from .workflow import build_workflow


def main() -> None:
    port = int(os.environ.get("DEVUI_PORT", "8090"))
    workflow = build_workflow(get_settings())
    serve(entities=[workflow], port=port, auto_open=False)


if __name__ == "__main__":
    main()
