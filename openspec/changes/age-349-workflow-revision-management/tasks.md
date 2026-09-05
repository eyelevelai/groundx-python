## 1. Generated dependency and source selection

- [ ] 1.1 Reconcile the Fern-generated revision methods/models with the active
  compiler retirement plan; confirm .fernignore still protects all handwritten paths.
- [ ] 1.2 Add failing sync/async helper tests for revision_id with workflow_id,
  omitted revision, empty revision, revision without workflow ID, and returned
  identity mismatch. Verify the current-read endpoint is never used on explicit failure.
- [ ] 1.3 Extend both loaders in src/groundx/ingest.py and the shared saved-extract
  parser in src/groundx/extract/workflows.py. Consume the real generated revision
  wrapper and canonical compiled extract, preserving prepared=None.

## 2. Safe updates and public response compatibility

- [ ] 2.1 Extend tests/extract/test_raw_yaml_workflow_authoring.py to assert
  exact YAML bytes and supplied versus omitted expected_updated_at in both clients.
- [ ] 2.2 Forward the token through existing update_extraction_workflow methods;
  retain name/request_options semantics. Preserve server response metadata.
- [ ] 2.3 Test HTTP errors through generated clients: missing revision/source,
  stale update, unauthorized access, and storage failure. No blind overwrite,
  silent current fallback, or local source reconstruction.
- [ ] 2.4 Extend tests/custom/test_extraction_workflow_client_exports.py for
  the new keyword arguments and existing exports without creating duplicate
  wrappers for list/history/restore operations.

## 3. Validation and release

- [ ] 3.1 Run poetry run pytest tests/custom tests/extract, poetry run mypy .,
  poetry build, and scripts/check-line-endings.sh --all. Run existing sync/async
  transport variants without live credentials. Do not weaken protected replay.
- [ ] 3.2 Run current configured fixture coverage, including ADP v4, and record
  separate ADP v1 compatibility evidence or the verified unsupported boundary.
- [ ] 3.3 Update README.md and helper docstrings for exact revision reads and
  expected_updated_at conflicts using available service/client methods.
- [ ] 3.4 Prepare the human release handoff after Fern generation and backend
  revision-read readiness. Record the minimum released version for Arcadia and
  Harness; no release tag, workflow dispatch, or package publishing by the agent.
- [ ] 3.5 Validate the OpenSpec change, reconcile related remaining work, and
  archive only after generated clients, helpers, docs, tests, and consumer release
  dependencies are fulfilled. Initialize/close owned local evidence before archive.
