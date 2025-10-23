import json, pytest, traceback, typing

pytest.importorskip("PIL")

from PIL.Image import Image

from smolagents import (  # pyright: ignore[reportMissingTypeStubs]
    CodeAgent,
    Tool,
    ToolCallingAgent,
)
from smolagents.models import (  # pyright: ignore[reportMissingTypeStubs]
    OpenAIServerModel,
)

from ..services.logger import Logger
from ..settings.settings import AgentSettings
from ..utility.classes import clean_json


prompt_suffix = """
Return only your response using the `final_answer` tool format:

```json
{{"answer": {{"type": RESPONSE_HERE, "description": "The final answer to the problem"}}}}
```
"""


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
        logger: Logger,
        name: typing.Optional[str] = None,
        description: typing.Optional[str] = None,
        tools: typing.Optional[typing.List[Tool]] = None,
        verbosity: typing.Optional[int] = 0,
    ):
        if tools is None:
            tools = []

        model = OpenAIServerModel(
            model_id=settings.model_id,
            api_base=settings.api_base,
            api_key=settings.get_api_key(),
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

        self.logger = logger

    def process(
        self,
        conflict: str,
        images: typing.List[Image],
        expected_types: typing.Union[type, typing.Tuple[type, ...]] = dict,
        attempt: int = 0,
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

            self.logger.debug_msg(
                f"agent process result is not of expected type(s) {expected_types!r}: [{e}], attempting again [{attempt+1}]\n\n{res}"
            )

            return self.process(conflict, images, expected_types, attempt + 1)


class AgentTool(ToolCallingAgent):
    def __init__(
        self,
        settings: AgentSettings,
        logger: Logger,
        name: typing.Optional[str] = None,
        description: typing.Optional[str] = None,
        tools: typing.Optional[typing.List[Tool]] = None,
        verbosity: typing.Optional[int] = 0,
    ):
        if tools is None:
            tools = []

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

        self.logger = logger

    def process(
        self,
        conflict: str,
        images: typing.List[Image],
        expected_types: typing.Union[type, typing.Tuple[type, ...]] = dict,
        attempt: int = 0,
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

            print(
                f"agent process result is not of expected type(s) {expected_types!r}: [{e}], attempting again [{attempt+1}]\n\n{res}"
            )

            return self.process(conflict, images, expected_types, attempt + 1)
