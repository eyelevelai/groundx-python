# Adversarial Review

## Scope

Fresh review of the SDK implementation after generated models, extract YAML
metadata, persisted metadata reload, and custom X-Ray/readback parsing were
implemented.

## Findings

### Fixed: Reserved route template tokens were treated as user template values

The first generated-client and YAML tests used `CUSTOM_WORKFLOW_*` values in
`workflow.template`. That contradicted the cashbot runtime, where those tokens
are reserved and injected per output route. The tests now use a normal user
template key, `BILLING_HINT`, while the SDK keeps `CUSTOM_WORKFLOW_*` reserved.

### Fixed: Authored repeated list paths dropped the list field name

The initial authored YAML traversal emitted `/invoice/*/description` for a list
field `invoice.charges[].description`. The correct schema pointer is
`/invoice/charges/*/description`. A regression test now covers this case and
the traversal keeps the list field name while omitting `*` from the
`workflow_field` value.

### Fixed: Custom steps without output routes were accepted

The initial authored metadata path allowed `workflow.custom_steps` without any
field-level `workflow_output_key`, producing metadata the runtime would reject.
The SDK now fails early for authored and persisted custom metadata that defines
custom steps without matching output routes and leaf fields.

### Fixed: Workflow create/update calls were not directly covered

The generated type tests covered `WorkflowRequest` and `WorkflowDetail`, but not
the actual workflow create/update call bodies. The tests now record the raw
workflow client request body after the same HTTP encoding path used by the SDK
and assert `template`, `customSteps`, `outputRoutes`, and `leafFields` survive
both POST and PUT calls.

### Fixed: Duplicate custom output destinations were accepted

The route/leaf one-to-one check did not reject two fields that targeted the same
custom step output destination, such as `line_item_labels.label`. The SDK now
fails these duplicate destinations during authored and persisted metadata
validation.

## Residual Risk

- Local generated SDK output was produced from Fern/OpenAPI with
  `fern generate --group python-sdk --local --version 3.6.4
  --no-require-env-vars`; it is verification evidence, not a public release.
- End-to-end SDK publishing remains a later publish-last gate; downstream
  dependency movement should wait for a published-artifact e2e.
