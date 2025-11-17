import typing, yaml

from ..classes.element import Element
from ..classes.field import ExtractedField
from ..classes.group import Group
from ..classes.prompt import Prompt
from .source import Source


def _element_from_mapping(data: typing.Dict[str, typing.Any]) -> Element:
    if "fields" in data:
        return _group_from_mapping(data)

    if any(k in data for k in ("value", "conflicts", "confidence")):
        return ExtractedField(**data)

    return Element(**data)


def _group_from_mapping(data: typing.Dict[str, typing.Any]) -> Group:
    prompt_data = data.get("prompt")
    prompt: typing.Optional[Prompt] = None

    if prompt_data:
        prompt = Prompt(**prompt_data)

    raw_fields: typing.Dict[str, typing.Any] = data.get("fields", {}) or {}
    fields: typing.Dict[
        str,
        typing.Union[
            Element,
            typing.Dict[str, Element],
            typing.List[Element],
        ],
    ] = {}

    for name, n in raw_fields.items():
        if isinstance(n, list):
            node = typing.cast(typing.List[typing.Any], n)
            elements_list: typing.List[Element] = []
            for item in node:
                if not isinstance(item, dict):
                    raise TypeError(
                        f"Expected dict for list item under field '{name}', got {type(item)}"
                    )
                elem = _element_from_mapping(
                    typing.cast(typing.Dict[str, typing.Any], item)
                )
                elements_list.append(elem)
            fields[name] = elements_list
        elif isinstance(n, dict):
            node = typing.cast(typing.Dict[str, typing.Any], n)
            if "prompt" in node or "fields" in node or "value" in node:
                elem = _element_from_mapping(node)
                fields[name] = elem
            else:
                inner_dict: typing.Dict[str, Element] = {}
                for sub_name, sub_node in node.items():
                    if not isinstance(sub_node, dict):
                        raise TypeError(
                            f"Expected dict for '{name}.{sub_name}', got {type(sub_node)}"
                        )
                    inner_dict[sub_name] = _element_from_mapping(
                        typing.cast(typing.Dict[str, typing.Any], sub_node)
                    )
                fields[name] = inner_dict
        else:
            raise TypeError(f"Unexpected YAML node type for field '{name}': {type(n)}")

    return Group(prompt=prompt, fields=fields)


def load_from_yaml(raw_yaml: str) -> Group:
    data = yaml.safe_load(raw_yaml)
    if not isinstance(data, dict):
        raise TypeError(f"Expected top-level YAML mapping, got {type(data)}")

    if "fields" in data:
        return _group_from_mapping(typing.cast(typing.Dict[str, typing.Any], data))

    return _group_from_mapping({"fields": data})


class PromptManager:
    def __init__(self, config_source: Source) -> None:
        self._config_source: Source = config_source
        self._cache: typing.Optional[typing.Dict[str, Prompt]] = None
        self._version: typing.Optional[str] = None

        raw, version = self._config_source.fetch()
        self._cache = self._build_prompts_from_raw(raw, version)

    def reload_if_changed(self) -> None:
        version = self._config_source.peek()
        if not self._version or version != self._version:
            raw, version = self._config_source.fetch()
            self._cache = self._build_prompts_from_raw(raw, version)

    def _build_prompts_from_raw(
        self, raw: str, version: str
    ) -> typing.Dict[str, Prompt]:
        root_group = load_from_yaml(raw)
        self._version = version

        prompts: typing.Dict[str, Prompt] = {}

        def walk(element: Element, prefix: str = "") -> None:
            if element.prompt is not None:
                key = prefix.rstrip(".")
                if key:
                    prompts[key] = element.prompt

            if isinstance(element, Group) and getattr(element, "fields", None):
                for name, child in element.fields.items():
                    child_prefix = f"{prefix}.{name}" if prefix else name
                    if isinstance(child, Element):
                        walk(child, child_prefix)
                    elif isinstance(child, dict):
                        for sub_name, sub_elem in child.items():
                            walk(sub_elem, f"{child_prefix}.{sub_name}")
                    else:
                        for idx, sub_elem in enumerate(child):
                            walk(sub_elem, f"{child_prefix}[{idx}]")

        walk(root_group, prefix="")

        return prompts

    @property
    def fields(self) -> typing.Dict[str, Prompt]:
        if self._cache is None:
            raw, version = self._config_source.fetch()
            self._cache = self._build_prompts_from_raw(raw, version)

        return self._cache
