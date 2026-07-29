import types
import typing

import pytest

try:
    from groundx.extract.agents import agent as agent_module
    from groundx.extract.agents.agent import AgentCode, AgentTool
except ModuleNotFoundError:
    pytest.skip("smolagents extra is not installed", allow_module_level=True)

from groundx.extract.services.deadline import operation_deadline
from groundx.extract.services.logger import Logger
from groundx.extract.settings.settings import AgentSettings


class CapturingOpenAIModel:
    calls: typing.List[typing.Dict[str, typing.Any]] = []

    def __init__(self, **kwargs: typing.Any) -> None:
        self.kwargs = kwargs
        CapturingOpenAIModel.calls.append(kwargs)


def patch_agent_constructors(monkeypatch: pytest.MonkeyPatch) -> None:
    CapturingOpenAIModel.calls = []
    monkeypatch.setattr(agent_module, "OpenAIServerModel", CapturingOpenAIModel)

    def init_tool_agent(self: typing.Any, **kwargs: typing.Any) -> None:
        self.model = kwargs["model"]

    def init_code_agent(self: typing.Any, **kwargs: typing.Any) -> None:
        self.model = kwargs["model"]
        self.python_executor = types.SimpleNamespace(static_tools=None)

    monkeypatch.setattr(agent_module.ToolCallingAgent, "__init__", init_tool_agent)
    monkeypatch.setattr(agent_module.CodeAgent, "__init__", init_code_agent)


def test_agent_tool_uses_current_default_model_without_reasoning_effort(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    patch_agent_constructors(monkeypatch)

    AgentTool(
        AgentSettings(api_key="test-key"),
        Logger("agent-tool-model-settings", "error"),
    )

    assert CapturingOpenAIModel.calls[-1]["model_id"] == "gpt-5.4-mini"
    assert "reasoning_effort" not in CapturingOpenAIModel.calls[-1]


def test_agent_code_omits_reasoning_effort_when_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    patch_agent_constructors(monkeypatch)

    AgentCode(
        AgentSettings(api_key="test-key", reasoning_effort=None),
        Logger("agent-code-model-settings", "error"),
    )

    assert CapturingOpenAIModel.calls[-1]["model_id"] == "gpt-5.4-mini"
    assert "reasoning_effort" not in CapturingOpenAIModel.calls[-1]


def test_agent_code_preserves_explicit_model_and_reasoning_overrides(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    patch_agent_constructors(monkeypatch)

    AgentCode(
        AgentSettings(
            api_key="test-key",
            model_id="gpt-5-reasoning",
            reasoning_effort="medium",
        ),
        Logger("agent-code-model-settings", "error"),
    )

    assert CapturingOpenAIModel.calls[-1]["model_id"] == "gpt-5-reasoning"
    assert CapturingOpenAIModel.calls[-1]["reasoning_effort"] == "medium"


def test_agent_model_client_uses_remaining_shared_deadline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from groundx.extract.agents.agent import _DeadlineOpenAIClient

    calls: typing.List[typing.Dict[str, typing.Any]] = []

    class Completions:
        def create(self, **kwargs: typing.Any) -> str:
            calls.append(kwargs)
            return "ok"

    class Client:
        def __init__(self) -> None:
            self.chat = types.SimpleNamespace(completions=Completions())

        def with_options(self, **options: typing.Any) -> "Client":
            calls.append(options)
            return self

    client = _DeadlineOpenAIClient(Client())

    with operation_deadline(9):
        result = client.chat.completions.create(model="test")

    assert result == "ok"
    assert calls[0]["max_retries"] == 0
    assert 0 < calls[0]["timeout"] <= 9
    assert calls[1] == {"model": "test"}
