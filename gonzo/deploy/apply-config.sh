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

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/hermes-config.yaml"
DEST="${HERMES_HOME:-$HOME/.hermes}/config.yaml"

[ -f "$SRC" ] || { echo "không thấy nguồn: $SRC" >&2; exit 1; }

if [ "${1:-}" != "--write" ]; then
  echo "nguồn : $SRC"
  echo "đích  : $DEST"
  echo
  if [ -f "$DEST" ]; then
    if diff -u "$DEST" "$SRC" > /dev/null; then
      echo "không có gì đổi."
    else
      echo "sẽ đổi (- đang chạy, + trong repo):"
      diff -u "$DEST" "$SRC" | tail -n +3 || true
    fi
  else
    echo "$DEST chưa tồn tại — sẽ tạo mới."
  fi
  echo
  echo "chạy lại với --write để ghi."
  exit 0
fi

mkdir -p "$(dirname "$DEST")"
cp "$SRC" "$DEST"
echo "đã ghi $DEST"

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
