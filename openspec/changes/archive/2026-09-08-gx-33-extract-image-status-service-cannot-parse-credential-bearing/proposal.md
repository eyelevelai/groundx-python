## Why

`groundx.extract.services.Status.__init__` (`src/groundx/extract/services/status.py`) builds its
Redis client by string-stripping the broker URL returned by `cfg.status_broker()` — it trims a
trailing `/0`, strips a `redis://`/`rediss://` prefix, and splits the remainder on the last `:` for
the port. It never handles `user:pass@` userinfo and never extracts a username or password. A
credential-bearing broker URL (`rediss://user:pass@host:6379/0`) therefore yields an invalid host
(`user:pass@host`, a DNS failure) and an unauthenticated client, so the extract-image status/
rate-limit service (and anything depending on it via `wait-for-extract`) cannot connect and stays
unready. GX-24 (authenticated Redis) is what makes the on-prem chart render credential-bearing
broker URLs in the first place — the extract-image `Status` client was outside GX-24's PR #56 scope
and needs its own fix.

## What Changes

- Replace the string-stripping derivation in `Status.__init__` with `urllib.parse` parsing
  (`urlparse`) of the value `cfg.status_broker()` returns: derive `host` from `.hostname`, `port`
  from `.port` (falling back to `6379` when unset), `ssl` from the URL scheme being `rediss`,
  `username`/`password` from the parsed userinfo (percent-unquoted via `urllib.parse.unquote`), and
  `db` from the path segment (mirroring `redis-py`'s own `from_url` semantics; a user-directed
  scope amendment during review — see `design.md` D3's amendment note for provenance).
- The whole parse is guarded end to end: `urlparse(broker_url)` itself, `parsed.port`, and the `db`
  path-segment-to-integer conversion each catch their own failure mode inside `try`/`except`, so no
  broker string — malformed, schemeless, non-numeric, or an over-limit digit string — can crash
  `Status.__init__`; each guarded point instead falls back to a safe default (see `design.md` D5).
- Pass the derived `username`/`password` into the `redis.Redis(...)` constructor call, so a
  credential-bearing broker URL produces an authenticated, connectable client — today the
  constructor call never passes credentials at all.
- Preserve the existing schemeless/bare-address fallback: `status_broker()` returns an unvalidated
  string, and `urlparse` on a value with no `redis(s)://` scheme (e.g. `host:6379/0`) does not
  populate `.hostname`/`.port` from a bare `host:port` the way a schemed URL does. The current
  behavior for that shape must keep working; this is captured as a regression test, not just a
  design note.
- Preserve the existing `redis.Redis` hardening kwargs unchanged: `decode_responses=True`,
  `retry=Retry(NoBackoff(), 0)`, `socket_connect_timeout=5.0`, `socket_timeout=5.0`. The
  exact-kwargs assertion at `tests/extract/services/test_status.py:50` gets the new
  `username`/`password`/`ssl` expectations **added** to it; none of the existing asserted kwargs are
  relaxed or removed.
- Out of scope for this change: `ssl_cert_reqs` handling for self-signed/internal certs (a
  design-phase confirmation, not a build task here). `db` derivation was originally out of scope
  and is not — it is now derived from the broker URL's path segment (see the amended bullet above
  and `design.md` D3's amendment note).
- Not a breaking change: the public `Status(cfg, logger)` constructor signature is unchanged — only
  the internal connection-parameter derivation and the resulting `redis.Redis(...)` kwargs change.

## Capabilities

### New Capabilities
- `extract-status-broker-parsing`: how `Status.__init__` derives Redis connection parameters (host,
  port, username, password, ssl, db) from the broker URL `status_broker()` returns, including the
  schemeless/bare-address fallback, the guard against every malformed-input raise point (never
  crashes on any broker string), and the unchanged hardening-kwargs invariant. No existing
  `openspec/specs/` capability covers this constructor logic — the current specs are all
  extraction-YAML/workflow-authoring capabilities.

### Modified Capabilities
none

## Impact

- Affected code: `src/groundx/extract/services/status.py` (`Status.__init__`) only. No other
  method on `Status` changes.
- Affected tests: `tests/extract/services/test_status.py` — extend the existing exact-kwargs
  assertion (line 50) with `username`/`password`/`ssl`, and add a credential-bearing-URL test plus
  a schemeless-fallback regression test.
- Both paths are on `.fernignore` (`src/groundx/extract` and `tests/extract` are hand-written,
  untouched by Fern regeneration) — confirmed against `.fernignore`.
- `Status` is re-exported from `groundx.extract.__init__` (`__all__`, lazy import) as part of the
  `groundx[extract]` optional-extra public surface, but its constructor signature does not change,
  so this is a behavior fix, not an API-shape change.
- Downstream consumers: `groundx-on-prem`'s `eyelevel/extract` image is the runtime consumer that
  actually exercises this path (reference-only edge, soft bind via constructor signature — GX-24's
  chart is what renders the credential-bearing broker URL that trips the current defect).
  `internal-arcadia-agents` imports `groundx[extract]>=3.4.3` but does not construct `Status`
  directly, so it is unaffected. No consumer needs a dependency-pin bump for this fix; a package
  release/version bump is a separate release decision outside this change's scope.
- `ai-server`'s own `status.py` (GX-24 PR #56, branch `gx-24-authenticated-redis-all-consumers`)
  already applies the equivalent credentialed-URL parse for its own service and is **not** part of
  this change — it is reference context only, per the confirmed GX-33 scope (groundx-python only).
