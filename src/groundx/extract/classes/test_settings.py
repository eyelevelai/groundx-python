import typing, os, unittest

from .settings import (
    AgentSettings,
    ContainerSettings,
    ContainerUploadSettings,
    GroundXSettings,
    AWS_REGION,
    CALLBACK_KEY,
    GX_AGENT_KEY,
    GX_API_KEY,
    GX_KEY,
    GX_REGION,
    GX_SECRET,
    VALID_KEYS,
)


AWS_KEY: str = "AWS_ACCESS_KEY_ID"
AWS_SECRET: str = "AWS_SECRET_ACCESS_KEY"
AWS_TOKEN: str = "AWS_SESSION_TOKEN"


def clearEnv() -> None:
    os.environ.clear()


class TestAgentSettings(unittest.TestCase):
    def test(self) -> None:
        tsts: typing.List[typing.Dict[str, typing.Any]] = [
            {
                "expect": {
                    "api_base": None,
                    "api_key": Exception,
                    "max_steps": 7,
                    "model_id": "gpt-5-mini",
                },
            },
            {
                "api_base": "http://test.com",
                "api_key": "mykey",
                "api_key_env_val": "val",
                "max_steps": 4,
                "model_id": "gpt-5",
                "expect": {
                    "api_base": "http://test.com",
                    "api_key": "mykey",
                    "api_key_env": "myenv",
                    "max_steps": 4,
                    "model_id": "gpt-5",
                },
            },
            {
                "api_key_env_val": "val",
                "expect": {
                    "api_base": None,
                    "api_key": "val",
                    "max_steps": 7,
                    "model_id": "gpt-5-mini",
                },
            },
        ]

        for _, tst in enumerate(tsts):
            clearEnv()

            input: typing.Dict[str, typing.Any] = {}
            if "api_base" in tst:
                input["api_base"] = tst["api_base"]
            if "api_key" in tst:
                input["api_key"] = tst["api_key"]
            if "api_key_env_val" in tst:
                os.environ.update({GX_AGENT_KEY: tst["api_key_env_val"]})
            if "max_steps" in tst:
                input["max_steps"] = tst["max_steps"]
            if "model_id" in tst:
                input["model_id"] = tst["model_id"]

            settings = AgentSettings(**input)

            self.assertIsInstance(settings, AgentSettings)

            self.assertEqual(settings.api_base, tst["expect"]["api_base"])

            if tst["expect"]["api_key"] == Exception:
                self.assertRaises(Exception, settings.get_api_key)
            else:
                self.assertEqual(settings.get_api_key(), tst["expect"]["api_key"])

            self.assertEqual(settings.max_steps, tst["expect"]["max_steps"])

            self.assertEqual(settings.model_id, tst["expect"]["model_id"])


