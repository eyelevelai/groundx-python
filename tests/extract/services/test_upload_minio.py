import contextlib
import sys
import threading
import time
import types
import typing
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock, patch

from groundx.extract.services.http import WallClockDeadlineExceeded
from groundx.extract.services.logger import Logger
from groundx.extract.services.upload_minio import MinIOClient
from groundx.extract.settings.settings import ContainerSettings, ContainerUploadSettings


class FakeMinioResponse:
    def __init__(self, body: bytes) -> None:
        self.body = body
        self.closed = False
        self.released = False
        self.headers = {
            "ETag": '"etag-1"',
        }

    def read(self) -> bytes:
        return self.body

    def close(self) -> None:
        self.closed = True

    def release_conn(self) -> None:
        self.released = True


class FakeMinioClient:
    def __init__(self) -> None:
        self.response = FakeMinioResponse(b"statement: {}")

    def get_object(self, bucket: str, key: str) -> FakeMinioResponse:
        return self.response

    def stat_object(self, bucket: str, key: str) -> typing.Any:
        return type(
            "Stat",
            (),
            {"etag": "etag-1", "last_modified": None},
        )()

    def put_object(self, **kwargs: typing.Any) -> None:
        self.put = kwargs


class TestMinIOClient(unittest.TestCase):
    def test_minio_client_has_bounded_io_and_no_hidden_retries(self) -> None:
        mock_minio = Mock()
        minio_module = types.ModuleType("minio")
        setattr(minio_module, "Minio", mock_minio)
        mock_minio.return_value.bucket_exists.return_value = True
        settings = ContainerSettings(
            broker="",
            service="minio",
            upload=ContainerUploadSettings(
                base_domain="minio.test",
                bucket="eyelevel",
                type="minio",
                url="",
            ),
            workers=1,
        )

        with patch.dict(sys.modules, {"minio": minio_module}):
            MinIOClient(settings, Logger("test", "debug"))

        http_client = mock_minio.call_args.kwargs["http_client"]
        timeout = http_client.connection_pool_kw["timeout"]
        self.assertEqual(timeout.connect_timeout, 5)
        self.assertEqual(timeout.read_timeout, 20)
        self.assertFalse(http_client.connection_pool_kw["retries"].total)

    def test_bucket_provisioning_is_explicit(self) -> None:
        cl = self._client()
        client = Mock()
        client.bucket_exists.return_value = False
        cl.client = client

        cl.provision_bucket()

        client.bucket_exists.assert_called_once_with("eyelevel")
        client.make_bucket.assert_called_once_with("eyelevel")
        client.set_bucket_policy.assert_called_once()

    def _client(self) -> MinIOClient:
        logger = Logger("parse_url", "debug")
        return MinIOClient(
            settings=ContainerSettings(
                broker="",
                service="parse_url",
                upload=ContainerUploadSettings(
                    base_domain="",
                    bucket="eyelevel",
                    type="",
                    url="",
                ),
                workers=1,
            ),
            logger=logger,
        )

    def test_load_parse_url_1(self) -> None:
        cl = self._client()

        obj = cl.parse_url("/eyelevel/layout")
        self.assertEqual(obj, "layout")

        obj = cl.parse_url("s3://eyelevel/prod/file")
        self.assertEqual(obj, "prod/file")

        obj = cl.parse_url("eyelevel/layout")
        self.assertEqual(obj, "layout")

        obj = cl.parse_url("/layout/prod")
        self.assertEqual(obj, "layout/prod")

        obj = cl.parse_url("layout/prod")
        self.assertEqual(obj, "layout/prod")

        obj = cl.parse_url(
            "/eyelevel/layout/raw/prod/db5915cc-69ae-4cea-884e-fa029712cd16/78b97664-47ac-4363-89d9-9004938d8161/1.jpg"
        )
        self.assertEqual(
            obj,
            "layout/raw/prod/db5915cc-69ae-4cea-884e-fa029712cd16/78b97664-47ac-4363-89d9-9004938d8161/1.jpg",
        )

    def test_get_object_closes_response(self) -> None:
        cl = self._client()
        fake = FakeMinioClient()
        cl.client = typing.cast(typing.Any, fake)

        with fake_minio_error_module():
            body = cl.get_object("s3://eyelevel/workflows/extract/latest.yaml")

        self.assertEqual(body, b"statement: {}")
        self.assertTrue(fake.response.closed)
        self.assertTrue(fake.response.released)

    def test_get_object_uses_bounded_client_and_closes_response(self) -> None:
        cl = self._client()
        bounded = FakeMinioClient()
        create_client = Mock(return_value=bounded)
        setattr(cl, "_create_client", create_client)

        with fake_minio_error_module():
            body = cl.get_object(
                "s3://eyelevel/workflows/extract/latest.yaml",
                connect_timeout_seconds=0.2,
                read_timeout_seconds=0.5,
                total_timeout_seconds=0.8,
            )

        self.assertEqual(body, b"statement: {}")
        self.assertTrue(bounded.response.closed)
        self.assertTrue(bounded.response.released)
        create_client.assert_called_once_with(
            connect_timeout_seconds=0.2,
            read_timeout_seconds=0.5,
            total_timeout_seconds=0.8,
        )

    def test_get_object_requires_complete_positive_timeout_budget(self) -> None:
        cl = self._client()
        cl.client = typing.cast(typing.Any, FakeMinioClient())

        with fake_minio_error_module():
            with self.assertRaisesRegex(ValueError, "all required"):
                cl.get_object(
                    "s3://eyelevel/workflow.yaml",
                    connect_timeout_seconds=0.2,
                )

            with self.assertRaisesRegex(ValueError, "must be positive"):
                cl.get_object(
                    "s3://eyelevel/workflow.yaml",
                    connect_timeout_seconds=0.2,
                    read_timeout_seconds=0,
                    total_timeout_seconds=0.8,
                )

            with self.assertRaisesRegex(ValueError, "exceed total"):
                cl.get_object(
                    "s3://eyelevel/workflow.yaml",
                    connect_timeout_seconds=0.4,
                    read_timeout_seconds=0.5,
                    total_timeout_seconds=0.8,
                )

    def test_timeout_client_cache_closes_evicted_http_pool(self) -> None:
        class Pool:
            def __init__(self) -> None:
                self.cleared = False

            def clear(self) -> None:
                self.cleared = True

        class Client:
            def __init__(self) -> None:
                setattr(self, "_http", Pool())

        cl = self._client()
        created: typing.List[Client] = []

        def create_client(**_kwargs: float) -> Client:
            client = Client()
            created.append(client)
            return client

        setattr(cl, "_create_client", create_client)
        cache = getattr(cl, "_timeout_clients")
        for total in range(1, 10):
            client_context = getattr(cl, "_client_for_timeouts")(
                connect_timeout_seconds=0.2,
                read_timeout_seconds=0.5,
                total_timeout_seconds=float(total),
            )
            with client_context:
                pass

        self.assertEqual(len(created), 9)
        self.assertEqual(len(getattr(cache, "_clients")), 8)
        self.assertTrue(typing.cast(Pool, getattr(created[0], "_http")).cleared)
        self.assertFalse(typing.cast(Pool, getattr(created[-1], "_http")).cleared)

    def test_get_object_total_deadline_includes_body_read_and_closes_response(
        self,
    ) -> None:
        class StalledResponse(FakeMinioResponse):
            def read(self) -> bytes:
                time.sleep(0.20)
                return super().read()

        class StalledMinioClient(FakeMinioClient):
            def __init__(self) -> None:
                self.response = StalledResponse(b"statement: {}")

        cl = self._client()
        bounded = StalledMinioClient()
        setattr(cl, "_create_client", Mock(return_value=bounded))

        started = time.monotonic()
        with fake_minio_error_module():
            with self.assertRaisesRegex(TimeoutError, "MinIO get_object exceeded"):
                cl.get_object(
                    "s3://eyelevel/workflow.yaml",
                    connect_timeout_seconds=0.01,
                    read_timeout_seconds=0.01,
                    total_timeout_seconds=0.06,
                )

        self.assertLess(time.monotonic() - started, 0.15)
        self.assertTrue(bounded.response.closed)
        self.assertTrue(bounded.response.released)

    def test_worker_thread_deadline_closes_stalled_response_and_raises_timeout(
        self,
    ) -> None:
        class StalledResponse(FakeMinioResponse):
            def __init__(self) -> None:
                super().__init__(b"statement: {}")
                self.closed_event = threading.Event()

            def read(self) -> bytes:
                if not self.closed_event.wait(timeout=2):
                    raise AssertionError("deadline did not close stalled MinIO response")
                return super().read()

            def close(self) -> None:
                super().close()
                self.closed_event.set()

        class StalledMinioClient(FakeMinioClient):
            def __init__(self) -> None:
                self.response = StalledResponse()

        cl = self._client()
        bounded = StalledMinioClient()
        setattr(cl, "_create_client", Mock(return_value=bounded))

        started = time.monotonic()
        with fake_minio_error_module(), ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                cl.get_object,
                "s3://eyelevel/workflow.yaml",
                connect_timeout_seconds=0.01,
                read_timeout_seconds=0.01,
                total_timeout_seconds=0.06,
            )
            with self.assertRaisesRegex(
                WallClockDeadlineExceeded,
                "MinIO get_object exceeded",
            ):
                future.result(timeout=1)

        self.assertLess(time.monotonic() - started, 0.15)
        self.assertTrue(bounded.response.closed)
        self.assertTrue(bounded.response.released)

    def test_get_object_and_metadata_closes_response(self) -> None:
        cl = self._client()
        fake = FakeMinioClient()
        cl.client = typing.cast(typing.Any, fake)

        with fake_minio_error_module():
            body, metadata = typing.cast(
                typing.Tuple[bytes, typing.Dict[str, str]],
                cl.get_object_and_metadata("s3://eyelevel/workflows/extract/latest.yaml"),
            )

        self.assertEqual(body, b"statement: {}")
        self.assertEqual(metadata, {"ETag": "etag-1"})
        self.assertTrue(fake.response.closed)
        self.assertTrue(fake.response.released)

    def test_get_object_and_metadata_preserves_last_modified_header(self) -> None:
        cl = self._client()
        fake = FakeMinioClient()
        fake.response.headers["Last-Modified"] = "Wed, 12 Aug 2026 06:00:00 GMT"
        cl.client = typing.cast(typing.Any, fake)

        with fake_minio_error_module():
            _body, metadata = typing.cast(
                typing.Tuple[bytes, typing.Dict[str, str]],
                cl.get_object_and_metadata("s3://eyelevel/workflows/extract/latest.yaml"),
            )

        self.assertEqual(metadata["LastModified"], "1786514400.0")

    def test_get_object_and_metadata_uses_bounded_leased_client(self) -> None:
        cl = self._client()
        bounded = FakeMinioClient()
        create_client = Mock(return_value=bounded)
        setattr(cl, "_create_client", create_client)

        with fake_minio_error_module():
            body, metadata = typing.cast(
                typing.Tuple[bytes, typing.Dict[str, str]],
                cl.get_object_and_metadata(
                    "s3://eyelevel/workflows/extract/latest.yaml",
                    connect_timeout_seconds=0.2,
                    read_timeout_seconds=0.5,
                    total_timeout_seconds=0.8,
                ),
            )

        self.assertEqual(body, b"statement: {}")
        self.assertEqual(metadata, {"ETag": "etag-1"})
        self.assertTrue(bounded.response.closed)
        self.assertTrue(bounded.response.released)
        create_client.assert_called_once_with(
            connect_timeout_seconds=0.2,
            read_timeout_seconds=0.5,
            total_timeout_seconds=0.8,
        )

    def test_head_object_uses_bounded_leased_client(self) -> None:
        cl = self._client()
        bounded = FakeMinioClient()
        create_client = Mock(return_value=bounded)
        setattr(cl, "_create_client", create_client)

        with fake_minio_error_module():
            metadata = cl.head_object(
                "s3://eyelevel/workflows/extract/latest.yaml",
                connect_timeout_seconds=0.2,
                read_timeout_seconds=0.5,
            )

        self.assertEqual(metadata, {"ETag": "etag-1"})
        create_client.assert_called_once_with(
            connect_timeout_seconds=0.2,
            read_timeout_seconds=0.5,
            total_timeout_seconds=None,
        )

    def test_worker_thread_head_and_put_use_transport_bounded_client(self) -> None:
        cl = self._client()
        bounded = FakeMinioClient()
        create_client = Mock(return_value=bounded)
        setattr(cl, "_create_client", create_client)

        with fake_minio_error_module(), ThreadPoolExecutor(max_workers=1) as executor:
            head = executor.submit(
                cl.head_object,
                "s3://eyelevel/workflow.yaml",
                connect_timeout_seconds=0.2,
                read_timeout_seconds=0.5,
            )
            put = executor.submit(
                cl.put_json_stream,
                "eyelevel",
                "trace.json",
                b"{}",
                "application/json",
                connect_timeout_seconds=0.2,
                read_timeout_seconds=0.5,
                total_timeout_seconds=0.8,
            )

            self.assertEqual(head.result(timeout=1), {"ETag": "etag-1"})
            put.result(timeout=1)

        self.assertEqual(create_client.call_count, 2)
        create_client.assert_any_call(
            connect_timeout_seconds=0.2,
            read_timeout_seconds=0.5,
            total_timeout_seconds=None,
        )
        create_client.assert_any_call(
            connect_timeout_seconds=0.2,
            read_timeout_seconds=0.5,
            total_timeout_seconds=0.8,
        )
        self.assertEqual(bounded.put["object_name"], "trace.json")

    def test_worker_thread_slow_head_has_no_false_hard_total_deadline(self) -> None:
        class SlowMinioClient(FakeMinioClient):
            def stat_object(self, bucket: str, key: str) -> typing.Any:
                time.sleep(0.20)
                return super().stat_object(bucket, key)

        cl = self._client()
        bounded = SlowMinioClient()
        setattr(cl, "_create_client", Mock(return_value=bounded))

        started = time.monotonic()
        with fake_minio_error_module(), ThreadPoolExecutor(max_workers=1) as executor:
            metadata = executor.submit(
                cl.head_object,
                "s3://eyelevel/workflow.yaml",
                connect_timeout_seconds=0.01,
                read_timeout_seconds=0.01,
            ).result(timeout=1)

        self.assertEqual(metadata, {"ETag": "etag-1"})
        self.assertGreaterEqual(time.monotonic() - started, 0.18)

    def test_worker_thread_slow_put_has_no_false_hard_total_deadline(self) -> None:
        class SlowMinioClient(FakeMinioClient):
            def put_object(self, **kwargs: typing.Any) -> None:
                time.sleep(0.20)
                super().put_object(**kwargs)

        cl = self._client()
        bounded = SlowMinioClient()
        setattr(cl, "_create_client", Mock(return_value=bounded))

        started = time.monotonic()
        with fake_minio_error_module(), ThreadPoolExecutor(max_workers=1) as executor:
            executor.submit(
                cl.put_json_stream,
                "eyelevel",
                "trace.json",
                b"{}",
                "application/json",
                connect_timeout_seconds=0.01,
                read_timeout_seconds=0.01,
                transport_total_timeout_seconds=0.06,
            ).result(timeout=1)

        self.assertGreaterEqual(time.monotonic() - started, 0.18)
        self.assertEqual(bounded.put["object_name"], "trace.json")

    def test_put_json_stream_uses_single_attempt_bounded_client(self) -> None:
        cl = self._client()
        bounded = FakeMinioClient()
        create_client = Mock(return_value=bounded)
        setattr(cl, "_create_client", create_client)

        with fake_minio_error_module():
            cl.put_json_stream(
                "eyelevel",
                "trace.json",
                b"{}",
                "application/json",
                connect_timeout_seconds=0.2,
                read_timeout_seconds=0.5,
                total_timeout_seconds=0.8,
            )

        create_client.assert_called_once_with(
            connect_timeout_seconds=0.2,
            read_timeout_seconds=0.5,
            total_timeout_seconds=0.8,
        )
        self.assertEqual(bounded.put["bucket_name"], "eyelevel")
        self.assertEqual(bounded.put["object_name"], "trace.json")
        self.assertEqual(bounded.put["length"], 2)

    def test_put_json_stream_without_timeouts_preserves_default_client(self) -> None:
        cl = self._client()
        default = FakeMinioClient()
        create_client = Mock()
        cl.client = typing.cast(typing.Any, default)
        setattr(cl, "_create_client", create_client)

        cl.put_json_stream(
            "eyelevel",
            "trace.json",
            b"{}",
            "application/json",
        )

        create_client.assert_not_called()
        self.assertEqual(default.put["object_name"], "trace.json")
        self.assertEqual(default.put["length"], 2)

    def test_bounded_client_configures_socket_and_total_timeouts_without_retries(
        self,
    ) -> None:
        cl = self._client()

        with (
            patch("minio.Minio") as create_client,
            patch("urllib3.PoolManager") as create_pool,
        ):
            getattr(cl, "_create_client")(
                connect_timeout_seconds=0.2,
                read_timeout_seconds=0.5,
                total_timeout_seconds=0.8,
            )

        timeout = create_pool.call_args.kwargs["timeout"]
        self.assertEqual(timeout.connect_timeout, 0.2)
        self.assertEqual(timeout.read_timeout, 0.5)
        self.assertEqual(timeout.total, 0.8)
        self.assertIs(create_pool.call_args.kwargs["retries"], False)
        self.assertIs(
            create_client.call_args.kwargs["http_client"],
            create_pool.return_value,
        )

    def test_legacy_put_total_is_native_not_hard_deadline(self) -> None:
        class StalledMinioClient(FakeMinioClient):
            def put_object(self, **kwargs: typing.Any) -> None:
                time.sleep(0.03)
                time.sleep(0.20)

        cl = self._client()
        bounded = StalledMinioClient()
        setattr(cl, "_create_client", Mock(return_value=bounded))

        started = time.monotonic()
        cl.put_json_stream(
            "eyelevel",
            "trace.json",
            b"{}",
            "application/json",
            connect_timeout_seconds=0.01,
            read_timeout_seconds=0.01,
            total_timeout_seconds=0.06,
        )

        self.assertGreaterEqual(time.monotonic() - started, 0.18)


@contextlib.contextmanager
def fake_minio_error_module() -> typing.Iterator[None]:
    previous_minio = sys.modules.get("minio")
    previous_error = sys.modules.get("minio.error")

    minio_module = types.ModuleType("minio")
    error_module = types.ModuleType("minio.error")
    setattr(error_module, "S3Error", Exception)
    setattr(minio_module, "error", error_module)

    sys.modules["minio"] = minio_module
    sys.modules["minio.error"] = error_module
    try:
        yield
    finally:
        if previous_minio is None:
            sys.modules.pop("minio", None)
        else:
            sys.modules["minio"] = previous_minio

        if previous_error is None:
            sys.modules.pop("minio.error", None)
        else:
            sys.modules["minio.error"] = previous_error
