## Goals / Non-Goals

**Goals:**
- `Status.__init__` (`src/groundx/extract/services/status.py`) derives `host`, `port`, `username`,
  `password`, and `ssl` for `redis.Redis(...)` by parsing `cfg.status_broker()`'s return value with
  `urllib.parse.urlparse`, so a credential-bearing broker URL produces an authenticated,
  connectable client.
- The schemeless/bare-address fallback (`status_broker()` can return an unvalidated,
  scheme-free string) keeps working exactly as it does today.
- The four existing `redis.Redis(...)` hardening kwargs (`decode_responses`, `retry`,
  `socket_connect_timeout`, `socket_timeout`) are untouched.

**Non-Goals (confirmed scope boundary, not deferred follow-ups):**
- Deriving `db` from the broker URL's path segment. `redis.Redis`'s own default (`db=0`) is kept
  regardless of what path segment a broker URL carries.
- `ssl_cert_reqs` handling for self-signed/internal certs. The Linear issue body raises it as
  something to "also consider," and the confirmed source-of-truth table marks it "a design-phase
  confirmation, not a build task" for GX-33 — this design confirms it stays out, it is not a TODO
  this change owes a follow-up ticket for.
- `ai-server`'s own `status.py` (GX-24 PR #56) is a different service on a different scope; this
  change does not touch it.

## Decisions

**D1 — Parse with `urlparse`, branch on whether it resolved a hostname.** `cfg.status_broker()`
returns an unvalidated string that is sometimes a full `redis://`/`rediss://` URL and sometimes a
bare `host:port` address with no scheme (confirmed: `urlparse("host:6379/0").hostname is None`,
verified against Python 3's stdlib `urllib.parse` behavior). So `Status.__init__` parses the value
once and branches on `parsed.hostname`:
- **`parsed.hostname` is not `None`** (a schemed URL): use the structured parse — `host =
  parsed.hostname`; `port = parsed.port or 6379`; `ssl = parsed.scheme == "rediss"`; `username =
  unquote(parsed.username) if parsed.username else None`; `password = unquote(parsed.password) if
  parsed.password is not None else None`.
- **`parsed.hostname` is `None`** (schemeless/bare-address): fall back to the existing
  string-stripping derivation, byte-for-byte as it exists today — trim a trailing `/0`, then split
  the remainder on the last `:` for a numeric port — and keep `ssl=False`, `username=None`,
  `password=None`. This is the same branch that runs today for every input, so its behavior for
  this input shape does not change.

Alternative considered: always call `urlparse` and treat a missing hostname as an error. Rejected —
`status_broker()`'s contract is "an unvalidated string," and the schemeless shape is a real,
currently-working input per the reproduction table in the Linear issue body; erroring on it would
be a regression, not a fix.

**D2 — Always pass `username=`/`password=`/`ssl=` to `redis.Redis(...)`, including `None`-valued.**
Rather than conditionally omitting `username`/`password` kwargs when the broker URL carries no
credentials, `Status.__init__` always passes them (value `None` when absent). This keeps the
connection-kwargs construction single-pathed (one dict literal, not a conditionally-assembled one)
and matches `redis.Redis`'s own defaults for those two kwargs (`None`), so it is a no-op
functionally for a credential-free broker URL. This also means the schemeless-fallback branch and
any credential-free schemed-URL input now assert `username=None, password=None, ssl=False`
explicitly in the exact-kwargs test, rather than omitting those keys.

**D3 — `db` is never derived; the constructor never receives a `db` kwarg from this parsing path.**
Confirmed non-goal (see Non-Goals). `redis.Redis`'s own default (`db=0`) is preserved.

**D4 — No ADR.** This is a single-function bug fix inside an already-hand-written, already-`stdlib`
module (`urllib.parse` and `redis`'s own kwargs, no new dependency, no new architectural pattern,
no data-model or cross-module contract change). It does not meet the repo's own ADR bar
("architecturally significant or hard-to-reverse decisions").

## `.fernignore` scope confirmation

Both paths this change touches are hand-written and confirmed present in `.fernignore`:
`src/groundx/extract` (line 9) and `tests/extract` (line 12). `openspec/` itself is also on
`.fernignore` (line 13), so this change folder survives a future Fern regeneration. No generated
path (`src/groundx/client.py`, `core/`, resource clients, `pyproject.toml`, `reference.md`, or the
regenerated `tests/` root) is touched.

## Risks / Trade-offs

- [Risk] A future broker-URL shape neither schemed nor a clean bare `host:port` (e.g. malformed
  input) could fall into the schemeless branch and produce an unexpected host/port via the legacy
  string-stripping logic. → Mitigation: this is the pre-existing behavior for any input the current
  code already accepts; this change does not widen or narrow what `Status.__init__` tolerates as
  input, it only adds correct credential/ssl derivation for the schemed case.
- [Risk] Always passing `username=None, password=None` to `redis.Redis(...)` changes the exact
  kwargs dict for every existing and new test, not just the credentialed one. → Mitigation:
  `tasks.md` explicitly updates every existing assertion in `tests/extract/services/test_status.py`
  that constructs a `Status` and checks `redis_factory.call_args.kwargs`, not just the credentialed
  scenario, so no assertion is left asserting a now-inaccurate kwargs shape.
