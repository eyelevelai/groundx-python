## ADDED Requirements

### Requirement: The SDK provides one schema-driven coercion contract

The hand-written extraction SDK SHALL expose one helper that accepts a JSON
value and an optional declared type of `str`, `int`, `float`, `list`, `dict`, or
a list of those types, and returns the selected value, match status, conversion
status, and an optional content-free warning.

#### Scenario: Value already matches the declared type

- **WHEN** the helper receives a value whose exact Python type matches an allowed
  declared type
- **THEN** it returns the original value with matched status and without
  conversion.

#### Scenario: No declared type exists

- **WHEN** the helper receives no declared type
- **THEN** it returns the original value with matched status and without
  conversion.

### Requirement: Coercion cannot fail document processing

The helper SHALL NOT raise for any JSON-compatible input. When no supported
conversion exists, it SHALL return a type-safe null, mark the result unmatched,
and return a warning containing source and target type names without the raw
value.

#### Scenario: Container cannot become a number

- **WHEN** a list or dict is supplied for an `int` or `float` target
- **THEN** the helper returns null, marks it unmatched, and returns a warning
- **AND** sibling fields remain eligible for processing.

#### Scenario: Invalid JSON string targets a container

- **WHEN** a non-JSON string is supplied for a `list` or `dict` target
- **THEN** the helper returns null, marks it unmatched, and returns a warning
  instead of raising.

#### Scenario: Unknown target type is declared

- **WHEN** the helper receives an unsupported declared type name
- **THEN** it returns null and an unmatched warning instead of guessing a
  conversion.

### Requirement: Scalar conversion is deterministic

The helper SHALL convert scalar JSON values according to one shared matrix.
Exact type checks SHALL prevent Python booleans from matching integer or float
targets before conversion.

#### Scenario: Boolean targets a string

- **WHEN** `true` or `false` is supplied for a `str` target
- **THEN** the helper returns lowercase `"true"` or `"false"`.

#### Scenario: Number targets a string

- **WHEN** an integer or float is supplied for a `str` target
- **THEN** the helper returns its JSON scalar text.

#### Scenario: String zero targets a string

- **WHEN** `"0"` is supplied for a `str` target
- **THEN** the helper preserves `"0"` as an exact string.

#### Scenario: Boolean targets a number

- **WHEN** a boolean is supplied for an `int` or `float` target
- **THEN** the helper returns null, marks it unmatched, and returns a warning
- **AND** it does not turn the boolean into zero or one.

#### Scenario: Numeric text targets an integer

- **WHEN** numeric text, including comma-formatted or decimal text, is supplied
  for an `int` target
- **THEN** the helper returns an integer and retains the current truncation
  toward zero for decimal values
- **AND** integer text is not routed through binary floating point or changed by
  floating-point precision limits.

#### Scenario: Numeric text targets a float

- **WHEN** numeric text, including comma-formatted text, is supplied for a
  `float` target
- **THEN** the helper returns the parsed float.

#### Scenario: Empty text targets a number

- **WHEN** an empty string is supplied for an `int` or `float` target
- **THEN** the helper returns null, marks it unmatched, and returns a warning
  instead of inventing numeric zero.

#### Scenario: Non-numeric text targets a number

- **WHEN** text cannot be parsed for an `int` or `float` target
- **THEN** the helper returns null, marks it unmatched, and returns a warning.

### Requirement: Container conversion uses JSON semantics

The helper SHALL use JSON encoding and decoding for conversions between string
and container targets.

#### Scenario: List or dict targets a string

- **WHEN** a list or dict is supplied for a `str` target
- **THEN** the helper returns compact valid JSON text, not Python representation
  text.

#### Scenario: JSON array text targets a list

- **WHEN** a string containing a JSON array is supplied for a `list` target
- **THEN** the helper returns the parsed list.

#### Scenario: JSON object text targets a dict

- **WHEN** a string containing a JSON object is supplied for a `dict` target
- **THEN** the helper returns the parsed dict.

#### Scenario: Parsed JSON has the wrong container shape

- **WHEN** JSON array text targets `dict` or JSON object text targets `list`
- **THEN** the helper returns null, marks it unmatched, and returns a warning.

### Requirement: Union coercion has stable precedence

The helper SHALL preserve an exact allowed input type before attempting
conversions. When conversion is required, it SHALL prefer numeric interpretation
for an `int` and `float` union and otherwise use declared order.

#### Scenario: Decimal text targets an integer and float union

- **WHEN** decimal text targets `['int', 'float']`
- **THEN** the helper returns a float without truncation.

#### Scenario: Integer text targets an integer and float union

- **WHEN** integer text targets `['int', 'float']`
- **THEN** the helper returns an integer.

#### Scenario: Exact union member is supplied

- **WHEN** a value already has an exact type listed in a union
- **THEN** the helper preserves that value regardless of declared order.

### Requirement: SDK field handling uses the shared contract

`ExtractedField`, `Prompt.valid_value`, and SDK confidence validation SHALL use
the shared coercion and exact-type rules instead of separate primitive
conversion logic. Existing date normalization SHALL remain separate.

#### Scenario: Boolean is assigned to a string field

- **WHEN** `ExtractedField` receives `True` for a prompt declared as `str`
- **THEN** its value reads back as `"true"`, not `"1.0"`, `"True"`, or an
  exception.

#### Scenario: Unsupported value reaches field handling

- **WHEN** a field value cannot match or convert to its declared type
- **THEN** field handling produces a nonfatal null and a field-scoped warning
- **AND** it does not put the incompatible value in typed extracted JSON
- **AND** it does not fail sibling fields or the document.

#### Scenario: Null remains null for every declared type

- **WHEN** a field is missing or conversion to `str`, `int`, `float`, `list`, or
  `dict` is impossible
- **THEN** the field remains present with a null value through field readback and
  typed output serialization
- **AND** the SDK does not replace null with an empty string, list, or dict.

#### Scenario: Successful conversion is quiet

- **WHEN** field handling converts a compatible mismatched value
- **THEN** the SDK emits no ordinary log record.

### Requirement: Existing callers have a narrow migration path

`coerce_numeric_string` SHALL remain available as a compatibility wrapper over
the shared helper, preserving its call signature and primitive return shape. It
SHALL NOT contain a second conversion policy.

#### Scenario: Existing caller uses the old helper

- **WHEN** a caller invokes `coerce_numeric_string(value, expected_types)`
- **THEN** it receives the shared helper's selected value without changing its
  call signature.

### Requirement: Protected extraction paths retain behavior

The change SHALL include regression evidence for the current reproduction,
Arcadia legacy, Arcadia v1, generic v1, and ADP v1 extraction paths.

#### Scenario: Protected path receives coercible mismatched output

- **WHEN** any protected path receives a JSON value that can be converted to the
  declared field type
- **THEN** it uses the shared result and completes without losing sibling
  fields.

#### Scenario: Protected path receives unmatched output

- **WHEN** any protected path receives a JSON value that cannot be converted to
  the declared field type
- **AND** no valid prior value exists for that field
- **THEN** it emits a type-safe null for that field, records one field-aware
  warning through the consumer boundary, and continues the document.

#### Scenario: Unmatched update targets a valid field

- **WHEN** reconcile, QA, or another model-driven update cannot be converted to
  the declared type
- **AND** the target field already contains a valid typed value
- **THEN** the consumer preserves the prior value
- **AND** it does not overwrite that value with null or the incompatible raw
  value
- **AND** it records the unmatched metadata through the consumer boundary and
  continues the document.
