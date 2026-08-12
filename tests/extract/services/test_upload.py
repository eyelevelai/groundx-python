import math
import typing

import pytest

from groundx.extract.services.upload import Upload, validate_upload_timeouts


class _Client:
    def __init__(self) -> None:
        self.kwargs: typing.Dict[str, typing.Any] = {}

    def get_object(self, url: str, **kwargs: typing.Any) -> typing.Optional[bytes]:
        self.url = url
        self.kwargs = kwargs
        return b"workflow"

    def put_json_stream(
        self,
        bucket: str,
        key: str,
        data: bytes,
        content_type: str,
        **kwargs: typing.Any,
    ) -> None:
        self.kwargs = kwargs


def test_upload_forwards_network_timeout_budget() -> None:
    client = _Client()
    upload = Upload.__new__(Upload)
    upload.client = typing.cast(typing.Any, client)

    upload.put_json_stream(
        "eyelevel",
        "trace.json",
        b"{}",
        "application/json",
        connect_timeout_seconds=0.2,
        read_timeout_seconds=0.5,
        total_timeout_seconds=0.8,
    )

    assert client.kwargs == {
        "connect_timeout_seconds": 0.2,
        "read_timeout_seconds": 0.5,
        "total_timeout_seconds": 0.8,
    }


def test_upload_forwards_object_read_timeout_budget() -> None:
    client = _Client()
    upload = Upload.__new__(Upload)
    upload.client = typing.cast(typing.Any, client)

    body = upload.get_object(
        "s3://eyelevel/workflow.yaml",
        connect_timeout_seconds=0.2,
        read_timeout_seconds=0.5,
        total_timeout_seconds=0.8,
    )

    assert body == b"workflow"
    assert client.url == "s3://eyelevel/workflow.yaml"
    assert client.kwargs == {
        "connect_timeout_seconds": 0.2,
        "read_timeout_seconds": 0.5,
        "total_timeout_seconds": 0.8,
    }


def test_upload_preserves_unbounded_object_read_call() -> None:
    client = _Client()
    upload = Upload.__new__(Upload)
    upload.client = typing.cast(typing.Any, client)

    body = upload.get_object("s3://eyelevel/workflow.yaml")

    assert body == b"workflow"
    assert client.kwargs == {}


@pytest.mark.parametrize("invalid", [math.nan, math.inf, -math.inf])
@pytest.mark.parametrize(
    "component",
    [
        "connect_timeout_seconds",
        "read_timeout_seconds",
        "total_timeout_seconds",
    ],
)
def test_upload_timeout_components_must_be_finite(
    component: str,
    invalid: float,
) -> None:
    values = {
        "connect_timeout_seconds": 0.2,
        "read_timeout_seconds": 0.5,
        "total_timeout_seconds": 0.8,
    }
    values[component] = invalid

    with pytest.raises(ValueError, match="finite"):
        validate_upload_timeouts(**values)
