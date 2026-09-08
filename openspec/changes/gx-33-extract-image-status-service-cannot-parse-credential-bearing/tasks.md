## 1. Broker URL parsing regression tests (RED)

- [x] 1.1 Parametrize the exact-kwargs test in `tests/extract/services/test_status.py` (renamed
      `test_status_redis_client_derives_connection_params_from_broker_url`) to cover a
      credential-bearing `rediss://` broker URL, a credential-bearing plaintext `redis://` broker
      URL, a broker URL with a non-`/0` db path segment, and the schemeless bare-address fallback —
      each asserting the full `redis.Redis(...)` kwargs dict (`host`, `port`, `ssl`, `username`,
      `password`, plus the four unchanged hardening kwargs). Written in this authoring pass; on
      unchanged code this fails for all four parametrized cases (credentialed cases: wrong
      `host`/missing `username`/`password`; db-path case: wrong `host`/`port`; schemeless case:
      missing `username`/`password` keys the exact-dict comparison now requires).
      check: poetry run pytest "tests/extract/services/test_status.py::test_status_redis_client_derives_connection_params_from_broker_url" -q

## 2. Implement urlparse-based broker URL parsing (GREEN)

- [x] 2.1 In `Status.__init__` (`src/groundx/extract/services/status.py`), replace the
      string-stripping derivation with the `urlparse`-based derivation from `design.md` (D1–D3):
      parse `cfg.status_broker()` once with `urllib.parse.urlparse`; when `parsed.hostname` is not
      `None`, derive `host`/`port`/`ssl`/`username`/`password` from the parsed result
      (`username`/`password` unquoted via `urllib.parse.unquote`, `port` falling back to `6379`,
      `ssl` true only for scheme `rediss`); when `parsed.hostname` is `None` (schemeless
      bare-address input), fall back to the existing string-stripping logic unchanged, with
      `ssl=False`, `username=None`, `password=None`. Never derive `db` from any path segment. Pass
      `username=`/`password=`/`ssl=` to `redis.Redis(...)` unconditionally (value `None` when
      absent), alongside the four existing hardening kwargs, unchanged.
      check: poetry run pytest "tests/extract/services/test_status.py::test_status_redis_client_derives_connection_params_from_broker_url" -q
- [x] 2.2 Run the full `tests/extract/services/test_status.py` file to confirm the other `Status`
      tests (`prompt_init_lock`, `get_service_state` scan/deadline tests) are unaffected by the
      `__init__` change.
      check: poetry run pytest tests/extract/services/test_status.py -q

## 3. Static verification

- [x] 3.1 Type-check with the CI-declared mypy gate (`poetry run mypy .`, no `--extras extract` —
      the extract package falls back to `Any` under that gate, so this is a cheap sanity pass, not
      the primary correctness signal for this change).
      check: n/a — CI static type gate (mypy), not a behavioral acceptance check; passes on unchanged code by design

Note: no consumer needs a dependency-pin bump for this fix (see `proposal.md` Impact) — the public
`Status(cfg, logger)` constructor signature is unchanged, and `internal-arcadia-agents` (the only
package-import consumer of `groundx[extract]`) does not construct `Status` directly. A package
release/version bump, if any, is a separate release decision outside this change's scope, not a
task here.
