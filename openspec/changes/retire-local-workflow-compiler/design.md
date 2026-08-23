# Design: retire the local workflow compiler

## Boundary

Cashbot is the only authoring compiler. The SDK may read a YAML file or accept
YAML text, but it sends those bytes to `workflows.create` or
`workflows.update` without parsing, normalizing, validating, hashing, or
building execution metadata.

Server workflow readback remains supported. Reassembly and relationship
selection consume the canonical metadata returned by the server and do not
derive missing metadata from YAML, names, prompts, or output shape.

## Compatibility

This is an intentional breaking release. Remove definition, mapping, and
prepared-object authoring inputs instead of retaining a hidden compiled-JSON
fallback. Remove the public compiler and compiler-only types only after source
scans show that supported consumers have moved to raw YAML or server metadata.

## Verification

Tests prove byte-preserving sync and async create/update calls, source
selection errors before API mutation, exact server-metadata readback, and
unchanged reassembly and stable-first relationship selection. The final
four-case proof is owned by PR 125 and uses the single governed Harness path.