class TestContainerUploadSettings(unittest.TestCase):
    def test(self) -> None:
        tsts: typing.List[typing.Dict[str, typing.Any]] = [
            {
                "base_domain": "https://base.com",
                "bucket": "test-bucket",
                "type": "s3",
                "url": "https://test.com",
                "aws_key_env_val": "valk",
                "aws_region_env_val": "vale",
                "aws_secret_env_val": "vals",
                "expect": {
                    "base_domain": "https://base.com",
                    "base_path": "layout/processed/",
                    "bucket": "test-bucket",
                    "ssl": False,
                    "type": "s3",
                    "url": "https://test.com",
                    "key": None,
                    "region": "vale",
                    "secret": None,
                },
            },
            {
                "base_domain": "https://base.com",
                "bucket": "test-bucket",
                "type": "s3",
                "url": "https://test.com",
                "expect": {
                    "base_domain": "https://base.com",
                    "base_path": "layout/processed/",
                    "bucket": "test-bucket",
                    "ssl": False,
                    "type": "s3",
                    "url": "https://test.com",
                    "key": None,
                    "region": None,
                    "secret": None,
                },
            },
            {
                "base_domain": "https://base.com",
                "base_path": "layout/",
                "bucket": "test-bucket",
                "ssl": True,
                "type": "s3",
                "url": "https://test.com",
                "key": "mykey",
                "gx_key_env_val": "valk",
                "region": "myregion",
                "gx_region_env_val": "vale",
                "secret": "mysecret",
                "gx_secret_env_val": "vals",
                "expect": {
                    "base_domain": "https://base.com",
                    "base_path": "layout/",
                    "bucket": "test-bucket",
                    "ssl": True,
                    "type": "s3",
                    "url": "https://test.com",
                    "key": "mykey",
                    "region": "myregion",
                    "secret": "mysecret",
                },
            },
            {
                "base_domain": "https://base.com",
                "bucket": "test-bucket",
                "type": "s3",
                "url": "https://test.com",
                "gx_key_env_val": "valk",
                "gx_region_env_val": "vale",
                "gx_secret_env_val": "vals",
                "expect": {
                    "base_domain": "https://base.com",
                    "base_path": "layout/processed/",
                    "bucket": "test-bucket",
                    "ssl": False,
                    "type": "s3",
                    "url": "https://test.com",
                    "key": "valk",
                    "region": "vale",
                    "secret": "vals",
                },
            },
            {
                "base_domain": "https://base.com",
                "bucket": "test-bucket",
                "type": "s3",
                "url": "https://test.com",
                "gx_key_env_val": "valk",
                "gx_region_env_val": "vale",
                "gx_secret_env_val": "vals",
                "expect": {
                    "base_domain": "https://base.com",
                    "base_path": "layout/processed/",
                    "bucket": "test-bucket",
                    "ssl": False,
                    "type": "s3",
                    "url": "https://test.com",
                    "key": "valk",
                    "region": "vale",
                    "secret": "vals",
                },
            },
        ]

        for _, tst in enumerate(tsts):
            clearEnv()

            input: typing.Dict[str, typing.Any] = {}
            if "base_domain" in tst:
                input["base_domain"] = tst["base_domain"]
            if "base_path" in tst:
                input["base_path"] = tst["base_path"]
            if "bucket" in tst:
                input["bucket"] = tst["bucket"]
            if "ssl" in tst:
                input["ssl"] = tst["ssl"]
            if "type" in tst:
                input["type"] = tst["type"]
            if "url" in tst:
                input["url"] = tst["url"]
            if "key" in tst:
                input["key"] = tst["key"]
            if "gx_key_env_val" in tst:
                os.environ.update({GX_KEY: tst["gx_key_env_val"]})
            if "aws_key_env_val" in tst:
                os.environ.update({AWS_KEY: tst["aws_key_env_val"]})
            if "region" in tst:
                input["region"] = tst["region"]
            if "gx_region_env_val" in tst:
                os.environ.update({GX_REGION: tst["gx_region_env_val"]})
            if "aws_region_env_val" in tst:
                os.environ.update({AWS_REGION: tst["aws_region_env_val"]})
            if "secret" in tst:
                input["secret"] = tst["secret"]
            if "gx_secret_env_val" in tst:
                os.environ.update({GX_SECRET: tst["gx_secret_env_val"]})
            if "aws_secret_env_val" in tst:
                os.environ.update({AWS_SECRET: tst["aws_secret_env_val"]})

            settings = ContainerUploadSettings(**input)

            self.assertIsInstance(settings, ContainerUploadSettings)

            self.assertEqual(settings.base_domain, tst["expect"]["base_domain"])

            self.assertEqual(settings.base_path, tst["expect"]["base_path"])

            self.assertEqual(settings.bucket, tst["expect"]["bucket"])

            self.assertEqual(settings.ssl, tst["expect"]["ssl"])

            self.assertEqual(settings.type, tst["expect"]["type"])

            self.assertEqual(settings.url, tst["expect"]["url"])

            if tst["expect"]["key"] == None:
                self.assertIsNone(settings.get_key())
            else:
                self.assertEqual(settings.get_key(), tst["expect"]["key"])

            if tst["expect"]["region"] == None:
                self.assertIsNone(settings.get_region())
            else:
                self.assertEqual(settings.get_region(), tst["expect"]["region"])

            if tst["expect"]["secret"] == None:
                self.assertIsNone(settings.get_secret())
            else:
                self.assertEqual(settings.get_secret(), tst["expect"]["secret"])


