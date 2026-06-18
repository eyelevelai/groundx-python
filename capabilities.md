# groundx-python — capabilities.md

> **Purpose.** Ground-truth, code-verified *execution* layer for local-phase agents. The
> authored-vs-generated boundary, the `ingest.py` line-level deep-dive, the upload-then-ingest
> data flow, the two-tier resource clients, and the change seams are already in
> `ARCHITECTURE_NOTES.md` + `service.yaml` — **not restated here**. This file documents the one
> surface those flag as *unexplored*: the **`extract/` subsystem** (the layer
> `internal-arcadia-agents` imports — the only real cross-repo package import in the workspace),
> plus the precise build/test/lint config.

---

## 1. Authored vs generated (frame only — detail in `ARCHITECTURE_NOTES.md`)

`.fernignore` is the editable allowlist; everything else under `src/groundx/` is Fern-generated
and overwritten on regen. Hand-authored: `ingest.py`, `csv_splitter.py`, **`extract/`**,
`test.py`, `tests/custom`, `tests/extract`, plus docs/config. Public `GroundX`/`AsyncGroundX`
are re-exported from `ingest.py` (subclass the generated `GroundXBase`). For the ingest data
flow and seams, read `ARCHITECTURE_NOTES.md` — not repeated here.

## 2. The `extract/` subsystem (`src/groundx/extract/`, ~37 files)

A standalone, optional document-extraction framework gated behind the `extract` extra (§3).
Independent of the SDK's ingest/search path. This is the surface `internal-arcadia-agents`
consumes via `from groundx.extract import …`.

**Public API — the import contract** (`extract/__init__.py`, lazy-loaded via `importlib` +
`_EXPORT_MODULES`; `__all__`). These symbols are what consumers depend on — **constructor
signatures are the contract and nothing validates it cross-repo** (per `dependency-graph.json`):

| From | Exported symbols |
| --- | --- |
| `.agents` | `AgentCode`, `AgentTool` |
| `.classes` | `AgentRequest`, `Document`, `DocumentRequest`, `Element`, `ExtractedField`, `GroundXDocument`, `Group`, `ProcessResponse`, `Prompt`, `TestChunk`, `TestDocumentPage`, `TestField`, `TestXRay`, `XRayDocument` |
| `.prompt` (+ `.prompt.utility`) | `FinalFieldPath`, `ObjectStore`, `PreparedExtractionYaml`, `PromptManager`, `Source`, `prepare_extraction_yaml` |
| `.services` | `Logger`, `RateLimit`, `SheetsClient`, `Status`, `Upload` |
| `.settings` | `AgentSettings`, `ContainerSettings`, `ContainerUploadSettings`, `GroundXSettings` |
| `.workflows` | `ExtractionDefinition` |

**Module map (subpackage → role):**

| Subpackage | Role |
| --- | --- |
| `workflows.py` | `ExtractionDefinition` + `load_extraction_definition_from_yaml(...)` — the YAML-driven extraction entry point |
| `agents/agent.py` | `AgentCode(CodeAgent)` and `AgentTool(ToolCallingAgent)` — **smolagents** subclasses (the LLM agents) |
| `classes/` | Pydantic domain models: `GroundXDocument`, `XRayDocument`, `Chunk`, `DocumentPage`, `BoundingBox`, `Element`, `ExtractedField`, `Group`, `Prompt`, plus the `Test*` fixtures |
| `prompt/` | `PromptManager`, `Source`, `ObjectStore`, `prepare_extraction_yaml`, `FinalFieldPath` — prompt assembly + extraction-YAML prep |
| `services/` | object stores (`S3Client`, `MinIOClient`) behind `Upload` (and the `UploadClient` Protocol); `SheetsClient` (gspread); `RateLimit`, `Status`, `Logger`, `csv` |
| `settings/` | env-var-driven config models (below) |
| `tasks/utility.py` | Celery task helpers — `error_response` / `success_response(...)` build the callback payloads (the `extract.tasks.utility` mypy `call-arg` override exists for these) |
| `post_process/`, `utility/` | result post-processing + shared helpers |

