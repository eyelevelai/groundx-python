# Workflow Revision SDK Helper Design

## Reuse existing interfaces

At main 1dc8a28989ae6cb582c859893d4c3b3a1cce0eb3,
GroundX and AsyncGroundX in src/groundx/ingest.py expose
load_extraction_definition, load_extraction_definition_from_workflow,
create_extraction_workflow, and update_extraction_workflow. Workflow reads use
src/groundx/extract/workflows.py's load_extraction_definition_from_workflow_response.
Create/update submit raw authored YAML through generated workflows methods.

Add keyword-only revision_id: Optional[str] = None to both workflow-backed
loaders, preserving existing positional workflow_id calls. The generic loader
accepts revision_id only with workflow_id; a revision without a workflow ID or
an empty revision string raises ValueError before HTTP. Existing non-revision
source-selection semantics stay unchanged. A supplied revision uses the generated
workflows.get_revision method; an omitted revision retains workflows.get.

Use the existing saved-extract parser beneath both response adapters. The new
revision response wrapper must be validated before selecting its compiled
settings.extract. Confirm returned workflow/revision identity matches the request.
Do not wrap current settings in an invented historical response, parse YAML to
reconstruct metadata, or recompile source. Missing extraction settings remains
an explicit ValueError; HTTP/auth/storage failures propagate through the generated
error path. Explicit revision failures never retry the current-workflow endpoint.
The returned ExtractionDefinition preserves saved extract and prepared=None;
server revision metadata must remain accessible through generated revision reads.

Add keyword-only expected_updated_at to sync/async update_extraction_workflow,
using the SDK's existing OMIT convention. Forward it unchanged when supplied;
omit it when absent. Preserve name omission, request_options, customer context,
raw source bytes, and the existing requirement for one source. No second restore
wrapper: callers use the generated workflows.restore_revision operation.

## Compatibility and generated boundary

Inspect .fernignore before edits. Do not hand-edit src/groundx/workflows,
src/groundx/types, generated clients, pyproject.toml, or reference.md. Fern owns
schemas, method names, generated metadata and both language targets. Require the
matching generated revision API before enabling new helper options. Existing
calls work without revision arguments. All sync changes have async counterparts.

Read active retire-local-workflow-compiler and archived
2026-06-11-persist-authored-extraction-yaml-in-workflows before editing loaders.
Preserve canonical persisted metadata and shared relationship selection. Do not
turn historical read support into another compiler or expand removed authoring APIs.

## Tests and release

Extend tests/custom/test_extraction_workflow_client_exports.py,
tests/extract/test_extraction_workflow_definitions.py, and
tests/extract/test_raw_yaml_workflow_authoring.py. Use the real helper and
generated clients with mocked HTTP, not substitute implementations. Assert
URLs/query formats, original YAML bytes, unchanged request_options and token,
exact A read after update B, malformed identity rejection, and no fallback after
404/409/5xx. Test sync and async parity.

Run protected replay through tests/extract/test_compact_fixture_pack_replay.py.
The current configured ADP fixture is v4. Preserve Arcadia legacy, Arcadia v1,
generic v1, and ADP v1 supported input behavior separately; do not reinstate a
retired ADP v1 frozen packet to satisfy an obsolete matrix label.

Document current versus historical inspection and conflict handling in README.md
and helper docstrings. Public examples use client.ingest. Produce a release
handoff with source commit, requested version, tests, and downstream pins; a human
chooses the version and runs Fern release workflows. No package publication here.

## Delivery boundary

This is a plan-only change. Implementation tasks remain unchecked. The
[producer-owned design](https://github.com/EyeLevel-ai/cashbot-go/blob/backend/age-349-workflow-revision-plan/openspec/changes/age-349-workflow-revision-management/design.md) defines revision identity, persistence,
authorization, restore, and rollout. This companion owns only its repository's
implementation. Changes to that shared contract must update the producer and
consumers together.

Workflow revisions record configuration, not the runtime software build. Coordinate
with AGE-350 runtime provenance without replacing or claiming its implementation.
