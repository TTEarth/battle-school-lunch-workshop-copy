"""공용 테스트 도우미: 가짜 채팅 클라이언트/에이전트 팩토리."""

from __future__ import annotations

import json

from agent_framework import Agent, Content, Message
from agent_framework._types import ChatResponse, ChatResponseUpdate, ResponseStream

from app.config import Settings

TEST_SETTINGS = Settings(
    mcp_url="http://localhost:9999/mcp",
    llm_backend="github-models",
    github_token="test-token",
    github_models_base_url="http://localhost:9999/inference",
    github_models_model="test-model",
    copilot_model="",
    host="127.0.0.1",
    port=8002,
)

SCHOOL_A = {"atpt_code": "B10", "school_code": "S1", "school_name": "가나중학교"}
SCHOOL_B = {"atpt_code": "B10", "school_code": "S2", "school_name": "다라중학교"}


def make_prompt(date: str = "2026-08-13") -> str:
    config = {"schools": [SCHOOL_A, SCHOOL_B], "date": date}
    return (
        "두 학교 급식을 비교해 주세요.\n"
        f"```json\n{json.dumps(config, ensure_ascii=False)}\n```"
    )


def area_reply(score_a: int, score_b: int) -> str:
    return json.dumps(
        {
            "not_scorable": False,
            "not_scorable_reason": None,
            "schools": [
                {"school_code": "S1", "score": score_a, "rationale": "근거 A"},
                {"school_code": "S2", "score": score_b, "rationale": "근거 B"},
            ],
        },
        ensure_ascii=False,
    )


NOT_SCORABLE_REPLY = json.dumps(
    {"not_scorable": True, "not_scorable_reason": "잔반율 데이터 없음", "schools": []},
    ensure_ascii=False,
)


class FakeChatClient:
    """항상 고정 응답을 돌려주는 SupportsChatGetResponse 구현."""

    def __init__(self, reply: str) -> None:
        self.reply = reply

    def get_response(self, messages, *, stream=False, options=None, **kwargs):
        reply = self.reply
        if not stream:

            async def _run() -> ChatResponse:
                return ChatResponse(messages=[Message("assistant", [reply])])

            return _run()

        async def gen():
            yield ChatResponseUpdate(
                contents=[Content("text", text=reply)],
                role="assistant",
                finish_reason="stop",
            )

        return ResponseStream(gen(), finalizer=ChatResponse.from_updates)


def make_agent_factory(replies: dict[str, str]):
    """에이전트 이름별 고정 응답을 돌려주는 팩토리를 만든다."""

    def factory(settings: Settings, name: str, instructions: str) -> Agent:
        return Agent(
            client=FakeChatClient(replies[name]), instructions=instructions, name=name
        )

    return factory


DEFAULT_REPLIES = {
    "nutrition-agent": area_reply(4, 5),
    "diversity-agent": area_reply(5, 3),
    "quality-agent": area_reply(3, 4),
    "satisfaction-agent": NOT_SCORABLE_REPLY,
    "judge-agent": "총점 기준 다라중학교의 우세입니다. 개선안을 제안합니다.",
}


async def fake_meals(url: str, school, date: str):
    return [
        {
            "meal_date": date,
            "meal_name": "중식",
            "dishes": ["쌀밥", "미역국", "제육볶음"],
            "calories": "800 Kcal",
        }
    ]
