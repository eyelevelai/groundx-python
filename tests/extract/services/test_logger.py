import unittest
from unittest.mock import patch

import requests

from groundx.extract.services.logger import Logger


class TestLoggerCallbacks(unittest.TestCase):
    def test_report_error_uses_bounded_callback_timeout(self) -> None:
        logger = Logger("callback-timeout-test", "error")

        with patch("requests.post") as post:
            logger.report_error(
                api_key="key",
                callback_url="https://callback.test/error",
                req={"code": 500},
                msg="failed",
            )

        self.assertEqual(post.call_args.kwargs["timeout"], (3.0, 10.0))

    def test_report_result_timeout_is_bounded(self) -> None:
        logger = Logger("callback-result-timeout-test", "error")

        with (
            patch("requests.post", side_effect=requests.Timeout("stalled")) as post,
            patch("groundx.extract.services.http.time.sleep"),
        ):
            with self.assertRaises(RuntimeError) as cm:
                logger.report_result(
                    api_key="key",
                    callback_url="https://callback.test/result",
                    req={"code": 200},
                )

        self.assertEqual(post.call_count, 2)
        self.assertIn("after 2 attempts", str(cm.exception))
