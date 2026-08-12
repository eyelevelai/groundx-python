import contextlib
import math
import re
import threading
import typing
from collections import OrderedDict
from types import MappingProxyType

from ..settings.settings import ContainerSettings
from .logger import Logger

OBJECT_STORE_CONNECT_TIMEOUT_SECONDS = 5.0
OBJECT_STORE_READ_TIMEOUT_SECONDS = 20.0
OBJECT_STORE_TOTAL_TIMEOUT_SECONDS = 25.0
MAX_CACHED_TIMEOUT_CLIENTS = 8
MAX_OBJECT_TAGS = 10
MAX_OBJECT_TAG_KEY_LENGTH = 128
MAX_OBJECT_TAG_VALUE_LENGTH = 256
OBJECT_TAG_SAFE_PATTERN = re.compile(r"^[A-Za-z0-9 _.:/=+\-@]+$")


class _TimeoutClientEntry:
    def __init__(self, client: typing.Any) -> None:
        self.client = client
        self.active_leases = 0
        self.close_pending = False
        self.closed = False


TimeoutClientKey = typing.Tuple[float, float, typing.Optional[float]]


class TimeoutClientCache:
    def __init__(self, close_client: typing.Callable[[typing.Any], None]) -> None:
        self._clients: OrderedDict[TimeoutClientKey, _TimeoutClientEntry] = OrderedDict()
        self._close_client = close_client
        self._lock = threading.Lock()

    def _get_or_create_locked(
        self,
        timeout: TimeoutClientKey,
        create_client: typing.Callable[[], typing.Any],
    ) -> typing.Tuple[_TimeoutClientEntry, typing.Optional[typing.Any]]:
        entry = self._clients.pop(timeout, None)
        if entry is None:
            entry = _TimeoutClientEntry(create_client())
        self._clients[timeout] = entry

        close_client: typing.Optional[typing.Any] = None
        if len(self._clients) > MAX_CACHED_TIMEOUT_CLIENTS:
            _, evicted = self._clients.popitem(last=False)
            close_client = self._retire_locked(evicted)
        return entry, close_client

    @staticmethod
    def _retire_locked(entry: _TimeoutClientEntry) -> typing.Optional[typing.Any]:
        entry.close_pending = True
        if entry.active_leases == 0 and not entry.closed:
            entry.closed = True
            return entry.client
        return None

    def _close_safely(self, client: typing.Optional[typing.Any]) -> None:
        if client is None:
            return
        try:
            self._close_client(client)
        except Exception:
            pass

    @contextlib.contextmanager
    def lease(
        self,
        timeout: TimeoutClientKey,
        create_client: typing.Callable[[], typing.Any],
    ) -> typing.Iterator[typing.Any]:
        with self._lock:
            entry, close_client = self._get_or_create_locked(timeout, create_client)
            entry.active_leases += 1
        self._close_safely(close_client)

        try:
            yield entry.client
        finally:
            close_client = None
            with self._lock:
                entry.active_leases -= 1
                if entry.close_pending:
                    close_client = self._retire_locked(entry)
            self._close_safely(close_client)


