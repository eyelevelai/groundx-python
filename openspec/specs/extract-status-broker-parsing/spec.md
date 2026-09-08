# extract-status-broker-parsing Specification

## Purpose
TBD - created by archiving change gx-33-extract-image-status-service-cannot-parse-credential-bearing. Update Purpose after archive.
## Requirements
### Requirement: Status derives Redis connection parameters by parsing the broker URL
`groundx.extract.services.Status.__init__` SHALL derive the `redis.Redis(...)` connection
parameters (`host`, `port`, `username`, `password`, `ssl`, `db`) by parsing the value
`cfg.status_broker()` returns with `urllib.parse.urlparse`, rather than by string-stripping a
scheme prefix and a trailing `/0`. `username` and `password` SHALL be percent-unquoted via
`urllib.parse.unquote` before being passed to `redis.Redis(...)`. `db` SHALL be derived from the
parsed URL's path segment, mirroring `redis-py`'s own `from_url` semantics: an integer path
segment (e.g. `/2`) sets `db` to that integer, converted inside a guard that catches exactly
`int()`'s own failure mode (`ValueError`) rather than pre-validating the segment with a predicate.
Any path segment `int()` rejects — empty, absent, non-integer, a Unicode digit character `int()`
does not accept (e.g. a superscript digit), or a digit string over Python's integer-string
conversion limit (4300+ digits) — SHALL default `db` to `0` (the guard that keeps a schemeless,
path-less, non-integer, or over-limit path segment from crashing this derivation). `port` SHALL be
derived from `parsed.port`: an explicit port,
**including `0`**, SHALL be honored as given (distinguishing "unset" from the falsy value `0`), an
unset port defaults to `6379`, and an unparseable port segment — non-numeric (e.g. `not-a-port`)
or out-of-range (e.g. `99999999`, where `ParseResult.port` itself raises `ValueError`) — SHALL also
default to `6379` rather than propagating the exception out of `Status.__init__`.

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

#### Scenario: Broker URL path segment derives a non-default db
- **WHEN** `cfg.status_broker()` returns a broker URL with a non-`/0` database path segment, e.g.
  `"rediss://user:pass@host:6379/2"`
- **THEN** `Status.__init__` passes `db=2` to `redis.Redis(...)`, derived from the `/2` path
  segment
- **AND** the constructed client is NOT given the `redis.Redis` default `db=0`

#### Scenario: Empty or absent path segment guards db to the default
- **WHEN** `cfg.status_broker()` returns a schemed broker URL with no path segment, e.g.
  `"rediss://host:6379"`
- **THEN** `Status.__init__` passes `db=0` to `redis.Redis(...)` — the empty-path guard defaults
  `db` rather than raising or passing a non-integer value
- **AND** `Status.__init__` does NOT raise when the path segment is empty, absent, or
  non-integer

#### Scenario: Unicode-digit path segment guards db to the default instead of crashing
- **WHEN** `cfg.status_broker()` returns a schemed broker URL whose path segment is a Unicode
  digit character `int()` rejects, e.g. `"rediss://host:6379/²"`
- **THEN** `Status.__init__` passes `db=0` to `redis.Redis(...)` — the `try`/`except ValueError`
  guard around the `int()` conversion defaults `db` for this input rather than propagating the
  exception `int()` raises for it
- **AND** `Status.__init__` does NOT raise `ValueError`

#### Scenario: An over-integer-string-limit path segment guards db to the default instead of crashing
- **WHEN** `cfg.status_broker()` returns a schemed broker URL whose path segment is an all-digit
  string over Python's integer-string conversion limit (4300+ digits), e.g.
  `"rediss://host:6379/" + "1" * 4301`
- **THEN** `Status.__init__` passes `db=0` to `redis.Redis(...)` — the `try`/`except ValueError`
  guard around the `int()` conversion defaults `db` for this input rather than propagating the
  `ValueError` `int()` raises for it
- **AND** `Status.__init__` does NOT raise `ValueError`, even though this path segment would pass
  a `str.isdecimal()` pre-check — the guard is on the conversion itself, not on a predicate that
  approximates what `int()` accepts

