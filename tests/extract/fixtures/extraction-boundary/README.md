# Extraction Boundary Fixtures

This repository's writer registry (`writer_registry.json`) owns one artifact,
`groundx_python_xray_reassembly` consumes two exact captured inputs for each
protected extraction case: Arcadia's untouched `input.xray.json` predecessor
envelope and the matching untouched workflow-load handoff. Its committed output
is the reviewed result of GroundX Python's X-Ray-to-structured-output reassembly.

`tests/extract/test_extraction_boundary_reassembly.py` is the replay consumer.
Each case validates the predecessor envelope's raw model bytes, byte count,
SHA-256, complete `value`, and live run, process, and document identity. It then
passes `value` plus the matching handoff's workflow through the production SDK
reassembly function and compares the complete stable result with the reviewed
expected output. There is no rebuilt X-Ray sidecar or fallback input.

Accepted fixtures must be exact captures from a registered test case, reviewed
by a non-author for repository storage, and byte-identical to their recorded
source hashes. The adjacent review records and fixture verifier establish that
status. These are standard CI inputs, not a live test or scoring rule.
Document-specific meter, charge, or field counts must never enter SDK runtime
behavior.

Expected output may change only after the behavior change is reviewed. Generate
a candidate diff separately, explain why the old behavior is wrong, and obtain
Benjamin Fletcher's approval before replacing an accepted fixture. Never update
an expected file merely because a new run differs.

For an intentional reassembly change, declare the exact output paths allowed to change
before editing SDK behavior. The old fixture remains the before-state, and a candidate
may replace only those declared output differences. Every undeclared difference remains a regression.
Current SDK output cannot approve itself; non-author review and guarded promotion are
still required before accepted fixtures change.

When the reviewed exact X-Ray predecessor or workflow-load input changes,
generate matching SDK output candidates with:

```bash
poetry run python tests/extract/build_extraction_boundary_candidates.py \
  --xray-candidate-manifest <capture-candidate-root>/fixture_candidate_manifest.json \
  --candidate-root <empty-sdk-candidate-root>
```

This command calls `reassemble_custom_outputs_from_xray` and writes only to the
candidate root. For each selected surface, it must replay both exact inputs from
the same capture candidate manifest. It rejects changed consumer copies,
cross-run pairs, invalid raw-model hashes, incomplete identity, and parsed values
that differ from the captured bytes. Candidate generation freezes observed
behavior; human review decides whether that behavior replaces the accepted
fixture. Do not promote either input without its matching SDK output candidate.

Only the external model/provider response may be replaced by a fixed fixture.
Tests must call production reassembly functions unchanged.

Fixture capture, diagnosis, updates, and final certification use the canonical
private Studio Harness guide only: `groundx-extraction-workflows`,
`references/certification.private.md`.
