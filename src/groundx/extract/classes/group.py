import typing

from .element import Element
from .field import ExtractedField


class Group(Element):
    fields: typing.Dict[
        str, typing.Union[Element, typing.Dict[str, Element], typing.List[Element]]
    ]

    def get(
        self, name: str
    ) -> typing.Optional[
        typing.Union[Element, typing.Dict[str, Element], typing.List[Element]]
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

    def get_list(self, name: str) -> typing.Optional[typing.List[Element]]:
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
            typing.Union[Element, typing.Dict[str, Element], typing.List[Element]]
        ],
    ) -> None:
        if not nf:
            if name in self.fields:
                self.fields.pop(name)
            return

        self.fields[name] = nf
