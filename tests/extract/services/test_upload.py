import math
import typing

import pytest

from groundx.extract.services.upload import TimeoutClientCache, Upload, validate_upload_timeouts


class _Client:
    def __init__(self) -> None:
        self.kwargs: typing.Dict[str, typing.Any] = {}

    def get_object(self, url: str, **kwargs: typing.Any) -> typing.Optional[bytes]:
        self.url = url
        self.kwargs = kwargs
        return b"workflow"

    def get_object_and_metadata(
        self,
        url: str,
        **kwargs: typing.Any,
    ) -> typing.Tuple[bytes, typing.Dict[str, str]]:
        self.url = url
        self.kwargs = kwargs
        return b"workflow", {"ETag": '"version"'}

    def head_object(
        self,
        url: str,
        **kwargs: typing.Any,
    ) -> typing.Dict[str, str]:
        self.url = url
        self.kwargs = kwargs
        return {"ETag": '"version"'}

    def put_json_stream(
        self,
        bucket: str,
        key: str,
        data: bytes,
        content_type: str,
        **kwargs: typing.Any,
    ) -> None:
        self.kwargs = kwargs

    def provision_bucket(self) -> None:
        self.provisioned = True


class _CachedClient:
    def __init__(self) -> None:
        self.closed = False

    def close(self) -> None:
        self.closed = True


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


def test_upload_forwards_preferred_transport_total_timeout() -> None:
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
        transport_total_timeout_seconds=0.8,
    )

    assert client.kwargs == {
        "connect_timeout_seconds": 0.2,
        "read_timeout_seconds": 0.5,
        "transport_total_timeout_seconds": 0.8,
    }


def test_put_rejects_both_legacy_and_transport_total_timeouts() -> None:
    client = _Client()
    upload = Upload.__new__(Upload)
    upload.client = typing.cast(typing.Any, client)

    with pytest.raises(ValueError, match="mutually exclusive"):
        upload.put_json_stream(
            "eyelevel",
            "trace.json",
            b"{}",
            "application/json",
            connect_timeout_seconds=0.2,
            read_timeout_seconds=0.5,
            total_timeout_seconds=0.8,
            transport_total_timeout_seconds=0.8,
        )


def test_upload_provisions_bucket_only_when_explicitly_requested() -> None:
    client = _Client()
    upload = Upload.__new__(Upload)
    upload.client = typing.cast(typing.Any, client)

    upload.provision_bucket()

    assert client.provisioned


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


def test_upload_forwards_metadata_read_timeout_budget() -> None:
    client = _Client()
    upload = Upload.__new__(Upload)
    upload.client = typing.cast(typing.Any, client)

    result = upload.get_object_and_metadata(
        "s3://eyelevel/workflow.yaml",
        connect_timeout_seconds=0.2,
        read_timeout_seconds=0.5,
        total_timeout_seconds=0.8,
    )

    assert result == (b"workflow", {"ETag": '"version"'})
    assert client.kwargs == {
        "connect_timeout_seconds": 0.2,
        "read_timeout_seconds": 0.5,
        "total_timeout_seconds": 0.8,
    }


def test_upload_forwards_head_transport_timeout_bounds() -> None:
    client = _Client()
    upload = Upload.__new__(Upload)
    upload.client = typing.cast(typing.Any, client)

    result = upload.head_object(
        "s3://eyelevel/workflow.yaml",
        connect_timeout_seconds=0.2,
        read_timeout_seconds=0.5,
    )

    assert result == {"ETag": '"version"'}
    assert client.kwargs == {
        "connect_timeout_seconds": 0.2,
        "read_timeout_seconds": 0.5,
    }


def test_upload_preserves_unbounded_metadata_and_head_calls() -> None:
    client = _Client()
    upload = Upload.__new__(Upload)
    upload.client = typing.cast(typing.Any, client)

    upload.get_object_and_metadata("s3://eyelevel/workflow.yaml")
    assert client.kwargs == {}

    upload.head_object("s3://eyelevel/workflow.yaml")
    assert client.kwargs == {}


def test_timeout_client_cache_closes_evicted_client_after_last_lease() -> None:
    cache = TimeoutClientCache(lambda client: client.close())
    created: typing.List[_CachedClient] = []

    def create_client() -> _CachedClient:
        client = _CachedClient()
        created.append(client)
        return client

    first_lease = cache.lease((0.2, 0.5, 0.8), create_client)
    second_lease = cache.lease((0.2, 0.5, 0.8), create_client)
    with first_lease as first:
        with second_lease as second:
            assert first is second
            for total in range(1, 10):
                with cache.lease((0.2, 0.5, float(total)), create_client):
                    pass
            assert not first.closed
        assert not first.closed

    assert first.closed


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
