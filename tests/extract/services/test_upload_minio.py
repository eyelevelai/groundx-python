import unittest
import contextlib
import sys
import types
import typing

from groundx.extract.services.logger import Logger
from groundx.extract.settings.settings import ContainerSettings, ContainerUploadSettings
from groundx.extract.services.upload_minio import MinIOClient


class FakeMinioResponse:
    def __init__(self, body: bytes) -> None:
        self.body = body
        self.closed = False
        self.released = False

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


class TestMinIOClient(unittest.TestCase):
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

    def test_get_object_and_metadata_closes_response(self) -> None:
        cl = self._client()
        fake = FakeMinioClient()
        cl.client = typing.cast(typing.Any, fake)

        with fake_minio_error_module():
            body, metadata = typing.cast(
                typing.Tuple[bytes, typing.Dict[str, str]],
                cl.get_object_and_metadata(
                    "s3://eyelevel/workflows/extract/latest.yaml"
                ),
            )

        self.assertEqual(body, b"statement: {}")
        self.assertEqual(metadata, {"ETag": "etag-1"})
        self.assertTrue(fake.response.closed)
        self.assertTrue(fake.response.released)


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
