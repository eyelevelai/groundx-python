import typing

from groundx.extract.services.upload import Upload


class _Client:
    def __init__(self) -> None:
        self.kwargs: typing.Dict[str, typing.Any] = {}

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
