import typing

from ..settings.settings import ContainerSettings
from .http import wall_clock_operation_deadline
from .logger import Logger
from .upload import validate_upload_timeouts


class S3Client:
    def __init__(self, settings: ContainerSettings, logger: Logger) -> None:
        self.settings = settings
        self.client = None
        self._timeout_clients: typing.Dict[typing.Tuple[float, float, float], typing.Any] = {}
        self.logger = logger
        if self.settings.upload.type == "s3":
            self.client = self._create_client()

    def _create_client(
        self,
        *,
        connect_timeout_seconds: typing.Optional[float] = None,
        read_timeout_seconds: typing.Optional[float] = None,
        total_timeout_seconds: typing.Optional[float] = None,
    ) -> typing.Any:
        import boto3
        import certifi
        from botocore.config import Config

        timeout = validate_upload_timeouts(
            connect_timeout_seconds=connect_timeout_seconds,
            read_timeout_seconds=read_timeout_seconds,
            total_timeout_seconds=total_timeout_seconds,
        )
        config: typing.Dict[str, typing.Any] = {
            "connect_timeout": 5.0,
            "read_timeout": 20.0,
            "max_pool_connections": 50,
            "retries": {"total_max_attempts": 1, "mode": "standard"},
        }
        if timeout is not None:
            connect, read, _ = timeout
            config.update(
                connect_timeout=connect,
                read_timeout=read,
            )
        return boto3.client(  # pyright: ignore[reportUnknownMemberType]
            "s3",
            aws_access_key_id=self.settings.upload.get_key(),
            aws_secret_access_key=self.settings.upload.get_secret(),
            aws_session_token=self.settings.upload.get_token(),
            config=Config(**config),
            region_name=self.settings.upload.get_region(),
            verify=certifi.where(),
        )

    def _client_for_timeouts(
        self,
        *,
        connect_timeout_seconds: typing.Optional[float],
        read_timeout_seconds: typing.Optional[float],
        total_timeout_seconds: typing.Optional[float],
    ) -> typing.Any:
        timeout = validate_upload_timeouts(
            connect_timeout_seconds=connect_timeout_seconds,
            read_timeout_seconds=read_timeout_seconds,
            total_timeout_seconds=total_timeout_seconds,
        )
        if timeout is None:
            return self.client
        if timeout not in self._timeout_clients:
            self._timeout_clients[timeout] = self._create_client(
                connect_timeout_seconds=timeout[0],
                read_timeout_seconds=timeout[1],
                total_timeout_seconds=timeout[2],
            )
        return self._timeout_clients[timeout]

    def get_object(self, url: str) -> typing.Optional[bytes]:
        if not self.client:
            self.logger.warning_msg("get_object no client")
            return None

        try:
            s3_bucket, s3_key = self.parse_url(url)

            response = self.client.get_object(Bucket=s3_bucket, Key=s3_key)

            return self._read_body(response)
        except Exception as e:
            self.logger.error_msg(f"[{url}] exception: {e}")
            raise

    def get_object_and_metadata(self, url: str) -> typing.Optional[typing.Tuple[bytes, typing.Dict[str, str]]]:
        if not self.client:
            self.logger.warning_msg("get_object no client")
            return None

        try:
            s3_bucket, s3_key = self.parse_url(url)

            response = self.client.get_object(Bucket=s3_bucket, Key=s3_key)

            body = self._read_body(response)

            return body, self._metadata_from_response(response)

        except Exception as e:
            self.logger.error_msg(f"[{url}] exception: {e}")
            raise

    def head_object(self, url: str) -> typing.Optional[typing.Dict[str, str]]:
        if not self.client:
            self.logger.warning_msg("head_object no client")
            return None

        try:
            s3_bucket, s3_key = self.parse_url(url)

            response = self.client.head_object(Bucket=s3_bucket, Key=s3_key)

            return self._metadata_from_response(response)
        except Exception as e:
            self.logger.error_msg(f"[{url}] exception: {e}")
            raise

    def parse_url(self, key: str) -> typing.Tuple[str, str]:
        if key.startswith("s3://"):
            s3_uri_parts = key.replace("s3://", "").split("/")
            s3_bucket = s3_uri_parts[0]
            s3_key = "/".join(s3_uri_parts[1:])
        else:
            s3_bucket = self.settings.upload.bucket
            s3_key = key
            if key.startswith("/"):
                s3_key = key[1:]

        return s3_bucket, s3_key

    def put_object(
        self,
        bucket: str,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> None:
        if not self.client:
            return

        self.client.put_object(
            Bucket=bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )

    @staticmethod
    def _read_body(response: typing.Mapping[str, typing.Any]) -> bytes:
        body = response.get("Body")
        if body is None:
            raise Exception("S3 response missing Body")

        try:
            return typing.cast(bytes, body.read())
        finally:
            close = getattr(body, "close", None)
            if callable(close):
                close()

    @staticmethod
    def _metadata_from_response(response: typing.Mapping[str, typing.Any]) -> typing.Dict[str, str]:
        etag = response.get("ETag", "")
        metadata: typing.Dict[str, str] = {"ETag": str(etag) if etag is not None else ""}

        last_modified = response.get("LastModified")
        if last_modified:
            timestamp = getattr(last_modified, "timestamp", None)
            metadata["LastModified"] = str(timestamp() if callable(timestamp) else last_modified)

        return metadata

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
    ) -> None:
        timeout = validate_upload_timeouts(
            connect_timeout_seconds=connect_timeout_seconds,
            read_timeout_seconds=read_timeout_seconds,
            total_timeout_seconds=total_timeout_seconds,
        )

        def put() -> None:
            client = self._client_for_timeouts(
                connect_timeout_seconds=connect_timeout_seconds,
                read_timeout_seconds=read_timeout_seconds,
                total_timeout_seconds=total_timeout_seconds,
            )
            if not client:
                return
            client.put_object(
                Bucket=bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
            )

        if timeout is None:
            put()
            return
        with wall_clock_operation_deadline(
            timeout[2],
            operation="S3 put_object",
        ):
            put()
