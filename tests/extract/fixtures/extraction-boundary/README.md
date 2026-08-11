# Extraction Boundary Fixtures

This repository's writer registry (`writer_registry.json`) owns one artifact,
`groundx_python_xray_reassembly`: the committed sanitized expected output of
GroundX Python's X-Ray-to-structured-output reassembly for each protected
extraction case.

`tests/extract/test_extraction_boundary_reassembly.py` is the replay consumer.
Each case passes the committed handoff produced by the previous pipeline
boundary through the same reassembly functions used by the SDK and compares
the complete stable result with the reviewed expected output.

Accepted fixtures must be real-derived, privacy-reviewed, and sanitized with
recorded source hashes and transformations. The adjacent review records and
fixture verifier establish that status; this README does not. These are
standard CI inputs, not a live test or scoring rule. Document-specific meter,
charge, or field counts must never enter SDK runtime behavior.

Expected output may change only after the behavior change is reviewed. Generate
a candidate diff separately, explain why the old behavior is wrong, and obtain
Benjamin Fletcher's approval before replacing an accepted fixture. Never update
an expected file merely because a new run differs.

For an intentional reassembly change, declare the exact output paths allowed to change
before editing SDK behavior. The old fixture remains the before-state, and a candidate
may replace only those declared output differences. Every undeclared difference remains a regression.
Current SDK output cannot approve itself; non-author review and guarded promotion are
still required before accepted fixtures change.

When the reviewed X-Ray input candidate changes, generate matching SDK output
candidates with:

```bash
poetry run python tests/extract/build_extraction_boundary_candidates.py \
  --xray-candidate-manifest <xray-candidate-root>/fixture_candidate_manifest.json \
  --candidate-root <empty-sdk-candidate-root>
```

This command calls `reassemble_custom_outputs_from_xray` and writes only to the
candidate root. For each selected surface, it must replay both the proposed X-Ray
and the proposed `internal_arcadia_download_workflow_load` successor input from
that same provider candidate manifest. Mixing a proposed X-Ray with the accepted
old producer handoff is invalid lineage and must fail candidate generation.
Candidate generation freezes observed behavior; human review decides whether
that behavior replaces the accepted fixture. Do not promote an X-Ray input
without its matching SDK output candidate.

Only the external model/provider response may be replaced by a fixed fixture.
Tests must call production reassembly functions unchanged.

Fixture capture, diagnosis, updates, and final certification use the canonical
private Studio Harness guide only: `groundx-extraction-workflows`,
`references/certification.private.md`.
