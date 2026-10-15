import os
import typing
from unittest.mock import patch

import pytest

from groundx.extract.services.logger import Logger
from groundx.extract.services.upload import Upload
from groundx.extract.services.upload_minio import MinIOClient
from groundx.extract.services.upload_s3 import S3Client
from groundx.extract.settings.settings import (
    AWS_DEFAULT_REGION,
    AWS_REGION,
    GX_DEFAULT_REGION,
    GX_REGION,
    ContainerSettings,
    ContainerUploadSettings,
)

KEY = "layout/processed/doc.json"
KEY_WITH_LEADING_SLASH = "/layout/processed/doc.json"
REGION_ENV = {
    GX_REGION: "us-west-2",
    AWS_REGION: "us-west-2",
    GX_DEFAULT_REGION: "us-west-2",
    AWS_DEFAULT_REGION: "us-west-2",
}
PRIVATE_EVIDENCE_TAGS = {"groundx-artifact-class": "extraction-private-evidence"}
TOTAL_TIMEOUT_ARGUMENTS = ["total_timeout_seconds", "transport_total_timeout_seconds"]


def _upload(upload_type: str, region: typing.Optional[str] = None) -> Upload:
    return Upload(
        ContainerSettings(
            broker="",
            service="upload_s4",
            upload=ContainerUploadSettings(
                base_domain="s4.test:7480",
                bucket="eyelevel",
                region=region,
                type=upload_type,
                url="",
            ),
            workers=1,
        ),
        Logger("upload_s4", "debug"),
    )


def test_upload_type_s4_selects_s4_client_with_a_live_minio_client() -> None:
    with patch("minio.Minio") as minio_cls:
        upload = _upload("s4")

    from groundx.extract.services.upload_s4 import S4Client

    assert isinstance(upload.client, S4Client)
    assert upload.client.client is minio_cls.return_value


@pytest.mark.parametrize(
    ("upload_type", "expected_client"),
    [("minio", MinIOClient), ("s3", S3Client)],
)
def test_minio_and_s3_upload_types_keep_their_clients(upload_type: str, expected_client: type) -> None:
    with patch("minio.Minio"), patch("boto3.client"):
        upload = _upload(upload_type)

    assert type(upload.client) is expected_client


def test_upload_rejects_an_unknown_upload_type_before_building_a_client() -> None:
    with patch("minio.Minio") as minio_cls, patch("boto3.client") as boto3_client:
        with pytest.raises(Exception, match=r"unsupported upload\.type \[gcs\]"):
            _upload("gcs")

    minio_cls.assert_not_called()
    boto3_client.assert_not_called()


@pytest.mark.parametrize("total_timeout_argument", TOTAL_TIMEOUT_ARGUMENTS)
@pytest.mark.parametrize(
    ("upload_type", "configured_region", "expected_region"),
    [
        ("s4", "us-west-2", "us-east-1"),
        ("s4", None, "us-east-1"),
        ("minio", None, "us-west-2"),
    ],
)
def test_s4_signs_for_us_east_1_and_minio_keeps_the_configured_region(
    upload_type: str,
    configured_region: typing.Optional[str],
    expected_region: str,
    total_timeout_argument: str,
) -> None:
    total_timeout: typing.Dict[str, typing.Any] = {total_timeout_argument: 0.8}
    with patch.dict(os.environ, REGION_ENV), patch("minio.Minio") as minio_cls:
        upload = _upload(upload_type, region=configured_region)
        upload.put_json_stream(
            "eyelevel",
            KEY,
            b"{}",
            "application/json",
            connect_timeout_seconds=0.2,
            read_timeout_seconds=0.5,
            **total_timeout,
        )

    assert [call.kwargs["region"] for call in minio_cls.call_args_list] == [expected_region, expected_region]


@pytest.mark.parametrize(
    ("upload_type", "key", "stored_key"),
    [
        ("s4", KEY_WITH_LEADING_SLASH, KEY),
        ("s4", KEY, KEY),
        ("minio", KEY_WITH_LEADING_SLASH, KEY_WITH_LEADING_SLASH),
    ],
)
def test_put_object_trims_a_leading_slash_only_in_s4_mode(upload_type: str, key: str, stored_key: str) -> None:
    with patch("minio.Minio") as minio_cls:
        upload = _upload(upload_type)
        upload.put_object("eyelevel", key, b"{}", "application/json")

    put = minio_cls.return_value.put_object.call_args.kwargs
    assert put["bucket_name"] == "eyelevel"
    assert put["object_name"] == stored_key


@pytest.mark.parametrize("total_timeout_argument", TOTAL_TIMEOUT_ARGUMENTS)
@pytest.mark.parametrize(
    ("upload_type", "key", "stored_key"),
    [
        ("s4", KEY_WITH_LEADING_SLASH, KEY),
        ("s4", KEY, KEY),
        ("minio", KEY_WITH_LEADING_SLASH, KEY_WITH_LEADING_SLASH),
    ],
)
def test_put_json_stream_trims_a_leading_slash_only_in_s4_mode_and_keeps_tags_and_timeouts(
    upload_type: str,
    key: str,
    stored_key: str,
    total_timeout_argument: str,
) -> None:
    total_timeout: typing.Dict[str, typing.Any] = {total_timeout_argument: 0.8}
    with patch("minio.Minio") as minio_cls:
        upload = _upload(upload_type)
        upload.put_json_stream(
            "eyelevel",
            key,
            b"{}",
            "application/json",
            connect_timeout_seconds=0.2,
            read_timeout_seconds=0.5,
            object_tags=PRIVATE_EVIDENCE_TAGS,
            **total_timeout,
        )

    put = minio_cls.return_value.put_object.call_args.kwargs
    assert put["bucket_name"] == "eyelevel"
    assert put["object_name"] == stored_key
    assert dict(put["tags"]) == PRIVATE_EVIDENCE_TAGS
    assert minio_cls.call_args.kwargs["http_client"].connection_pool_kw["timeout"].total == 0.8
