from __future__ import annotations

from agent_core import CoreSettings, JsonFileRunStore
from agent_core.spi import LLMCompletionResult, LLMMessage, LLMTokenUsage, LLMToolCall

from poem_agent.app import WORKSPACE, build_run_service, execute_poem, render_poem


class PoemProvider:
    def __init__(self) -> None:
        self.calls = 0

    def complete_text(self, *, messages, model, temperature, options=None) -> LLMCompletionResult:
        _ = (messages, model, temperature, options)
        return LLMCompletionResult(content="unused")

    def complete_with_tools(self, *, messages, tools, model, temperature, options=None) -> LLMCompletionResult:
        _ = (tools, temperature, options)
        self.calls += 1
        assert all(isinstance(message, LLMMessage) for message in messages)
        if self.calls == 1:
            return LLMCompletionResult(
                content="",
                tool_calls=[
                    LLMToolCall(
                        id="read-theme-1",
                        name="read_workspace_file",
                        arguments_json='{"path":"theme.txt"}',
                    )
                ],
                usage=LLMTokenUsage(input_tokens=20, output_tokens=5, total_tokens=25),
                provider="test",
                model=model,
            )
        assert any(message.role == "tool" and "lighthouse" in message.content.lower() for message in messages)
        if options is not None and options.response_format:
            return LLMCompletionResult(
                content='{"poem":"Salt light turns through patient fog"}',
                usage=LLMTokenUsage(input_tokens=35, output_tokens=7, total_tokens=42),
                provider="test",
                model=model,
            )
        return LLMCompletionResult(
            content="Old circuits hum\nPatience outlives the storm",
            usage=LLMTokenUsage(input_tokens=30, output_tokens=8, total_tokens=38),
            provider="test",
            model=model,
        )


def test_poem_example_runs_as_a_persisted_agent_core_run(tmp_path) -> None:
    provider = PoemProvider()
    settings = CoreSettings(
        model="test-model",
        session_file=tmp_path / "session.json",
        allowed_read_roots=[WORKSPACE],
    )
    store = JsonFileRunStore(tmp_path / "runs")
    service = build_run_service(settings=settings, provider=provider, run_store=store)

    result = execute_poem(
        "Write about patience",
        service=service,
        run_id="poem-test",
    )

    assert render_poem(result, json_mode=False).startswith("Old circuits hum")
    assert result.to_dict()["usage"] == {
        "call_count": 2,
        "calls_with_token_usage": 2,
        "token_usage_complete": True,
        "input_tokens": 50,
        "output_tokens": 13,
        "total_tokens": 63,
        "reported_input_tokens": 50,
        "reported_output_tokens": 13,
    }
    persisted = store.load(namespace_id="poem-agent", run_id="poem-test")
    assert persisted is not None
    assert persisted.status == "completed"
    assert persisted.result is not None
    assert len(persisted.result.llm_calls) == 2


def test_poem_example_supports_locally_validated_json_output(tmp_path) -> None:
    provider = PoemProvider()
    settings = CoreSettings(
        model="test-model",
        session_file=tmp_path / "session.json",
        allowed_read_roots=[WORKSPACE],
    )
    service = build_run_service(
        settings=settings,
        provider=provider,
        run_store=JsonFileRunStore(tmp_path / "runs"),
    )

    result = execute_poem(
        "Write a JSON poem",
        json_mode=True,
        service=service,
        run_id="poem-json",
    )

    assert result.ok is True
    assert '"poem": "Salt light turns through patient fog"' in render_poem(result, json_mode=True)
    assert result.to_dict()["usage"]["call_count"] == 3
