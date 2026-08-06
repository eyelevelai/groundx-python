import types
import typing
from unittest.mock import patch

import pytest

from groundx.extract.prompt.manager import PromptManager
from groundx.extract.services.deadline import operation_deadline


class _Logger:
    def debug_msg(self, *_args: typing.Any, **_kwargs: typing.Any) -> None:
        pass

    def info_msg(self, *_args: typing.Any, **_kwargs: typing.Any) -> None:
        pass


class _Source:
    def fetch(self, _workflow_id: str) -> typing.NoReturn:
        raise FileNotFoundError

    def peek(self, _workflow_id: str) -> None:
        return None


def _assert_bounded_request_options(options: typing.Any, maximum: float) -> None:
    assert options["max_retries"] == 0
    assert 0 < options["timeout_in_seconds"] <= maximum


def test_prompt_manager_bounds_generated_discovery_calls() -> None:
    calls: typing.List[typing.Dict[str, typing.Any]] = []

    class Workflows:
        def get_account(
            self,
            *,
            request_options: typing.Optional[typing.Dict[str, typing.Any]] = None,
        ) -> typing.Any:
            calls.append(typing.cast(typing.Dict[str, typing.Any], request_options))
            return types.SimpleNamespace(workflow=None)

        def list(
            self,
            *,
            request_options: typing.Optional[typing.Dict[str, typing.Any]] = None,
        ) -> typing.Any:
            calls.append(typing.cast(typing.Dict[str, typing.Any], request_options))
            return types.SimpleNamespace(workflows=[])

    with (
        operation_deadline(9.0),
        patch.object(PromptManager, "cache_workflow", side_effect=RuntimeError),
    ):
        PromptManager(
            cache_source=typing.cast(typing.Any, _Source()),
            config_source=typing.cast(typing.Any, _Source()),
            gx_client=typing.cast(
                typing.Any,
                types.SimpleNamespace(workflows=Workflows()),
            ),
            logger=typing.cast(typing.Any, _Logger()),
        )

    assert len(calls) == 2
    for options in calls:
        _assert_bounded_request_options(options, 9.0)


def test_prompt_manager_bounds_generated_workflow_get() -> None:
    calls: typing.List[typing.Dict[str, typing.Any]] = []

    class Workflows:
        def get(
            self,
            id: str,
            *,
            request_options: typing.Optional[typing.Dict[str, typing.Any]] = None,
        ) -> typing.Any:
            assert id == "workflow-1"
            calls.append(typing.cast(typing.Dict[str, typing.Any], request_options))
            return types.SimpleNamespace(
                workflow=types.SimpleNamespace(extract={"statement": {}})
            )

    manager = object.__new__(PromptManager)
    manager._gx_client = typing.cast(  # type: ignore[attr-defined]
        typing.Any,
        types.SimpleNamespace(workflows=Workflows()),
    )

    with operation_deadline(7.0):
        extract, version = manager._fetch_workflow_extract("workflow-1")

    assert extract == {"statement": {}}
    assert version
    assert len(calls) == 1
    _assert_bounded_request_options(calls[0], 7.0)


def test_prompt_manager_does_not_retry_generated_workflow_type_error() -> None:
    calls = 0

    class Workflows:
        def get(
            self,
            id: str,
            *,
            request_options: typing.Optional[typing.Dict[str, typing.Any]] = None,
        ) -> typing.NoReturn:
            nonlocal calls
            assert id == "workflow-1"
            _assert_bounded_request_options(request_options, 7.0)
            calls += 1
            raise TypeError("response decode failed")

    manager = object.__new__(PromptManager)
    manager._gx_client = typing.cast(  # type: ignore[attr-defined]
        typing.Any,
        types.SimpleNamespace(workflows=Workflows()),
    )

    with operation_deadline(7.0), pytest.raises(TypeError, match="response decode"):
        manager._fetch_workflow_extract("workflow-1")

    assert calls == 1
