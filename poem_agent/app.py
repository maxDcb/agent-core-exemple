from __future__ import annotations

import json
import os
from pathlib import Path
from uuid import uuid4

from agent_core import (
    AgentRunResult,
    AgentRunService,
    CoreSettings,
    JsonFileRunStore,
    RunContext,
    RunStore,
    StructuredOutputContract,
    StructuredTaskSpec,
)
from agent_core.spi import BaseLLMProvider, LLMProviderError, PolicyEngine, ToolRegistry, build_provider
from pydantic import BaseModel, ConfigDict, Field

from poem_agent.tools import ReadWorkspaceFileTool, validate_workspace_read


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = PROJECT_ROOT / "workspace"


class PoemResponse(BaseModel):
    """The JSON mode is intentionally tiny: {"poem": "..."}."""

    model_config = ConfigDict(extra="forbid")

    poem: str = Field(description="The final poem content.")


def build_settings() -> CoreSettings:
    return CoreSettings(
        llm_provider=os.getenv("LLM_PROVIDER", "openai"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        azure_openai_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview"),
        azure_anthropic_endpoint=os.getenv("AZURE_ANTHROPIC_ENDPOINT"),
        azure_anthropic_api_key=os.getenv("AZURE_ANTHROPIC_API_KEY"),
        azure_anthropic_api_version=os.getenv("AZURE_ANTHROPIC_API_VERSION"),
        azure_anthropic_version=os.getenv("AZURE_ANTHROPIC_VERSION"),
        model=os.getenv("AGENT_CORE_MODEL") or os.getenv("AGENT_MODEL", "gpt-4.1-mini"),
        temperature=float(os.getenv("AGENT_TEMPERATURE", "0.7")),
        session_file=PROJECT_ROOT / "sessions" / "session.json",
        allowed_read_roots=[WORKSPACE],
        base_system_prompt=(
            "You are a small poetry agent. Use tools only when useful. "
            "When writing, combine the user's request with observed file content."
        ),
    )


def build_run_service(
    *,
    settings: CoreSettings | None = None,
    provider: BaseLLMProvider | None = None,
    run_store: RunStore | None = None,
) -> AgentRunService:
    settings = settings or build_settings()
    registry = ToolRegistry()
    registry.register(ReadWorkspaceFileTool())

    policy = PolicyEngine(validators={"read_workspace_file": validate_workspace_read})
    return AgentRunService(
        settings=settings,
        provider=provider or build_provider(settings),
        tool_registry=registry,
        policy_engine=policy,
        run_store=run_store or JsonFileRunStore(PROJECT_ROOT / "sessions" / "agent-runs"),
    )


def build_spec(user_input: str, *, json_mode: bool) -> StructuredTaskSpec:
    contract = None
    if json_mode:
        contract = StructuredOutputContract(
            name="poem_response",
            schema=PoemResponse.model_json_schema(),
            strict=True,
            instructions=["Return exactly one object with a poem string."],
        )

    return StructuredTaskSpec(
        task_id="write_workspace_poem",
        system_prompt=(
            "Before writing, call read_workspace_file with path 'theme.txt'. "
            "Use the file theme as inspiration, not as text to quote directly."
        ),
        objective=f"Write a short poem for this user request: {user_input}",
        constraints=[
            "Read only the committed workspace theme file.",
            "Keep the poem under 12 lines.",
            "Do not mention implementation details.",
        ],
        allowed_tools=["read_workspace_file"],
        output_contract=contract,
        max_tool_calls=1,
        max_iterations=3,
    )


def execute_poem(
    user_input: str,
    *,
    json_mode: bool = False,
    service: AgentRunService | None = None,
    run_id: str | None = None,
) -> AgentRunResult:
    service = service or build_run_service()
    resolved_run_id = run_id or f"poem-{uuid4().hex}"
    return service.execute(
        spec=build_spec(user_input, json_mode=json_mode),
        context=RunContext(
            namespace_id="poem-agent",
            run_id=resolved_run_id,
            application_context={"workspace": str(WORKSPACE)},
        ),
        run_id=resolved_run_id,
    )


def render_poem(result: AgentRunResult, *, json_mode: bool) -> str:
    if not result.ok:
        raise RuntimeError(result.failure_reason or result.raw_content or "agent-core run failed")

    if not json_mode:
        return result.raw_content.strip()

    poem = PoemResponse.model_validate(result.output)
    return poem.model_dump_json(indent=2)


def run_poem(user_input: str, *, json_mode: bool = False) -> str:
    result = execute_poem(user_input, json_mode=json_mode)
    return render_poem(result, json_mode=json_mode)


def run_cli(user_input: str, *, json_mode: bool, show_usage: bool = False) -> int:
    try:
        result = execute_poem(user_input, json_mode=json_mode)
        print(render_poem(result, json_mode=json_mode))
        if show_usage:
            print(json.dumps(result.to_dict()["usage"], indent=2))
    except LLMProviderError as exc:
        print(exc.user_message)
        return 2
    except Exception as exc:
        print(f"Error: {exc}")
        return 1
    return 0