class TestContainerSettings(unittest.TestCase):
    def test(self) -> None:
        tsts: typing.List[typing.Dict[str, typing.Any]] = [
            {
                "broker": "mybroker",
                "service": "myservice",
                "workers": 1,
                "upload": {
                    "base_domain": "https://base.com",
                    "bucket": "test-bucket",
                    "type": "s3",
                    "url": "https://test.com",
                },
                "expect": {
                    "broker": "mybroker",
                    "cache_to": 300,
                    "google_sheets_drive_id": None,
                    "google_sheets_template_id": None,
                    "log_level": "info",
                    "metrics_broker": None,
                    "refresh_to": 60,
                    "service": "myservice",
                    "task_to": 600,
                    "workers": 1,
                    "callback_api_key": Exception,
                    "valid_api_keys": Exception,
                    "loglevel": "INFO",
                    "status_broker": "mybroker",
                },
            },
            {
                "broker": "mybroker",
                "cache_to": 100,
                "google_sheets_drive_id": "drive_id",
                "google_sheets_template_id": "template_id",
                "log_level": "error",
                "metrics_broker": "mymetrics",
                "refresh_to": 30,
                "service": "myservice",
                "task_to": 300,
                "workers": 1,
                "upload": {
                    "base_domain": "https://base.com",
                    "bucket": "test-bucket",
                    "type": "s3",
                    "url": "https://test.com",
                },
                "callback_api_key": "cbkey",
                "callback_api_key_env_val": "vale",
                "valid_api_keys": ["vkeys"],
                "valid_api_keys_env_val": '["valv"]',
                "expect": {
                    "broker": "mybroker",
                    "cache_to": 100,
                    "google_sheets_drive_id": "drive_id",
                    "google_sheets_template_id": "template_id",
                    "log_level": "error",
                    "metrics_broker": "mymetrics",
                    "refresh_to": 30,
                    "service": "myservice",
                    "task_to": 300,
                    "workers": 1,
                    "callback_api_key": "cbkey",
                    "valid_api_keys": ["vkeys"],
                    "loglevel": "ERROR",
                    "status_broker": "mymetrics",
                },
            },
            {
                "broker": "mybroker",
                "service": "myservice",
                "workers": 1,
                "upload": {
                    "base_domain": "https://base.com",
                    "bucket": "test-bucket",
                    "type": "s3",
                    "url": "https://test.com",
                },
                "callback_api_key_env_val": "vale",
                "valid_api_keys_env_val": '["valv"]',
                "expect": {
                    "broker": "mybroker",
                    "cache_to": 300,
                    "google_sheets_drive_id": None,
                    "google_sheets_template_id": None,
                    "log_level": "info",
                    "metrics_broker": None,
                    "refresh_to": 60,
                    "service": "myservice",
                    "task_to": 600,
                    "workers": 1,
                    "callback_api_key": "vale",
                    "valid_api_keys": ["valv"],
                    "loglevel": "INFO",
                    "status_broker": "mybroker",
                },
            },
        ]

        for _, tst in enumerate(tsts):
            clearEnv()

            input: typing.Dict[str, typing.Any] = {}
            if "broker" in tst:
                input["broker"] = tst["broker"]
            if "cache_to" in tst:
                input["cache_to"] = tst["cache_to"]
            if "google_sheets_drive_id" in tst:
                input["google_sheets_drive_id"] = tst["google_sheets_drive_id"]
            if "google_sheets_template_id" in tst:
                input["google_sheets_template_id"] = tst["google_sheets_template_id"]
            if "log_level" in tst:
                input["log_level"] = tst["log_level"]
            if "metrics_broker" in tst:
                input["metrics_broker"] = tst["metrics_broker"]
            if "refresh_to" in tst:
                input["refresh_to"] = tst["refresh_to"]
            if "service" in tst:
                input["service"] = tst["service"]
            if "task_to" in tst:
                input["task_to"] = tst["task_to"]
            if "upload" in tst:
                input["upload"] = tst["upload"]
            if "workers" in tst:
                input["workers"] = tst["workers"]
            if "callback_api_key" in tst:
                input["callback_api_key"] = tst["callback_api_key"]
            if "callback_api_key_env_val" in tst:
                os.environ.update({CALLBACK_KEY: tst["callback_api_key_env_val"]})
            if "valid_api_keys" in tst:
                input["valid_api_keys"] = tst["valid_api_keys"]
            if "valid_api_keys_env_val" in tst:
                os.environ.update({VALID_KEYS: tst["valid_api_keys_env_val"]})

            settings = ContainerSettings(**input)

            self.assertIsInstance(settings, ContainerSettings)

            self.assertEqual(settings.broker, tst["expect"]["broker"])

            self.assertEqual(settings.cache_to, tst["expect"]["cache_to"])

            self.assertEqual(
                settings.google_sheets_drive_id, tst["expect"]["google_sheets_drive_id"]
            )

            self.assertEqual(
                settings.google_sheets_template_id,
                tst["expect"]["google_sheets_template_id"],
            )

            self.assertEqual(settings.log_level, tst["expect"]["log_level"])

            self.assertEqual(settings.metrics_broker, tst["expect"]["metrics_broker"])

            self.assertEqual(settings.refresh_to, tst["expect"]["refresh_to"])

            self.assertEqual(settings.service, tst["expect"]["service"])

            self.assertEqual(settings.task_to, tst["expect"]["task_to"])

            self.assertEqual(settings.workers, tst["expect"]["workers"])

            if tst["expect"]["callback_api_key"] == Exception:
                self.assertRaises(Exception, settings.get_callback_api_key)
            else:
                self.assertEqual(
                    settings.get_callback_api_key(), tst["expect"]["callback_api_key"]
                )

            if tst["expect"]["valid_api_keys"] == Exception:
                self.assertRaises(Exception, settings.get_valid_api_keys)
            else:
                self.assertEqual(
                    settings.get_valid_api_keys(), tst["expect"]["valid_api_keys"]
                )

            self.assertEqual(settings.loglevel(), tst["expect"]["loglevel"])

            self.assertEqual(settings.status_broker(), tst["expect"]["status_broker"])


