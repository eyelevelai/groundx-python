# Proposal — fix-persisted-workflow-derivation

## Why

Live prod testing (2026-07-08, cashbot-go `accept-workflow-yaml-source` E2E) proved that **any
workflow with repeating groups (meters/charges-style list output) fails extraction** when the
runtime derives its reassembly metadata from the persisted workflow. Five deployed workflows
(four Go-compiled + the platform's own `studio-demo` from May) all fail; a local reproduction
against the persisted forms isolated two defects in `src/groundx/extract/prompt/utility.py`
(identical in 3.7.7 and 3.7.8):

1. **Wildcard poisoning** — `_apply_custom_workflow_field_paths` copies each persisted route's
   `final_path` verbatim into `workflow_field_paths`. Harness-dialect workflows store
   `/charges/*/amount` (3 segments, not a valid RFC 6901 pointer); the reassembly parser
   (`extraction_reassembly._parse_final_path`) requires exactly 2 segments and rejects them →
   `route ... must have exactly two non-empty path segments` / `missing routed group` 500s.
   The authored-YAML path derives correct 2-segment paths; only persisted-readback breaks.

2. **Hash false-positive** — `_normalize_persisted_custom_workflow_metadata` recomputes the
   schema hash over its *re-normalized* structures and compares it to the stored hash that was
   computed over the *original* (harness-dialect) structures. Different canonicalization →
   guaranteed mismatch → `ValueError: caller schema_hash does not match route metadata`. The
   runtime's metadata loader swallows the exception and proceeds with no metadata (observed as
   the v1/utility extraction hang).

Root context: two long-standing compiled dialects exist (harness `compile_workflow.py`:
3-segment + `is_repeated: true`; SDK `prepare_extraction_yaml`: 2-segment + flags), documented
in cashbot-go `pkg/testdata/workflowyaml/goldens/FINDINGS.md`. Production deploys the harness
dialect; the extraction runtime reads the SDK dialect. This change makes the SDK reader
**dialect-tolerant** so every already-stored workflow works; the companion cashbot-go change
(`canonical-workflow-metadata`) makes the API store a single canonical form going forward.

## What changes

- `_apply_custom_workflow_field_paths` is pinned VERBATIM (re-scoped by fresh-scan P1/P2: `*`
  tokens are the SDK's own row-routing vocabulary — field-level lists — so stripping them here
  broke 7 SDK tests). The wildcard normalization for the reassembly parser's 2-segment
  contract moves to its only consumer's export boundary: internal-arcadia-agents
  `workflow_reassembly_metadata` (task 3.2).
- Readers STOP verifying writer hashes entirely (adversarial finding F1: even an as-received
  recompute diverges across hash implementations — proven SDK `896b…` vs stored Go `f1a2…`
  over identical structures). The stored `schema_hash` is writer-owned and opaque; read-time
  integrity is structural validation; the server becomes the only hash authority
  (cashbot-go `canonical-workflow-metadata` 2.3).
- Regression tests pinned to **both dialect goldens** (harness-dialect and SDK-dialect
  persisted extracts) must derive byte-identical `workflow_field_paths` and pass reassembly
  preflight; plus an end-to-end repeated-group reassembly test — the exact case production
  missed.

## Impact

- Affected: only the persisted-workflow read path (`prepare_extraction_yaml` "persisted"
  classification). Today that path always fails for repeated groups, so the change strictly
  enables; SDK-dialect inputs are byte-identical before/after.
- Consumers: internal-arcadia-agents (extract pods) via `prepare_arcadia_extraction_yaml`.
  Rollout = SDK release → internal-arcadia-agents pin bump → extract pod redeploy → rerun the
  cashbot-go live proof matrix (repeated-group population).
- Out of scope here: what the API stores (cashbot-go `canonical-workflow-metadata`), the
  internal-arcadia-agents exception-swallowing (follow-up noted in tasks).
