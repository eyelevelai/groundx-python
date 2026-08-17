# Tasks — default-first-stable-ties

- [x] 1.1 Flip behavior-table row R16, the seam reassembly tie test, the
      duplicate-parents reassembly test, and the at-scale strategy test to the
      `first_stable` default, red before the source change.
- [x] 1.2 `select_relationship_parent`: treat an absent
      `multiple_match_strategy` as `first_stable` on multiple direct matches;
      update the primitive and result-dataclass docstrings, including the
      corrected `origin/main` baseline citation.
- [x] 1.3 Rewrite `test_pending_accepted_inputs_declare_one_ambiguity_strategy`
      to reject only a foreign declared strategy; drop its `pending_decision`
      marker and the promotion-time declaration requirement.
- [x] 1.4 Full `tests/extract` suite: no failures beyond the 14 pre-existing
      on `origin/main` (verified by identical baseline run in the same venv).
- [ ] 1.5 Release the change (next patch after 3.9.9) and update consumer pins
      (internal-arcadia-agents `requirements.txt` and `Dockerfile.extract`;
      Studio Harness `templates/requirements.txt` floor). Gated on Benjamin's
      release approval. Remaining work is routed to the consolidated plan at
      internal-arcadia-agents/openspec/changes/complete-extraction-boundary-regression-coverage/tasks.md
      (tasks 9.1 and 9.5f own the pin, rebuild, and capture rerun); this change
      archives with that plan's closeout.
