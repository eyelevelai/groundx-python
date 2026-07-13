import os
import time
import typing

import requests

DEFAULT_HTTP_CONNECT_TIMEOUT_SECONDS = 5.0
DEFAULT_HTTP_READ_TIMEOUT_SECONDS = 30.0
DEFAULT_HTTP_MAX_ATTEMPTS = 2
DEFAULT_HTTP_BACKOFF_CAP_SECONDS = 5.0
DEFAULT_HTTP_OPERATION_DEADLINE_SECONDS = 75.0

DEFAULT_CALLBACK_CONNECT_TIMEOUT_SECONDS = 3.0
DEFAULT_CALLBACK_READ_TIMEOUT_SECONDS = 10.0
DEFAULT_CALLBACK_MAX_ATTEMPTS = 2
DEFAULT_CALLBACK_BACKOFF_CAP_SECONDS = 3.0
DEFAULT_CALLBACK_OPERATION_DEADLINE_SECONDS = 30.0


class BoundedRequestError(RuntimeError):
    def __init__(
        self,
        *,
        operation: str,
        url: str,
        attempts: int,
        cause: BaseException,
    ) -> None:
        self.operation = operation
        self.url = url
        self.attempts = attempts
        self.cause = cause
        super().__init__(
            f"Error fetching {operation} from {url} after {attempts} attempts: {cause}"
        )


class BoundedRequestTimeout(BoundedRequestError):
    pass


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    return float(raw)


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    return int(raw)


def _bounded_request(
    method: typing.Callable[..., requests.Response],
    url: str,
    *,
    operation: str,
    connect_timeout: float,
    read_timeout: float,
    max_attempts: int,
    backoff_cap_seconds: float,
    operation_deadline_seconds: float,
    sleep_between_attempts: bool = True,
    **kwargs: typing.Any,
) -> requests.Response:
    started = time.monotonic()
    attempts = max(1, max_attempts)
    last_exc: typing.Optional[requests.RequestException] = None

    for attempt in range(attempts):
        remaining = operation_deadline_seconds - (time.monotonic() - started)
        if remaining <= 0:
            cause = requests.Timeout(
                f"{operation} exceeded {operation_deadline_seconds} second deadline"
            )
            raise BoundedRequestTimeout(
                operation=operation, url=url, attempts=attempt, cause=cause
            ) from cause

        try:
            return method(
                url,
                timeout=(connect_timeout, min(read_timeout, remaining)),
                **kwargs,
            )
        except requests.RequestException as exc:
            last_exc = exc
            if attempt == attempts - 1:
                error_type = (
                    BoundedRequestTimeout
                    if isinstance(exc, requests.Timeout)
                    else BoundedRequestError
                )
                raise error_type(
                    operation=operation,
                    url=url,
                    attempts=attempts,
                    cause=exc,
                ) from exc

            if sleep_between_attempts:
                backoff = min(float(attempt + 1), backoff_cap_seconds)
                elapsed = time.monotonic() - started
                remaining_after_attempt = operation_deadline_seconds - elapsed
                if remaining_after_attempt <= 0:
                    continue
                time.sleep(min(backoff, remaining_after_attempt))

    assert last_exc is not None
    raise BoundedRequestError(
        operation=operation, url=url, attempts=attempts, cause=last_exc
    ) from last_exc


def bounded_get(
    url: str,
    *,
    operation: str,
    connect_timeout: typing.Optional[float] = None,
    read_timeout: typing.Optional[float] = None,
    max_attempts: typing.Optional[int] = None,
    backoff_cap_seconds: typing.Optional[float] = None,
    operation_deadline_seconds: typing.Optional[float] = None,
    sleep_between_attempts: bool = True,
    **kwargs: typing.Any,
) -> requests.Response:
    return _bounded_request(
        requests.get,
        url,
        operation=operation,
        connect_timeout=connect_timeout
        if connect_timeout is not None
        else _env_float(
            "GROUNDX_EXTRACT_HTTP_CONNECT_TIMEOUT_SECONDS",
            DEFAULT_HTTP_CONNECT_TIMEOUT_SECONDS,
        ),
        read_timeout=read_timeout
        if read_timeout is not None
        else _env_float(
            "GROUNDX_EXTRACT_HTTP_READ_TIMEOUT_SECONDS",
            DEFAULT_HTTP_READ_TIMEOUT_SECONDS,
        ),
        max_attempts=max_attempts
        if max_attempts is not None
        else _env_int(
            "GROUNDX_EXTRACT_HTTP_MAX_ATTEMPTS",
            DEFAULT_HTTP_MAX_ATTEMPTS,
        ),
        backoff_cap_seconds=backoff_cap_seconds
        if backoff_cap_seconds is not None
        else _env_float(
            "GROUNDX_EXTRACT_HTTP_BACKOFF_CAP_SECONDS",
            DEFAULT_HTTP_BACKOFF_CAP_SECONDS,
        ),
        operation_deadline_seconds=operation_deadline_seconds
        if operation_deadline_seconds is not None
        else _env_float(
            "GROUNDX_EXTRACT_HTTP_OPERATION_DEADLINE_SECONDS",
            DEFAULT_HTTP_OPERATION_DEADLINE_SECONDS,
        ),
        sleep_between_attempts=sleep_between_attempts,
        **kwargs,
    )


def bounded_post(
    url: str,
    *,
    operation: str = "callback",
    connect_timeout: typing.Optional[float] = None,
    read_timeout: typing.Optional[float] = None,
    max_attempts: typing.Optional[int] = None,
    backoff_cap_seconds: typing.Optional[float] = None,
    operation_deadline_seconds: typing.Optional[float] = None,
    sleep_between_attempts: bool = True,
    **kwargs: typing.Any,
) -> requests.Response:
    return _bounded_request(
        requests.post,
        url,
        operation=operation,
        connect_timeout=connect_timeout
        if connect_timeout is not None
        else _env_float(
            "GROUNDX_EXTRACT_CALLBACK_CONNECT_TIMEOUT_SECONDS",
            DEFAULT_CALLBACK_CONNECT_TIMEOUT_SECONDS,
        ),
        read_timeout=read_timeout
        if read_timeout is not None
        else _env_float(
            "GROUNDX_EXTRACT_CALLBACK_READ_TIMEOUT_SECONDS",
            DEFAULT_CALLBACK_READ_TIMEOUT_SECONDS,
        ),
        max_attempts=max_attempts
        if max_attempts is not None
        else _env_int(
            "GROUNDX_EXTRACT_CALLBACK_MAX_ATTEMPTS",
            DEFAULT_CALLBACK_MAX_ATTEMPTS,
        ),
        backoff_cap_seconds=backoff_cap_seconds
        if backoff_cap_seconds is not None
        else _env_float(
            "GROUNDX_EXTRACT_CALLBACK_BACKOFF_CAP_SECONDS",
            DEFAULT_CALLBACK_BACKOFF_CAP_SECONDS,
        ),
        operation_deadline_seconds=operation_deadline_seconds
        if operation_deadline_seconds is not None
        else _env_float(
            "GROUNDX_EXTRACT_CALLBACK_OPERATION_DEADLINE_SECONDS",
            DEFAULT_CALLBACK_OPERATION_DEADLINE_SECONDS,
        ),
        sleep_between_attempts=sleep_between_attempts,
        **kwargs,
    )
