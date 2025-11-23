import typing

from ..classes.element import Element
from ..classes.group import Group
from ..classes.prompt import Prompt
from .source import Source
from .utility import load_from_yaml


class PromptManager:
    def __init__(
        self, config_source: Source, default_workflow_id: str = "latest"
    ) -> None:
        self._config_source: Source = config_source
        # Cache: workflow_id -> { field_key -> Prompt }
        self._cache: typing.Dict[str, typing.Dict[str, Group]] = {}
        self._default_workflow_id: str = default_workflow_id
        self._versions: typing.Dict[str, str] = {}

        self._ensure_loaded(default_workflow_id)

    def _ensure_loaded(self, workflow_id: str) -> None:
        if workflow_id in self._cache:
            return

        raw, version = self._config_source.fetch(workflow_id)
        prompts = load_from_yaml(raw)
        self._cache[workflow_id] = prompts
        self._versions[workflow_id] = version

    def get_fields_for_workflow(
        self, workflow_id: typing.Optional[str] = None
    ) -> typing.Dict[str, Group]:
        if not workflow_id:
            workflow_id = self._default_workflow_id

        self._ensure_loaded(workflow_id)

        return self._cache[workflow_id]

    def group_definition(
        self, group_name: str, workflow_id: typing.Optional[str] = None
    ) -> str:
        grp = self.group_load(group_name=group_name, workflow_id=workflow_id)

        if not grp.prompt:
            return ""

        return grp.prompt.prompt

    def group_descriptions(
        self, group_name: str, indent: int = 2, workflow_id: typing.Optional[str] = None
    ) -> str:
        desc: typing.List[str] = []
        grp = self.group_load(group_name, workflow_id=workflow_id)

        for _, v in grp.fields.items():
            if isinstance(v, Group):
                continue
            elif isinstance(v, Element):
                if v.prompt and v.prompt.description:
                    desc.append(
                        (" " * indent)
                        + f"- **{v.prompt.prompt_name()}** - {v.prompt.description}"
                    )

        return "\n".join(desc)

    def group_field(
        self, group_name: str, attr_name: str, workflow_id: typing.Optional[str] = None
    ) -> typing.Optional[Prompt]:
        fld = self.group_fields(group_name, workflow_id=workflow_id)
        if attr_name in fld:
            return fld[attr_name]

        return None

    def group_field_prompts(
        self, group_name: str, workflow_id: typing.Optional[str] = None
    ) -> str:
        return "".join(
            p.prompt
            for p in self.group_fields(group_name, workflow_id=workflow_id).values()
            if p.prompt
        )

    def group_fields(
        self, group_name: str, workflow_id: typing.Optional[str] = None
    ) -> typing.Dict[str, Prompt]:
        fields: typing.Dict[str, Prompt] = {}
        grp = self.group_load(group_name, workflow_id=workflow_id)

        for k, v in grp.fields.items():
            if isinstance(v, Group):
                continue
            elif isinstance(v, Element):
                if v.prompt:
                    fields[k] = v.prompt

        return fields

    def group_load(
        self, group_name: str, workflow_id: typing.Optional[str] = None
    ) -> Group:
        if not group_name:
            raise Exception(f"group_name is empty")

        res = self.get_fields_for_workflow(workflow_id)

        path = group_name.split(".")
        root = path[0]
        remainder = path[1:]

        if root not in res:
            raise Exception(f"[{workflow_id}].yaml is missing a {root} entry")

        grp = res[root]

        lineage = root
        for p in remainder:
            if p not in grp.fields:
                raise Exception(
                    f"[{workflow_id}].yaml is missing a [{p}] entry at [{lineage + '.' + p}]"
                )
            nv = grp.fields[p]
            if not isinstance(nv, Group):
                raise Exception(
                    f"[{workflow_id}].yaml entry at [{lineage + '.' + p}] is not a group"
                )

            lineage += "." + p
            grp = nv

        return grp

    def reload_if_changed(self, workflow_id: typing.Optional[str] = None) -> None:
        if not workflow_id:
            workflow_id = self._default_workflow_id

        current_version = self._config_source.peek(workflow_id)
        previous_version = self._versions.get(workflow_id)

        if not previous_version or current_version != previous_version:
            raw, version = self._config_source.fetch(workflow_id)
            prompts = load_from_yaml(raw)
            self._cache[workflow_id] = prompts
            self._versions[workflow_id] = version
