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


class MinIOClient:
    def __init__(
        self,
        settings: ContainerSettings,
        logger: Logger,
    ) -> None:
        self.settings = settings
        self.client = None
        self._timeout_clients = TimeoutClientCache(self._close_client)
        self.logger = logger
        if self.settings.upload.type == "minio":
            self.client = self._create_client()

    def provision_bucket(self) -> None:
        """Explicitly create and publish the configured MinIO bucket."""
        if not self.client or self.client.bucket_exists(self.settings.upload.bucket):
            return

        import json

        try:
            self.client.make_bucket(self.settings.upload.bucket)
            self.logger.info_msg(f"Bucket '{self.settings.upload.bucket}' created.")
            self.client.set_bucket_policy(
                self.settings.upload.bucket,
                json.dumps(
                    {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Principal": {"AWS": ["*"]},
                                "Action": ["s3:GetObject"],
                                "Resource": [f"arn:aws:s3:::{self.settings.upload.bucket}/*"],
                            }
                        ],
                    }
                ),
            )
        except Exception as e:
            self.logger.warning_msg(str(e))
            self.logger.warning_msg(f"error creating bucket [{self.settings.upload.bucket}]")

    def _create_client(
        self,
        *,
        connect_timeout_seconds: typing.Optional[float] = None,
        read_timeout_seconds: typing.Optional[float] = None,
        total_timeout_seconds: typing.Optional[float] = None,
    ) -> typing.Any:
        import urllib3
        from minio import Minio

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
            connect, read, total = 5.0, 20.0, None
        else:
            connect, read = transport
            total = total_timeout_seconds

        pool_kwargs: typing.Dict[str, typing.Any] = {
            "timeout": urllib3.Timeout(
                connect=connect,
                read=read,
                total=total,
            ),
            "retries": False,
        }
        if self.settings.upload.ssl:
            import certifi

            pool_kwargs.update(
                cert_reqs="CERT_REQUIRED",
                ca_certs=certifi.where(),
            )
        return Minio(
            self.settings.upload.base_domain,
            access_key=self.settings.upload.get_key(),
            secret_key=self.settings.upload.get_secret(),
            region=self.settings.upload.get_region(),
            session_token=self.settings.upload.get_token(),
            secure=self.settings.upload.ssl,
            http_client=urllib3.PoolManager(**pool_kwargs),
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
        http_client = getattr(client, "_http", None)
        clear = getattr(http_client, "clear", None)
        if callable(clear):
            clear()

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
                    return None

                from minio.error import S3Error

                try:
                    response = client.get_object(
                        self.settings.upload.bucket,
                        self.parse_url(url),
                    )

                    return read_response_body_with_deadline(
                        response.read,
                        lambda: self._close_response(response),
                        abort_response=lambda: self._abort_response(response),
                        total_timeout_seconds=timeout[2] if timeout is not None else None,
                        started_at=started_at,
                        operation="MinIO get_object",
                    )
                except S3Error as e:
                    self.logger.error_msg(f"Failed to get object from [{url}] [{self.parse_url(url)}]: {str(e)}")
                    raise

        if timeout is None:
            return get()
        with wall_clock_operation_deadline(
            timeout[2],
            operation="MinIO get_object",
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
                    return None

                from minio.error import S3Error

                try:
                    response = client.get_object(
                        self.settings.upload.bucket,
                        self.parse_url(url),
                    )
                    body = read_response_body_with_deadline(
                        response.read,
                        lambda: self._close_response(response),
                        abort_response=lambda: self._abort_response(response),
                        total_timeout_seconds=timeout[2] if timeout is not None else None,
                        started_at=started_at,
                        operation="MinIO get_object_and_metadata",
                    )
                    metadata = self._metadata_from_get_response(response)
                    return body, metadata
                except S3Error as e:
                    self.logger.error_msg(f"Failed to get object from [{url}] [{self.parse_url(url)}]: {str(e)}")
                    raise

        if timeout is None:
            return get()
        with wall_clock_operation_deadline(
            timeout[2],
            operation="MinIO get_object_and_metadata",
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
                    return None

                from minio.error import S3Error

                try:
                    response = client.stat_object(
                        self.settings.upload.bucket,
                        self.parse_url(url),
                    )
                    if not response:
                        return None

                    res: typing.Dict[str, str] = {}
                    if response.etag:
                        res["ETag"] = response.etag
                    if response.last_modified:
                        res["LastModified"] = str(response.last_modified.timestamp())
                    return res
                except S3Error as e:
                    self.logger.error_msg(f"Failed to get object from [{url}] [{self.parse_url(url)}]: {str(e)}")
                    raise

        return head()

    def parse_url(self, ur: str) -> str:
        minio_uri_parts = ur.replace("s3://", "").split("/")
        if len(minio_uri_parts) > 0 and minio_uri_parts[0] == "":
            minio_uri_parts = minio_uri_parts[1:]

        nur = "/".join(minio_uri_parts)
        if nur.startswith("/"):
            nur = nur[1:]

        if len(minio_uri_parts) < 1:
            if minio_uri_parts[0] == self.settings.upload.bucket:
                return ""

            return nur

        if minio_uri_parts[0] == self.settings.upload.bucket:
            nur = "/".join(minio_uri_parts[1:])

            if nur.startswith("/"):
                nur = nur[1:]

        return nur

    def put_object(
        self,
        bucket: str,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> None:
        if not self.client:
            return

        import io

        from minio.error import S3Error

        try:
            if isinstance(data, str):
                data = data.encode("utf-8")

            self.client.put_object(
                bucket_name=bucket,
                object_name=key,
                data=io.BytesIO(data),
                length=len(data),
                content_type=content_type,
            )
        except S3Error as e:
            self.logger.error_msg(f"Failed to put object in [{bucket}/{key}]: {str(e)}")
            raise

    @staticmethod
    def _close_response(response: typing.Any) -> None:
        close = getattr(response, "close", None)
        if callable(close):
            close()

        release_conn = getattr(response, "release_conn", None)
        if callable(release_conn):
            release_conn()

    @classmethod
    def _abort_response(cls, response: typing.Any) -> None:
        shutdown = getattr(response, "shutdown", None)
        if callable(shutdown):
            try:
                shutdown()
            except (OSError, RuntimeError, ValueError):
                pass
        cls._close_response(response)

    @staticmethod
    def _metadata_from_get_response(response: typing.Any) -> typing.Dict[str, str]:
        headers = getattr(response, "headers", {})
        etag = headers.get("ETag") or headers.get("etag")
        result: typing.Dict[str, str] = {}
        if etag:
            result["ETag"] = str(etag).strip('"')

        last_modified = headers.get("Last-Modified") or headers.get("last-modified")
        if last_modified:
            from email.utils import parsedate_to_datetime

            result["LastModified"] = str(parsedate_to_datetime(str(last_modified)).timestamp())
        return result

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
        """Write with native transport bounds, never a hard Python deadline.

        ``transport_total_timeout_seconds`` configures urllib3. The legacy
        ``total_timeout_seconds`` alias is retained for compatibility. Neither
        is a Python hard deadline; callers own the surrounding deadline.
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
        minio_object_tags: typing.Optional[typing.Any] = None
        if frozen_object_tags is not None:
            from minio.commonconfig import Tags

            minio_object_tags = Tags.new_object_tags()
            for tag_key, tag_value in frozen_object_tags.items():
                minio_object_tags[tag_key] = tag_value

        def put() -> None:
            client_context = self._client_for_timeouts(
                connect_timeout_seconds=connect_timeout_seconds,
                read_timeout_seconds=read_timeout_seconds,
                total_timeout_seconds=transport_total,
            )
            with client_context as client:
                if not client:
                    return
                import io

                put_kwargs: typing.Dict[str, typing.Any] = {
                    "bucket_name": bucket,
                    "object_name": key,
                    "data": io.BytesIO(data),
                    "length": len(data),
                    "content_type": content_type,
                }
                if minio_object_tags is not None:
                    put_kwargs["tags"] = minio_object_tags
                client.put_object(
                    **put_kwargs,
                )

        put()
