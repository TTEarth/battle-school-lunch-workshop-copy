"""Concurrent(팬아웃-팬인) 멀티에이전트 워크플로우.

토폴로지:
    dispatcher ─┬─> nutrition-agent ──┐
                ├─> diversity-agent ──┤
                ├─> quality-agent ────┼─> aggregator(채점 환산 + judge-agent 총평)
                └─> satisfaction-agent┘

- dispatcher: 프롬프트에서 분석 설정을 파싱하고 MCP 서버에서 두 학교의 중식
  데이터를 가져와 4개 영역 에이전트에 동일 입력을 팬아웃한다.
- 영역 에이전트: EVALUATION_RUBRIC.md 의 영역 하나씩을 전담해 1~5점 채점.
- aggregator: 영역 결과를 팬인해 채점 공식으로 총점을 결정적으로 환산하고,
  judge-agent 가 총평을 작성한 뒤 최종 JSON 결과를 출력한다.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from typing import Any, Protocol

from agent_framework import (
    AgentExecutor,
    AgentExecutorRequest,
    AgentExecutorResponse,
    Executor,
    Message,
    Workflow,
    WorkflowBuilder,
    WorkflowContext,
    handler,
)

from .config import Settings, get_settings
from .llm import create_agent
from .meal_source import MealDataError, fetch_lunch_meals
from .request_parser import RequestParseError, parse_analysis_request
from .rubric import JUDGE_INSTRUCTIONS, RUBRIC_AREAS, area_instructions
from .schemas import (
    AnalysisRequest,
    AnalysisResult,
    AreaEvaluation,
    SchoolResult,
)
from .scoring import compute_results, decide_winner


class SupportsRun(Protocol):
    async def run(self, prompt: str) -> Any: ...


def _error_json(message: str) -> str:
    return json.dumps(
        {"type": "analysis_error", "message": message}, ensure_ascii=False
    )


def build_evaluation_input(
    request: AnalysisRequest,
    meals: dict[str, list[dict[str, Any]]],
    free_text: str,
) -> str:
    """영역 에이전트에 전달할 공통 입력 텍스트를 구성한다."""
    lines = [
        f"비교 날짜: {request.date}",
        "아래 두 학교의 같은 날짜 중식 데이터를 담당 영역 기준으로 평가하세요.",
    ]
    for school in request.schools:
        data = meals.get(school.school_code, [])
        lines.append(
            f"\n[학교] {school.school_name} (school_code={school.school_code})\n"
            f"급식 데이터(JSON): {json.dumps(data, ensure_ascii=False)}"
        )
    if free_text:
        lines.append(f"\n사용자 요청 사항: {free_text}")
    return "\n".join(lines)


class Dispatcher(Executor):
    """분석 설정 파싱 + MCP 급식 조회 후 영역 에이전트로 팬아웃."""

    def __init__(self, settings: Settings, *, id: str = "dispatcher") -> None:
        super().__init__(id=id)
        self._settings = settings
        self.request: AnalysisRequest | None = None
        self.free_text: str = ""

    @handler
    async def dispatch(
        self,
        prompt: str,
        ctx: WorkflowContext[AgentExecutorRequest, str],
    ) -> None:
        await self._dispatch(prompt, ctx)

    @handler
    async def dispatch_messages(
        self,
        messages: list[Message],
        ctx: WorkflowContext[AgentExecutorRequest, str],
    ) -> None:
        """AG-UI 는 대화 메시지 목록을 입력으로 전달한다. 마지막 사용자 메시지를 사용한다."""
        prompt = ""
        for message in reversed(messages):
            if getattr(message, "role", None) == "user" and message.text:
                prompt = message.text
                break
        await self._dispatch(prompt, ctx)

    async def _dispatch(
        self,
        prompt: str,
        ctx: WorkflowContext[AgentExecutorRequest, str],
    ) -> None:
        try:
            request, free_text = parse_analysis_request(prompt)
        except RequestParseError as exc:
            await ctx.yield_output(_error_json(exc.message))
            return

        meals: dict[str, list[dict[str, Any]]] = {}
        for school in request.schools:
            try:
                data = await fetch_lunch_meals(
                    self._settings.mcp_url, school, request.date
                )
            except MealDataError as exc:
                await ctx.yield_output(_error_json(exc.message))
                return
            if not data:
                # 한 학교라도 해당 날짜 중식 데이터가 없으면 비교를 중단한다.
                await ctx.yield_output(
                    _error_json(
                        f"{school.school_name}의 {request.date} 중식 데이터가 없어 "
                        "비교 평가를 중단합니다. 다른 날짜를 선택해 주세요."
                    )
                )
                return
            meals[school.school_code] = data

        self.request = request
        self.free_text = free_text
        text = build_evaluation_input(request, meals, free_text)
        await ctx.send_message(
            AgentExecutorRequest(messages=[Message("user", [text])], should_respond=True)
        )


def parse_area_response(area_id: str, text: str) -> AreaEvaluation:
    """영역 에이전트의 JSON 응답을 파싱한다. 실패 시 채점 불가로 강등한다."""
    candidate = text.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", candidate, re.DOTALL)
    if fenced:
        candidate = fenced.group(1)
    else:
        start, end = candidate.find("{"), candidate.rfind("}")
        if start >= 0 and end > start:
            candidate = candidate[start : end + 1]
    try:
        payload = json.loads(candidate)
        return AreaEvaluation.model_validate({"area_id": area_id, **payload})
    except Exception:
        return AreaEvaluation(
            area_id=area_id,
            not_scorable=True,
            not_scorable_reason="에이전트 응답을 해석하지 못해 채점에서 제외했습니다.",
        )


def build_judge_prompt(
    request: AnalysisRequest,
    results: list[SchoolResult],
    excluded: list[str],
    winner_code: str | None,
    is_tie: bool,
) -> str:
    scoreboard = [r.model_dump() for r in results]
    verdict_line = (
        "동점"
        if is_tie
        else next(r.school_name for r in results if r.school_code == winner_code)
        + " 승리"
    )
    return (
        f"비교 날짜: {request.date}\n"
        f"영역별 채점과 애플리케이션이 환산한 총점: {json.dumps(scoreboard, ensure_ascii=False)}\n"
        f"채점 불가로 제외된 영역 id: {excluded}\n"
        f"총점 기준 판정: {verdict_line}\n"
        "위 결과를 검증하고 한국어 총평을 작성하세요."
    )


class Aggregator(Executor):
    """영역 결과 팬인 → 결정적 채점 환산 → judge-agent 총평 → 최종 JSON 출력."""

    def __init__(
        self,
        dispatcher: Dispatcher,
        judge: SupportsRun,
        *,
        id: str = "judge-aggregator",
    ) -> None:
        super().__init__(id=id)
        self._dispatcher = dispatcher
        self._judge = judge

    @handler
    async def aggregate(
        self,
        responses: list[AgentExecutorResponse],
        ctx: WorkflowContext[Any, str],
    ) -> None:
        request = self._dispatcher.request
        if request is None:  # 방어적 검사: dispatcher 가 정상 종료된 경우 도달 불가
            await ctx.yield_output(_error_json("분석 설정이 초기화되지 않았습니다."))
            return

        evaluations = [
            parse_area_response(resp.executor_id, resp.agent_response.text)
            for resp in responses
        ]
        try:
            results, excluded = compute_results(list(request.schools), evaluations)
            winner_code, is_tie = decide_winner(results)
        except ValueError as exc:
            await ctx.yield_output(_error_json(str(exc)))
            return

        judge_prompt = build_judge_prompt(request, results, excluded, winner_code, is_tie)
        judge_response = await self._judge.run(judge_prompt)
        verdict = getattr(judge_response, "text", str(judge_response))

        result = AnalysisResult(
            date=request.date,
            schools=results,
            winner_school_code=winner_code,
            is_tie=is_tie,
            excluded_areas=excluded,
            verdict=verdict,
        )
        await ctx.yield_output(result.model_dump_json())


AgentFactory = Callable[[Settings, str, str], Any]


def _default_agent_factory(settings: Settings, name: str, instructions: str) -> Any:
    return create_agent(settings, name=name, instructions=instructions)


def build_workflow(
    settings: Settings | None = None,
    agent_factory: AgentFactory | None = None,
) -> Workflow:
    """Concurrent 패턴 워크플로우를 구성한다.

    Args:
        settings: 앱 설정 (기본: 환경 변수 기반)
        agent_factory: (settings, name, instructions) -> 에이전트. 테스트 주입용.
    """
    settings = settings or get_settings()
    factory = agent_factory or _default_agent_factory
    dispatcher = Dispatcher(settings)
    area_executors = [
        AgentExecutor(
            factory(settings, area.agent_name, area_instructions(area)),
            id=area.id,
        )
        for area in RUBRIC_AREAS
    ]
    judge = factory(settings, "judge-agent", JUDGE_INSTRUCTIONS)
    aggregator = Aggregator(dispatcher, judge)
    return (
        WorkflowBuilder(
            name="lunch-battle-analysis",
            description="두 학교 중식을 EVALUATION_RUBRIC.md 기준으로 비교 평가하는 Concurrent 워크플로우",
            start_executor=dispatcher,
        )
        .add_fan_out_edges(dispatcher, area_executors)
        .add_fan_in_edges(area_executors, aggregator)
        .build()
    )
