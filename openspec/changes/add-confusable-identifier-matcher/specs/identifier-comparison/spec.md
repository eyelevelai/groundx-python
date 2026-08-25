## ADDED Requirements

### Requirement: One function owns string comparison keys

GroundX Python SHALL export `match_key(value)` from `groundx.extract`.
For string input it SHALL return a transient comparison string. For nonstring
input it SHALL return the input unchanged.

#### Scenario: String extraction noise is ignored

- **WHEN** two nonempty strings differ only by capitalization, whitespace, or
  substitutions within `{0, o}`, `{1, i, l}`, and `{8, b}`
- **THEN** `match_key` returns the same value for both strings
- **AND** it runs in linear time relative to input length.

#### Scenario: Unapproved differences remain significant

- **WHEN** two strings differ by punctuation, length after whitespace removal,
  or an unmapped character
- **THEN** `match_key` returns different values.

#### Scenario: Nonstrings are not transformed

- **WHEN** `match_key` receives a missing, numeric, boolean, list, mapping, or
  other nonstring value
- **THEN** it returns that value unchanged
- **AND** the caller retains its existing type, absence, and hashability rules.

### Requirement: One equality wrapper delegates to the key function

GroundX Python SHALL export `values_match(left, right)` from `groundx.extract`.
It SHALL return `match_key(left) == match_key(right)` and SHALL contain no second
case, whitespace, confusable, exact, profile, field, or workflow rule.

#### Scenario: Direct comparison uses the same transformation

- **WHEN** a production identity or relationship path directly compares two
  string values
- **THEN** it uses `values_match`
- **AND** generated string key components use `match_key`.

#### Scenario: Nonmatching equality is unchanged

- **WHEN** code compares scalar candidate evidence, route or schema identity,
  sorting values, rendered values, or transport values
- **THEN** it retains its existing behavior
- **AND** it does not use these functions merely because it compares values.

### Requirement: Exact metadata cannot bypass universal matching

Neither function SHALL accept an exact mode. Existing
`identity_match.exact_attrs` metadata MAY remain accepted for compatibility but
SHALL NOT change identity or relationship string equality.

#### Scenario: Legacy exact metadata is present

- **WHEN** a persisted workflow contains `identity_match.exact_attrs`
- **THEN** matching still ignores capitalization, whitespace, and approved OCR
  confusions
- **AND** the metadata does not select raw string equality.

### Requirement: Comparison never rewrites retained values

Comparison values SHALL remain transient and SHALL NOT replace source or output
values.

#### Scenario: Records match through the comparison key

- **WHEN** records match after case, whitespace, or OCR-confusable handling
- **THEN** retained fields, conflicts, provenance, X-Ray, diagnostics, and final
  output remain raw
- **AND** no comparison key is serialized or displayed.

### Requirement: Existing evidence changes require human approval

An existing test, fixture, expected output, or score SHALL NOT change unless a
human reviews and approves the specific behavioral difference.

#### Scenario: Existing assertion conflicts with universal matching

- **WHEN** implementation makes an existing evidence artifact fail
- **THEN** work stops before modifying it
- **AND** the review records the input, old result, new result, and downstream
  effect.
