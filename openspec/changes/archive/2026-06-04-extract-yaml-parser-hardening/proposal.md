# Change: Extract YAML Parser Hardening

Status: planned

## Problem

The pseudo-group YAML implementation is released and SDK package readiness is
proven in `groundx[extract]==3.6.0`. The core behavior is covered by
`tests/extract/prompt/test_manager.py`, but several explicit edge-case fixtures
were intentionally left as hardening work after release closeout.

## Goals

- Add named regression tests for parser and pseudo-group edge cases that are not
  already covered by existing manager tests.
- Keep this work SDK-owned; harness should test integration with SDK-prepared
  output, not duplicate the SDK parser matrix.
- Treat any discovered behavior gap as a focused bugfix with an adversarial
  review before closeout.

## Non-goals

- Do not change pseudo-group YAML syntax.
- Do not add harness, Arcadia, or Fern documentation work to this plan.
- Do not do broad Ruff/style cleanup in this change.
