import typing

from .upload_minio import MinIOClient

S4_REGION = "us-east-1"


class S4Client(MinIOClient):
    upload_type: typing.ClassVar[str] = "s4"

    def _region(self) -> str:
        return S4_REGION

    def _part_size(self, length: int) -> int:
        from minio.helpers import MIN_PART_SIZE

        return max(length, MIN_PART_SIZE)

    def put_object(
        self,
        bucket: str,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> None:
        super().put_object(bucket, _trim_leading_slash(key), data, content_type)

    def put_json_stream(
        self,
        bucket: str,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
        *,
        connect_timeout_seconds: typing.Optional[float] = None,
        read_timeout_seconds: typing.Optional[float] = None,
        total_timeout_seconds: typing.Optional[float] = None,
        transport_total_timeout_seconds: typing.Optional[float] = None,
        object_tags: typing.Optional[typing.Mapping[str, str]] = None,
    ) -> None:
        super().put_json_stream(
            bucket,
            _trim_leading_slash(key),
            data,
            content_type,
            connect_timeout_seconds=connect_timeout_seconds,
            read_timeout_seconds=read_timeout_seconds,
            total_timeout_seconds=total_timeout_seconds,
            transport_total_timeout_seconds=transport_total_timeout_seconds,
            object_tags=object_tags,
        )


def _trim_leading_slash(key: str) -> str:
    return key[1:] if key.startswith("/") else key
