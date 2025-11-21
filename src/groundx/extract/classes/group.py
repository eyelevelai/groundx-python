import typing

from .element import Element
from .field import ExtractedField

from pydantic import model_serializer, model_validator


class Group(Element):
    fields: typing.Dict[
        str, typing.Union[Element, typing.Dict[str, Element], typing.Sequence[Element]]
    ] = {}

    @model_validator(mode="before")
    @classmethod
    def _inflate_fields(
        cls,
        data: typing.Any,
    ) -> typing.Any:
        if isinstance(data, cls):
            return data

        if not isinstance(data, dict):
            return data

        model_fields: typing.Set[str] = set(cls.model_fields.keys())
        non_field_keys: typing.Set[str] = model_fields - {"fields"}

        base: typing.Dict[str, typing.Any] = {}
        dynamic_fields: typing.Dict[str, typing.Any] = {}

        data = typing.cast(typing.Dict[str, typing.Any], data)
        for key, value in data.items():
            if key in non_field_keys or key == "fields":
                base[key] = value
            elif value:
                dynamic_fields[key] = value

        if dynamic_fields:
            existing = base.get("fields")
            if isinstance(existing, dict):
                merged = typing.cast(typing.Dict[str, typing.Any], existing)
                merged.update(dynamic_fields)
                base["fields"] = merged
            else:
                base["fields"] = dynamic_fields

        return base

    @model_serializer(mode="wrap")
    def _flatten_fields(
        self,
        handler: typing.Callable[[typing.Any], typing.Dict[str, typing.Any]],
    ) -> typing.Dict[str, typing.Any]:
        data = handler(self)

        raw_fields = typing.cast(
            typing.Dict[str, typing.Any],
            data.pop("fields", {}) or {},
        )

        data.update(raw_fields)

        return data

    def get(
        self, name: str
    ) -> typing.Optional[
        typing.Union[Element, typing.Dict[str, Element], typing.Sequence[Element]]
    ]:
        if name in self.fields:
            return self.fields[name]

        if name.lower() in self.fields:
            return self.fields[name.lower()]

        for k, v in self.fields.items():
            if isinstance(v, ExtractedField):
                if v.prompt and v.prompt.key().lower() == name.lower():
                    return self.fields[k]

        return None

    def get_element(self, name: str) -> typing.Optional[Element]:
        obj = self.get(name)

        if not obj:
            return None

        if not isinstance(obj, Element):
            return None

        return obj

    def get_field(self, name: str) -> typing.Optional[ExtractedField]:
        ele = self.get_element(name)

        if not ele:
            return None

        if not isinstance(ele, ExtractedField):
            return None

        return ele

    def get_list(self, name: str) -> typing.Optional[typing.Sequence[Element]]:
        obj = self.get(name)

        if not obj:
            return None

        if not isinstance(obj, list):
            return None

        return obj

    def set(
        self,
        name: str,
        nf: typing.Optional[
            typing.Union[Element, typing.Dict[str, Element], typing.Sequence[Element]]
        ],
    ) -> None:
        if not nf:
            if name in self.fields:
                self.fields.pop(name)
            return

        self.fields[name] = nf