@typing.runtime_checkable
class UploadClient(typing.Protocol):
    def provision_bucket(self) -> None: ...

    def get_object(
        self,
        url: str,
        *,
        connect_timeout_seconds: typing.Optional[float] = None,
        read_timeout_seconds: typing.Optional[float] = None,
        total_timeout_seconds: typing.Optional[float] = None,
    ) -> typing.Optional[bytes]: ...

    def get_object_and_metadata(
        self,
        url: str,
        *,
        connect_timeout_seconds: typing.Optional[float] = None,
        read_timeout_seconds: typing.Optional[float] = None,
        total_timeout_seconds: typing.Optional[float] = None,
    ) -> typing.Optional[typing.Tuple[bytes, typing.Dict[str, str]]]: ...

    def head_object(
        self,
        url: str,
        *,
        connect_timeout_seconds: typing.Optional[float] = None,
        read_timeout_seconds: typing.Optional[float] = None,
    ) -> typing.Optional[typing.Dict[str, str]]: ...

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
        *,
        connect_timeout_seconds: typing.Optional[float] = None,
        read_timeout_seconds: typing.Optional[float] = None,
        total_timeout_seconds: typing.Optional[float] = None,
        transport_total_timeout_seconds: typing.Optional[float] = None,
        object_tags: typing.Optional[typing.Mapping[str, str]] = None,
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

        self.logger.info_msg(f"upload type [{self.settings.upload.type}] [{self.settings.upload.bucket}]")

        if self.settings.upload.type == "minio":
            from .upload_minio import MinIOClient

            self.client = MinIOClient(self.settings, self.logger)
        elif self.settings.upload.type == "s3":
            from .upload_s3 import S3Client

            self.client = S3Client(self.settings, self.logger)
        else:
            raise Exception(f"unsupported upload.type [{self.settings.upload.type}]")

    def get_object(
        self,
        url: str,
        *,
        connect_timeout_seconds: typing.Optional[float] = None,
        read_timeout_seconds: typing.Optional[float] = None,
        total_timeout_seconds: typing.Optional[float] = None,
    ) -> typing.Optional[bytes]:
        """Read with native connect/read bounds and a cancellable body deadline."""
        timeout_kwargs: typing.Dict[str, float] = {}
        if connect_timeout_seconds is not None or read_timeout_seconds is not None or total_timeout_seconds is not None:
            timeout_kwargs = {
                "connect_timeout_seconds": typing.cast(float, connect_timeout_seconds),
                "read_timeout_seconds": typing.cast(float, read_timeout_seconds),
                "total_timeout_seconds": typing.cast(float, total_timeout_seconds),
            }
        return self.client.get_object(url, **timeout_kwargs)

    def provision_bucket(self) -> None:
        """Run backend provisioning only when the caller requests it."""
        self.client.provision_bucket()

    def get_object_and_metadata(
        self,
        url: str,
        *,
        connect_timeout_seconds: typing.Optional[float] = None,
        read_timeout_seconds: typing.Optional[float] = None,
        total_timeout_seconds: typing.Optional[float] = None,
    ) -> typing.Optional[typing.Tuple[bytes, typing.Dict[str, str]]]:
        """Read body and metadata with the complete GET timeout contract."""
        timeout_kwargs: typing.Dict[str, float] = {}
        if connect_timeout_seconds is not None or read_timeout_seconds is not None or total_timeout_seconds is not None:
            timeout_kwargs = {
                "connect_timeout_seconds": typing.cast(float, connect_timeout_seconds),
                "read_timeout_seconds": typing.cast(float, read_timeout_seconds),
                "total_timeout_seconds": typing.cast(float, total_timeout_seconds),
            }
        return self.client.get_object_and_metadata(url, **timeout_kwargs)

    def head_object(
        self,
        url: str,
        *,
        connect_timeout_seconds: typing.Optional[float] = None,
        read_timeout_seconds: typing.Optional[float] = None,
    ) -> typing.Optional[typing.Dict[str, str]]:
        """Read metadata with native connect/read bounds, not a hard total."""
        timeout_kwargs: typing.Dict[str, float] = {}
        if connect_timeout_seconds is not None or read_timeout_seconds is not None:
            timeout_kwargs = {
                "connect_timeout_seconds": typing.cast(float, connect_timeout_seconds),
                "read_timeout_seconds": typing.cast(float, read_timeout_seconds),
            }
        return self.client.head_object(url, **timeout_kwargs)

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
        *,
        connect_timeout_seconds: typing.Optional[float] = None,
        read_timeout_seconds: typing.Optional[float] = None,
        total_timeout_seconds: typing.Optional[float] = None,
        transport_total_timeout_seconds: typing.Optional[float] = None,
        object_tags: typing.Optional[typing.Mapping[str, str]] = None,
    ) -> None:
        """Write with transport-native bounds, not a hard wall-clock deadline.

        ``transport_total_timeout_seconds`` names the preferred transport
        setting. ``total_timeout_seconds`` remains a compatibility alias.
        Neither is a Python hard deadline; S3 supports only connect/read bounds.
        """
        transport_total = resolve_transport_total_timeout(
            total_timeout_seconds=total_timeout_seconds,
            transport_total_timeout_seconds=transport_total_timeout_seconds,
        )
        frozen_object_tags = freeze_object_tags(object_tags)
        timeout_kwargs: typing.Dict[str, typing.Any] = {}
        if connect_timeout_seconds is not None or read_timeout_seconds is not None or transport_total is not None:
            timeout_kwargs = {
                "connect_timeout_seconds": typing.cast(float, connect_timeout_seconds),
                "read_timeout_seconds": typing.cast(float, read_timeout_seconds),
            }
            if transport_total_timeout_seconds is not None:
                timeout_kwargs["transport_total_timeout_seconds"] = typing.cast(
                    float,
                    transport_total,
                )
            elif total_timeout_seconds is not None:
                timeout_kwargs["total_timeout_seconds"] = typing.cast(
                    float,
                    transport_total,
                )
        if frozen_object_tags is not None:
            timeout_kwargs["object_tags"] = frozen_object_tags
        self.client.put_json_stream(
            bucket,
            key,
            data,
            content_type,
            **timeout_kwargs,
        )


