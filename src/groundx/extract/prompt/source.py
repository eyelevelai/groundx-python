import datetime, os, typing

from ..services.logger import Logger


class Source:
    def __init__(
        self,
        logger: Logger,
        cache_path: str = f"workflows/extract",
    ) -> None:
        self._cache_path = cache_path.rstrip("/")
        self._logger = logger

    @property
    def logger(self) -> Logger:
        return self._logger

    def workflow_path(self, workflow_id: str) -> str:
        return f"{self._cache_path}/{workflow_id}.yaml"

    def version_from_metadata(self, meta: typing.Dict[str, str]) -> str:
        etag = (meta.get("ETag") or "").strip('"')

        if not etag and meta.get("LastModified"):
            return str(meta["LastModified"])

        return etag

    def fetch(self, workflow_id: str) -> typing.Tuple[str, str]:
        path = self.workflow_path(workflow_id)

        try:
            with open(path, "r", encoding="utf-8") as f:
                raw_yaml = f.read()
        except FileNotFoundError:
            raise Exception(f"failed to get prompt yaml [{path}]")

        try:
            mtime = os.path.getmtime(path)
            version = datetime.datetime.fromtimestamp(
                mtime, tz=datetime.timezone.utc
            ).isoformat()
        except OSError:
            version = ""

        return raw_yaml, version

    def peek(self, workflow_id: str) -> typing.Optional[str]:
        path = self.workflow_path(workflow_id)

        try:
            mtime = os.path.getmtime(path)
        except OSError:
            return None

        return datetime.datetime.fromtimestamp(
            mtime, tz=datetime.timezone.utc
        ).isoformat()
