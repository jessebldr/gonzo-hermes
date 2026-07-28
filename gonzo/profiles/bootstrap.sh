#!/usr/bin/env bash
# Dry-run/apply the private Gonzo profile map.

set -euo pipefail

PROFILES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$PROFILES_DIR/../.." && pwd)"
HERMES_ROOT="${HERMES_HOME:-$HOME/.hermes}"
VAULT_ROOT="${GONZO_VAULT_ROOT:-$(cd "$REPO_ROOT/.." && pwd)/gonzo-vault}"
RUNTIME_MAP="${GONZO_RUNTIME_MAP:-$HERMES_ROOT/gonzo-runtime.yaml}"
SOURCE_ENV="$REPO_ROOT/.env"
PYTHON="$REPO_ROOT/.venv/bin/python"
[ -x "$PYTHON" ] || PYTHON="$REPO_ROOT/venv/bin/python"
[ -x "$PYTHON" ] || PYTHON="$(command -v python3)"

exec "$PYTHON" "$PROFILES_DIR/runtime_map.py" bootstrap "$RUNTIME_MAP" \
  --hermes-root "$HERMES_ROOT" \
  --repo-root "$REPO_ROOT" \
  --vault-root "$VAULT_ROOT" \
  --source-env "$SOURCE_ENV" \
  "$@"
