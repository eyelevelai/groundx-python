# Compiler Retirement Inventory

## Authoring boundary

| Former SDK responsibility | Canonical owner and protection |
| --- | --- |
| YAML validation and supported shapes | Cashbot `pkg/workflowyaml/compile_rules_test.go` and `canonical_v1_contract_test.go` |
| Legacy Arcadia synthesis | Cashbot `legacy_synthesis_test.go` |
| Custom steps, routes, leaf fields, and agent chain | Cashbot `TestCompileWorkflowYAMLRequestBody`, `Test_WorkflowYAML_EndToEndJourney`, and `TestWorkflowYAML_ProductCreateUpdateUsesExplicitOutputScope` |
| Create, update, readback, idempotence, and source preservation | Cashbot `workflow_test.go` and `workflow_persistence_test.go` YAML journey tests |
| V1 downgrade and malformed-source rejection | Cashbot workflow handler and compiler rule tests |
| SDK transport | `test_raw_yaml_workflow_authoring.py` and `test_create_extraction_workflow_sends_only_authored_yaml` |

SDK tests that asserted locally compiled `extract`, `customSteps`,
`outputRoutes`, `leafFields`, or fixed-step overlays were removed because those
outputs now belong to Cashbot. Their behavior tests remain in the owning service.

## Remaining compiler consumers

- Internal Arcadia still uses `prepare_extraction_yaml` for local prompt-source
  loading. Deployed workflow loading already consumes persisted prompts and
  task metadata without running the authoring compiler.
- Studio Harness still uses its own compiler for deploy, run, prompt manager,
  certification diagnostics, fanout, and field coverage.
- GroundX Python prompt-manager and compiler tests still consume
  `prepare_extraction_yaml`.

The public compiler and compiler-only types cannot be removed until these
supported consumers migrate. Raw-YAML create and update are safe now because
Internal Arcadia PR 125 already calls `workflows.create` and
`workflows.update` with authored YAML directly.
