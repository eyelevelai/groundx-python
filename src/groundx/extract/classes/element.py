import typing
from pydantic import BaseModel

from .prompt import Prompt


class Element(BaseModel):
    prompt: typing.Optional[Prompt] = None
