import typing

import dateparser
from ..utility import coerce_value, str_to_type_sequence
from .element import Element
from pydantic import Field, PrivateAttr
from typing_extensions import Annotated


class ExtractedField(Element):
    confidence: typing.Optional[str] = None
    conflicts: Annotated[typing.List[typing.Any], Field(default_factory=list)]

    value: typing.Any = None
    _coercion_warning: typing.Optional[str] = PrivateAttr(default=None)

    def __init__(
        self,
        value: typing.Any = None,
        **data: typing.Any,
    ) -> None:
        super().__init__(**data)

        self.set_value(value)

    @property
    def coercion_warning(self) -> typing.Optional[str]:
        return self._coercion_warning

    def attr_name(self) -> typing.Optional[str]:
        if not self.prompt:
            raise Exception("prompt is not set")

        return self.prompt.attr_name

    def contains(self, other: "ExtractedField") -> bool:
        self_val = self.get_value()
        other_val = other.get_value()
        if not (isinstance(self_val, (str, float, int))):
            raise Exception(f"unexpected self field value type [{type(self_val)}]")

        if self.equal_to_value(other_val):
            return True

        if other_val in self.conflicts:
            return True

        return False

    def empty_value(
        self,
    ) -> typing.Optional[typing.Optional[typing.Union[int, float, typing.Any]]]:
        ty = self.type()
        if ty is None:
            return None
        expected_types = str_to_type_sequence(ty)

        if any(t in (int, float) for t in expected_types):
            if float in expected_types:
                return float(0)
            return int(0)

        if str in expected_types:
            return ""

        if list in expected_types:
            return []

        if dict in expected_types:
            return {}

        return None

    def equal_to_field(self, other: "ExtractedField") -> bool:
        self_val = self.get_value()
        other_val = other.get_value()
        if not (isinstance(self_val, (str, float, int))):
            raise Exception(f"unexpected self field value type [{type(self_val)}]")

        return self.equal_to_value(other_val)

    def equal_to_value(self, other: typing.Any) -> bool:
        if not (isinstance(other, (str, float, int))):
            raise Exception(f"unexpected value type [{type(other)}]")

        exist = self.get_value()
        if isinstance(exist, int):
            exist = float(exist)
        if isinstance(other, int):
            other = float(other)
        if isinstance(exist, str):
            exist = exist.lower()
        if isinstance(other, str):
            other = other.lower()

        return type(other) == type(exist) and other == exist

    def get_value(
        self,
    ) -> typing.Any:
        if self.value is None:
            return None
        expected_type = self.prompt.type if self.prompt else None
        result = coerce_value(self.value, expected_type)
        self._set_coercion_warning(result.warning)
        return result.value

    def key(self) -> str:
        if not self.prompt:
            raise Exception("prompt is not set")

        return self.prompt.key()

    def none_value(
        self,
    ) -> typing.Optional[typing.Optional[typing.Union[int, float, typing.Any]]]:
        return None

    def remove_conflict(self, value: typing.Any) -> None:
        if value in self.conflicts:
            self.conflicts.remove(value)
        if not self.equal_to_value(value):
            self.conflicts.append(self.get_value())

    def render(self) -> str:
        if not self.prompt:
            raise Exception(f"prompt is not set\n{self.prompt}")

        if not self.prompt.attr_name:
            raise Exception(f"prompt.attr_name is not set\n{self.prompt}")

        if not self.prompt.identifiers:
            raise Exception(f"prompt.identifiers is not set for [{self.attr_name()}]")

        if self.prompt.type is None:
            raise Exception(f"prompt.type is not set for [{self.attr_name()}]")

        default = ""
        if self.prompt.default:
            default = f"\nDefault Value:          {self.prompt.default}"

        description = ""
        if self.prompt.description:
            description = f"\nDescription:            {self.prompt.description}"

        format = ""
        if self.prompt.format or self.prompt.type:
            if self.prompt.format:
                format = self.prompt.format
            elif isinstance(self.prompt.type, str):
                if self.prompt.type == "int" or self.prompt.type == "float":
                    format = "number (float or int)"
                elif self.prompt.type == "bool":
                    format = "native JSON boolean"
                elif self.prompt.type == "str":
                    format = "string"
            else:
                if "int" in self.prompt.type or "float" in self.prompt.type:
                    format = "number (float or int)"
                elif "str" in self.prompt.type:
                    format = "string"

            if format != "":
                format = f"\nFormat:                 {format}"

        return f"""
## {self.prompt.attr_name}

Field:                  {self.prompt.attr_name}{description}{default}{format}
Example Identifiers:    {", ".join(self.prompt.identifiers)}
Special Instructions:
{self.prompt.instructions}"""

    def required(self) -> bool:
        if not self.prompt:
            raise Exception("prompt is not set")

        return self.prompt.required

    def set_value(self, value: typing.Any) -> None:
        if type(value) is str and self.prompt and self.prompt.attr_name and "date" in self.prompt.key().lower():
            try:
                dt = dateparser.parse(value)
                if dt is not None:
                    value = dt.strftime("%Y-%m-%d")
            except Exception:
                pass

        expected_type = self.prompt.type if self.prompt else None
        result = coerce_value(value, expected_type)
        self.value = result.value
        self._set_coercion_warning(result.warning)

    def _set_coercion_warning(self, warning: typing.Optional[str]) -> None:
        if warning is None:
            self._coercion_warning = None
            return
        field_name = self.prompt.attr_name if self.prompt and self.prompt.attr_name else "unknown"
        self._coercion_warning = f"field {field_name}: {warning}"

    def type(self) -> typing.Optional[typing.Union[str, typing.List[str]]]:
        if not self.prompt:
            raise Exception("prompt is not set")

        return self.prompt.type

    def valid_value(self, value: typing.Any) -> bool:
        if not self.prompt:
            raise Exception("prompt is not set")

        return self.prompt.valid_value(value)


ExtractedField.model_rebuild()
