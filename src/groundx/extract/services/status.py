import time
import typing

from ..settings.settings import ContainerSettings
from .logger import Logger
from fastapi import Response

latency_to = 60
REDIS_CONNECT_TIMEOUT_SECONDS = 5.0
REDIS_SOCKET_TIMEOUT_SECONDS = 5.0
REDIS_SCAN_DEADLINE_SECONDS = 10.0
PROMPT_INIT_LOCK_TIMEOUT_SECONDS = 15.0


class Status:
    def __init__(
        self,
        cfg: ContainerSettings,
        logger: Logger,
    ) -> None:
        import redis

        rl_port = 6379
        rl_host = cfg.status_broker()
        rl_ssl = False
        if rl_host.endswith("/0"):
            rl_host = rl_host[:-2]
        if rl_host.startswith("redis://"):
            rl_host = rl_host[8:]
        elif rl_host.startswith("rediss://"):
            rl_host = rl_host[9:]
            rl_ssl = True
        if ":" in rl_host:
            base, number = rl_host.rsplit(":", 1)
            if number.isdigit():
                rl_port = int(number)
                rl_host = base

        self.client = redis.Redis(
            host=rl_host,
            port=rl_port,
            decode_responses=True,
            ssl=rl_ssl,
            retry=redis.retry.Retry(redis.backoff.NoBackoff(), 0),
            socket_connect_timeout=REDIS_CONNECT_TIMEOUT_SECONDS,
            socket_timeout=REDIS_SOCKET_TIMEOUT_SECONDS,
        )
        self.host = rl_host
        self.port = rl_port

        self.config = cfg
        self.logger = logger

        self.logger.info_msg(
            f"\n\t[{self.config.service}] [status.Status.__init__]\n\t\t{self.host}:{self.port}",
        )

    def get_worker_state(
        self, id: str, to: typing.Optional[int] = None
    ) -> typing.Tuple[typing.Optional[int], int]:
        online = self.client.get(self.key_worker_status(id))
        if online is None or online == "offline":
            return None, self.config.workers

        key_worker_available = self.key_worker_available(id)

        current_available = self.client.get(key_worker_available)
        if current_available is None:
            return None, self.config.workers

        return int(current_available), self.config.workers  # type: ignore

    def get_service_state(self) -> typing.Tuple[int, int]:
        deadline = time.monotonic() + REDIS_SCAN_DEADLINE_SECONDS
        available = self._sum_service_values(
            f"{self.config.service}:*:requests",
            deadline,
        )
        total = self._sum_service_values(
            f"{self.config.service}:*:total",
            deadline,
        )

        if total == 0:
            total = self.config.workers

        return available, total

    def _sum_service_values(self, match: str, deadline: float) -> int:
        cursor = 0
        total = 0
        while True:
            self._check_scan_deadline(deadline)
            cursor, keys = self.client.scan(cursor=cursor, match=match, count=1000)
            self._check_scan_deadline(deadline)
            for key in keys:
                value = self.client.get(key)
                self._check_scan_deadline(deadline)
                if value is not None:
                    total += int(value)
            if cursor == 0:
                return total

    def _check_scan_deadline(self, deadline: float) -> None:
        if time.monotonic() >= deadline:
            raise TimeoutError(
                f"service status scan exceeded {REDIS_SCAN_DEADLINE_SECONDS} seconds"
            )

    def key_api_latency(self, id: str) -> str:
        return f"{id}:{time.time_ns()}:latency"

    def key_worker_available(self, id: str) -> str:
        return f"{self.config.service}:{id}:requests"

    def key_worker_status(self, id: str) -> str:
        return f"{self.config.service}:{id}:status"

    def key_worker_total(self, id: str) -> str:
        return f"{self.config.service}:{id}:total"

    def prompt_init_lock(self) -> typing.Any:
        return self.client.lock(
            name="prompt_manager:init",
            timeout=PROMPT_INIT_LOCK_TIMEOUT_SECONDS,
            blocking_timeout=PROMPT_INIT_LOCK_TIMEOUT_SECONDS,
        )

    def refresh_worker(self, id: str, to: typing.Optional[int] = None) -> None:
        self.refresh_worker_online(id, to)
        self.refresh_worker_total(id, to)
        self.refresh_worker_available(id, to)

    def refresh_worker_available(
        self, id: str, to: typing.Optional[int] = None
    ) -> None:
        key_worker_available = self.key_worker_available(id)
        current_available = self.client.get(key_worker_available)
        if current_available is None:
            self.set_value(key_worker_available, self.config.workers, to)
        else:
            if to is not None:
                if to > 0:
                    self.client.expire(key_worker_available, to)
            else:
                self.client.expire(key_worker_available, self.config.cache_to)

    def refresh_worker_online(self, id: str, to: typing.Optional[int] = None) -> None:
        self.set_worker_online(id, to)

    def refresh_worker_total(self, id: str, to: typing.Optional[int] = None) -> None:
        self.set_value(self.key_worker_total(id), self.config.workers, to)

    def set_api_latency(
        self, id: str, val: int, to: typing.Optional[int] = None
    ) -> None:
        if to is None:
            global latency_to

            to = latency_to

        self.set_value(self.key_api_latency(id), val, to)

    def set_headers(
        self,
        response: Response,
        id: str,
        available: typing.Optional[int],
        total: typing.Optional[int],
    ) -> typing.Any:
        if available is None:
            available = 0
        if total is None:
            total = 0

        response.headers.update(
            {
                "X-RateLimit-Limit-Requests": str(total),
                "X-RateLimit-Remaining-Requests": str(max(0, available)),
                "X-ID": id,
            }
        )

        return response

    def set_value(
        self, key: str, value: typing.Union[str, int], to: typing.Optional[int] = None
    ) -> None:
        if to is not None:
            if to > 0:
                self.client.set(key, value, ex=to)
            else:
                self.client.set(key, value, ex=self.config.cache_to)
        else:
            self.client.set(key, value, ex=self.config.cache_to)

    def set_worker_available(self, id: str, to: typing.Optional[int] = None) -> None:
        self.refresh_worker_online(id, to)

        self.refresh_worker_total(id, to)

        key_worker_available = self.key_worker_available(id)
        current_available = self.client.get(key_worker_available)
        if current_available is None:
            available = self.config.workers
            self.set_value(key_worker_available, available, to)
        else:
            self.set_value(
                key_worker_available,
                min(self.config.workers, int(current_available) + 1),  # type: ignore
                to,
            )

    def set_worker_offline(self, id: str, to: typing.Optional[int] = None) -> None:
        if to is None:
            to = self.config.cache_to
        self.logger.info_msg(f"\n\n\t\t[{self.config.service}] offline [{id}]\n")
        self.set_value(self.key_worker_status(id), "offline", to)
        self.set_worker_unavailable(id, to)

    def set_worker_online(self, id: str, to: typing.Optional[int] = None) -> None:
        self.set_value(self.key_worker_status(id), "online", to)

    def set_worker_unavailable(self, id: str, to: typing.Optional[int] = None) -> None:
        self.refresh_worker_online(id, to)

        self.set_value(self.key_worker_total(id), self.config.workers, to)

        key_worker_available = self.key_worker_available(id)
        current_available = self.client.get(key_worker_available)
        if current_available is None:
            available = self.config.workers - 1
            self.set_value(key_worker_available, available, to)
        else:
            self.set_value(
                key_worker_available,
                max(0, int(current_available) - 1),  # type: ignore
                to,
            )
