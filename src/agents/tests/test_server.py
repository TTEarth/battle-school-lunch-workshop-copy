"""AG-UI 서버 통합 테스트: /agent 엔드포인트가 SSE 로 결과를 스트리밍하는지 검증한다."""

import json
from unittest.mock import patch

import httpx
from fastapi import FastAPI
from agent_framework.ag_ui import (
    AgentFrameworkWorkflow,
    add_agent_framework_fastapi_endpoint,
)

from app.workflow import build_workflow
from tests.helpers import DEFAULT_REPLIES, TEST_SETTINGS, fake_meals, make_agent_factory, make_prompt


def build_test_app() -> FastAPI:
    app = FastAPI()
    wrapper = AgentFrameworkWorkflow(
        workflow_factory=lambda thread_id: build_workflow(
            TEST_SETTINGS, agent_factory=make_agent_factory(DEFAULT_REPLIES)
        ),
        name="lunch-battle-analysis",
    )
    add_agent_framework_fastapi_endpoint(app, wrapper, "/agent")
    return app


def parse_sse_events(body: str) -> list[dict]:
    events = []
    for line in body.splitlines():
        if line.startswith("data:"):
            data = line[len("data:") :].strip()
            if data:
                events.append(json.loads(data))
    return events


async def test_agent_endpoint_streams_analysis_result() -> None:
    app = build_test_app()
    payload = {
        "threadId": "t1",
        "runId": "r1",
        "messages": [{"id": "m1", "role": "user", "content": make_prompt()}],
        "tools": [],
        "context": [],
        "state": {},
        "forwardedProps": {},
    }
    transport = httpx.ASGITransport(app=app)
    with patch("app.workflow.fetch_lunch_meals", fake_meals):
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test", timeout=60
        ) as client:
            response = await client.post(
                "/agent",
                json=payload,
                headers={"Accept": "text/event-stream"},
            )
    assert response.status_code == 200
    events = parse_sse_events(response.text)
    types = [e.get("type") for e in events]
    assert "RUN_STARTED" in types
    assert "RUN_FINISHED" in types

    text = "".join(
        e.get("delta", "") for e in events if e.get("type") == "TEXT_MESSAGE_CONTENT"
    )
    assert '"analysis_result"' in text
    start = text.find('{"type":"analysis_result"')
    result = json.loads(text[start : text.rfind("}") + 1])
    assert result["winner_school_code"] == "S2"
