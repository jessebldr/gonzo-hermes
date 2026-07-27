#!/usr/bin/env bash
set -euo pipefail

SERVER_PATH="${1:?usage: gonzo-vault-policy-mcp SERVER_PATH [server args...]}"
shift

if [ ! -f "$SERVER_PATH" ]; then
  echo "vault-policy server not found: $SERVER_PATH" >&2
  exit 1
fi

UV_PATH="$(command -v uv 2>/dev/null || true)"
if [ -z "$UV_PATH" ] && [ -x "$HOME/.local/bin/uv" ]; then
  UV_PATH="$HOME/.local/bin/uv"
fi
if [ -z "$UV_PATH" ]; then
  echo "uv is required to run the pinned vault-policy environment" >&2
  exit 1
fi

POLICY_CACHE_DIR="${HERMES_HOME:-$HOME/.hermes}/cache/vault-policy-uv"
PROJECT_DIR="$(cd "$(dirname "$SERVER_PATH")" && pwd)"
if [ ! -f "$PROJECT_DIR/pyproject.toml" ] || [ ! -f "$PROJECT_DIR/uv.lock" ]; then
  echo "vault-policy locked project not found beside server: $SERVER_PATH" >&2
  exit 1
fi

export PYTHONDONTWRITEBYTECODE=1
export UV_PROJECT_ENVIRONMENT="$POLICY_CACHE_DIR/environment"

exec "$UV_PATH" run \
  --project "$PROJECT_DIR" \
  --locked \
  --no-dev \
  --cache-dir "$POLICY_CACHE_DIR" \
  python "$SERVER_PATH" "$@"
