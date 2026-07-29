import sys
import types
import typing
import unittest
from unittest.mock import Mock, patch

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

    def get_object(self, Bucket: str, Key: str) -> typing.Dict[str, typing.Any]:
        return {
            "Body": self.body,
            "ETag": '"etag-1"',
        }

    def head_object(self, Bucket: str, Key: str) -> typing.Dict[str, typing.Any]:
        return {"ETag": '"etag-1"'}


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

    def test_head_object_handles_missing_last_modified(self) -> None:
        cl = self._client()
        cl.client = typing.cast(typing.Any, FakeS3Client())

        metadata = cl.head_object("s3://eyelevel/workflows/extract/latest.yaml")

        self.assertEqual(metadata, {"ETag": '"etag-1"'})
