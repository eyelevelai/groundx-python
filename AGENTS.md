# AGENTS.md

Table of contents. Read the route that matches the change; keep durable rules
in the linked docs, not in this entrypoint.

| Topic | Read when |
|---|---|
| [Contributor workflow](CONTRIBUTING.md) | You need setup, tests, release flow, PR guidance, validation, or rules for committed comments. |
| [`.fernignore`](.fernignore) | Before editing any SDK file. Only `.fernignore`-protected paths are safe to hand-edit here; use it for the generated-vs-hand-written boundary. |
| [`src/groundx/ingest.py`](src/groundx/ingest.py) | You are changing the hand-written ingest helper. |
| [`src/groundx/extract/`](src/groundx/extract/) | You are changing the hand-written extract helper surface. |
| [Extraction placement contract](openspec/specs/extraction-placement/spec.md) | You are changing extraction YAML parsing, compilation parity, route placement, or GroundX Python's relationship-aware X-Ray/custom-output reassembly. |
| [Custom output readback contract](openspec/specs/custom-output-readback/spec.md) | You are changing custom-output readback, the relationship matcher, or the exported `select_relationship_parent` parent-selection primitive and its `<field>__conflicts` read-side convention. |
| [Extraction fixture pack](tests/extract/test_compact_fixture_pack_replay.py) | Fixture capture, diagnosis, updates, and final certification follow the canonical private Studio Harness guide (`groundx-extraction-workflows` skill, `references/certification.private.md`). |
| Workflow authoring path | You are creating, updating, or managing extraction workflows. Follow the canonical statement in the Studio Harness `groundx-extraction-workflows` skill, `references/4_sdk_integration.md` §6 ("One workflow authoring path"). |
| [`tests/custom/`](tests/custom/) | You are adding hand-written regression coverage around generated or preserved SDK behavior. |
| [`eyelevel-fern-config`](https://github.com/eyelevelai/eyelevel-fern-config) | You need an API-shape, generated model, endpoint, package metadata, or SDK generation change. |
| [`scripts/check-line-endings.sh`](scripts/check-line-endings.sh) | You need to verify tracked files use LF line endings (run before pushing; also enforced in CI). |
| Private Studio Harness `engineering-review` skill | Before approving or executing a nontrivial plan, and before reviewing a ticket, comment thread, or pull request. A passing validator proves structure, not executability or behavioral protection. |
