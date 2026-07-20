# AGENTS.md

Table of contents. Read the route that matches the change; keep durable rules
in the linked docs, not in this entrypoint.

| Topic | Read when |
|---|---|
| [Repo guide](docs/agents/repo-guide.md) | You need the generated-vs-hand-written boundary, setup, tests, release flow, OpenSpec rules, or SDK agent boundaries. |
| [Contributor workflow](CONTRIBUTING.md) | You are preparing a PR, choosing validation, writing PR notes, or deciding what belongs in committed comments. |
| [`.fernignore`](.fernignore) | Before editing any SDK file. Only `.fernignore`-protected paths are safe to hand-edit here. |
| [`src/groundx/ingest.py`](src/groundx/ingest.py) | You are changing the hand-written ingest helper. |
| [`src/groundx/extract/`](src/groundx/extract/) | You are changing the hand-written extract helper surface. |
| [`tests/custom/`](tests/custom/) | You are adding hand-written regression coverage around generated or preserved SDK behavior. |
| [`eyelevel-fern-config`](https://github.com/eyelevelai/eyelevel-fern-config) | You need an API-shape, generated model, endpoint, package metadata, or SDK generation change. |
