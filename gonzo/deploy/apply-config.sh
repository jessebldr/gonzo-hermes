#!/usr/bin/env bash
# Áp config runtime của Hermes từ repo vào $HERMES_HOME.
#
# Vì sao cần script này thay vì để file ở gốc repo: fork có HAI loader config.
# `cli.load_cli_config()` chấp nhận `./cli-config.yaml` làm fallback, nhưng
# `hermes_cli.config.load_config()` — chỗ `auth.py` resolve provider và chỗ
# runtime thật sự đọc — CHỈ đọc `$HERMES_HOME/config.yaml`. Đặt config ở gốc
# repo thì CLI thấy còn agent không, và triệu chứng là
# "No inference provider configured" dù config trông đúng.
#
# Nên nguồn sự thật là file trong repo này, và bản đang chạy là một bản sao
# được áp bằng script — D-19: không patch tay ngoài repo, deploy reproducible.
#
#   ./gonzo/deploy/apply-config.sh          # xem sẽ đổi gì (mặc định, không ghi)
#   ./gonzo/deploy/apply-config.sh --write  # ghi thật
#
# Secret KHÔNG nằm ở đây. File này chỉ trỏ `key_env`; giá trị sống trong
# `.env` (gitignored, chmod 600).

set -euo pipefail

DEPLOY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$DEPLOY_DIR/../.." && pwd)"
SRC="$DEPLOY_DIR/hermes-config.yaml"
HERMES_ROOT="${HERMES_HOME:-$HOME/.hermes}"
VAULT_ROOT="${GONZO_VAULT_ROOT:-$(cd "$REPO_ROOT/.." && pwd)/gonzo-vault}"
DEST="$HERMES_ROOT/config.yaml"
LAUNCHER_SRC="$REPO_ROOT/gonzo/vault_policy/run-mcp.sh"
LAUNCHER_DEST="$HERMES_ROOT/bin/gonzo-vault-policy-mcp"
RUNTIME_MAP="${GONZO_RUNTIME_MAP:-$HERMES_ROOT/gonzo-runtime.yaml}"
PYTHON="$REPO_ROOT/.venv/bin/python"
[ -x "$PYTHON" ] || PYTHON="$REPO_ROOT/venv/bin/python"
[ -x "$PYTHON" ] || PYTHON="$(command -v python3)"

[ -f "$SRC" ] || { echo "không thấy nguồn: $SRC" >&2; exit 1; }
[ -f "$LAUNCHER_SRC" ] || { echo "không thấy launcher: $LAUNCHER_SRC" >&2; exit 1; }
[ -d "$VAULT_ROOT" ] || { echo "không thấy vault: $VAULT_ROOT" >&2; exit 1; }

escape_sed() {
  printf '%s' "$1" | sed 's/[&|]/\\&/g'
}

RENDERED="$(mktemp "${TMPDIR:-/tmp}/gonzo-hermes-config.XXXXXX")"
trap 'rm -f "$RENDERED"' EXIT
sed \
  -e "s|__HERMES_HOME__|$(escape_sed "$HERMES_ROOT")|g" \
  -e "s|__GONZO_HERMES_ROOT__|$(escape_sed "$REPO_ROOT")|g" \
  -e "s|__GONZO_VAULT_ROOT__|$(escape_sed "$VAULT_ROOT")|g" \
  "$SRC" > "$RENDERED"

{
  echo
  echo "# Runtime-only profile routing. Principal/chat IDs come from the private map, never git."
  if [ -f "$RUNTIME_MAP" ]; then
    "$PYTHON" "$REPO_ROOT/gonzo/profiles/runtime_map.py" render-routes "$RUNTIME_MAP"
  else
    echo "multiplex_profiles: false"
    echo "profile_routes: []"
  fi
} >> "$RENDERED"

if [ "${1:-}" != "--write" ]; then
  echo "nguồn : $SRC"
  echo "đích  : $DEST"
  echo
  if [ -f "$DEST" ]; then
    if diff -u "$DEST" "$RENDERED" > /dev/null; then
      echo "không có gì đổi."
    else
      echo "sẽ đổi (- đang chạy, + trong repo):"
      diff -u "$DEST" "$RENDERED" | tail -n +3 || true
    fi
  else
    echo "$DEST chưa tồn tại — sẽ tạo mới."
  fi
  echo "launcher: $LAUNCHER_DEST"
  if [ -f "$RUNTIME_MAP" ]; then
    echo "routes  : $RUNTIME_MAP"
  else
    echo "routes  : chưa có ($RUNTIME_MAP) — multiplex tắt"
  fi
  echo
  echo "chạy lại với --write để ghi."
  exit 0
fi

mkdir -p "$(dirname "$DEST")"
install -m 600 "$RENDERED" "$DEST"
mkdir -p "$(dirname "$LAUNCHER_DEST")"
install -m 755 "$LAUNCHER_SRC" "$LAUNCHER_DEST"
echo "đã ghi $DEST"
echo "đã cài $LAUNCHER_DEST"

# Kiểm key ở ĐÚNG chỗ Hermes đọc nó — `.env` — chứ không phải shell hiện tại.
# Hermes tự nạp `.env` lúc khởi động (cli.py:229), nên biến vắng mặt trong shell
# này là bình thường và không nói lên điều gì.
KEY_ENV="$(grep -m1 'key_env:' "$SRC" | awk '{print $2}')"
ENV_FILE="$(dirname "$(dirname "$(dirname "$SRC")")")/.env"
if [ -n "${KEY_ENV:-}" ]; then
  if grep -qE "^${KEY_ENV}=.+" "$ENV_FILE" 2>/dev/null; then
    echo "$KEY_ENV: có giá trị trong $ENV_FILE"
  else
    echo "$KEY_ENV: THIẾU hoặc rỗng trong $ENV_FILE — agent sẽ báo 'No inference provider configured'"
  fi
fi
