# Tasks — fix-persisted-workflow-derivation

## 1. Failing tests first (TDD; both are red today)

- [x] 1.1 (re-scoped, fresh-scan P1/P2) Tests in THIS repo: (a) harness-dialect stored hash
      never gates loading; (b) `workflow_field_paths` preserves starred `final_path` values
      VERBATIM (the `*` is SDK row-routing vocabulary); (c) recomputed hash attached, never
      compared. Fixture = the real prod readback. The 2-segment derivation tests MOVED to
      internal-arcadia-agents (3.2) — the reassembly export is the only 2-segment consumer.
- [x] 1.2 (lives in internal-arcadia-agents PR #81 with the export fix) Test: end-to-end repeated-group reassembly — workflow output with list groups
      (`meters`/`charges` rows) + harness-dialect persisted metadata reassembles into final
      arrays with zero diagnostics (the exact prod failure).
- [x] 1.3 Test: structural integrity still enforced — corrupt stored structures (drop a
      route's target, malform a leaf) → still raises via structural validation, WITHOUT any
      stored-hash comparison.

## 2. Implementation

- [x] 2.1 (re-scoped) `_apply_custom_workflow_field_paths` stays VERBATIM by design, with a
      comment pinning why (`*` = row-routing vocabulary; normalization is the Arcadia export's
      job). The wildcard normalization implementation moves to internal-arcadia-agents (3.2).
- [x] 2.2 (PR #38) `_normalize_persisted_custom_workflow_metadata`: STOP comparing stored `schema_hash`
      at read time entirely — repro #4 proved even an as-received recompute diverges across
      hash implementations (SDK `896b…` vs stored Go `f1a2…` over the same structures). The
      stored hash is writer-owned/opaque to readers; read-time integrity = structural
      validation (routes/leaves/steps well-formed); the recomputed canonical hash is attached
      for runtime use only, never compared against the stored one. (Server-side hash authority
      lands in cashbot-go `canonical-workflow-metadata` 2.3.)
- [x] 2.3 Confirm `agent_chain` handling unchanged (hash never covered it; keep it that way,
      pinned by a test).

## 3. Release + rollout

- [ ] 3.1 SDK publication was complete for the original persisted-workflow
      derivation work via the released 3.8.4 line, but new SDK code changes
      were added after that release for relationship child-row dedupe in
      `src/groundx/extract/custom_outputs.py`. A new SDK PR merge and release
      are required before deployed extract pods can prove the corrected
      Arcadia-family 24-30 nested meter-charge shape. Runtime verification
      remains owned by the consolidated deployment gate in
      `internal-arcadia-agents`.
- [x] 3.2 (PR #81 — ALSO fixes the hardcoded {meters,charges} array vocabulary: array-ness now derives from workflow metadata per the archived generalize-v1 spec, UNION legacy names per owner ruling; runtime pin/deploy verification tracked in the consolidated plan) internal-arcadia-agents — NOW OWNS THE WILDCARD NORMALIZATION (fresh-scan P2):
      `workflow_reassembly_metadata` normalizes group-repetition paths (`/g/*/f` → `/g/f`)
      when exporting `workflow_field_paths` for the reassembly parser; field-level list paths
      (still >2 tokens after the strip) get an EXPLICIT unsupported-in-reassembly error, not
      silence (fresh-scan P3). Tests: harness-dialect persisted workflow through
      `prepare_arcadia_extraction_yaml` + `reassemble_from_metadata` end-to-end (the moved
      2-segment tests live here); bump `groundx[extract]` pin.
- [x] 3.3 (folded into PR #81, NOT separate — adversarial finding: the export fix raises errors the swallow would eat) stop silently swallowing metadata
      loader exceptions (`classes/statement.py:1400`) — surface as a visible diagnostic; the
      prod hang was undebuggable because the ValueError vanished.
- [ ] 3.4 Diagnostics for the three un-root-caused live failures BEFORE declaring the retest
      gate: (a) confirm the v1/utility hang mechanism in pod logs (the swallowed
      `caller schema_hash` ValueError at the observed timestamps); (b) root-cause scaffold's
      empty workflow output (custom steps produced no groups at all — readback keys? steps
      never ran?); (c) root-cause legacy's all-empty values (legacy shape has no customSteps —
      is the standard pipeline expected to populate it at all, and if not, what should the API
      return?). Each becomes a test or a documented expected-behavior note.
- [ ] 3.5 Tolerance lifetime: this dialect tolerance is deleted ONLY when the cashbot-go store
      audit (canonical-workflow-metadata 4.2) shows zero non-canonical rows — not on a
      schedule. Cross-linked there.
- [ ] 3.6 Redeploy extract pods; rerun the cashbot-go live proof matrix (legacy, v1, utility,
      scaffold + studio-demo control) with the rich utility PDF; require populated
      `meters`/`charges` rows, not just completion. Then delete test workflows/buckets
      (30065-30068, 30096).
