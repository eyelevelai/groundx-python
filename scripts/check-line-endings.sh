#!/usr/bin/env bash
# Fails if any tracked text file contains CRLF or mixed line endings.
# Usage:
#   scripts/check-line-endings.sh           # scan files changed vs BASE_REF (default: origin/main)
#   scripts/check-line-endings.sh --all     # scan every tracked file in the repo
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

mode="changed"
if [[ "${1:-}" == "--all" ]]; then
  mode="all"
fi

if [[ "$mode" == "all" ]]; then
  mapfile -t files < <(git ls-files)
else
  base_ref="${BASE_REF:-origin/main}"
  if ! git rev-parse --verify -q "$base_ref" >/dev/null; then
    base_ref="main"
  fi
  merge_base="$(git merge-base "$base_ref" HEAD 2>/dev/null || echo "$base_ref")"
  mapfile -t files < <(git diff --name-only --diff-filter=ACMR "$merge_base" -- | sort -u)
fi

offenders=()
for f in "${files[@]}"; do
  [[ -f "$f" ]] || continue
  if [[ "$(git check-attr binary -- "$f" | awk -F': ' '{print $3}')" == "set" ]]; then
    continue
  fi
  if grep -qU $'\r' "$f" 2>/dev/null; then
    offenders+=("$f")
  fi
done

if [[ "${#offenders[@]}" -gt 0 ]]; then
  echo "Line-ending check FAILED — CRLF or mixed line endings found in:"
  printf '  %s\n' "${offenders[@]}"
  exit 1
fi

echo "Line-ending check passed — no CRLF/mixed line endings found."
exit 0
