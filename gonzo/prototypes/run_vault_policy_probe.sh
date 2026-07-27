#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROBE_CACHE_DIR="${TMPDIR:-/tmp}/gonzo-vault-policy-uv-cache"
export PYTHONDONTWRITEBYTECODE=1

exec uv run \
  --no-project \
  --isolated \
  --cache-dir "$PROBE_CACHE_DIR" \
  --with 'markdown-vault-mcp[embeddings]==3.1.0' \
  python "$SCRIPT_DIR/vault_policy_probe.py" "$@"
