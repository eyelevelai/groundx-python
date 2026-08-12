## ADDED Requirements

### Requirement: Configured parser retry is safe for ordinary output

The extraction SDK SHALL write no raw provider response or stack trace to
stdout, stderr, ordinary SDK logs, or raised parser exception messages when
response parsing fails or retries. Exact parser evidence SHALL remain available
through the existing `AgentTool` trace callback.

#### Scenario: Malformed JSON recovers

- **WHEN** the first provider response is malformed JSON
- **AND** a configured second attempt returns a valid expected response
- **THEN** the SDK returns the parsed second response
- **AND** it emits prompt, raw-response, parse-error, and parsed-response trace
  events with attempt numbers
- **AND** ordinary output contains no provider content or stack trace.

#### Scenario: Wrong native or parsed type is rejected

- **WHEN** a response has the wrong native type or parses to the wrong type
- **THEN** the SDK raises the existing parser exception after configured retries
  are exhausted
- **AND** ordinary output and the exception message contain no provider content
  or stack trace
- **AND** the trace callback retains the exact failure evidence.

#### Scenario: Response envelope contains the wrong inner type

- **WHEN** a native object or JSON string has a supported `answer.type` envelope
- **AND** the unwrapped value does not match the expected response type
- **THEN** final response validation treats it as a parser failure
- **AND** the configured parser retry applies
- **AND** exhaustion remains terminal with exact evidence in the trace callback.

### Requirement: Parser retry remains bounded and consumer-configured

The SDK SHALL preserve the configured `response_parse_max_retries` limit and
SHALL keep parser exhaustion terminal after that limit.

#### Scenario: One configured retry is exhausted

- **WHEN** a consumer configures one parser retry
- **AND** both provider responses fail parsing
- **THEN** the SDK makes exactly two provider calls
- **AND** it raises the existing terminal parser exception after the second
  failure.

#### Scenario: No retry is configured

- **WHEN** a consumer configures zero parser retries
- **THEN** the first parser failure remains terminal without an extra provider
  call.

### Requirement: Parser output safety does not change other retry owners

The SDK change SHALL NOT add model-client, transport, task, or stage retry
behavior.

#### Scenario: Provider transport fails

- **WHEN** the provider call fails before a response reaches the parser
- **THEN** response-parser retry is not consumed
- **AND** the consumer's existing transport policy remains the retry owner.

#### Scenario: Post-parser processing raises TypeError

- **WHEN** downstream processing raises `TypeError` after parsing succeeded
- **THEN** the SDK does not classify it as a response-parser failure.
