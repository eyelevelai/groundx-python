# Tasks: retire the local workflow compiler

## 1. Inventory

- [x] 1.1 Inventory every production and test caller of the compiler,
      compiler-only types, YAML definition loaders, and authoring helpers.
- [ ] 1.2 Confirm supported consumers use raw-YAML authoring or server metadata
      before removing each public surface.

## 2. Raw-YAML authoring

- [x] 2.1 Add failing sync and async tests proving create and update preserve
      YAML bytes and do not invoke local compilation.
- [x] 2.2 Make path and YAML-text helpers call the generated workflow client
      directly, with clear exclusive-source errors.
- [x] 2.3 Remove compiled definition, mapping, prepared, and workflow-setting
      overlay authoring inputs.

## 3. Compiler retirement

- [ ] 3.1 Remove persisted-workflow derivation and authored-YAML definition
      loaders while preserving exact server workflow readback.
- [ ] 3.2 Remove `prepare_extraction_yaml` and compiler-only public types after
      all supported callers are migrated.
- [ ] 3.3 Preserve server-metadata reassembly and stable-first relationship
      selection without derivation fallbacks.

## 4. Verification and release handoff

- [ ] 4.1 Pass focused tests, full tests, lint, type checks, build, and line
      endings on the supported Python version.
- [ ] 4.2 Pass the existing four-case owner replay without changing fixtures,
      expected outputs, scores, or gates.
- [ ] 4.3 Open the breaking SDK PR and provide the human release owner with the
      requested version, merged commit, evidence, and downstream pin changes.
- [ ] 4.4 After the approved release and final canonical-only certification,
      archive this change.
