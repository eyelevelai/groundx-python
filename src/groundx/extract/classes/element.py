import typing
from pydantic import BaseModel

from .prompt import Prompt


class Element(BaseModel):
    model_type: str = "element"

    prompt: typing.Optional[Prompt] = None
