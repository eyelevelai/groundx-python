## ADDED Requirements

### Requirement: Status derives Redis connection parameters by parsing the broker URL
`groundx.extract.services.Status.__init__` SHALL derive the `redis.Redis(...)` connection
parameters (`host`, `port`, `username`, `password`, `ssl`) by parsing the value
`cfg.status_broker()` returns with `urllib.parse.urlparse`, rather than by string-stripping a
scheme prefix and a trailing `/0`. `username` and `password` SHALL be percent-unquoted via
`urllib.parse.unquote` before being passed to `redis.Redis(...)`. `db` SHALL NOT be derived from
the broker URL; the `redis.Redis` default (`db=0`) is preserved regardless of any path segment
present in the broker URL.

#### Scenario: Credential-bearing rediss broker URL yields an authenticated, connectable client
- **WHEN** `cfg.status_broker()` returns `"rediss://svc_redis:S3cr3t%20p%40ss%2Fw%23rd@host:6379/0"`
- **THEN** `Status.__init__` constructs `redis.Redis(...)` with `host="host"`, `port=6379`,
  `ssl=True`, `username="svc_redis"`, and `password="S3cr3t p@ss/w#rd"` (the userinfo,
  percent-unquoted)
- **AND** the constructed client is NOT given `host="svc_redis:S3cr3t%20p%40ss%2Fw%23rd@host"` (the
  unparsed userinfo-plus-host string the prior string-stripping derivation produced) and is NOT
  constructed without `username`/`password` set

#### Scenario: Credential-bearing plaintext redis broker URL yields ssl=False with credentials parsed
- **WHEN** `cfg.status_broker()` returns `"redis://svc_redis:S3cr3t%20p%40ss%2Fw%23rd@host:6379/0"`
- **THEN** `Status.__init__` constructs `redis.Redis(...)` with `host="host"`, `port=6379`,
  `ssl=False`, `username="svc_redis"`, and `password="S3cr3t p@ss/w#rd"`
- **AND** the client is NOT constructed with `ssl=True` (the scheme is `redis`, not `rediss`) and
  is NOT constructed without `username`/`password` set

#### Scenario: Broker URL path segment never sets a non-default db
- **WHEN** `cfg.status_broker()` returns a broker URL with a non-`/0` database path segment, e.g.
  `"rediss://user:pass@host:6379/2"`
- **THEN** `Status.__init__` does NOT pass a `db` kwarg derived from `/2` to `redis.Redis(...)`
- **AND** the constructed client keeps the `redis.Redis` default `db=0`

### Requirement: Status falls back to legacy host/port derivation for schemeless broker strings
`Status.__init__` SHALL fall back to the existing string-stripping host/port derivation whenever
`cfg.status_broker()` returns a schemeless broker string — one with no `redis://`/`rediss://`
scheme, e.g. a bare `host:port` address, where `urlparse` does not populate `.hostname`/`.port` the
way a schemed URL does. `Status.__init__` SHALL detect that case by checking whether the parsed
`.hostname` is `None`, and in that case SHALL fall back to the existing string-stripping
derivation — trim a trailing `/0`, then split the remainder on the last `:` for a numeric port —
producing the same `host`, `port`, and `ssl=False` the prior implementation produced for that input
shape. This preserves current behavior for schemeless broker strings; it is a regression to be
protected by a test, not merely a design note.

#### Scenario: Schemeless bare-address broker string keeps working exactly as before
- **WHEN** `cfg.status_broker()` returns `"host:6379/0"` (no `redis://`/`rediss://` scheme)
- **THEN** `Status.__init__` constructs `redis.Redis(...)` with `host="host"`, `port=6379`, and
  `ssl=False`, matching the pre-fix behavior for this input shape
- **AND** `Status.__init__` does NOT raise and does NOT route this input through the credentialed
  URL-parse branch as if it were an unparseable/failing broker value — the schemeless case is
  intentionally skipped past that branch, not rejected by it

### Requirement: Status preserves the existing Redis client hardening kwargs unchanged
Regardless of the broker URL's shape, `Status.__init__` SHALL continue to pass
`decode_responses=True`, `retry=redis.retry.Retry(redis.backoff.NoBackoff(), 0)`,
`socket_connect_timeout=5.0`, and `socket_timeout=5.0` to `redis.Redis(...)`, unchanged by the
broker-URL-parsing fix.

#### Scenario: Hardening kwargs are present alongside the newly derived connection parameters
- **WHEN** `Status.__init__` is constructed with any broker URL (credentialed, schemeless, or
  credential-free schemed)
- **THEN** the `redis.Redis(...)` call includes `decode_responses=True`,
  `retry=redis.retry.Retry(redis.backoff.NoBackoff(), 0)`, `socket_connect_timeout=5.0`, and
  `socket_timeout=5.0`
- **AND** none of these four kwargs is omitted, renamed, or given a different value by the
  broker-URL-parsing fix — the exact-kwargs assertion gains new `username`/`password`/`ssl`
  expectations, it does not lose any of the four hardening kwargs it already asserts

## Amendments

### Amendment (2026-09-08): `db` derivation reversed

The "Status derives Redis connection parameters by parsing the broker URL" requirement above, as
originally archived, stated `db` SHALL NOT be derived from the broker URL. A user-directed scope
amendment on 2026-09-08 reversed that non-goal — see `design.md`'s D3 amendment note for the
rationale. The live, current requirement now reads:

`db` SHALL be derived from the parsed URL's path segment, mirroring `redis-py`'s own `from_url`
semantics: a numeric path segment (e.g. `/2`) sets `db` to that integer; an empty, absent, or
non-numeric path segment defaults `db` to `0` (the guard that keeps a schemeless or path-less URL
from crashing this derivation). The schemeless-fallback branch does not parse a `db` from its
input and continues to pass `db=0`.

The current, authoritative text of this requirement lives in
`openspec/specs/extract-status-broker-parsing/spec.md` — this archived delta is left as
originally shipped above, per the record-hygiene rule against silently rewriting a shipped
record.
