import typing

import pytest

try:
    from smolagents import CodeAgent, ToolCallingAgent
    from smolagents.agent_types import AgentText
    from smolagents.default_tools import FinalAnswerTool
    from smolagents.models import get_tool_json_schema
except ModuleNotFoundError:
    pytest.skip("smolagents extra is not installed", allow_module_level=True)

import groundx.extract.agents.agent as agent_module
from groundx.extract.agents.agent import AgentCode, AgentTool, process_response
from groundx.extract.services.logger import Logger
from groundx.extract.settings.settings import AgentSettings


def settings(retries: int) -> AgentSettings:
    return AgentSettings(
        api_key="test-key",
        model_id="test-model",
        max_steps=1,
        response_parse_max_retries=retries,
        imports=[],
    )


def test_prompt_suffix_matches_final_answer_tool_schema() -> None:
    schema = get_tool_json_schema(FinalAnswerTool())

    assert schema["function"]["parameters"] == {
        "type": "object",
        "properties": {
            "answer": {
                "type": "string",
                "description": "The final answer to the problem",
            }
        },
        "required": ["answer"],
    }
    assert agent_module.prompt_suffix == (
        "\nReturn exactly one `final_answer` tool call with exactly one argument named `answer`. "
        "The `answer` value must be a JSON string containing the requested JSON object. Do not include "
        'any other arguments. Example: {"answer":"{\\"field\\":null}"}\n'
    )


def test_process_response_validates_unwrapped_native_and_json_envelopes() -> None:
    for response in [
        {"answer": {"type": ["private value"]}},
        '{"answer":{"type":["private value"]}}',
        [{"answer": {"type": ["private value"]}}],
    ]:
        with pytest.raises(TypeError) as exc:
            process_response(response, dict)
        assert "expected type(s)" in str(exc.value)
        assert "private value" not in str(exc.value)


def test_process_response_preserves_an_exact_list_union_member() -> None:
    response = [{"answer": {"type": {"ok": True}}}]

    assert process_response(response, (dict, list)) == response


def test_process_response_parses_agent_text_string_subclass() -> None:
    response = AgentText('{"answer":{"type":{"ok":true}}}')

    assert process_response(response, dict) == {"ok": True}


def test_agent_tool_retries_one_parser_failure_without_ordinary_output(
    monkeypatch,
    capsys,
    caplog,
) -> None:
    responses = iter(["{private malformed", '{"answer":{"type":{"ok":true}}}'])
    calls = 0
    events: typing.List[typing.Dict[str, typing.Any]] = []

    def fake_run(self: typing.Any, task: str, images: typing.List[typing.Any]) -> str:
        nonlocal calls
        calls += 1
        return next(responses)

    monkeypatch.setattr(ToolCallingAgent, "run", fake_run)
    agent = AgentTool(settings(1), Logger("agent-retry-safe", "debug"))

    assert agent.process("parse", images=[], trace_callback=events.append) == {"ok": True}
    assert calls == 2
    assert [(event["event"], event["attempt"]) for event in events] == [
        ("prompt", 0),
        ("raw_response", 0),
        ("parse_error", 0),
        ("prompt", 1),
        ("raw_response", 1),
        ("parsed_response", 1),
    ]
    assert events[2]["raw_response"] == "{private malformed"
    captured = capsys.readouterr()
    ordinary_output = captured.out + captured.err + caplog.text
    assert "private malformed" not in ordinary_output
    assert "Traceback" not in ordinary_output


def test_agent_tool_parser_exhaustion_is_terminal_and_content_free(
    monkeypatch,
    capsys,
    caplog,
) -> None:
    calls = 0
    events: typing.List[typing.Dict[str, typing.Any]] = []

    def fake_run(self: typing.Any, task: str, images: typing.List[typing.Any]) -> str:
        nonlocal calls
        calls += 1
        return "{private malformed"

    monkeypatch.setattr(ToolCallingAgent, "run", fake_run)
    agent = AgentTool(settings(1), Logger("agent-exhaustion-safe", "debug"))

    with pytest.raises(TypeError) as exc:
        agent.process("parse", images=[], trace_callback=events.append)

    assert calls == 2
    assert "expected type(s)" in str(exc.value)
    assert "private malformed" not in str(exc.value)
    assert [event["event"] for event in events].count("parse_error") == 2
    assert events[-1]["raw_response"] == "{private malformed"
    captured = capsys.readouterr()
    ordinary_output = captured.out + captured.err + caplog.text
    assert "private malformed" not in ordinary_output
    assert "Traceback" not in ordinary_output


def test_agent_tool_does_not_retry_transport_or_unowned_type_errors(monkeypatch) -> None:
    calls = 0

    def transport_failure(self: typing.Any, task: str, images: typing.List[typing.Any]) -> str:
        nonlocal calls
        calls += 1
        raise RuntimeError("transport unavailable")

    monkeypatch.setattr(ToolCallingAgent, "run", transport_failure)
    agent = AgentTool(settings(1), Logger("agent-transport-owner", "error"))
    with pytest.raises(RuntimeError, match="transport unavailable"):
        agent.process("parse", images=[])
    assert calls == 1

    monkeypatch.setattr(ToolCallingAgent, "run", lambda *_args, **_kwargs: "{}")
    monkeypatch.setattr(
        agent_module,
        "process_response",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(TypeError("downstream type error")),
    )
    with pytest.raises(TypeError, match="downstream type error"):
        agent.process("parse", images=[])


def test_agent_code_parser_exhaustion_is_content_free(monkeypatch) -> None:
    calls = 0

    def fake_run(self: typing.Any, *args: typing.Any, **kwargs: typing.Any) -> str:
        nonlocal calls
        calls += 1
        return "{private malformed"

    monkeypatch.setattr(CodeAgent, "run", fake_run)
    agent = AgentCode(settings(1), Logger("agent-code-safe", "debug"))

    with pytest.raises(TypeError) as exc:
        agent.process("parse", images=[])

    assert calls == 2
    assert "expected type(s)" in str(exc.value)
    assert "private malformed" not in str(exc.value)