**Agents:** `AgentCode`/`AgentTool` subclass smolagents `CodeAgent`/`ToolCallingAgent`.
`AgentSettings` defaults: `model_id = "gpt-5-mini"`, `max_steps = 7`. `ContainerSettings` is the
Celery worker config (`broker`, `broker_type = "redis"`, `cache_dir`, `refresh_to`, `service`).

**Configuration is environment-variable driven** (`settings/settings.py` constant names → env):
`GROUNDX_AGENT_API_KEY`, `GROUNDX_CALLBACK_API_KEY`, `GROUNDX_API_KEY`, `GROUNDX_ACCESS_KEY_ID`,
`GROUNDX_SECRET_ACCESS_KEY`, `GROUNDX_SESSION_TOKEN`, `GROUNDX_REGION`/`GROUNDX_DEFAULT_REGION`,
`GROUNDX_VALID_API_KEYS`, `GROUNDX_ADMIN_API_KEY`/`GROUNDX_ADMIN_USERNAME`, `AWS_REGION`/
`AWS_DEFAULT_REGION`, `GCP_CREDENTIALS`. So `extract/` expects AWS/GCP creds + a Redis broker in
its environment — distinct from the SDK's single `X-API-Key`.

## 3. Build, test & quality gates (`pyproject.toml`, `.github/workflows/ci.yml`)

Poetry; **package version `3.7.1`** (note: `ARCHITECTURE_NOTES.md`/`service.yaml` say 3.5.8 —
stale). Two extras:

- `extract` → `boto3, celery, celery-types, dateparser, fastapi, google-api-python-client(+stubs),
  google-auth-stubs, gspread, minio, openai, pillow, redis, smolagents, PyYAML, types-boto3,
  types-dateparser, types-PyYAML` (18). **Required for any `extract/` work.**
- `aiohttp` → `aiohttp, httpx-aiohttp` (async-client tests).

Commands:

| Concern | Command |
| --- | --- |
| Install (base / extract / async) | `poetry install` · `poetry install --extras extract` · `poetry install --extras aiohttp` |
| Type gate (the CI compile job) | `poetry run mypy .` — **mypy `1.13.0`, `pydantic.mypy` plugin**, per-module `ignore_missing_imports` overrides for the extract deps |
| Tests | `poetry run pytest -rP -n auto .` (asyncio_mode `auto`, `testpaths=tests`, `pytest-xdist`) |
| Async subset | `poetry install --extras aiohttp` then run the `aiohttp`-marked tests |
| Lint | `ruff` (line-length 120; isort first-party grouping) |

CI `ci.yml` (on push): **`compile`** (poetry 1.5.1 → `mypy .`) · **`test`** (pytest base, then
`--extras aiohttp`) · **`publish`** (on tag → PyPI). Poetry pinned **1.5.1** in CI; Python 3.10.

> mypy is the **only** automated gate on the hand-written layer — `extract/` and `ingest.py`
> have effectively no behavioral tests (`tests/custom/test_client.py` is a skipped stub).

---

### Gaps (call before assuming)
- **Version drift:** code is `3.7.1`; the committed `ARCHITECTURE_NOTES.md`/`service.yaml` say
  `3.5.8`. Trust `pyproject.toml`.
- `extract/` symbols above are the **public** contract; individual constructor signatures
  (e.g. `ExtractionDefinition`, `GroundXSettings`, `Upload`) were not transcribed — read the
  class in its module when changing a consumer-facing signature, since arcadia depends on them
  unvalidated.
- The `ingest.py` / `csv_splitter.py` internals and the upload-then-ingest flow are documented
  in `ARCHITECTURE_NOTES.md`; this file does not duplicate them.
