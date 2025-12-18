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
                    bucket="eyelevel",
                    type="",
                    url="",
                ),
                workers=1,
            ),
            logger=logger,
        )

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
