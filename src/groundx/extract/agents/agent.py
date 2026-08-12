from __future__ import annotations

import json
import typing
from dataclasses import dataclass, field
from urllib.parse import urlparse

from ..services.deadline import remaining_operation_seconds
from ..services.logger import Logger
from ..settings.settings import AgentSettings
from ..utility.utility import clean_json
from smolagents import (  # pyright: ignore[reportMissingTypeStubs]
    CodeAgent,
    Tool,
    ToolCallingAgent,
)
from smolagents.memory import (  # pyright: ignore[reportMissingTypeStubs]
    FinalAnswerStep,
    SystemPromptStep,
    TaskStep,
)
from smolagents.models import (  # pyright: ignore[reportMissingTypeStubs]
    ChatMessage,
    MessageRole,
    OpenAIServerModel,
)

if typing.TYPE_CHECKING:
    from PIL.Image import Image


class _DeadlineOpenAICompletions:
    def __init__(self, client: typing.Any) -> None:
        self._client = client

    def create(self, *args: typing.Any, **kwargs: typing.Any) -> typing.Any:
        remaining = remaining_operation_seconds()
        client = self._client
        if remaining is not None:
            if remaining <= 0:
                raise TimeoutError("agent provider call exceeded task deadline")
            client = client.with_options(
                max_retries=0,
                timeout=remaining,
            )
        return client.chat.completions.create(*args, **kwargs)


class _DeadlineOpenAIChat:
    def __init__(self, client: typing.Any) -> None:
        self.completions = _DeadlineOpenAICompletions(client)


class _DeadlineOpenAIClient:
    def __init__(self, client: typing.Any) -> None:
        self._client = client
        self.chat = _DeadlineOpenAIChat(client)

    def __getattr__(self, name: str) -> typing.Any:
        return getattr(self._client, name)


def build_openai_server_model(settings: AgentSettings) -> OpenAIServerModel:
    model_kwargs: typing.Dict[str, typing.Any] = {
        "model_id": settings.model_id,
        "api_base": settings.api_base,
        "api_key": settings.get_api_key(),
    }
    if settings.reasoning_effort:
        model_kwargs["reasoning_effort"] = settings.reasoning_effort

    if settings.model_kwargs:
        model = OpenAIServerModel(**model_kwargs, **settings.model_kwargs)
    else:
        model = OpenAIServerModel(**model_kwargs)

    client = getattr(model, "client", None)
    if client is not None and not isinstance(client, _DeadlineOpenAIClient):
        model.client = _DeadlineOpenAIClient(client)
    return model


prompt_suffix = """
Return only your response using the `final_answer` tool format:

```json
{{"answer": {{"type": RESPONSE_HERE, "description": "The final answer to the problem"}}}}
```
"""

SUPPORTED_IMAGE_TRANSPORTS = {"pil", "data_url", "remote_url"}
AgentTraceCallback = typing.Callable[[typing.Dict[str, typing.Any]], None]


def _emit_agent_trace(
    log: Logger,
    trace_callback: typing.Optional[AgentTraceCallback],
    event: str,
    **payload: typing.Any,
) -> None:
    if trace_callback is None:
        return
    try:
        trace_callback({"event": event, **payload})
    except Exception as exc:
        log.debug_msg(f"agent trace callback failed: {exc.__class__.__name__}: {exc}")


@dataclass
class RemoteImageTaskStep(TaskStep):
    image_urls: typing.List[str] = field(default_factory=list)

    def to_messages(self, summary_mode: bool = False) -> typing.List[ChatMessage]:
        content: typing.List[typing.Dict[str, typing.Any]] = [{"type": "text", "text": f"New task:\n{self.task}"}]
        content.extend({"type": "image_url", "image_url": {"url": image_url}} for image_url in self.image_urls)
        return [ChatMessage(role=MessageRole.USER, content=content)]

    def dict(self) -> typing.Dict[str, typing.Any]:
        return {
            "task": self.task,
            "task_images": None,
            "image_urls": [_sanitize_image_url(image_url) for image_url in self.image_urls],
        }


def _sanitize_image_url(image_url: str) -> str:
    parsed = urlparse(image_url)
    if not parsed.scheme or not parsed.netloc:
        return "<invalid-image-url>"
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"


def extract_response(res: typing.Dict[str, typing.Any]) -> typing.Any:
    if "answer" in res and "type" in res["answer"]:
        return res["answer"]["type"]

    if "type" in res:
        return res["type"]

    return res


