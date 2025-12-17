import typing

from .logger import Logger
from ..settings.settings import ContainerSettings


@typing.runtime_checkable
class UploadClient(typing.Protocol):
    def get_object(self, url: str) -> typing.Optional[bytes]: ...

    def get_object_and_metadata(
        self, url: str
    ) -> typing.Optional[typing.Tuple[bytes, typing.Dict[str, str]]]: ...

    def head_object(self, url: str) -> typing.Optional[typing.Dict[str, str]]: ...

    def put_object(
        self,
        bucket: str,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> None: ...

    def put_json_stream(
        self,
        bucket: str,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> None: ...


class Upload:
    def __init__(
        self,
        settings: ContainerSettings,
        logger: Logger,
    ) -> None:
        self.client: UploadClient
        self.settings = settings
        self.logger = logger

        self.logger.info_msg(
            f"upload type [{self.settings.upload.type}] [{self.settings.upload.bucket}]"
        )

        if self.settings.upload.type == "minio":
            from .upload_minio import MinIOClient

            self.client = MinIOClient(self.settings, self.logger)
        elif self.settings.upload.type == "s3":
            from .upload_s3 import S3Client

            self.client = S3Client(self.settings, self.logger)
        else:
            raise Exception(f"unsupported upload.type [{self.settings.upload.type}]")

    def get_object(self, url: str) -> typing.Optional[bytes]:
        return self.client.get_object(url)

    def get_object_and_metadata(
        self, url: str
    ) -> typing.Optional[typing.Tuple[bytes, typing.Dict[str, str]]]:
        return self.client.get_object_and_metadata(url)

    def head_object(self, url: str) -> typing.Optional[typing.Dict[str, str]]:
        return self.client.head_object(url)

    def put_object(
        self,
        bucket: str,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> None:
        self.client.put_object(bucket, key, data, content_type)

    def put_json_stream(
        self,
        bucket: str,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> None:
        self.client.put_json_stream(bucket, key, data, content_type)
