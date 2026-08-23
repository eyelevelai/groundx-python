import asyncio
import typing
from pathlib import Path

import pytest

from groundx import AsyncGroundX, GroundX


class RecordingWorkflows:
    def __init__(self) -> None:
        self.calls: list[tuple[typing.Any, ...]] = []

    def create(self, **kwargs: typing.Any) -> str:
        self.calls.append(("create", kwargs))
        return "created"

    def update(self, workflow_id: str, **kwargs: typing.Any) -> str:
        self.calls.append(("update", workflow_id, kwargs))
        return "updated"


class AsyncRecordingWorkflows:
    def __init__(self) -> None:
        self.calls: list[tuple[typing.Any, ...]] = []

    async def create(self, **kwargs: typing.Any) -> str:
        self.calls.append(("create", kwargs))
        return "created"

    async def update(self, workflow_id: str, **kwargs: typing.Any) -> str:
        self.calls.append(("update", workflow_id, kwargs))
        return "updated"


def _client(workflows: RecordingWorkflows) -> GroundX:
    client = GroundX.__new__(GroundX)
    typing.cast(typing.Any, client)._workflows = workflows
    return client


def _async_client(workflows: AsyncRecordingWorkflows) -> AsyncGroundX:
    client = AsyncGroundX.__new__(AsyncGroundX)
    typing.cast(typing.Any, client)._workflows = workflows
    return client


def test_create_extraction_workflow_passes_yaml_text_unchanged() -> None:
    workflows = RecordingWorkflows()
    raw_yaml = "not: [locally valid\n"

    result = _client(workflows).create_extraction_workflow(
        name="raw workflow",
        yaml_text=raw_yaml,
    )

    assert result == "created"
    assert workflows.calls == [("create", {"name": "raw workflow", "yaml": raw_yaml, "request_options": None})]


def test_update_extraction_workflow_reads_path_without_rewriting(tmp_path: Path) -> None:
    workflows = RecordingWorkflows()
    raw_yaml = "statement:\n  fields: {}\n# preserve trailing comment\n"
    source = tmp_path / "workflow.yaml"
    source.write_text(raw_yaml, encoding="utf-8")

    result = _client(workflows).update_extraction_workflow(
        "workflow-1",
        path=source,
    )

    assert result == "updated"
    assert workflows.calls == [("update", "workflow-1", {"yaml": raw_yaml, "request_options": None})]


@pytest.mark.parametrize(
    "kwargs",
    [
        {},
        {"path": "workflow.yaml", "yaml_text": "statement: {}\n"},
    ],
)
def test_extraction_workflow_authoring_requires_one_raw_source(
    kwargs: dict[str, typing.Any],
) -> None:
    workflows = RecordingWorkflows()

    with pytest.raises(ValueError, match="exactly one.*path, yaml_text"):
        _client(workflows).create_extraction_workflow(name="raw workflow", **kwargs)

    assert workflows.calls == []


def test_async_extraction_workflow_authoring_passes_yaml_unchanged() -> None:
    async def run() -> None:
        workflows = AsyncRecordingWorkflows()
        raw_yaml = "not: [locally valid\n"
        client = _async_client(workflows)

        created = await client.create_extraction_workflow(
            name="raw workflow",
            yaml_text=raw_yaml,
        )
        updated = await client.update_extraction_workflow(
            "workflow-1",
            yaml_text=raw_yaml,
        )

        assert created == "created"
        assert updated == "updated"
        assert workflows.calls == [
            (
                "create",
                {"name": "raw workflow", "yaml": raw_yaml, "request_options": None},
            ),
            (
                "update",
                "workflow-1",
                {"yaml": raw_yaml, "request_options": None},
            ),
        ]

    asyncio.run(run())
