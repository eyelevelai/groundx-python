import typing

from ..services.logger import Logger
from ..services.upload import Upload
from ..settings.settings import ContainerSettings


class Source:
    def __init__(self, key: str, settings: ContainerSettings, logger: Logger) -> None:
        self._key = key
        self._upload = Upload(settings=settings, logger=logger)

    def _version_from_metadata(self, meta: typing.Dict[str, str]) -> str:
        etag = (meta.get("ETag") or "").strip('"')

        if not etag and meta.get("LastModified"):
            return str(meta["LastModified"])

        return etag

    def fetch(self) -> typing.Tuple[str, str]:
        res = self._upload.get_object_and_metadata(self._key)
        if not res:
            raise Exception(f"failed to get prompt yaml [{self._key}]")

        body_bytes, meta = res

        raw_yaml = body_bytes.decode("utf-8")
        version = self._version_from_metadata(meta)

        return raw_yaml, version

    def peek(self) -> typing.Optional[str]:
        meta = self._upload.head_object(self._key)
        if not meta:
            return None

        return self._version_from_metadata(meta)