class TestGroundXSettings(unittest.TestCase):
    def test(self) -> None:
        tsts: typing.List[typing.Dict[str, typing.Any]] = [
            {
                "api_key_env": "",
                "expect": {
                    "api_key": Exception,
                    "api_key_env": "",
                    "base_url": None,
                    "upload_url": "https://upload.eyelevel.ai",
                },
            },
            {
                "api_key": "mykey",
                "api_key_env_val": "val",
                "base_url": "http://api.example.com",
                "upload_url": "http://upload.example.com",
                "expect": {
                    "api_key": "mykey",
                    "base_url": "http://api.example.com",
                    "upload_url": "http://upload.example.com",
                },
            },
            {
                "api_key_env_val": "val",
                "expect": {
                    "api_key": "val",
                    "base_url": None,
                    "upload_url": "https://upload.eyelevel.ai",
                },
            },
        ]

        for _, tst in enumerate(tsts):
            clearEnv()

            input: typing.Dict[str, str] = {}
            if "api_key" in tst:
                input["api_key"] = tst["api_key"]
            if "api_key_env_val" in tst:
                os.environ.update({GX_API_KEY: tst["api_key_env_val"]})
            if "base_url" in tst:
                input["base_url"] = tst["base_url"]
            if "upload_url" in tst:
                input["upload_url"] = tst["upload_url"]

            settings = GroundXSettings(**input)

            self.assertIsInstance(settings, GroundXSettings)

            if tst["expect"]["api_key"] == Exception:
                self.assertRaises(Exception, settings.get_api_key)
            else:
                self.assertEqual(settings.get_api_key(), tst["expect"]["api_key"])

            if tst["expect"]["base_url"]:
                self.assertEqual(settings.base_url, tst["expect"]["base_url"])
            else:
                self.assertIsNone(settings.base_url)

            self.assertEqual(settings.upload_url, tst["expect"]["upload_url"])


if __name__ == "__main__":
    unittest.main()
