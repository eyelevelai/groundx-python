import typing

from .element import Element


class Group(Element):
    fields: typing.Dict[
        str, typing.Union[Element, typing.Dict[str, Element], typing.List[Element]]
    ]
