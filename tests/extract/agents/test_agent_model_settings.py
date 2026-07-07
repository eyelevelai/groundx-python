import types
import typing

import pytest

try:
    from groundx.extract.agents import agent as agent_module
    from groundx.extract.agents.agent import AgentCode, AgentTool
except ModuleNotFoundError:
    pytest.skip("smolagents extra is not installed", allow_module_level=True)

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
