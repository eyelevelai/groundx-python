# AGENTS.md

Table of contents. Read the route that matches the change; keep durable rules
in the linked docs, not in this entrypoint.

| Topic | Read when |
|---|---|
| [Contributor workflow](CONTRIBUTING.md) | You need setup, tests, release flow, PR guidance, validation, or rules for committed comments. |
| [`.fernignore`](.fernignore) | Before editing any SDK file. Only `.fernignore`-protected paths are safe to hand-edit here; use it for the generated-vs-hand-written boundary. |
| [`src/groundx/ingest.py`](src/groundx/ingest.py) | You are changing the hand-written ingest helper. |
| [`src/groundx/extract/`](src/groundx/extract/) | You are changing the hand-written extract helper surface. |
| [Extraction boundary fixtures](tests/extract/fixtures/extraction-boundary/README.md) | You are changing X-Ray reassembly, relationship behavior, expected outputs, or the reviewed fixture-update path. |
| [`tests/custom/`](tests/custom/) | You are adding hand-written regression coverage around generated or preserved SDK behavior. |
| [Extraction boundary fixtures](tests/extract/fixtures/extraction-boundary/README.md) | A four-case X-Ray reassembly test changed or failed. Read this before changing any accepted fixture, then follow the Studio Harness **Normal Fixture Update Path**. |
| [`eyelevel-fern-config`](https://github.com/eyelevelai/eyelevel-fern-config) | You need an API-shape, generated model, endpoint, package metadata, or SDK generation change. |
| [`scripts/check-line-endings.sh`](scripts/check-line-endings.sh) | You need to verify tracked files use LF line endings (run before pushing; also enforced in CI). |
