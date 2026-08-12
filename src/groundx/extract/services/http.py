import contextlib
import os
import signal
import threading
import time
import typing

import requests
from .deadline import remaining_operation_seconds

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
DEFAULT_GENERATED_CLIENT_TIMEOUT_SECONDS = 30.0


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
        super().__init__(f"Error fetching {operation} from {url} after {attempts} attempts: {cause}")


class BoundedRequestTimeout(BoundedRequestError):
    pass


class WallClockDeadlineExceeded(TimeoutError):
    pass


def bounded_generated_request_options(
    timeout_seconds: float = DEFAULT_GENERATED_CLIENT_TIMEOUT_SECONDS,
) -> typing.Dict[str, typing.Any]:
    remaining = remaining_operation_seconds(timeout_seconds)
    assert remaining is not None
    if remaining <= 0:
        raise TimeoutError("generated client call exceeded operation deadline")
    return {
        "timeout_in_seconds": remaining,
        "max_retries": 0,
    }


@contextlib.contextmanager
def wall_clock_operation_deadline(
    seconds: float,
    *,
    operation: str,
) -> typing.Iterator[None]:
    """Use SIGALRM for a hard main-thread deadline.

    Worker threads rely on transport-native connect/read limits. Streaming
    response bodies add a per-response abort timer through
    ``read_response_body_with_deadline``.
    """
    if seconds <= 0:
        raise ValueError("operation deadline must be greater than zero")
    set_timer = getattr(signal, "setitimer", None)
    get_timer = getattr(signal, "getitimer", None)
    alarm_signal = getattr(signal, "SIGALRM", None)
    if (
        threading.current_thread() is not threading.main_thread()
        or not callable(set_timer)
        or not callable(get_timer)
        or alarm_signal is None
    ):
        yield
        return

    previous_delay, _ = typing.cast(
        typing.Tuple[float, float],
        get_timer(signal.ITIMER_REAL),
    )
    if previous_delay > 0:
        raise RuntimeError("wall-clock deadline cannot replace an active alarm")
    previous_handler = signal.getsignal(alarm_signal)

    def raise_timeout(_signum: int, _frame: typing.Any) -> typing.NoReturn:
        raise WallClockDeadlineExceeded(f"{operation} exceeded {seconds} second deadline")

    signal.signal(alarm_signal, raise_timeout)
    set_timer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        set_timer(signal.ITIMER_REAL, 0)
        signal.signal(alarm_signal, previous_handler)


def read_response_body_with_deadline(
    read_body: typing.Callable[[], bytes],
    close_response: typing.Callable[[], None],
    *,
    abort_response: typing.Optional[typing.Callable[[], None]] = None,
    total_timeout_seconds: typing.Optional[float],
    started_at: typing.Optional[float],
    operation: str,
) -> bytes:
    """Read and close one response within its operation's remaining budget.

    A joined non-daemon timer aborts only this response if the body stalls. On
    the main thread, SIGALRM also bounds the complete operation when available.
    Neither mechanism closes the leased client or affects unrelated requests.
    """
    if total_timeout_seconds is None:
        try:
            return read_body()
        finally:
            close_response()

    if started_at is None:
        raise ValueError("started_at is required for a bounded response read")

    remaining = total_timeout_seconds - (time.monotonic() - started_at)
    if remaining <= 0:
        close_response()
        raise WallClockDeadlineExceeded(f"{operation} exceeded {total_timeout_seconds} second deadline")

    state_lock = threading.Lock()
    close_lock = threading.Lock()
    completed = False
    expired = False
    closed = False

    def close_once(*, abort: bool = False) -> None:
        nonlocal closed
        with close_lock:
            if closed:
                return
            closed = True
        if abort and abort_response is not None:
            abort_response()
        else:
            close_response()

    def expire() -> None:
        nonlocal expired
        with state_lock:
            if completed:
                return
            expired = True
        close_once(abort=True)

    timer = threading.Timer(remaining, expire)
    timer.daemon = False
    timer.start()
    try:
        try:
            result = read_body()
        except BaseException as exc:
            with state_lock:
                completed = True
                did_expire = expired
            if did_expire:
                raise WallClockDeadlineExceeded(
                    f"{operation} exceeded {total_timeout_seconds} second deadline"
                ) from exc
            raise
        else:
            with state_lock:
                completed = True
                did_expire = expired
            if did_expire:
                raise WallClockDeadlineExceeded(f"{operation} exceeded {total_timeout_seconds} second deadline")
            return result
    finally:
        timer.cancel()
        timer.join()
        close_once()


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
        local_remaining = operation_deadline_seconds - (time.monotonic() - started)
        remaining = remaining_operation_seconds(local_remaining)
        assert remaining is not None
        if remaining <= 0:
            cause = requests.Timeout(f"{operation} exceeded {operation_deadline_seconds} second deadline")
            raise BoundedRequestTimeout(operation=operation, url=url, attempts=attempt, cause=cause) from cause

        try:
            return method(
                url,
                timeout=(
                    min(connect_timeout, remaining),
                    min(read_timeout, remaining),
                ),
                **kwargs,
            )
        except requests.RequestException as exc:
            last_exc = exc
            if attempt == attempts - 1:
                error_type = BoundedRequestTimeout if isinstance(exc, requests.Timeout) else BoundedRequestError
                raise error_type(
                    operation=operation,
                    url=url,
                    attempts=attempts,
                    cause=exc,
                ) from exc

            if sleep_between_attempts:
                backoff = min(float(attempt + 1), backoff_cap_seconds)
                elapsed = time.monotonic() - started
                local_remaining = operation_deadline_seconds - elapsed
                remaining_after_attempt = remaining_operation_seconds(local_remaining)
                assert remaining_after_attempt is not None
                if remaining_after_attempt <= 0:
                    continue
                time.sleep(min(backoff, remaining_after_attempt))

    assert last_exc is not None
    raise BoundedRequestError(operation=operation, url=url, attempts=attempts, cause=last_exc) from last_exc


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


def bounded_head(
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
        requests.head,
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
