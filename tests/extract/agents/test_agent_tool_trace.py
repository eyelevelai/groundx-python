import typing

import pytest

try:
    from smolagents import ToolCallingAgent
except ModuleNotFoundError:
    pytest.skip("smolagents extra is not installed", allow_module_level=True)

from groundx.extract.agents.agent import AgentTool, prompt_suffix
from groundx.extract.services.logger import Logger
from groundx.extract.settings.settings import AgentSettings


def _agent() -> AgentTool:
    return AgentTool(
        AgentSettings(api_key="test-key", model_id="test-model", max_steps=1),
        Logger("agent-tool-trace", "error"),
    )


def test_agent_tool_trace_callback_records_exact_prompt_raw_and_parsed_response(
    monkeypatch,
) -> None:
    events: typing.List[typing.Dict[str, typing.Any]] = []

    def fake_run(
        self: typing.Any,
        task: str,
        images: typing.List[typing.Any],
    ) -> str:
        assert images == []
        return '{"answer": {"type": {"ok": true}}}'

    monkeypatch.setattr(ToolCallingAgent, "run", fake_run)

    result = _agent().process(
        "trace me",
        images=[],
        type="qa_statement",
        trace_callback=events.append,
    )

    assert result == {"ok": True}
    assert events == [
        {
            "attempt": 0,
            "event": "prompt",
            "image_transport": "pil",
            "prompt": "trace me" + prompt_suffix,
            "request_type": "qa_statement",
        },
        {
            "attempt": 0,
            "event": "raw_response",
            "image_transport": "pil",
            "request_type": "qa_statement",
            "value": '{"answer": {"type": {"ok": true}}}',
        },
        {
            "attempt": 0,
            "event": "parsed_response",
            "image_transport": "pil",
            "request_type": "qa_statement",
            "value": {"ok": True},
        },
    ]


def test_agent_tool_trace_callback_records_parse_error(monkeypatch) -> None:
    events: typing.List[typing.Dict[str, typing.Any]] = []

    def fake_run(
        self: typing.Any,
        task: str,
        images: typing.List[typing.Any],
    ) -> str:
        return "{not json"

    monkeypatch.setattr(ToolCallingAgent, "run", fake_run)

    with pytest.raises(TypeError, match="agent process result is not of expected type"):
        _agent().process(
            "bad json",
            images=[],
            attempt=3,
            type="qa_statement",
            trace_callback=events.append,
        )

    assert events[0]["event"] == "prompt"
    assert events[0]["prompt"] == "bad json" + prompt_suffix
    assert events[1] == {
        "attempt": 3,
        "event": "raw_response",
        "image_transport": "pil",
        "request_type": "qa_statement",
        "value": "{not json",
    }
    assert events[2]["event"] == "parse_error"
    assert events[2]["attempt"] == 3
    assert events[2]["image_transport"] == "pil"
    assert events[2]["request_type"] == "qa_statement"
    assert events[2]["raw_response"] == "{not json"
    assert events[2]["error_type"] == "JSONDecodeError"