class _ResponseTypeError(TypeError):
    pass


def _matches_expected_type(
    value: typing.Any,
    expected_types: typing.Union[type, typing.Tuple[type, ...]],
) -> bool:
    return isinstance(value, expected_types)


def _expects_dict(expected_types: typing.Union[type, typing.Tuple[type, ...]]) -> bool:
    return isinstance({}, expected_types)


def _unwrap_response(
    value: typing.Any,
    expected_types: typing.Union[type, typing.Tuple[type, ...]],
) -> typing.Any:
    if (
        type(value) is list
        and not _matches_expected_type(value, expected_types)
        and _expects_dict(expected_types)
        and len(value) == 1
    ):
        value = value[0]
    if type(value) is dict:
        return extract_response(value)
    return value


def _raise_response_type_error(
    value: typing.Any,
    expected_types: typing.Union[type, typing.Tuple[type, ...]],
) -> typing.NoReturn:
    raise _ResponseTypeError(f"agent process result is not of expected type(s) {expected_types!r}, got {type(value)!r}")


def process_response(
    res: typing.Any,
    expected_types: typing.Union[type, typing.Tuple[type, ...]] = dict,
) -> typing.Any:
    candidate = res
    if not _matches_expected_type(candidate, expected_types):
        if type(candidate) is list and _expects_dict(expected_types) and len(candidate) == 1:
            pass
        elif type(candidate) is str:
            candidate = json.loads(clean_json(candidate))
        else:
            _raise_response_type_error(candidate, expected_types)

    candidate = _unwrap_response(candidate, expected_types)
    if not _matches_expected_type(candidate, expected_types):
        _raise_response_type_error(candidate, expected_types)
    return candidate


class AgentCode(CodeAgent):
    def __init__(
        self,
        settings: AgentSettings,
        log: Logger,
        name: typing.Optional[str] = None,
        description: typing.Optional[str] = None,
        tools: typing.Optional[typing.List[Tool]] = None,
        verbosity: typing.Optional[int] = 0,
    ):
        if tools is None:
            tools = []

        model = build_openai_server_model(settings)

        super().__init__(  # pyright: ignore[reportUnknownMemberType]
            name=name,
            description=description,
            additional_authorized_imports=settings.imports,
            tools=tools,
            model=model,
            max_steps=settings.max_steps,
            verbosity_level=verbosity,
        )

        if self.python_executor.static_tools is None:  # type: ignore
            self.python_executor.static_tools = {}  # type: ignore

        self.python_executor.static_tools.update({"open": open})  # type: ignore

        self.log = log
        self.response_parse_max_retries = settings.response_parse_max_retries

    def process(
        self,
        conflict: str,
        images: typing.List[Image],
        expected_types: typing.Union[type, typing.Tuple[type, ...]] = dict,
        attempt: int = 0,
        type: str = "",
    ) -> typing.Any:
        res = super().run(  # pyright: ignore[reportUnknownMemberType]
            conflict + prompt_suffix,
            images=images,
        )

        try:
            return process_response(res=res, expected_types=expected_types)

        except (json.JSONDecodeError, _ResponseTypeError) as e:
            if attempt >= self.response_parse_max_retries:
                raise TypeError(
                    f"agent process result is not of expected type(s) {expected_types!r} after {attempt + 1} attempt(s)"
                ) from None

            return self.process(conflict, images, expected_types, attempt + 1)


