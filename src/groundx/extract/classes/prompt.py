import typing

from pydantic import BaseModel

from ..utility import str_to_type_sequence


class Prompt(BaseModel):
    attr_name: typing.Optional[str] = None
    default: typing.Optional[str] = None
    description: typing.Optional[str] = None
    format: typing.Optional[str] = None
    identifiers: typing.Optional[typing.List[str]] = None
    instructions: str
    required: bool = False
    type: typing.Optional[typing.Union[str, typing.List[str]]] = None

    class Config:
        validate_by_name = True

    def key(self) -> str:
        if self.attr_name:
            return self.attr_name

        raise ValueError(f"missing attr_name")

    def valid_value(self, value: typing.Any) -> bool:
        ty = self.type
        if not ty:
            return True

        types: typing.List[typing.Type[typing.Any]] = []
        if isinstance(ty, list):
            for t in ty:
                if t == "int" or t == "float":
                    types.extend([int, float])
                elif t == "str":
                    types.append(str)

            return isinstance(value, tuple(types))

        exp = str_to_type_sequence(ty)
        for et in exp:
            if et in (int, float):
                types.extend([int, float])
            else:
                types.append(et)
        types = list(dict.fromkeys(types))
        return isinstance(value, tuple(types))
