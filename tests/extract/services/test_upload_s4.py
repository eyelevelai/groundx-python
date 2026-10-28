import os
import typing
import urllib.parse
from io import BytesIO
from unittest.mock import Mock, patch

import pytest
from PIL import Image

from groundx.extract.classes.document import DocumentRequest
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
WRITE_METHODS = ["put_object", "put_json_stream"]
SIX_MIB = 6 * 1024 * 1024
MULTIPART_REQUESTS = [
    ("POST", ("uploads",)),
    ("PUT", ("partNumber", "uploadId")),
    ("PUT", ("partNumber", "uploadId")),
    ("POST", ("uploadId",)),
]


class _OverFiveGiB(bytes):
    def __len__(self) -> int:
        return 5 * 1024 * 1024 * 1024 + 1


def _record_storage_requests(
    requests: typing.List[typing.Tuple[str, typing.Tuple[str, ...]]],
) -> typing.Any:
    import urllib3

    def urlopen(_pool: typing.Any, method: str, url: str, **kwargs: typing.Any) -> typing.Any:
        query = tuple(sorted(urllib.parse.parse_qs(urllib.parse.urlsplit(url).query, keep_blank_values=True)))
        requests.append((method, query))
        body = b""
        if method == "POST" and query == ("uploads",):
            body = b"<InitiateMultipartUploadResult><UploadId>u1</UploadId></InitiateMultipartUploadResult>"
        elif method == "POST":
            body = b"<CompleteMultipartUploadResult><ETag>e</ETag></CompleteMultipartUploadResult>"
        return urllib3.HTTPResponse(
            body=body,
            status=200,
            headers={"ETag": '"e"', "Content-Type": "application/xml"},
            preload_content=kwargs.get("preload_content", True),
        )

    return patch.object(urllib3.PoolManager, "urlopen", urlopen)


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


@pytest.mark.parametrize("upload_type", ["s3", "minio", "s4"])
@pytest.mark.parametrize("key", ["/literal%252F+name.jpg", "file/s3://source.test/a.jpg", "eyelevel/original.jpg"])
def test_alias_image_reads_preserve_exact_native_object_keys(upload_type: str, key: str) -> None:
    image = BytesIO()
    Image.new("RGB", (2, 2), color="red").save(image, format="PNG")
    response = Mock()
    response.read.return_value = image.getvalue()
    with patch("minio.Minio") as minio_cls, patch("boto3.client") as boto3_client:
        native = boto3_client.return_value if upload_type == "s3" else minio_cls.return_value
        native.get_object.return_value = {"Body": response} if upload_type == "s3" else response
        upload = _upload(upload_type)
        upload.settings.upload.url = "https://current.test/delivery"
        upload.settings.upload.url_aliases = ["https://old.test/delivery"]
        request = DocumentRequest.model_construct()
        images = request.load_images(["https://old.test/delivery/" + key], upload=upload)

    assert len(images) == 1
    assert images[0].getpixel((0, 0)) == (255, 0, 0)
    if upload_type == "s3":
        native.get_object.assert_called_once_with(Bucket="eyelevel", Key=key)
    else:
        native.get_object.assert_called_once_with("eyelevel", key)


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


@pytest.mark.parametrize("method", WRITE_METHODS)
@pytest.mark.parametrize(
    ("upload_type", "expected_requests"),
    [("s4", [("PUT", ())]), ("minio", MULTIPART_REQUESTS)],
)
def test_s4_sends_an_upload_over_five_mib_as_one_put_and_minio_keeps_multipart(
    method: str,
    upload_type: str,
    expected_requests: typing.List[typing.Tuple[str, typing.Tuple[str, ...]]],
) -> None:
    requests: typing.List[typing.Tuple[str, typing.Tuple[str, ...]]] = []
    with _record_storage_requests(requests):
        upload = _upload(upload_type, region="us-east-1")
        getattr(upload, method)("eyelevel", KEY, b"x" * SIX_MIB, "application/json")

    assert sorted(requests) == sorted(expected_requests)


@pytest.mark.parametrize("method", WRITE_METHODS)
@pytest.mark.parametrize("size", [0, 4 * 1024])
def test_s4_sends_an_upload_under_five_mib_as_one_put(method: str, size: int) -> None:
    requests: typing.List[typing.Tuple[str, typing.Tuple[str, ...]]] = []
    with _record_storage_requests(requests):
        upload = _upload("s4", region="us-east-1")
        getattr(upload, method)("eyelevel", KEY, b"x" * size, "application/json")

    assert requests == [("PUT", ())]


@pytest.mark.parametrize("method", WRITE_METHODS)
def test_s4_refuses_an_upload_over_five_gib_without_sending_a_request(method: str) -> None:
    requests: typing.List[typing.Tuple[str, typing.Tuple[str, ...]]] = []
    with _record_storage_requests(requests):
        upload = _upload("s4")
        with pytest.raises(ValueError):
            getattr(upload, method)("eyelevel", KEY, _OverFiveGiB(b"{}"), "application/json")

    assert requests == []
