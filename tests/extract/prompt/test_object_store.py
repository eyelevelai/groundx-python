import threading
import time
import typing
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock, patch

from groundx.extract.prompt.object_store import ObjectStore
from groundx.extract.services.http import WallClockDeadlineExceeded
from groundx.extract.services.logger import Logger
from groundx.extract.services.upload import Upload
from groundx.extract.services.upload_s3 import S3Client
from groundx.extract.settings.settings import ContainerSettings, ContainerUploadSettings


class RecordingClient:
    def __init__(self) -> None:
        self.fetch_call: typing.Optional[typing.Tuple[str, typing.Dict[str, float]]] = None
        self.peek_call: typing.Optional[typing.Tuple[str, typing.Dict[str, float]]] = None

    def get_object_and_metadata(
        self,
        url: str,
        **kwargs: float,
    ) -> typing.Tuple[bytes, typing.Dict[str, str]]:
        self.fetch_call = (url, kwargs)
        return b"statement: {}", {"ETag": '"workflow-v1"'}

    def head_object(
        self,
        url: str,
        **kwargs: float,
    ) -> typing.Dict[str, str]:
        self.peek_call = (url, kwargs)
        return {"ETag": '"workflow-v1"'}


def _settings(upload_type: str = "s3") -> ContainerSettings:
    return ContainerSettings(
        broker="",
        service="object-store",
        upload=ContainerUploadSettings(
            base_domain="",
            bucket="eyelevel",
            type=upload_type,
            url="",
        ),
        workers=1,
    )


def _upload(client: typing.Any) -> Upload:
    upload = Upload.__new__(Upload)
    upload.client = client
    return upload


def test_object_store_fetch_uses_complete_bounded_read_contract() -> None:
    client = RecordingClient()
    with patch(
        "groundx.extract.prompt.object_store.Upload",
        return_value=_upload(client),
    ):
        store = ObjectStore(settings=_settings(), logger=Logger("test", "debug"))

    assert store.fetch("workflow-1") == ("statement: {}", "workflow-v1")
    assert client.fetch_call == (
        "workflows/extract/workflow-1.yaml",
        {
            "connect_timeout_seconds": 5.0,
            "read_timeout_seconds": 20.0,
            "total_timeout_seconds": 25.0,
        },
    )


def test_object_store_minio_reads_do_not_provision_bucket() -> None:
    with patch("minio.Minio") as create_client:
        client = create_client.return_value
        response = Mock()
        response.read.return_value = b"statement: {}"
        response.headers = {"ETag": '"workflow-v1"'}
        client.get_object.return_value = response
        client.stat_object.return_value = type(
            "Stat",
            (),
            {"etag": "workflow-v1", "last_modified": None},
        )()
        store = ObjectStore(
            settings=_settings(upload_type="minio"),
            logger=Logger("test", "debug"),
        )
        assert store.fetch("workflow-1") == ("statement: {}", "workflow-v1")
        assert store.peek("workflow-1") == "workflow-v1"

    assert create_client.call_count == 3
    client.bucket_exists.assert_not_called()
    client.make_bucket.assert_not_called()
    client.set_bucket_policy.assert_not_called()


def test_object_store_peek_uses_complete_bounded_head_contract() -> None:
    client = RecordingClient()
    with patch(
        "groundx.extract.prompt.object_store.Upload",
        return_value=_upload(client),
    ):
        store = ObjectStore(settings=_settings(), logger=Logger("test", "debug"))

    assert store.peek("workflow-1") == "workflow-v1"
    assert client.peek_call == (
        "workflows/extract/workflow-1.yaml",
        {
            "connect_timeout_seconds": 5.0,
            "read_timeout_seconds": 20.0,
        },
    )


def test_object_store_fetch_worker_deadline_closes_stalled_s3_body() -> None:
    class StalledBody:
        def __init__(self) -> None:
            self.closed = False
            self.closed_event = threading.Event()

        def read(self) -> bytes:
            if not self.closed_event.wait(timeout=2):
                raise AssertionError("ObjectStore deadline did not close S3 body")
            return b"statement: {}"

        def close(self) -> None:
            self.closed = True
            self.closed_event.set()

    class StalledS3:
        def __init__(self) -> None:
            self.body = StalledBody()

        def get_object(self, **_kwargs: str) -> typing.Dict[str, typing.Any]:
            return {"Body": self.body, "ETag": '"workflow-v1"'}

        def close(self) -> None:
            pass

    settings = _settings(upload_type="")
    storage = S3Client(settings, Logger("test", "debug"))
    bounded = StalledS3()
    setattr(storage, "_create_client", Mock(return_value=bounded))

    with (
        patch(
            "groundx.extract.prompt.object_store.Upload",
            return_value=_upload(storage),
        ),
        patch(
            "groundx.extract.prompt.object_store.OBJECT_STORE_CONNECT_TIMEOUT_SECONDS",
            0.01,
        ),
        patch(
            "groundx.extract.prompt.object_store.OBJECT_STORE_READ_TIMEOUT_SECONDS",
            0.01,
        ),
        patch(
            "groundx.extract.prompt.object_store.OBJECT_STORE_TOTAL_TIMEOUT_SECONDS",
            0.06,
        ),
    ):
        store = ObjectStore(settings=settings, logger=Logger("test", "debug"))

        started = time.monotonic()
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(store.fetch, "workflow-1")
            try:
                future.result(timeout=1)
            except WallClockDeadlineExceeded as exc:
                assert "S3 get_object_and_metadata exceeded" in str(exc)
            else:
                raise AssertionError("stalled ObjectStore fetch should time out")

    assert time.monotonic() - started < 0.15
    assert bounded.body.closed
