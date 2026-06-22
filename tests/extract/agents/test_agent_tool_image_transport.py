import copy
import json
import typing

import pytest

try:
    from smolagents.models import (
        ChatMessage,
        ChatMessageToolCall,
        ChatMessageToolCallFunction,
        MessageRole,
    )
except ModuleNotFoundError:
    pytest.skip("smolagents extra is not installed", allow_module_level=True)

from groundx.extract.agents.agent import AgentTool
from groundx.extract.services.logger import Logger
from groundx.extract.settings.settings import AgentSettings


class CapturingModel:
    model_id = "capturing-model"

    def __init__(self) -> None:
        self.messages: typing.List[typing.List[typing.Any]] = []

    def generate(
        self,
        messages: typing.List[typing.Any],
        **_: typing.Any,
    ) -> ChatMessage:
        self.messages.append(copy.deepcopy(messages))
        return ChatMessage(
            role=MessageRole.ASSISTANT,
            content=None,
            tool_calls=[
                ChatMessageToolCall(
                    id="call-1",
                    type="function",
                    function=ChatMessageToolCallFunction(
                        name="final_answer",
                        arguments={"answer": {"type": {"ok": True}}},
                    ),
                )
            ],
        )


class RejectingModel:
    model_id = "rejecting-model"

    def generate(
        self,
        messages: typing.List[typing.Any],
        **_: typing.Any,
    ) -> ChatMessage:
        raise RuntimeError("provider rejected remote image URL")


def build_agent() -> typing.Tuple[AgentTool, CapturingModel]:
    agent = AgentTool(
        AgentSettings(api_key="test-key", model_id="test-model", max_steps=1),
        Logger("agent-tool-image-transport", "error"),
    )
    model = CapturingModel()
    agent.model = model  # type: ignore[assignment]
    return agent, model


def last_user_content(model: CapturingModel) -> typing.List[typing.Dict[str, typing.Any]]:
    assert model.messages
    first_call = model.messages[0]
    user_messages = [message for message in first_call if message.role == MessageRole.USER]
    assert user_messages
    content = user_messages[-1].content
    assert isinstance(content, list)
    return content


def test_agent_tool_preserves_existing_pil_image_process_path() -> None:
    image_module = pytest.importorskip("PIL.Image")
    agent, model = build_agent()
    image = image_module.new("RGB", (2, 2), "white")

    result = agent.process("read this", images=[image])

    assert result == {"ok": True}
    content = last_user_content(model)
    assert any(item.get("type") == "image" for item in content)


def test_agent_tool_remote_url_transport_uses_image_url_blocks_without_fetching() -> None:
    agent, model = build_agent()
    remote_url = "https://upload.eyelevel.ai/workflows/pages/page-1.png?sig=secret"

    result = agent.process(
        "read this",
        images=[],
        image_urls=[remote_url],
        image_transport="remote_url",
    )

    assert result == {"ok": True}
    content = last_user_content(model)
    assert {"type": "image_url", "image_url": {"url": remote_url}} in content
    assert not any(item.get("type") == "image" for item in content)
    assert "sig=secret" not in json.dumps(agent.memory.get_full_steps())


def test_agent_tool_uses_agent_settings_image_transport_default() -> None:
    agent = AgentTool(
        AgentSettings(
            api_key="test-key",
            model_id="test-model",
            max_steps=1,
            image_transport="remote_url",
        ),
        Logger("agent-tool-image-transport", "error"),
    )
    model = CapturingModel()
    agent.model = model  # type: ignore[assignment]
    remote_url = "https://upload.eyelevel.ai/workflows/pages/page-1.png"

    result = agent.process("read this", images=[], image_urls=[remote_url])

    assert result == {"ok": True}
    content = last_user_content(model)
    assert {"type": "image_url", "image_url": {"url": remote_url}} in content


def test_agent_tool_data_url_transport_keeps_inline_image_path() -> None:
    image_module = pytest.importorskip("PIL.Image")
    agent, model = build_agent()
    image = image_module.new("RGB", (2, 2), "white")

    result = agent.process("read this", images=[image], image_transport="data_url")

    assert result == {"ok": True}
    content = last_user_content(model)
    assert any(item.get("type") == "image" for item in content)
    assert not any(item.get("type") == "image_url" for item in content)


def test_agent_tool_data_url_transport_uses_inline_image_url_blocks() -> None:
    agent, model = build_agent()
    data_url = "data:image/jpeg;base64,/9j/test"

    result = agent.process(
        "read this",
        images=[],
        image_urls=[data_url],
        image_transport="data_url",
    )

    assert result == {"ok": True}
    content = last_user_content(model)
    assert {"type": "image_url", "image_url": {"url": data_url}} in content
    assert not any(item.get("type") == "image" for item in content)
    assert data_url not in json.dumps(agent.memory.get_full_steps())


def test_agent_tool_remote_url_provider_rejection_is_not_silently_retried_inline() -> None:
    agent = AgentTool(
        AgentSettings(api_key="test-key", model_id="test-model", max_steps=1),
        Logger("agent-tool-image-transport", "error"),
    )
    agent.model = RejectingModel()  # type: ignore[assignment]

    with pytest.raises(RuntimeError, match="provider rejected remote image URL"):
        agent.process(
            "read this",
            images=[],
            image_urls=["https://upload.eyelevel.ai/workflows/pages/page-1.png"],
            image_transport="remote_url",
        )


def test_agent_tool_rejects_unsupported_or_mixed_image_transports() -> None:
    agent, _ = build_agent()

    with pytest.raises(ValueError, match="unsupported image_transport"):
        agent.process("read this", images=[], image_transport="auto")

    with pytest.raises(ValueError, match="image_urls require image_transport='data_url' or 'remote_url'"):
        agent.process("read this", images=[], image_urls=["https://example.com/a.png"])

    with pytest.raises(ValueError, match="remote_url transport does not accept PIL images"):
        agent.process(
            "read this",
            images=[typing.cast(typing.Any, object())],
            image_urls=["https://example.com/a.png"],
            image_transport="remote_url",
        )
