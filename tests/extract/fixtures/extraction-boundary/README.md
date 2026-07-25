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

Only the external model/provider response may be replaced by a fixed fixture.
Tests must call production reassembly functions unchanged.
