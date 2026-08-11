import typing

from ..utility import coerce_value
from pydantic import BaseModel, ConfigDict


class Prompt(BaseModel):
    model_config = ConfigDict(validate_by_name=True)

    attr_name: typing.Optional[str] = None
    default: typing.Optional[str] = None
    description: typing.Optional[str] = None
    format: typing.Optional[str] = None
    identifiers: typing.Optional[typing.List[str]] = None
    instructions: str
    required: bool = False
    type: typing.Optional[typing.Union[str, typing.List[str]]] = None

    def key(self) -> str:
        if self.attr_name:
            return self.attr_name

        raise ValueError("missing attr_name")

    def valid_value(self, value: typing.Any) -> bool:
        ty = self.type
        if not ty:
            return True

        result = coerce_value(value, ty)
        return result.matched and not result.converted
