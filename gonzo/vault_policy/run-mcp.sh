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
export PYTHONDONTWRITEBYTECODE=1

exec "$UV_PATH" run \
  --no-project \
  --isolated \
  --cache-dir "$POLICY_CACHE_DIR" \
  --with 'markdown-vault-mcp[embeddings]==3.1.0' \
  --with 'mcp==1.26.0' \
  --with 'pyyaml==6.0.3' \
  python "$SERVER_PATH" "$@"
