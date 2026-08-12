import contextlib
import time
import typing

from ..settings.settings import ContainerSettings
from .http import read_response_body_with_deadline, wall_clock_operation_deadline
from .logger import Logger
from .upload import (
    TimeoutClientCache,
    freeze_object_tags,
    resolve_transport_total_timeout,
    validate_transport_timeouts,
    validate_upload_timeouts,
)


class S3Client:
    def __init__(self, settings: ContainerSettings, logger: Logger) -> None:
        self.settings = settings
        self.client = None
        self._timeout_clients = TimeoutClientCache(self._close_client)
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

        transport = validate_transport_timeouts(
            connect_timeout_seconds=connect_timeout_seconds,
            read_timeout_seconds=read_timeout_seconds,
        )
        if total_timeout_seconds is not None:
            validate_upload_timeouts(
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
        if transport is not None:
            connect, read = transport
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
    ) -> typing.ContextManager[typing.Any]:
        transport = validate_transport_timeouts(
            connect_timeout_seconds=connect_timeout_seconds,
            read_timeout_seconds=read_timeout_seconds,
        )
        if total_timeout_seconds is not None:
            validate_upload_timeouts(
                connect_timeout_seconds=connect_timeout_seconds,
                read_timeout_seconds=read_timeout_seconds,
                total_timeout_seconds=total_timeout_seconds,
            )
        if transport is None:
            return contextlib.nullcontext(self.client)
        return self._timeout_clients.lease(
            (transport[0], transport[1], total_timeout_seconds),
            lambda: self._create_client(
                connect_timeout_seconds=transport[0],
                read_timeout_seconds=transport[1],
                total_timeout_seconds=total_timeout_seconds,
            ),
        )

    @staticmethod
    def _close_client(client: typing.Any) -> None:
        close = getattr(client, "close", None)
        if callable(close):
            close()

    def provision_bucket(self) -> None:
        """S3 bucket provisioning is owned outside this SDK."""
        raise NotImplementedError("S3 bucket provisioning is not supported")

    def get_object(
        self,
        url: str,
        *,
        connect_timeout_seconds: typing.Optional[float] = None,
        read_timeout_seconds: typing.Optional[float] = None,
        total_timeout_seconds: typing.Optional[float] = None,
    ) -> typing.Optional[bytes]:
        timeout = validate_upload_timeouts(
            connect_timeout_seconds=connect_timeout_seconds,
            read_timeout_seconds=read_timeout_seconds,
            total_timeout_seconds=total_timeout_seconds,
        )
        started_at = time.monotonic() if timeout is not None else None

        def get() -> typing.Optional[bytes]:
            client_context = self._client_for_timeouts(
                connect_timeout_seconds=connect_timeout_seconds,
                read_timeout_seconds=read_timeout_seconds,
                total_timeout_seconds=total_timeout_seconds,
            )
            with client_context as client:
                if not client:
                    self.logger.warning_msg("get_object no client")
                    return None

                try:
                    s3_bucket, s3_key = self.parse_url(url)
                    response = client.get_object(Bucket=s3_bucket, Key=s3_key)
                    return self._read_body(
                        response,
                        total_timeout_seconds=timeout[2] if timeout is not None else None,
                        started_at=started_at,
                        operation="S3 get_object",
                    )
                except Exception as e:
                    self.logger.error_msg(f"[{url}] exception: {e}")
                    raise

        if timeout is None:
            return get()
        with wall_clock_operation_deadline(
            timeout[2],
            operation="S3 get_object",
        ):
            return get()

    def get_object_and_metadata(
        self,
        url: str,
        *,
        connect_timeout_seconds: typing.Optional[float] = None,
        read_timeout_seconds: typing.Optional[float] = None,
        total_timeout_seconds: typing.Optional[float] = None,
    ) -> typing.Optional[typing.Tuple[bytes, typing.Dict[str, str]]]:
        timeout = validate_upload_timeouts(
            connect_timeout_seconds=connect_timeout_seconds,
            read_timeout_seconds=read_timeout_seconds,
            total_timeout_seconds=total_timeout_seconds,
        )
        started_at = time.monotonic() if timeout is not None else None

        def get() -> typing.Optional[typing.Tuple[bytes, typing.Dict[str, str]]]:
            client_context = self._client_for_timeouts(
                connect_timeout_seconds=connect_timeout_seconds,
                read_timeout_seconds=read_timeout_seconds,
                total_timeout_seconds=total_timeout_seconds,
            )
            with client_context as client:
                if not client:
                    self.logger.warning_msg("get_object no client")
                    return None

                try:
                    s3_bucket, s3_key = self.parse_url(url)
                    response = client.get_object(Bucket=s3_bucket, Key=s3_key)
                    body = self._read_body(
                        response,
                        total_timeout_seconds=timeout[2] if timeout is not None else None,
                        started_at=started_at,
                        operation="S3 get_object_and_metadata",
                    )
                    return body, self._metadata_from_response(response)
                except Exception as e:
                    self.logger.error_msg(f"[{url}] exception: {e}")
                    raise

        if timeout is None:
            return get()
        with wall_clock_operation_deadline(
            timeout[2],
            operation="S3 get_object_and_metadata",
        ):
            return get()

    def head_object(
        self,
        url: str,
        *,
        connect_timeout_seconds: typing.Optional[float] = None,
        read_timeout_seconds: typing.Optional[float] = None,
    ) -> typing.Optional[typing.Dict[str, str]]:
        validate_transport_timeouts(
            connect_timeout_seconds=connect_timeout_seconds,
            read_timeout_seconds=read_timeout_seconds,
        )

        def head() -> typing.Optional[typing.Dict[str, str]]:
            client_context = self._client_for_timeouts(
                connect_timeout_seconds=connect_timeout_seconds,
                read_timeout_seconds=read_timeout_seconds,
                total_timeout_seconds=None,
            )
            with client_context as client:
                if not client:
                    self.logger.warning_msg("head_object no client")
                    return None

                try:
                    s3_bucket, s3_key = self.parse_url(url)
                    response = client.head_object(Bucket=s3_bucket, Key=s3_key)
                    return self._metadata_from_response(response)
                except Exception as e:
                    self.logger.error_msg(f"[{url}] exception: {e}")
                    raise

        return head()

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
    def _read_body(
        response: typing.Mapping[str, typing.Any],
        *,
        total_timeout_seconds: typing.Optional[float] = None,
        started_at: typing.Optional[float] = None,
        operation: str = "S3 get_object",
    ) -> bytes:
        body = response.get("Body")
        if body is None:
            raise Exception("S3 response missing Body")

        def close_body() -> None:
            close = getattr(body, "close", None)
            if callable(close):
                close()

        def abort_body() -> None:
            raw_stream = getattr(body, "_raw_stream", None)
            shutdown = getattr(raw_stream, "shutdown", None)
            if callable(shutdown):
                try:
                    shutdown()
                except (OSError, RuntimeError, ValueError):
                    pass
            close_body()

        return read_response_body_with_deadline(
            lambda: typing.cast(bytes, body.read()),
            close_body,
            abort_response=abort_body,
            total_timeout_seconds=total_timeout_seconds,
            started_at=started_at,
            operation=operation,
        )

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
        transport_total_timeout_seconds: typing.Optional[float] = None,
        object_tags: typing.Optional[typing.Mapping[str, str]] = None,
    ) -> None:
        """Write with native connect/read bounds and no hard wall-clock claim.

        Botocore has no operation-total setting.
        ``transport_total_timeout_seconds`` is preferred. The legacy
        ``total_timeout_seconds`` alias is retained for compatibility. Botocore
        does not enforce either; callers own the surrounding hard deadline.
        """
        transport_total = resolve_transport_total_timeout(
            total_timeout_seconds=total_timeout_seconds,
            transport_total_timeout_seconds=transport_total_timeout_seconds,
        )
        validate_upload_timeouts(
            connect_timeout_seconds=connect_timeout_seconds,
            read_timeout_seconds=read_timeout_seconds,
            total_timeout_seconds=transport_total,
        )
        frozen_object_tags = freeze_object_tags(object_tags)
        put_kwargs: typing.Dict[str, typing.Any] = {
            "Bucket": bucket,
            "Key": key,
            "Body": data,
            "ContentType": content_type,
        }
        if frozen_object_tags is not None:
            from urllib.parse import urlencode

            put_kwargs["Tagging"] = urlencode(tuple(frozen_object_tags.items()))

        def put() -> None:
            client_context = self._client_for_timeouts(
                connect_timeout_seconds=connect_timeout_seconds,
                read_timeout_seconds=read_timeout_seconds,
                total_timeout_seconds=transport_total,
            )
            with client_context as client:
                if not client:
                    return
                client.put_object(**put_kwargs)

        put()
