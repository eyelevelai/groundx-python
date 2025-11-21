import typing, yaml

from ..classes.element import Element
from ..classes.field import ExtractedField
from ..classes.group import Group
from ..classes.prompt import Prompt
from .source import Source


def _element_from_mapping(
    data: typing.Dict[str, typing.Any], key: typing.Optional[str] = None
) -> Element:
    if "fields" in data:
        grp = _group_from_mapping(data)
        if key and grp.prompt and not grp.prompt.attr_name:
            grp.prompt.attr_name = key
        return grp

    if any(k in data for k in ("value", "conflicts", "confidence")):
        ef = ExtractedField(**data)
        if key and ef.prompt and not ef.prompt.attr_name:
            ef.prompt.attr_name = key
        return ef

    ele = Element(**data)
    if key and ele.prompt and not ele.prompt.attr_name:
        ele.prompt.attr_name = key
    return ele


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
            typing.Sequence[Element],
        ],
    ] = {}

    for name, n in raw_fields.items():
        if isinstance(n, list):
            nl = typing.cast(typing.List[typing.Any], n)
            elements_list: typing.List[Element] = []
            for item in nl:
                if not isinstance(item, dict):
                    raise TypeError(
                        f"Expected dict for list item under field '{name}', got {type(item)}"
                    )
                elem = _element_from_mapping(
                    typing.cast(typing.Dict[str, typing.Any], item), name
                )
                elements_list.append(elem)
            fields[name] = elements_list
        elif isinstance(n, dict):
            nd = typing.cast(typing.Dict[str, typing.Any], n)
            if "prompt" in nd or "fields" in nd or "value" in nd:
                elem = _element_from_mapping(nd, name)
                fields[name] = elem
            else:
                inner_dict: typing.Dict[str, Element] = {}
                for sub_name, sub_node in nd.items():
                    if not isinstance(sub_node, dict):
                        raise TypeError(
                            f"Expected dict for '{name}.{sub_name}', got {type(sub_node)}"
                        )
                    inner_dict[sub_name] = _element_from_mapping(
                        typing.cast(typing.Dict[str, typing.Any], sub_node), sub_name
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
    def __init__(
        self, config_source: Source, default_workflow_id: str = "latest"
    ) -> None:
        self._config_source: Source = config_source
        # Cache: workflow_id -> { field_key -> Prompt }
        self._cache: typing.Dict[str, Group] = {}
        self._default_workflow_id: str = default_workflow_id
        self._versions: typing.Dict[str, str] = {}

        self._ensure_loaded(default_workflow_id)

    def _build_prompts_from_raw(
        self,
        raw: str,
    ) -> Group:
        return load_from_yaml(raw)

    def _ensure_loaded(self, workflow_id: str) -> None:
        if workflow_id in self._cache:
            return

        raw, version = self._config_source.fetch(workflow_id)
        prompts = self._build_prompts_from_raw(raw)
        self._cache[workflow_id] = prompts
        self._versions[workflow_id] = version

    def reload_if_changed(self, workflow_id: typing.Optional[str] = None) -> None:
        if not workflow_id:
            workflow_id = self._default_workflow_id

        current_version = self._config_source.peek(workflow_id)
        previous_version = self._versions.get(workflow_id)

        if not previous_version or current_version != previous_version:
            raw, version = self._config_source.fetch(workflow_id)
            prompts = self._build_prompts_from_raw(raw)
            self._cache[workflow_id] = prompts
            self._versions[workflow_id] = version

    def get_fields_for_workflow(
        self, workflow_id: typing.Optional[str] = None
    ) -> Group:
        if not workflow_id:
            workflow_id = self._default_workflow_id

        self._ensure_loaded(workflow_id)

        return self._cache[workflow_id]
