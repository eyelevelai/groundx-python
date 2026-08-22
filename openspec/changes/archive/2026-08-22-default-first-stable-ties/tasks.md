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
- [x] 1.5 Release the change and update consumer pins. GroundX Python 3.9.10
      contains PR 71. Internal Arcadia now pins 3.9.15 in `requirements.txt`
      and `Dockerfile.extract`; Studio Harness requires
      `groundx[extract]>=3.9.10`. The consolidated four-case closeout passed
      and archived on 2026-08-22.
