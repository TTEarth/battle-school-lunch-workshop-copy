"""LLM 백엔드 팩토리.

이슈 요구에 따라 Microsoft Foundry 대신 GitHub Copilot SDK 를 기본 백엔드로
채택했다(AGENT_LLM_BACKEND=copilot). Copilot CLI 를 사용할 수 없는 환경을 위해
GitHub Models(OpenAI 호환) 폴백(github-models)을 제공한다.
"""

from __future__ import annotations

from typing import Any

from .config import Settings


def create_agent(settings: Settings, *, name: str, instructions: str) -> Any:
    """설정된 백엔드로 MAF 에이전트를 생성한다."""
    if settings.llm_backend == "copilot":
        from agent_framework.github import GitHubCopilotAgent, GitHubCopilotOptions

        options = (
            GitHubCopilotOptions(model=settings.copilot_model)
            if settings.copilot_model
            else None
        )
        return GitHubCopilotAgent(
            instructions=instructions,
            name=name,
            default_options=options,
        )
    if settings.llm_backend == "github-models":
        from agent_framework import Agent
        from agent_framework.openai import OpenAIChatCompletionClient

        client = OpenAIChatCompletionClient(
            api_key=settings.github_token,
            base_url=settings.github_models_base_url,
            model=settings.github_models_model,
        )
        return Agent(client=client, instructions=instructions, name=name)
    raise ValueError(
        f"지원하지 않는 LLM 백엔드: {settings.llm_backend} (copilot | github-models)"
    )
