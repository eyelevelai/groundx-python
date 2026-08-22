# Tasks: preserve persisted workflow readback

## 1. Boundary contract

- [x] 1.1 Add a regression using a historical persisted authored snapshot with
      `final_value_aliases`; prove readback does not compile it.
- [x] 1.2 Add a regression using the real v1 contract shape with a persisted
      agent chain that current authoring validation would reject; prove
      readback preserves it.
- [x] 1.3 Keep structural validation for persisted execution metadata and
      authoring-only key leakage.

## 2. Implementation

- [x] 2.1 Remove `prepare_extraction_yaml()` from workflow-response and explicit
      `workflow_extract` loading.
- [x] 2.2 Preserve the persisted extract and workflow-level settings exactly.
- [x] 2.3 Return `prepared=None` for every existing-workflow readback.
- [x] 2.4 Document the authored-input and persisted-readback boundary on sync
      and async clients.

## 3. Verification and rollout

- [x] 3.1 Closed as superseded by the supported runtime. The package now
      requires Python 3.10 or newer, so the obsolete Python 3.9 gate was not
      run. PR 77 merged, and the final promoted-fixture main CI passed at
      `8b1479e` on the supported runtime.
- [x] 3.2 Replay the exact protected workflow readbacks and record compact
      inputs, outputs, identities, and failures.
- [x] 3.3 Open and merge the SDK PR through normal repository gates. PR 77
      merged as `da9423d`.
- [x] 3.4 Human release owner publishes the next SDK version. The change shipped
      in GroundX Python 3.9.15.
- [x] 3.5 Update Internal Arcadia's SDK pin, deploy the approved production
      branch, and verify extract, reconcile, QA, and save handoffs on the exact
      saved files before capture resumes. Internal Arcadia pins 3.9.15. The
      four-case configured-set certification passed with
      `certification_eligible: true` before the consolidated plan archived on
      2026-08-22.
