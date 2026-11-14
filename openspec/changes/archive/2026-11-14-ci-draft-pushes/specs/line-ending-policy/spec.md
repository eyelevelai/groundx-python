## REMOVED Requirements

### Requirement: The guard runs in a separate CI workflow from the generated `ci.yml`

**Reason**: The SDK workflow is now maintained under .fernignore.
**Migration**: Keep the line-ending workflow independent with its existing triggers.

## ADDED Requirements

### Requirement: The guard runs in a separate CI workflow from the SDK suite
The GitHub Actions workflow at `.github/workflows/line-endings.yml` SHALL run
`scripts/check-line-endings.sh --all` on `push` and `pull_request`, independently of
the SDK suite in `.github/workflows/ci.yml`.

#### Scenario: A pull request is opened or updated
- **WHEN** a pull request is opened against this repo or a push lands on any branch
- **THEN** `.github/workflows/line-endings.yml` runs `scripts/check-line-endings.sh --all` and
  the job fails if the script exits non-zero
