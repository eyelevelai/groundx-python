from __future__ import annotations

import json, traceback, typing
from dataclasses import dataclass, field
from urllib.parse import urlparse

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

from ..services.logger import Logger
from ..settings.settings import AgentSettings
from ..utility.utility import clean_json

if typing.TYPE_CHECKING:
    from PIL.Image import Image


prompt_suffix = """
Return only your response using the `final_answer` tool format:

```json
{{"answer": {{"type": RESPONSE_HERE, "description": "The final answer to the problem"}}}}
```
"""

SUPPORTED_IMAGE_TRANSPORTS = {"pil", "data_url", "remote_url"}


@dataclass
class RemoteImageTaskStep(TaskStep):
    image_urls: typing.List[str] = field(default_factory=list)

    def to_messages(self, summary_mode: bool = False) -> typing.List[ChatMessage]:
        content: typing.List[typing.Dict[str, typing.Any]] = [
            {"type": "text", "text": f"New task:\n{self.task}"}
        ]
        content.extend(
            {"type": "image_url", "image_url": {"url": image_url}}
            for image_url in self.image_urls
        )
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


def process_response(
    res: typing.Any,
    expected_types: typing.Union[type, typing.Tuple[type, ...]] = dict,
) -> typing.Any:
    if not isinstance(res, expected_types):
        if (
            isinstance(res, list)
            and isinstance(dict(), expected_types)
            and len(res) == 1  # pyright: ignore[reportUnknownArgumentType]
        ):
            return extract_response(
                res[0]  # pyright: ignore[reportUnknownArgumentType]
            )

        if not isinstance(res, str):
            traceback.print_stack()
            raise TypeError(
                f"agent process result is not of expected type(s) {expected_types!r}, got {type(res)!r}"  # type: ignore
            )

        res = clean_json(res)

        loaded = json.loads(res)
        if not isinstance(loaded, expected_types):
            if isinstance(loaded, list) and isinstance(dict(), expected_types) and len(loaded) == 1:  # type: ignore
                return extract_response(loaded[0])  # type: ignore

            traceback.print_stack()
            raise TypeError(
                f"agent process result is not of expected type(s) {expected_types!r} after JSON parsing, got {type(loaded)!r}"  # type: ignore
            )

        if isinstance(loaded, typing.Dict):
            return extract_response(loaded)  # type: ignore

        return loaded

    if isinstance(res, typing.Dict):
        return extract_response(res)  # type: ignore

    return res


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

        if settings.model_kwargs:
            model = OpenAIServerModel(
                model_id=settings.model_id,
                api_base=settings.api_base,
                api_key=settings.get_api_key(),
                reasoning_effort=settings.reasoning_effort,
                **settings.model_kwargs,
            )
        else:
            model = OpenAIServerModel(
                model_id=settings.model_id,
                api_base=settings.api_base,
                api_key=settings.get_api_key(),
                reasoning_effort=settings.reasoning_effort,
            )

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

        except Exception as e:
            if attempt > 2:
                raise TypeError(
                    f"agent process result is not of expected type(s) {expected_types!r}: [{e}]\n\n{res}"
                )

            self.log.debug_msg(
                f"agent process result is not of expected type(s) {expected_types!r}: [{e}], attempting again [{attempt+1}]\n\n{res}"
            )

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

        if settings.model_kwargs:
            if settings.reasoning_effort:
                model = OpenAIServerModel(
                    model_id=settings.model_id,
                    api_base=settings.api_base,
                    api_key=settings.get_api_key(),
                    reasoning_effort=settings.reasoning_effort,
                    **settings.model_kwargs,
                )
            else:
                model = OpenAIServerModel(
                    model_id=settings.model_id,
                    api_base=settings.api_base,
                    api_key=settings.get_api_key(),
                    **settings.model_kwargs,
                )
        elif settings.reasoning_effort:
            model = OpenAIServerModel(
                model_id=settings.model_id,
                api_base=settings.api_base,
                api_key=settings.get_api_key(),
                reasoning_effort=settings.reasoning_effort,
            )
        else:
            model = OpenAIServerModel(
                model_id=settings.model_id,
                api_base=settings.api_base,
                api_key=settings.get_api_key(),
            )

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

    def process(
        self,
        conflict: str,
        images: typing.List[Image],
        expected_types: typing.Union[type, typing.Tuple[type, ...]] = dict,
        attempt: int = 0,
        type: str = "",
        image_urls: typing.Optional[typing.Sequence[str]] = None,
        image_transport: typing.Optional[str] = None,
    ) -> typing.Any:
        selected_image_transport = image_transport or self.image_transport
        transport = self._validate_image_inputs(
            images=images,
            image_urls=image_urls,
            image_transport=selected_image_transport,
        )
        if transport == "remote_url":
            res = self._run_with_remote_image_urls(
                conflict + prompt_suffix,
                list(image_urls or []),
            )
        else:
            res = super().run(  # pyright: ignore[reportUnknownMemberType]
                conflict + prompt_suffix,
                images=images,
            )

        try:
            return process_response(res=res, expected_types=expected_types)

        except Exception as e:
            if attempt > 2:
                raise TypeError(
                    f"agent process result is not of expected type(s) {expected_types!r}: [{e}]\n\n{res}"
                )

            print(
                f"agent process result is not of expected type(s) {expected_types!r}: [{e}], attempting again [{attempt+1}]\n\n{res}"
            )

            return self.process(
                conflict,
                images,
                expected_types,
                attempt + 1,
                type,
                image_urls=image_urls,
                image_transport=transport,
            )

    def _run_with_remote_image_urls(
        self,
        task: str,
        image_urls: typing.List[str],
    ) -> typing.Any:
        self.task = task
        self.interrupt_switch = False
        self.memory.system_prompt = SystemPromptStep(system_prompt=self.system_prompt)
        self.memory.reset()
        self.monitor.reset()
        self.memory.steps.append(
            RemoteImageTaskStep(task=self.task, task_images=None, image_urls=image_urls)
        )

        try:
            try:
                steps = list(self._run_stream(task=self.task, max_steps=self.max_steps, images=None))
            except Exception as exc:
                raise RuntimeError(f"remote_url image transport failed: {exc}") from exc
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
                "unsupported image_transport "
                f"[{image_transport}]; expected one of {sorted(SUPPORTED_IMAGE_TRANSPORTS)}"
            )
        if image_urls and image_transport != "remote_url":
            raise ValueError("image_urls require image_transport='remote_url'")
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
