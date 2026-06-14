import typing

from .logger import Logger
from ..settings.settings import ContainerSettings


class S3Client:
    def __init__(self, settings: ContainerSettings, logger: Logger) -> None:
        self.settings = settings
        self.client = None
        self.logger = logger
        if self.settings.upload.type == "s3":
            import boto3, certifi
            from botocore.config import Config

            self.client = boto3.client(  # pyright: ignore[reportUnknownMemberType]
                "s3",
                aws_access_key_id=self.settings.upload.get_key(),
                aws_secret_access_key=self.settings.upload.get_secret(),
                aws_session_token=self.settings.upload.get_token(),
                config=Config(max_pool_connections=50),
                region_name=self.settings.upload.get_region(),
                verify=certifi.where(),
            )

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

    def get_object_and_metadata(
        self, url: str
    ) -> typing.Optional[typing.Tuple[bytes, typing.Dict[str, str]]]:
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
    def _read_body(response: typing.Dict[str, typing.Any]) -> bytes:
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
    def _metadata_from_response(
        response: typing.Dict[str, typing.Any]
    ) -> typing.Dict[str, str]:
        etag = response.get("ETag", "")
        metadata: typing.Dict[str, str] = {
            "ETag": str(etag) if etag is not None else ""
        }

        last_modified = response.get("LastModified")
        if last_modified:
            timestamp = getattr(last_modified, "timestamp", None)
            metadata["LastModified"] = str(
                timestamp() if callable(timestamp) else last_modified
            )

        return metadata

    def put_json_stream(
        self,
        bucket: str,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> None:
        if not self.client:
            return

        import io

        json_stream = io.BytesIO()

        if isinstance(data, str):
            data = data.encode("utf-8")

        json_stream.write(data)
        json_stream.seek(0)

        self.put_object(
            bucket,
            key,
            json_stream.getvalue(),
            content_type,
        )
