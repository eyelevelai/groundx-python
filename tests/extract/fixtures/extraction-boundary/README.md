# Extraction Boundary Fixtures

These fixtures freeze GroundX Python's X-Ray-to-structured-output reassembly
behavior for Arcadia legacy, Arcadia v1, generic v1, and ADP v1.

Each case consumes the committed handoff produced by the previous pipeline
boundary. `test_extraction_boundary_reassembly.py` passes that input through the
same reassembly functions used by the SDK and compares the complete stable
result with the reviewed expected output.

Accepted fixtures must be real-derived, privacy-reviewed, and sanitized with
recorded source hashes and transformations. The adjacent review records and
fixture verifier establish that status; this README does not. These are
standard CI inputs, not a live test or scoring rule. Document-specific meter,
charge, or field counts must never enter SDK runtime behavior.

Expected output may change only after the behavior change is reviewed. Generate
a candidate diff separately, explain why the old behavior is wrong, and obtain
Benjamin Fletcher's approval before replacing an accepted fixture. Never update
an expected file merely because a new run differs.

When the reviewed X-Ray input candidate changes, generate matching SDK output
candidates with:

```bash
poetry run python tests/extract/build_extraction_boundary_candidates.py \
  --xray-candidate-manifest <xray-candidate-root>/fixture_candidate_manifest.json \
  --candidate-root <empty-sdk-candidate-root>
```

This command calls `reassemble_custom_outputs_from_xray` and writes only to the
candidate root. It records shape and diagnostic assertions but does not require
them to pass; candidate generation freezes observed behavior, while human review
decides whether that behavior should replace the accepted fixture. Review and
approve both candidate-manifest hashes before using the Studio Harness promotion
command. Do not promote an X-Ray input without its matching SDK output candidate.

Only the external model/provider response may be replaced by a fixed fixture.
Tests must call production reassembly functions unchanged.

GroundX Python's reassembly boundary has no external I/O call to replace. Its
input is the committed X-Ray handoff, so `writer_registry.json` declares an
empty mock allowlist. The source-discovery tests require the certifying replay
to call `reassemble_custom_outputs_from_xray` and reject replacement of that
module's parser, relationship, reassembly, or result-building code.
