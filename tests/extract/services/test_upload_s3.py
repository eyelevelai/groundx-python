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
from groundx.extract.services.upload_s3 import S3Client
from groundx.extract.settings.settings import ContainerSettings, ContainerUploadSettings


class FakeBody:
    def __init__(self, body: bytes) -> None:
        self.body = body
        self.closed = False

    def read(self) -> bytes:
        return self.body

    def close(self) -> None:
        self.closed = True


class FakeS3Client:
    def __init__(self) -> None:
        self.body = FakeBody(b"statement: {}")
        self.closed = False

    def get_object(self, Bucket: str, Key: str) -> typing.Dict[str, typing.Any]:
        return {
            "Body": self.body,
            "ETag": '"etag-1"',
        }

    def head_object(self, Bucket: str, Key: str) -> typing.Dict[str, typing.Any]:
        return {"ETag": '"etag-1"'}

    def put_object(self, **kwargs: typing.Any) -> None:
        self.put = kwargs

    def close(self) -> None:
        self.closed = True


class FakeConfig:
    def __init__(self, **kwargs: typing.Any) -> None:
        self.__dict__.update(kwargs)


class TestS3Client(unittest.TestCase):
    def test_s3_client_has_bounded_io_and_no_hidden_retries(self) -> None:
        mock_boto_client = Mock()
        boto3_module = types.ModuleType("boto3")
        certifi_module = types.ModuleType("certifi")
        botocore_module = types.ModuleType("botocore")
        botocore_config_module = types.ModuleType("botocore.config")
        setattr(boto3_module, "client", mock_boto_client)
        setattr(certifi_module, "where", lambda: "/tmp/ca.pem")
        setattr(botocore_config_module, "Config", FakeConfig)
        setattr(botocore_module, "config", botocore_config_module)
        settings = ContainerSettings(
            broker="",
            service="s3",
            upload=ContainerUploadSettings(
                base_domain="",
                bucket="eyelevel",
                type="s3",
                url="",
            ),
            workers=1,
        )
        with patch.dict(
            sys.modules,
            {
                "boto3": boto3_module,
                "certifi": certifi_module,
                "botocore": botocore_module,
                "botocore.config": botocore_config_module,
            },
        ):
            S3Client(settings, Logger("test", "debug"))

        config = mock_boto_client.call_args.kwargs["config"]
        self.assertEqual(config.connect_timeout, 5)
        self.assertEqual(config.read_timeout, 20)
        self.assertEqual(config.retries["total_max_attempts"], 1)

    def _client(self) -> S3Client:
        logger = Logger("s3", "debug")
        return S3Client(
            settings=ContainerSettings(
                broker="",
                service="s3",
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

    def test_get_object_closes_body(self) -> None:
        cl = self._client()
        fake = FakeS3Client()
        cl.client = typing.cast(typing.Any, fake)

        body = cl.get_object("s3://eyelevel/workflows/extract/latest.yaml")

        self.assertEqual(body, b"statement: {}")
        self.assertTrue(fake.body.closed)

    def test_get_object_uses_bounded_client_and_closes_body(self) -> None:
        cl = self._client()
        bounded = FakeS3Client()
        create_client = Mock(return_value=bounded)
        setattr(cl, "_create_client", create_client)

        body = cl.get_object(
            "s3://eyelevel/workflows/extract/latest.yaml",
            connect_timeout_seconds=0.2,
            read_timeout_seconds=0.5,
            total_timeout_seconds=0.8,
        )

        self.assertEqual(body, b"statement: {}")
        self.assertTrue(bounded.body.closed)
        create_client.assert_called_once_with(
            connect_timeout_seconds=0.2,
            read_timeout_seconds=0.5,
            total_timeout_seconds=0.8,
        )

    def test_get_object_requires_complete_positive_timeout_budget(self) -> None:
        cl = self._client()
        cl.client = typing.cast(typing.Any, FakeS3Client())

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

    def test_timeout_client_cache_is_bounded_and_closes_evicted_client(self) -> None:
        cl = self._client()
        created: typing.List[FakeS3Client] = []

        def create_client(**_kwargs: float) -> FakeS3Client:
            client = FakeS3Client()
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
        self.assertTrue(created[0].closed)
        self.assertFalse(created[-1].closed)

    def test_timeout_client_cache_creates_one_client_for_concurrent_key(self) -> None:
        cl = self._client()
        ready = threading.Barrier(8)
        created: typing.List[FakeS3Client] = []
        created_lock = threading.Lock()

        def create_client(**_kwargs: float) -> FakeS3Client:
            time.sleep(0.03)
            client = FakeS3Client()
            with created_lock:
                created.append(client)
            return client

        setattr(cl, "_create_client", create_client)

        def load(_index: int) -> typing.Any:
            ready.wait(timeout=1)
            client_context = getattr(cl, "_client_for_timeouts")(
                connect_timeout_seconds=0.2,
                read_timeout_seconds=0.5,
                total_timeout_seconds=0.8,
            )
            with client_context as client:
                return client

        with ThreadPoolExecutor(max_workers=8) as executor:
            clients = list(executor.map(load, range(8)))

        self.assertEqual(len(created), 1)
        self.assertEqual(len({id(client) for client in clients}), 1)

    def test_timeout_client_cache_defers_close_while_read_is_active(self) -> None:
        reading = threading.Event()
        churn_complete = threading.Event()

        class BlockingBody(FakeBody):
            def __init__(self, owner: "BlockingS3Client") -> None:
                super().__init__(b"statement: {}")
                self.owner = owner
                self.owner_closed_while_reading = False

            def read(self) -> bytes:
                reading.set()
                if not churn_complete.wait(timeout=2):
                    raise TimeoutError("cache churn did not complete")
                self.owner_closed_while_reading = self.owner.closed
                return super().read()

        class BlockingS3Client(FakeS3Client):
            def __init__(self) -> None:
                self.closed = False
                self.body: BlockingBody = BlockingBody(self)

        cl = self._client()
        active = BlockingS3Client()
        created: typing.List[FakeS3Client] = []

        def create_client(**_kwargs: float) -> FakeS3Client:
            client: FakeS3Client = active if not created else FakeS3Client()
            created.append(client)
            return client

        setattr(cl, "_create_client", create_client)

        def churn_cache() -> None:
            if not reading.wait(timeout=2):
                return
            cache = getattr(cl, "_timeout_clients")
            for total in range(1, 10):
                client_context = cache.lease(
                    (0.2, 0.5, float(total)),
                    lambda: create_client(),
                )
                with client_context:
                    pass
            churn_complete.set()

        churn = threading.Thread(target=churn_cache)
        churn.start()
        try:
            body = cl.get_object(
                "s3://eyelevel/workflows/extract/latest.yaml",
                connect_timeout_seconds=0.2,
                read_timeout_seconds=0.5,
                total_timeout_seconds=0.8,
            )
        finally:
            churn_complete.set()
            churn.join(timeout=2)

        self.assertEqual(body, b"statement: {}")
        self.assertFalse(active.body.owner_closed_while_reading)
        self.assertTrue(active.closed)

    def test_get_object_total_deadline_includes_body_read(self) -> None:
        class StalledBody(FakeBody):
            def read(self) -> bytes:
                time.sleep(0.20)
                return super().read()

        class StalledS3Client(FakeS3Client):
            def __init__(self) -> None:
                self.body = StalledBody(b"statement: {}")

        cl = self._client()
        bounded = StalledS3Client()
        setattr(cl, "_create_client", Mock(return_value=bounded))

        started = time.monotonic()
        with self.assertRaisesRegex(TimeoutError, "S3 get_object exceeded"):
            cl.get_object(
                "s3://eyelevel/workflow.yaml",
                connect_timeout_seconds=0.01,
                read_timeout_seconds=0.01,
                total_timeout_seconds=0.06,
            )

        self.assertLess(time.monotonic() - started, 0.15)
        self.assertTrue(bounded.body.closed)

    def test_worker_thread_deadline_closes_stalled_body_and_raises_timeout(self) -> None:
        class StalledBody(FakeBody):
            def __init__(self) -> None:
                super().__init__(b"statement: {}")
                self.closed_event = threading.Event()

            def read(self) -> bytes:
                if not self.closed_event.wait(timeout=2):
                    raise AssertionError("deadline did not close stalled S3 body")
                return super().read()

            def close(self) -> None:
                super().close()
                self.closed_event.set()

        class StalledS3Client(FakeS3Client):
            def __init__(self) -> None:
                self.body = StalledBody()
                self.closed = False

        cl = self._client()
        bounded = StalledS3Client()
        setattr(cl, "_create_client", Mock(return_value=bounded))

        started = time.monotonic()
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                cl.get_object_and_metadata,
                "s3://eyelevel/workflow.yaml",
                connect_timeout_seconds=0.01,
                read_timeout_seconds=0.01,
                total_timeout_seconds=0.06,
            )
            with self.assertRaisesRegex(
                WallClockDeadlineExceeded,
                "S3 get_object_and_metadata exceeded",
            ):
                future.result(timeout=1)

        self.assertLess(time.monotonic() - started, 0.15)
        self.assertTrue(bounded.body.closed)
        self.assertFalse(any(isinstance(thread, threading.Timer) for thread in threading.enumerate()))

    def test_worker_timeout_does_not_close_shared_client_or_other_response(
        self,
    ) -> None:
        class StalledBody(FakeBody):
            def __init__(self) -> None:
                super().__init__(b"stalled")
                self.closed_event = threading.Event()

            def read(self) -> bytes:
                if not self.closed_event.wait(timeout=2):
                    raise AssertionError("deadline did not close stalled S3 body")
                return super().read()

            def close(self) -> None:
                super().close()
                self.closed_event.set()

        class SharedS3Client(FakeS3Client):
            def __init__(self) -> None:
                self.stalled = StalledBody()
                self.fast = FakeBody(b"fast")
                self.closed = False

            def get_object(
                self,
                Bucket: str,
                Key: str,
            ) -> typing.Dict[str, typing.Any]:
                return {
                    "Body": self.stalled if Key == "stalled" else self.fast,
                    "ETag": '"etag-1"',
                }

        cl = self._client()
        shared = SharedS3Client()
        setattr(cl, "_create_client", Mock(return_value=shared))

        with ThreadPoolExecutor(max_workers=2) as executor:
            stalled = executor.submit(
                cl.get_object,
                "s3://eyelevel/stalled",
                connect_timeout_seconds=0.01,
                read_timeout_seconds=0.01,
                total_timeout_seconds=0.06,
            )
            fast = executor.submit(
                cl.get_object,
                "s3://eyelevel/fast",
                connect_timeout_seconds=0.01,
                read_timeout_seconds=0.01,
                total_timeout_seconds=0.06,
            )

            self.assertEqual(fast.result(timeout=1), b"fast")
            with self.assertRaises(WallClockDeadlineExceeded):
                stalled.result(timeout=1)

        self.assertTrue(shared.stalled.closed)
        self.assertTrue(shared.fast.closed)
        self.assertFalse(shared.closed)

    def test_get_object_and_metadata_handles_missing_last_modified(self) -> None:
        cl = self._client()
        fake = FakeS3Client()
        cl.client = typing.cast(typing.Any, fake)

        body, metadata = typing.cast(
            typing.Tuple[bytes, typing.Dict[str, str]],
            cl.get_object_and_metadata("s3://eyelevel/workflows/extract/latest.yaml"),
        )

        self.assertEqual(body, b"statement: {}")
        self.assertEqual(metadata, {"ETag": '"etag-1"'})
        self.assertTrue(fake.body.closed)

    def test_get_object_and_metadata_uses_bounded_leased_client(self) -> None:
        cl = self._client()
        bounded = FakeS3Client()
        create_client = Mock(return_value=bounded)
        setattr(cl, "_create_client", create_client)

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
        self.assertEqual(metadata, {"ETag": '"etag-1"'})
        self.assertTrue(bounded.body.closed)
        create_client.assert_called_once_with(
            connect_timeout_seconds=0.2,
            read_timeout_seconds=0.5,
            total_timeout_seconds=0.8,
        )

    def test_head_object_handles_missing_last_modified(self) -> None:
        cl = self._client()
        cl.client = typing.cast(typing.Any, FakeS3Client())

        metadata = cl.head_object("s3://eyelevel/workflows/extract/latest.yaml")

        self.assertEqual(metadata, {"ETag": '"etag-1"'})

    def test_head_object_uses_bounded_leased_client(self) -> None:
        cl = self._client()
        bounded = FakeS3Client()
        create_client = Mock(return_value=bounded)
        setattr(cl, "_create_client", create_client)

        metadata = cl.head_object(
            "s3://eyelevel/workflows/extract/latest.yaml",
            connect_timeout_seconds=0.2,
            read_timeout_seconds=0.5,
        )

        self.assertEqual(metadata, {"ETag": '"etag-1"'})
        create_client.assert_called_once_with(
            connect_timeout_seconds=0.2,
            read_timeout_seconds=0.5,
            total_timeout_seconds=None,
        )

    def test_worker_thread_head_and_put_use_transport_bounded_client(self) -> None:
        cl = self._client()
        bounded = FakeS3Client()
        create_client = Mock(return_value=bounded)
        setattr(cl, "_create_client", create_client)

        with ThreadPoolExecutor(max_workers=1) as executor:
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

            self.assertEqual(head.result(timeout=1), {"ETag": '"etag-1"'})
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
        self.assertEqual(bounded.put["Key"], "trace.json")

    def test_worker_thread_slow_head_has_no_false_hard_total_deadline(self) -> None:
        class SlowS3Client(FakeS3Client):
            def head_object(
                self,
                Bucket: str,
                Key: str,
            ) -> typing.Dict[str, typing.Any]:
                time.sleep(0.20)
                return super().head_object(Bucket=Bucket, Key=Key)

        cl = self._client()
        bounded = SlowS3Client()
        setattr(cl, "_create_client", Mock(return_value=bounded))

        started = time.monotonic()
        with ThreadPoolExecutor(max_workers=1) as executor:
            metadata = executor.submit(
                cl.head_object,
                "s3://eyelevel/workflow.yaml",
                connect_timeout_seconds=0.01,
                read_timeout_seconds=0.01,
            ).result(timeout=1)

        self.assertEqual(metadata, {"ETag": '"etag-1"'})
        self.assertGreaterEqual(time.monotonic() - started, 0.18)

    def test_worker_thread_slow_put_has_no_false_hard_total_deadline(self) -> None:
        class SlowS3Client(FakeS3Client):
            def put_object(self, **kwargs: typing.Any) -> None:
                time.sleep(0.20)
                super().put_object(**kwargs)

        cl = self._client()
        bounded = SlowS3Client()
        setattr(cl, "_create_client", Mock(return_value=bounded))

        started = time.monotonic()
        with ThreadPoolExecutor(max_workers=1) as executor:
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
        self.assertEqual(bounded.put["Key"], "trace.json")

    def test_s3_bucket_provisioning_is_explicitly_unsupported(self) -> None:
        cl = self._client()

        with self.assertRaisesRegex(NotImplementedError, "S3 bucket provisioning"):
            cl.provision_bucket()

    def test_main_thread_without_setitimer_closes_stalled_body_at_deadline(
        self,
    ) -> None:
        class StalledBody(FakeBody):
            def __init__(self) -> None:
                super().__init__(b"statement: {}")
                self.closed_event = threading.Event()

            def read(self) -> bytes:
                if not self.closed_event.wait(timeout=2):
                    raise AssertionError("deadline did not close stalled S3 body")
                return super().read()

            def close(self) -> None:
                super().close()
                self.closed_event.set()

        class StalledS3Client(FakeS3Client):
            def __init__(self) -> None:
                self.body = StalledBody()
                self.closed = False

        cl = self._client()
        bounded = StalledS3Client()
        setattr(cl, "_create_client", Mock(return_value=bounded))

        started = time.monotonic()
        with (
            patch("groundx.extract.services.http.signal.setitimer", None),
            self.assertRaisesRegex(
                WallClockDeadlineExceeded,
                "S3 get_object exceeded",
            ),
        ):
            cl.get_object(
                "s3://eyelevel/workflow.yaml",
                connect_timeout_seconds=0.01,
                read_timeout_seconds=0.01,
                total_timeout_seconds=0.06,
            )

        self.assertLess(time.monotonic() - started, 0.15)
        self.assertTrue(bounded.body.closed)

    def test_put_json_stream_uses_single_attempt_bounded_client(self) -> None:
        cl = self._client()
        bounded = FakeS3Client()
        create_client = Mock(return_value=bounded)
        setattr(cl, "_create_client", create_client)

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
        self.assertEqual(bounded.put["Bucket"], "eyelevel")
        self.assertEqual(bounded.put["Key"], "trace.json")
        self.assertEqual(bounded.put["Body"], b"{}")

    def test_put_json_stream_without_timeouts_preserves_default_client(self) -> None:
        cl = self._client()
        default = FakeS3Client()
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
        self.assertEqual(default.put["Key"], "trace.json")
        self.assertEqual(default.put["Body"], b"{}")

    def test_bounded_client_configures_socket_timeouts_without_sdk_retries(
        self,
    ) -> None:
        cl = self._client()

        with patch("boto3.client") as create_client:
            getattr(cl, "_create_client")(
                connect_timeout_seconds=0.2,
                read_timeout_seconds=0.5,
                total_timeout_seconds=0.8,
            )

        config = create_client.call_args.kwargs["config"]
        self.assertEqual(config.connect_timeout, 0.2)
        self.assertEqual(config.read_timeout, 0.5)
        self.assertEqual(config.retries["total_max_attempts"], 1)

    def test_legacy_put_total_is_native_not_hard_deadline(self) -> None:
        class StalledS3Client:
            def put_object(self, **kwargs: typing.Any) -> None:
                time.sleep(0.03)
                time.sleep(0.20)

        cl = self._client()
        bounded = StalledS3Client()
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
