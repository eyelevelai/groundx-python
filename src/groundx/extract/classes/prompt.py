import typing

from pydantic import BaseModel

from .utility import str_to_type


class Prompt(BaseModel):
    attr_name: str
    prompt: str
    type: typing.Union[str, typing.List[str]]

    class Config:
        validate_by_name = True

    def valid_value(self, value: typing.Any) -> bool:
        ty = self.type

        if isinstance(ty, list):
            types: list[typing.Type[typing.Any]] = []
            for t in ty:
                if t == "int" or t == "float":
                    types.extend([int, float])
                elif t == "str":
                    types.append(str)

            return isinstance(value, tuple(types))

        exp = str_to_type(ty)

        origin = typing.get_origin(exp)
        if origin is typing.Union:
            args = typing.get_args(exp)
            types: list[typing.Type[typing.Any]] = []
            for t in args:
                if t is int or t is float:
                    types.extend([int, float])
                else:
                    types.append(t)
            types = list(dict.fromkeys(types))
            return any(isinstance(value, t) for t in types)

        if exp is int or exp is float:
            return isinstance(value, (int, float))

        return isinstance(value, exp)
