import typing

from ..services.upload import (
    OBJECT_STORE_CONNECT_TIMEOUT_SECONDS,
    OBJECT_STORE_READ_TIMEOUT_SECONDS,
    OBJECT_STORE_TOTAL_TIMEOUT_SECONDS,
    Upload,
)
from ..settings.settings import ContainerSettings
from .source import Source


class ObjectStore(Source):
    def __init__(
        self,
        settings: ContainerSettings,
        **data: typing.Any,
    ) -> None:
        super().__init__(**data)

        self._settings = settings
        self._upload = Upload(settings=settings, logger=self.logger)

    def fetch(self, workflow_id: str) -> typing.Tuple[str, str]:
        res = self._upload.get_object_and_metadata(
            self.workflow_path(workflow_id),
            connect_timeout_seconds=OBJECT_STORE_CONNECT_TIMEOUT_SECONDS,
            read_timeout_seconds=OBJECT_STORE_READ_TIMEOUT_SECONDS,
            total_timeout_seconds=OBJECT_STORE_TOTAL_TIMEOUT_SECONDS,
        )
        if not res:
            raise Exception(f"failed to get prompt yaml [{self.workflow_path(workflow_id)}]")

        body_bytes, meta = res

        raw_yaml = body_bytes.decode("utf-8")
        version = self._version_from_metadata(meta)

        return raw_yaml, version

    def peek(self, workflow_id: str) -> typing.Optional[str]:
        meta = self._upload.head_object(
            self.workflow_path(workflow_id),
            connect_timeout_seconds=OBJECT_STORE_CONNECT_TIMEOUT_SECONDS,
            read_timeout_seconds=OBJECT_STORE_READ_TIMEOUT_SECONDS,
        )
        if not meta:
            return None

        return self._version_from_metadata(meta)

    def _version_from_metadata(self, meta: typing.Dict[str, str]) -> str:
        etag = (meta.get("ETag") or "").strip('"')

        if not etag and meta.get("LastModified"):
            return str(meta["LastModified"])

        return etag
