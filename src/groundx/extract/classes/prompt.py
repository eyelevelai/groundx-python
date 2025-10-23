import typing

from pydantic import BaseModel

from ..utility.classes import str_to_type_sequence


class Prompt(BaseModel):
    attr_name: str
    prompt: str
    type: typing.Union[str, typing.List[str]]

    class Config:
        validate_by_name = True

    def valid_value(self, value: typing.Any) -> bool:
        ty = self.type

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
