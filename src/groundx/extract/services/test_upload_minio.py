import unittest

from .logger import Logger
from ..settings.settings import ContainerSettings, ContainerUploadSettings
from .upload_minio import MinIOClient


class TestMinIOClient(unittest.TestCase):
    def test_load_parse_url_1(self) -> None:
        logger = Logger("parse_url", "debug")

        cl = MinIOClient(
            settings=ContainerSettings(
                broker="",
                service="parse_url",
                upload=ContainerUploadSettings(
                    base_domain="",
                    bucket="eyeleve",
                    type="",
                    url="",
                ),
                workers=1,
            ),
            logger=logger,
        )

        obj = cl.parse_url("/eyelevel/layout")
        self.assertEqual(obj, "eyelevel/layout")

        obj = cl.parse_url("s3://eyelevel/prod/file")
        self.assertEqual(obj, "eyelevel/prod/file")

        obj = cl.parse_url("eyelevel/layout")
        self.assertEqual(obj, "eyelevel/layout")

        obj = cl.parse_url("/layout/prod")
        self.assertEqual(obj, "layout/prod")

        obj = cl.parse_url("layout/prod")
        self.assertEqual(obj, "layout/prod")
