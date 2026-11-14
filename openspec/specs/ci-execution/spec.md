# ci-execution Specification

## Purpose
Keep full CI on ready PR revisions while avoiding expensive setup on drafts.
## Requirements
### Requirement: Required regression checks on ready PRs

A human SHALL control when a draft PR becomes ready. GitHub Actions SHALL run
the existing test suite on that transition and on later pushes while the PR is
ready. Draft PR runs SHALL leave the required check unsuccessful without
installing dependencies or executing tests.

Main and tag pushes SHALL run both SDK jobs and retain the existing tag publishing conditions. Manual dispatch SHALL run the SDK jobs without publishing. The separate line-ending workflow SHALL retain its existing triggers.

#### Scenario: A draft receives a commit
- **WHEN** a commit is pushed to a draft PR
- **THEN** the workflow stops before dependency setup and the required check does not pass

#### Scenario: A human marks a PR ready
- **WHEN** a human marks a draft PR ready for review
- **THEN** the existing suite runs and must pass before merge

#### Scenario: A ready PR receives a commit
- **WHEN** another commit is pushed to a ready PR
- **THEN** CI automatically runs the same suite against the new revision
