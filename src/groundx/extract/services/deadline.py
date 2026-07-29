from __future__ import annotations

import contextlib
import contextvars
import time
import typing

_deadline: contextvars.ContextVar[typing.Optional[float]] = contextvars.ContextVar(
    "groundx_extract_operation_deadline",
    default=None,
)


@contextlib.contextmanager
def operation_deadline(seconds: float) -> typing.Iterator[None]:
    if seconds <= 0:
        raise ValueError("operation deadline must be greater than zero")

    candidate = time.monotonic() + seconds
    current = _deadline.get()
    token = _deadline.set(min(candidate, current) if current is not None else candidate)
    try:
        yield
    finally:
        _deadline.reset(token)


def remaining_operation_seconds(
    default: typing.Optional[float] = None,
) -> typing.Optional[float]:
    deadline = _deadline.get()
    if deadline is None:
        return default

    remaining = max(0.0, deadline - time.monotonic())
    if default is None:
        return remaining
    return min(default, remaining)
