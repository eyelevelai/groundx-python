# Tasks

- [x] Add SDK regression tests for singular-copy scope, defensive isolation, nested paths, and missing paths.
- [x] Implement targeted singular lookups without bypassing existing cache/version checks or changing whole-workflow getters.
- [x] Audit Arcadia's request-scoped field/group caches and direct role lookups. Remove duplicate copy-avoidance workarounds only where the SDK contract replaces them, while retaining routing and pinned-task safeguards.
- [ ] Test Arcadia charge, meter, statement, nested-route, and protected fixture paths against the local SDK change. Replay the captured Nitel charge boundary without changing customer evidence.
- [ ] Run SDK and Arcadia validation, adversarially review both diffs, and record measured evidence and remaining release/dependency work. The Arcadia dependency pin changes only after an approved SDK release.