def freeze_object_tags(
    object_tags: object,
) -> typing.Optional[typing.Mapping[str, str]]:
    """Validate and detach optional object tags before storage I/O."""
    if object_tags is None:
        return None
    if not isinstance(object_tags, typing.Mapping):
        raise ValueError("object_tags must be a mapping")

    raw_tags = typing.cast(typing.Mapping[object, object], object_tags)
    items = tuple(raw_tags.items())
    if not items:
        return None
    if len(items) > MAX_OBJECT_TAGS:
        raise ValueError(f"object_tags supports at most {MAX_OBJECT_TAGS} tags")

    validated_items: typing.List[typing.Tuple[str, str]] = []
    for key, value in items:
        if not isinstance(key, str) or not isinstance(value, str):
            raise ValueError("object tag keys and values must be strings")
        if not key:
            raise ValueError("object tag keys must be nonempty")
        if not value:
            raise ValueError("object tag values must be nonempty")
        if len(key) > MAX_OBJECT_TAG_KEY_LENGTH:
            raise ValueError(f"object tag keys must be at most {MAX_OBJECT_TAG_KEY_LENGTH} characters")
        if len(value) > MAX_OBJECT_TAG_VALUE_LENGTH:
            raise ValueError(f"object tag values must be at most {MAX_OBJECT_TAG_VALUE_LENGTH} characters")
        if OBJECT_TAG_SAFE_PATTERN.fullmatch(key) is None:
            raise ValueError("object tag keys contain unsupported characters")
        if OBJECT_TAG_SAFE_PATTERN.fullmatch(value) is None:
            raise ValueError("object tag values contain unsupported characters")
        validated_items.append((key, value))

    return MappingProxyType(dict(sorted(validated_items)))


def validate_upload_timeouts(
    *,
    connect_timeout_seconds: typing.Optional[float],
    read_timeout_seconds: typing.Optional[float],
    total_timeout_seconds: typing.Optional[float],
) -> typing.Optional[typing.Tuple[float, float, float]]:
    values = (
        connect_timeout_seconds,
        read_timeout_seconds,
        total_timeout_seconds,
    )
    if all(value is None for value in values):
        return None
    if any(value is None for value in values):
        raise ValueError("connect, read, and total upload timeouts are all required")
    connect = typing.cast(float, connect_timeout_seconds)
    read = typing.cast(float, read_timeout_seconds)
    total = typing.cast(float, total_timeout_seconds)
    if not all(math.isfinite(value) for value in (connect, read, total)):
        raise ValueError("upload timeouts must be finite")
    if connect <= 0 or read <= 0 or total <= 0:
        raise ValueError("upload timeouts must be positive")
    if connect + read > total:
        raise ValueError("connect and read upload timeouts exceed total timeout")
    return connect, read, total


def validate_transport_timeouts(
    *,
    connect_timeout_seconds: typing.Optional[float],
    read_timeout_seconds: typing.Optional[float],
) -> typing.Optional[typing.Tuple[float, float]]:
    values = (connect_timeout_seconds, read_timeout_seconds)
    if all(value is None for value in values):
        return None
    if any(value is None for value in values):
        raise ValueError("connect and read upload timeouts are both required")
    connect = typing.cast(float, connect_timeout_seconds)
    read = typing.cast(float, read_timeout_seconds)
    if not all(math.isfinite(value) for value in (connect, read)):
        raise ValueError("upload timeouts must be finite")
    if connect <= 0 or read <= 0:
        raise ValueError("upload timeouts must be positive")
    return connect, read


def resolve_transport_total_timeout(
    *,
    total_timeout_seconds: typing.Optional[float],
    transport_total_timeout_seconds: typing.Optional[float],
) -> typing.Optional[float]:
    if total_timeout_seconds is not None and transport_total_timeout_seconds is not None:
        raise ValueError("total_timeout_seconds and transport_total_timeout_seconds are mutually exclusive")
    if transport_total_timeout_seconds is not None:
        return transport_total_timeout_seconds
    return total_timeout_seconds