#### Scenario: Unparseable or out-of-range port segment guards port to the default
- **WHEN** `cfg.status_broker()` returns a schemed broker URL whose port segment
  `ParseResult.port` cannot parse — non-numeric (e.g. `"redis://host:not-a-port/0"`) or
  out-of-range (e.g. `"rediss://host:99999999/0"`)
- **THEN** `Status.__init__` passes `port=6379` to `redis.Redis(...)`, the same default used for
  an unset port
- **AND** `Status.__init__` does NOT raise `ValueError` and does NOT propagate the exception
  `parsed.port` raises for that input

#### Scenario: An explicit zero port is honored, not defaulted
- **WHEN** `cfg.status_broker()` returns a schemed broker URL with an explicit `:0` port, e.g.
  `"rediss://host:0/0"`
- **THEN** `Status.__init__` passes `port=0` to `redis.Redis(...)` — the falsy value `0` is
  distinguished from an unset port and is NOT overridden to `6379`
- **AND** `Status.__init__` does NOT treat `parsed.port == 0` as equivalent to `parsed.port is
  None`

### Requirement: Status falls back to legacy host/port derivation for schemeless or unparseable broker strings
`Status.__init__` SHALL fall back to the existing string-stripping host/port derivation whenever
`cfg.status_broker()` returns a schemeless broker string — one with no `redis://`/`rediss://`
scheme, e.g. a bare `host:port` address, where `urlparse` does not populate `.hostname`/`.port` the
way a schemed URL does. `Status.__init__` SHALL detect that case by checking whether the parsed
`.hostname` is `None`, and in that case SHALL fall back to the existing string-stripping
derivation — trim a trailing `/0`, then split the remainder on the last `:` for a numeric port —
producing the same `host`, `port`, and `ssl=False` the prior implementation produced for that input
shape. This branch does NOT parse a `db` from the schemeless string's path; `db` defaults to `0`,
as it always has for this input shape. This preserves current behavior for schemeless broker
strings; it is a regression to be protected by a test, not merely a design note.

`Status.__init__` SHALL also take this same fallback derivation whenever `urlparse` itself raises
`ValueError` on `cfg.status_broker()`'s return value — e.g. a malformed bracketed authority such as
`"rediss://[bad:6379/0"` ("Invalid IPv6 URL"). `Status.__init__` SHALL catch that `ValueError` and
treat the parse failure identically to a missing `.hostname`, taking the legacy string-strip
derivation against the raw broker string. This is the last of the three points inside this
derivation that could raise on untrusted input (`urlparse(broker_url)` itself, `parsed.port`, and
`int()` on the `db` path segment); with this guard in place, no `broker_url` value can propagate an
exception out of `Status.__init__`.

#### Scenario: Schemeless bare-address broker string keeps working exactly as before
- **WHEN** `cfg.status_broker()` returns `"host:6379/0"` (no `redis://`/`rediss://` scheme)
- **THEN** `Status.__init__` constructs `redis.Redis(...)` with `host="host"`, `port=6379`,
  `ssl=False`, and `db=0`, matching the pre-fix behavior for this input shape
- **AND** `Status.__init__` does NOT raise and does NOT route this input through the credentialed
  URL-parse branch as if it were an unparseable/failing broker value — the schemeless case is
  intentionally skipped past that branch, not rejected by it

#### Scenario: A broker string urlparse cannot parse falls back to the legacy derivation
- **WHEN** `cfg.status_broker()` returns a broker string `urlparse` raises `ValueError` on, e.g.
  `"rediss://[bad:6379/0"` (an unbalanced bracketed authority)
- **THEN** `Status.__init__` does NOT raise `ValueError` and does NOT propagate the exception
  `urlparse` raises for that input
- **AND** `Status.__init__` derives `host`, `port`, and `ssl` via the same legacy string-strip
  derivation used for a schemeless broker string, against the raw (unparsed) broker string, with
  `username=None`, `password=None`, and `db=0`

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
  broker-URL-parsing fix — the exact-kwargs assertion gains new `username`/`password`/`ssl`/`db`
  expectations, it does not lose any of the four hardening kwargs it already asserts

