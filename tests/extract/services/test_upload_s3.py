import typing
import unittest

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


class TestS3Client(unittest.TestCase):
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
