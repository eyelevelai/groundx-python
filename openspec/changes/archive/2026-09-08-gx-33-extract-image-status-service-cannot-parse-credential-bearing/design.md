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
- ~~Deriving `db` from the broker URL's path segment. `redis.Redis`'s own default (`db=0`) is kept
  regardless of what path segment a broker URL carries.~~ **Reversed 2026-09-08 — see D3's
  amendment note below.**
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

> **Amendment (2026-09-08): D3 reversed.** A user-directed scope amendment on 2026-09-08 reversed
> this non-goal. `Status.__init__` now derives `db` from the schemed URL's path segment, mirroring
> `redis-py`'s own `from_url` semantics: `db_path = parsed.path.lstrip("/")`; the conversion itself
> is guarded — `try: db = int(db_path)` / `except ValueError: db = 0` (F4 below first hardened the
> guard from a predicate `isdigit()` to `isdecimal()`; F6 then found `isdecimal()` still leaks a
> case `int()` rejects — a path segment over Python's 4300-digit integer-string conversion limit —
> so the guard now wraps the conversion itself in `try`/`except ValueError` instead of pre-checking
> it with any predicate, which catches every case a predicate could ever miss). The guard exists
> specifically so an empty, path-less, non-decimal, or over-limit path segment
> (`rediss://host:6379`, no `/N` segment) cannot crash this derivation — it defaults to `0` instead.
> The schemeless-fallback branch (D1,
> `parsed.hostname is None`) is unaffected: it still does not parse a `db` from its input, and
> continues to pass `db=0` (now passed explicitly rather than implicitly relying on `redis.Redis`'s
> own default, matching D2's "always pass explicitly" pattern). See
> `specs/extract-status-broker-parsing/spec.md`'s own requirement text for the corresponding
> spec-level reversal, and `openspec/specs/extract-status-broker-parsing/spec.md` for the current,
> authoritative requirement text.

**D4 — No ADR.** This is a single-function bug fix inside an already-hand-written, already-`stdlib`
module (`urllib.parse` and `redis`'s own kwargs, no new dependency, no new architectural pattern,
no data-model or cross-module contract change). It does not meet the repo's own ADR bar
("architecturally significant or hard-to-reverse decisions").

**D5 — every conversion point is guarded by `try`/`except`, not a pre-check predicate;
`Status.__init__` cannot crash on any broker string (F5, F6).** Invariant, stated once and applied
identically at all three points: **a value derived from untrusted input is never validated by a
predicate that approximates what the converter accepts — it is derived inside a `try`/`except` that
catches exactly the converter's own failure mode, so no input shape the predicate didn't anticipate
can still reach the converter unguarded.** A cross-family review finding (F5) showed `parsed =
urlparse(broker_url)` — the derivation's own entry point — raises `ValueError` for a malformed
bracketed authority (e.g. `"rediss://[bad:6379/0"`, "Invalid IPv6 URL"), crashing the constructor
before D1's `parsed.hostname is not None` branch ever runs. `Status.__init__` now calls `urlparse`
inside a `try`/`except ValueError`, setting `parsed = None` on failure; D1's branch condition
becomes `parsed is not None and parsed.hostname is not None`, so a parse failure takes the same
schemeless/legacy string-strip path as a `None` hostname. A second review finding (F6) showed the
`db` guard violated the same invariant in its own right: a `str.isdecimal()` pre-check (D3's
amendment, itself a hardening of an earlier `str.isdigit()` pre-check per F4) still passes a
path segment over Python's 4300-digit integer-string conversion limit through to `int()`, which
then raises `ValueError` — a predicate approximating `int()`'s acceptance criteria, not enforcing
it. The fix replaces the predicate with `try: db = int(db_path)` / `except ValueError: db = 0`,
guarding the conversion itself rather than pre-validating its input. All three points inside this
derivation that can raise from untrusted input — `urlparse(broker_url)`, `parsed.port`, and
`int(db_path)` — are now guarded this same way: a `try`/`except` around the conversion, never a
predicate in front of it; none propagates out of `Status.__init__`.

## `.fernignore` scope confirmation

Both paths this change touches are hand-written and confirmed present in `.fernignore`:
`src/groundx/extract` (line 9) and `tests/extract` (line 12). `openspec/` itself is also on
`.fernignore` (line 13), so this change folder survives a future Fern regeneration. No generated
path (`src/groundx/client.py`, `core/`, resource clients, `pyproject.toml`, `reference.md`, or the
regenerated `tests/` root) is touched.

## Risks / Trade-offs

- [Risk, resolved by D5] A broker-URL shape neither schemed nor a clean bare `host:port` (e.g. a
  malformed bracketed authority `urlparse` cannot parse at all) could crash `Status.__init__`
  instead of degrading gracefully. → Resolution: D5 routes any `urlparse` failure into the same
  legacy string-strip branch used for a schemeless string, so this input class now produces a
  best-effort `host`/`port` via the legacy string-stripping logic instead of raising — the same
  behavior this change already guarantees for the schemeless case, extended to cover a
  parse-failing case D1 alone did not.
- [Risk] Always passing `username=None, password=None` to `redis.Redis(...)` changes the exact
  kwargs dict for every existing and new test, not just the credentialed one. → Mitigation:
  `tasks.md` explicitly updates every existing assertion in `tests/extract/services/test_status.py`
  that constructs a `Status` and checks `redis_factory.call_args.kwargs`, not just the credentialed
  scenario, so no assertion is left asserting a now-inaccurate kwargs shape.
