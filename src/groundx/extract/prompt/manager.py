import typing

from pydantic import PrivateAttr

from groundx import GroundX, WorkflowResponse

from ..classes.element import Element
from ..classes.field import ExtractedField
from ..classes.group import Group
from ..classes.prompt import Prompt
from ..services.logger import Logger
from .source import Source
from .utility import do_not_remove_fields, load_from_yaml


class PromptManager:
    _gx_client: GroundX = PrivateAttr()
    _logger: Logger = PrivateAttr()
    is_init: bool = False

    def __init__(
        self,
        cache_source: Source,
        config_source: Source,
        gx_client: typing.Optional[GroundX] = None,
        logger: typing.Optional[Logger] = None,
        default_file_name: typing.Optional[str] = None,
        default_workflow_id: typing.Optional[str] = None,
    ) -> None:
        self._cache_source: Source = cache_source
        self._config_source: Source = config_source

        self._cache: typing.Dict[str, typing.Dict[str, Group]] = {}

        if not default_file_name:
            default_file_name = "latest"
        if not default_workflow_id:
            default_workflow_id = "latest"

        self._default_file_name: str = default_file_name.replace(".yaml", "")
        self._default_workflow_id: str = default_workflow_id.replace(".yaml", "")

        if gx_client:
            self._gx_client = gx_client
        if logger:
            self._logger = logger
        else:
            self.logger = Logger("prompt-manager", "WARNING")

        self._versions: typing.Dict[str, str] = {}

        if (
            (
                self._default_file_name != "latest"
                and self._default_workflow_id != "latest"
            )
            or not gx_client
            or not logger
        ):
            self.logger.info_msg(
                f"[{self._default_workflow_id}] [{self._default_file_name}.yaml] loading cache_workflow"
            )

            try:
                self.cache_workflow(self._default_file_name, self._default_workflow_id)
                self.is_init = True
                return
            except Exception as e:
                self.logger.debug_msg(f"workflows.cache_workflow [1] exception: {e}")

        self.logger.info_msg(
            f"[{self._default_file_name}.yaml] init",
            workflow_id=self._default_workflow_id,
        )

        if self._default_workflow_id == "latest":
            res: typing.Optional[WorkflowResponse] = None
            try:
                res = self._gx_client.workflows.get_account()
            except Exception as e:
                self.logger.debug_msg(
                    f"workflows.get_account exception: {e}",
                    workflow_id=self._default_workflow_id,
                )

            if res and res.workflow and res.workflow.workflow_id:
                self.default_workflow_id = res.workflow.workflow_id
                self.logger.info_msg(
                    f"workflow_id from get_account, assigned to account",
                    workflow_id=self.default_workflow_id,
                )

                try:
                    self.cache_workflow(
                        self.default_file_name, self.default_workflow_id
                    )
                    self.is_init = True
                    return
                except Exception as e:
                    self.logger.debug_msg(
                        f"workflows.cache_workflow [2] exception: {e}",
                        workflow_id=self.default_workflow_id,
                    )

        if "latest" in self._default_file_name:
            try:
                ls = self._gx_client.workflows.list()
                for wf in ls.workflows:
                    if wf.workflow_id and wf.relationships and wf.relationships.account:
                        self.default_workflow_id = wf.workflow_id
                        self.logger.info_msg(
                            f"workflow_id from list, assigned to account",
                            workflow_id=self.default_workflow_id,
                        )

                        try:
                            self.cache_workflow(
                                self.default_file_name, self.default_workflow_id
                            )
                            self.is_init = True
                            return
                        except Exception as e:
                            self.logger.debug_msg(
                                f"workflows.cache_workflow [3] exception: {e}",
                                workflow_id=self.default_workflow_id,
                            )
            except Exception as e:
                self.logger.debug_msg(
                    f"workflows.list exception: {e}",
                    workflow_id=self.default_workflow_id,
                )

    @property
    def default_file_name(self) -> str:
        return self._default_file_name

    @default_file_name.setter
    def default_file_name(self, value: str) -> None:
        self._default_file_name = value

    @default_file_name.deleter
    def default_file_name(self) -> None:
        del self._default_file_name

    @property
    def default_workflow_id(self) -> str:
        return self._default_workflow_id

    @default_workflow_id.setter
    def default_workflow_id(self, value: str) -> None:
        self._default_workflow_id = value

    @default_workflow_id.deleter
    def default_workflow_id(self) -> None:
        del self._default_workflow_id

    @property
    def gx_client(self) -> GroundX:
        return self._gx_client

    @gx_client.setter
    def gx_client(self, value: GroundX) -> None:
        self._gx_client = value

    @gx_client.deleter
    def gx_client(self) -> None:
        del self._gx_client

    @property
    def logger(self) -> Logger:
        return self._logger

    @logger.setter
    def logger(self, value: Logger) -> None:
        self._logger = value

    @logger.deleter
    def logger(self) -> None:
        del self._logger

    def cache_workflow(self, file_name: str, workflow_id: str) -> None:
        if workflow_id in self._cache:
            return

        try:
            raw, version = self._config_source.fetch(workflow_id)
        except Exception as e:
            self.logger.info_msg(
                f"_config_source.fetch exception [{e}]\ntrying _cache_source [{file_name}.yaml]...",
                workflow_id=workflow_id,
            )
            raw, version = self._cache_source.fetch(file_name)

        prompts = load_from_yaml(raw)
        self._cache[workflow_id] = prompts
        self._versions[workflow_id] = version

    def file_name(self, file_name: typing.Optional[str] = None) -> str:
        if not file_name:
            return self._default_file_name

        return file_name

    def get_fields_for_workflow(
        self,
        file_name: typing.Optional[str] = None,
        workflow_id: typing.Optional[str] = None,
    ) -> typing.Dict[str, Group]:
        workflow_id = self.workflow_id(workflow_id)

        self.cache_workflow(self.file_name(file_name), workflow_id)

        return self._cache[workflow_id]

    def get_prompt(
        self,
        name: str,
        file_name: typing.Optional[str] = None,
        workflow_id: typing.Optional[str] = None,
    ) -> typing.Optional[Prompt]:
        if not name:
            raise Exception(f"name is empty")

        res = self.get_fields_for_workflow(file_name, workflow_id)

        file_name = self.file_name(file_name)
        workflow_id = self.workflow_id(workflow_id)

        path = name.split(".")
        root = path[0]
        remainder = path[1:]

        if root not in res:
            raise Exception(
                f"[{workflow_id}] [{file_name}.yaml] is missing a [{root}] entry"
            )

        grp = res[root]

        if not remainder:
            return grp.prompt

        lineage = root
        idx = 1
        n = len(remainder)

        for p in remainder:
            if p not in grp.fields:
                raise Exception(
                    f"[{workflow_id}] [{file_name}.yaml] is missing a [{p}] entry at [{lineage + '.' + p}]"
                )
            nv = grp.fields[p]
            if (
                isinstance(nv, dict)
                or isinstance(nv, list)
                or isinstance(nv, typing.Sequence)
            ):
                raise Exception(
                    f"[{workflow_id}] [{file_name}.yaml] entry at [{lineage + '.' + p}] is not an element"
                )

            if idx == n:
                return nv.prompt

            if not isinstance(nv, Group):
                raise Exception(
                    f"[{workflow_id}] [{file_name}.yaml] entry at [{lineage + '.' + p}] is not a group"
                )

            lineage += "." + p
            grp = nv
            idx += 1

        return None

    def group(
        self,
        group_name: str,
        file_name: typing.Optional[str] = None,
        workflow_id: typing.Optional[str] = None,
    ) -> typing.Dict[str, Element]:
        fields: typing.Dict[str, Element] = {}
        grp = self.group_load(
            group_name=group_name, file_name=file_name, workflow_id=workflow_id
        )

        for k, v in grp.fields.items():
            if isinstance(v, ExtractedField) or isinstance(v, Group):
                fields[k] = v

        return fields

    def group_definition(
        self,
        group_name: str,
        file_name: typing.Optional[str] = None,
        workflow_id: typing.Optional[str] = None,
    ) -> str:
        grp = self.group_load(
            group_name=group_name, file_name=file_name, workflow_id=workflow_id
        )

        pmp = grp.render()
        if not pmp:
            return ""

        return pmp

    def group_descriptions(
        self,
        group_name: str,
        indent: int = 2,
        file_name: typing.Optional[str] = None,
        workflow_id: typing.Optional[str] = None,
    ) -> str:
        desc: typing.List[str] = []
        grp = self.group_load(
            group_name=group_name, file_name=file_name, workflow_id=workflow_id
        )

        for _, v in grp.fields.items():
            if isinstance(v, ExtractedField):
                if v.prompt and v.prompt.description:
                    desc.append(
                        (" " * indent)
                        + f"- **{v.prompt.key()}** - {v.prompt.description}"
                    )

        return "\n".join(desc)

    def group_field(
        self,
        group_name: str,
        attr_name: str,
        file_name: typing.Optional[str] = None,
        workflow_id: typing.Optional[str] = None,
    ) -> typing.Optional[ExtractedField]:
        fld = self.group_fields(
            group_name=group_name, file_name=file_name, workflow_id=workflow_id
        )
        if attr_name in fld:
            return fld[attr_name]

        return None

    def group_field_prompts(
        self,
        group_name: str,
        file_name: typing.Optional[str] = None,
        workflow_id: typing.Optional[str] = None,
    ) -> str:
        return "".join(
            p.render()
            for p in self.group_fields(
                group_name=group_name, file_name=file_name, workflow_id=workflow_id
            ).values()
            if p.render()
        )

    def group_fields(
        self,
        group_name: str,
        file_name: typing.Optional[str] = None,
        workflow_id: typing.Optional[str] = None,
    ) -> typing.Dict[str, ExtractedField]:
        fields: typing.Dict[str, ExtractedField] = {}
        grp = self.group_load(
            group_name=group_name, file_name=file_name, workflow_id=workflow_id
        )

        for k, v in grp.fields.items():
            if isinstance(v, ExtractedField):
                fields[k] = v

        return fields

    def group_field_keys(
        self,
        group_name: str,
        file_name: typing.Optional[str] = None,
        workflow_id: typing.Optional[str] = None,
    ) -> typing.List[str]:
        grp = self.group_load(
            group_name=group_name, file_name=file_name, workflow_id=workflow_id
        )

        attrs: typing.List[str] = []
        for k, v in grp.fields.items():
            if isinstance(v, ExtractedField):
                attrs.append(k)

        return attrs

    def group_keys(
        self,
        group_name: str,
        file_name: typing.Optional[str] = None,
        workflow_id: typing.Optional[str] = None,
    ) -> typing.List[str]:
        grp = self.group_load(
            group_name=group_name, file_name=file_name, workflow_id=workflow_id
        )

        attrs: typing.List[str] = []
        for k, v in grp.fields.items():
            if isinstance(v, ExtractedField) or isinstance(v, Group):
                attrs.append(k)

        return attrs

    def group_load(
        self,
        group_name: str,
        file_name: typing.Optional[str] = None,
        workflow_id: typing.Optional[str] = None,
    ) -> Group:
        if not group_name:
            raise Exception(f"group_name is empty")

        res = self.get_fields_for_workflow(file_name, workflow_id)

        file_name = self.file_name(file_name)
        workflow_id = self.workflow_id(workflow_id)

        path = group_name.split(".")
        root = path[0]
        remainder = path[1:]

        if root not in res:
            raise Exception(
                f"[{workflow_id}] [{file_name}.yaml] is missing a {root} entry"
            )

        grp = res[root]

        lineage = root
        for p in remainder:
            if p not in grp.fields:
                raise Exception(
                    f"[{workflow_id}] [{file_name}.yaml] is missing a [{p}] entry at [{lineage + '.' + p}]"
                )
            nv = grp.fields[p]
            if not isinstance(nv, Group):
                raise Exception(
                    f"[{workflow_id}] [{file_name}.yaml] entry at [{lineage + '.' + p}] is not a group"
                )

            lineage += "." + p
            grp = nv

        return grp

    def reload_if_changed(self, workflow_id: typing.Optional[str] = None) -> None:
        workflow_id = self.workflow_id(workflow_id)

        current_version = self._config_source.peek(workflow_id)
        previous_version = self._versions.get(workflow_id)

        if not previous_version or current_version != previous_version:
            raw, version = self._config_source.fetch(workflow_id)
            prompts = load_from_yaml(raw)
            self._cache[workflow_id] = prompts
            self._versions[workflow_id] = version

    def workflow_extract_dict(
        self,
        file_name: typing.Optional[str] = None,
        workflow_id: typing.Optional[str] = None,
    ) -> typing.Dict[str, typing.Dict[str, typing.Any]]:
        wf = self.get_fields_for_workflow(file_name, workflow_id)

        wfd: typing.Dict[str, typing.Dict[str, typing.Any]] = {}
        for k, v in wf.items():
            v = do_not_remove_fields(v)

            wfd[k] = v.model_dump(
                exclude_defaults=True, exclude_none=True, exclude_unset=True
            )

        return wfd

    def workflow_id(self, workflow_id: typing.Optional[str] = None) -> str:
        if not workflow_id:
            return self._default_workflow_id

        return workflow_id
