import sys
import types
import typing
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from groundx.extract.services.status import Status


class _Logger:
    def info_msg(self, *_args: typing.Any, **_kwargs: typing.Any) -> None:
        pass


class _Settings:
    service = "summary"
    workers = 4
    cache_to = 300

    def status_broker(self) -> str:
        return "rediss://redis.test:6380/0"


def _status_with_client(client: typing.Any) -> Status:
    status = typing.cast(typing.Any, object.__new__(Status))
    status.client = client
    status.config = SimpleNamespace(service="summary", workers=4)
    status.logger = _Logger()
    return typing.cast(Status, status)


def test_status_redis_client_has_explicit_socket_bounds() -> None:
    redis_factory = Mock()
    no_backoff = object()
    retry_policy = object()
    no_backoff_factory = Mock(return_value=no_backoff)
    retry_factory = Mock(return_value=retry_policy)
    redis_module = types.ModuleType("redis")
    setattr(redis_module, "Redis", redis_factory)
    setattr(
        redis_module, "backoff", types.SimpleNamespace(NoBackoff=no_backoff_factory)
    )
    setattr(redis_module, "retry", types.SimpleNamespace(Retry=retry_factory))

    with patch.dict(sys.modules, {"redis": redis_module}):
        Status(_Settings(), _Logger())  # type: ignore[arg-type]

    assert redis_factory.call_args.kwargs == {
        "decode_responses": True,
        "host": "redis.test",
        "port": 6380,
        "retry": retry_policy,
        "socket_connect_timeout": 5.0,
        "socket_timeout": 5.0,
        "ssl": True,
    }
    no_backoff_factory.assert_called_once_with()
    retry_factory.assert_called_once_with(no_backoff, 0)


def test_prompt_init_lock_has_bounded_acquisition() -> None:
    client = Mock()

    _status_with_client(client).prompt_init_lock()

    client.lock.assert_called_once_with(
        name="prompt_manager:init",
        timeout=15.0,
        blocking_timeout=15.0,
    )


def test_get_service_state_preserves_complete_scan_totals() -> None:
    class RedisClient:
        values = {
            "summary:a:requests": "2",
            "summary:b:requests": "1",
            "summary:a:total": "3",
            "summary:b:total": "2",
        }

        def scan(
            self,
            cursor: int,
            *,
            match: str,
            count: int,
        ) -> typing.Tuple[int, typing.List[str]]:
            assert count == 1000
            suffix = match.rsplit(":", 1)[-1]
            keys = [key for key in self.values if key.endswith(f":{suffix}")]
            return 0, keys

        def get(self, key: str) -> str:
            return self.values[key]

    assert _status_with_client(RedisClient()).get_service_state() == (3, 5)


def test_get_service_state_stops_when_total_scan_deadline_expires() -> None:
    clock = [0.0]

    class SlowRedisClient:
        def scan(
            self,
            cursor: int,
            *,
            match: str,
            count: int,
        ) -> typing.Tuple[int, typing.List[str]]:
            clock[0] += 3.0
            return 1, ["summary:a:requests"]

        def get(self, key: str) -> str:
            clock[0] += 3.0
            return "1"

    with (
        patch(
            "groundx.extract.services.status.REDIS_SCAN_DEADLINE_SECONDS",
            5.0,
        ),
        patch(
            "groundx.extract.services.status.time.monotonic",
            side_effect=lambda: clock[0],
        ),
        pytest.raises(TimeoutError, match="service status scan exceeded"),
    ):
        _status_with_client(SlowRedisClient()).get_service_state()