class AgentTool(ToolCallingAgent):
    def __init__(
        self,
        settings: AgentSettings,
        log: Logger,
        name: typing.Optional[str] = None,
        description: typing.Optional[str] = None,
        tools: typing.Optional[typing.List[Tool]] = None,
        verbosity: typing.Optional[int] = 0,
    ):
        if tools is None:
            tools = []

        model = build_openai_server_model(settings)

        super().__init__(  # pyright: ignore[reportUnknownMemberType]
            name=name,
            description=description,
            tools=tools,
            model=model,
            max_steps=settings.max_steps,
            verbosity_level=verbosity,
        )

        self.log = log
        self.image_transport = settings.image_transport
        self.response_parse_max_retries = settings.response_parse_max_retries

    def process(
        self,
        conflict: str,
        images: typing.List[Image],
        expected_types: typing.Union[type, typing.Tuple[type, ...]] = dict,
        attempt: int = 0,
        type: str = "",
        image_urls: typing.Optional[typing.Sequence[str]] = None,
        image_transport: typing.Optional[str] = None,
        trace_callback: typing.Optional[AgentTraceCallback] = None,
    ) -> typing.Any:
        selected_image_transport = image_transport or self.image_transport
        transport = self._validate_image_inputs(
            images=images,
            image_urls=image_urls,
            image_transport=selected_image_transport,
        )
        task = conflict + prompt_suffix
        trace_base = {
            "attempt": attempt,
            "image_transport": transport,
            "request_type": type,
        }
        _emit_agent_trace(
            self.log,
            trace_callback,
            "prompt",
            **trace_base,
            prompt=task,
        )
        if transport in {"data_url", "remote_url"} and image_urls:
            res = self._run_with_image_urls(
                task,
                list(image_urls or []),
                image_transport=transport,
            )
        else:
            res = super().run(  # pyright: ignore[reportUnknownMemberType]
                task,
                images=images,
            )

        _emit_agent_trace(
            self.log,
            trace_callback,
            "raw_response",
            **trace_base,
            value=res,
        )
        try:
            parsed = process_response(res=res, expected_types=expected_types)
            _emit_agent_trace(
                self.log,
                trace_callback,
                "parsed_response",
                **trace_base,
                value=parsed,
            )
            return parsed

        except (json.JSONDecodeError, _ResponseTypeError) as e:
            _emit_agent_trace(
                self.log,
                trace_callback,
                "parse_error",
                **trace_base,
                error_message=str(e),
                error_type=e.__class__.__name__,
                raw_response=res,
            )
            if attempt >= self.response_parse_max_retries:
                raise TypeError(
                    f"agent process result is not of expected type(s) {expected_types!r} after {attempt + 1} attempt(s)"
                ) from None

            return self.process(
                conflict,
                images,
                expected_types,
                attempt + 1,
                type,
                image_urls=image_urls,
                image_transport=transport,
                trace_callback=trace_callback,
            )

    def _run_with_image_urls(
        self,
        task: str,
        image_urls: typing.List[str],
        *,
        image_transport: str,
    ) -> typing.Any:
        self.task = task
        self.interrupt_switch = False
        self.memory.system_prompt = SystemPromptStep(system_prompt=self.system_prompt)
        self.memory.reset()
        self.monitor.reset()
        self.memory.steps.append(RemoteImageTaskStep(task=self.task, task_images=None, image_urls=image_urls))

        try:
            try:
                steps = list(self._run_stream(task=self.task, max_steps=self.max_steps, images=None))
            except Exception as exc:
                raise RuntimeError(f"{image_transport} image transport failed: {exc}") from exc
            assert isinstance(steps[-1], FinalAnswerStep)
            return steps[-1].output
        finally:
            self._sanitize_remote_image_urls_in_memory()

    def _validate_image_inputs(
        self,
        *,
        images: typing.Sequence[Image],
        image_urls: typing.Optional[typing.Sequence[str]],
        image_transport: str,
    ) -> str:
        if image_transport not in SUPPORTED_IMAGE_TRANSPORTS:
            raise ValueError(
                f"unsupported image_transport [{image_transport}]; expected one of {sorted(SUPPORTED_IMAGE_TRANSPORTS)}"
            )
        if image_urls and image_transport not in {"data_url", "remote_url"}:
            raise ValueError("image_urls require image_transport='data_url' or 'remote_url'")
        if image_transport == "data_url" and image_urls and images:
            raise ValueError("data_url transport does not accept PIL images when image_urls are provided")
        if image_transport == "remote_url":
            if images:
                raise ValueError("remote_url transport does not accept PIL images")
            if not image_urls:
                raise ValueError("remote_url transport requires image_urls")
        return image_transport

    def _sanitize_remote_image_urls_in_memory(self) -> None:
        for step in self.memory.steps:
            model_input_messages = getattr(step, "model_input_messages", None)
            if not model_input_messages:
                continue
            for message in model_input_messages:
                content = getattr(message, "content", None)
                if not isinstance(content, list):
                    continue
                for item in content:
                    if not isinstance(item, dict) or item.get("type") != "image_url":
                        continue
                    image_url = item.get("image_url")
                    if isinstance(image_url, dict) and isinstance(image_url.get("url"), str):
                        image_url["url"] = _sanitize_image_url(image_url["url"])
