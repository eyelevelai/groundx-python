from unittest.mock import patch

from groundx.extract.services.deadline import operation_deadline
from groundx.extract.services.http import (
    BoundedRequestTimeout,
    bounded_get,
    bounded_head,
    bounded_post,
)


class _Response:
    pass


def test_bounded_get_uses_remaining_shared_deadline() -> None:
    now = [100.0]

    with (
        patch(
            "groundx.extract.services.deadline.time.monotonic",
            side_effect=lambda: now[0],
        ),
        patch(
            "groundx.extract.services.http.time.monotonic",
            side_effect=lambda: now[0],
        ),
        patch("requests.get", return_value=_Response()) as get,
        operation_deadline(3.0),
    ):
        bounded_get("https://example.test/page", operation="page")

    assert get.call_args.kwargs["timeout"] == (3.0, 3.0)


def test_nested_deadline_cannot_extend_parent() -> None:
    now = [100.0]

    with (
        patch(
            "groundx.extract.services.deadline.time.monotonic",
            side_effect=lambda: now[0],
        ),
        patch(
            "groundx.extract.services.http.time.monotonic",
            side_effect=lambda: now[0],
        ),
        patch("requests.get", return_value=_Response()) as get,
        operation_deadline(4.0),
    ):
        with operation_deadline(30.0):
            bounded_get("https://example.test/page", operation="page")

    assert get.call_args.kwargs["timeout"] == (4.0, 4.0)


def test_expired_shared_deadline_does_not_start_http_request() -> None:
    now = [100.0]

    with (
        patch(
            "groundx.extract.services.deadline.time.monotonic",
            side_effect=lambda: now[0],
        ),
        patch(
            "groundx.extract.services.http.time.monotonic",
            side_effect=lambda: now[0],
        ),
        patch("requests.get") as get,
        operation_deadline(2.0),
    ):
        now[0] = 103.0
        try:
            bounded_get("https://example.test/page", operation="page")
        except BoundedRequestTimeout:
            pass
        else:
            raise AssertionError("expired deadline should fail")

    get.assert_not_called()


def test_bounded_head_uses_remaining_shared_deadline() -> None:
    now = [100.0]

    with (
        patch(
            "groundx.extract.services.deadline.time.monotonic",
            side_effect=lambda: now[0],
        ),
        patch(
            "groundx.extract.services.http.time.monotonic",
            side_effect=lambda: now[0],
        ),
        patch("requests.head", return_value=_Response()) as head,
        operation_deadline(2.0),
    ):
        bounded_head("https://example.test/page", operation="page metadata")

    assert head.call_args.kwargs["timeout"] == (2.0, 2.0)


def test_bounded_post_uses_remaining_shared_deadline() -> None:
    now = [100.0]

    with (
        patch(
            "groundx.extract.services.deadline.time.monotonic",
            side_effect=lambda: now[0],
        ),
        patch(
            "groundx.extract.services.http.time.monotonic",
            side_effect=lambda: now[0],
        ),
        patch("requests.post", return_value=_Response()) as post,
        operation_deadline(2.0),
    ):
        bounded_post("https://example.test/callback", json={"code": 200})

    assert post.call_args.kwargs["timeout"] == (2.0, 2.0)
