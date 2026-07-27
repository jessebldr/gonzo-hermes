# `deploy` — deploy và rollback phải reproducible bằng script

Quyết định chi phối: **D-18** (cutover đảo được), **D-19** (production chỉ chạy release
tag), **D-21** (bus factor giảm bằng hệ thống, không bằng người). Workstream ⑦.

Thư mục script + config, không phải package Python — cố ý không có `__init__.py`.

## Nội dung dự kiến

- launchd plist cho gateway và các specialist process thực sự cần tách + KeepAlive, cùng
  **health-check script nhẹ** (Hermes watchdog chỉ có systemd — macOS không có; theo dõi
  1 tuần ở Gate 5). Personal profiles cùng trust domain có thể multiplex.
- Backup/restore Kanban: SQLite online backup API hoặc `VACUUM INTO` — **không** copy file DB
  đang chạy. ≥1 bản off-device, có retention, **restore test tự động**.
- Script deploy + rollback. **Rollback drill phải pass ở Gate 6** trước khi cutover.
- Routing flag của D-18: một thao tác kéo toàn bộ task về legacy runtime.

## Bất biến

- **Production chỉ chạy release tag/commit của fork — không chạy working tree** (D-19).
- **Không patch tay ngoài repo.** Mọi sửa đổi là một commit có test. Không có ngoại lệ
  "sửa nhanh trên máy".
- **Cutover là thao tác đảo được**: ngừng giao task mới cho hệ cũ, không xoá, không tắt.
  Legacy giữ chạy thêm 4 tuần. Retire chỉ sau 4 tuần ổn **và** một lần restore/rollback drill
  thành công.
- **Rollback ngay lập tức, không họp**, khi có: truth-integrity breach · mất task/state ·
  approval hoặc retrieval gate bị bypass. Kéo flag trước, điều tra sau.
- **Không secret trong repo.** Lark app secret, token, mapping `lark_user_id → role/domain`
  sống ở runtime config ngoài git.

## Đã có

- `hermes-config.yaml` — config runtime, **nguồn sự thật**. Không chứa secret; key chỉ được
  trỏ tới bằng `key_env`, giá trị sống ở `.env` (gitignored, chmod 600).
- `apply-config.sh` — áp nó vào `$HERMES_HOME/config.yaml`. Mặc định chỉ in diff; `--write`
  mới ghi. Kèm kiểm `key_env` có giá trị trong `.env` chưa.

**Hiện trạng an toàn:** `hermes-config.yaml` chưa có `terminal:` nên Hermes rơi về local
backend. Runtime hiện tại **không** có filesystem boundary và đã đọc được raw sibling
`gonzo-vault` qua absolute path. Không nối vault raw, không thêm user thứ hai, và không coi
process/profile là sandbox. Lifecycle propagation đã được sửa và probe Docker pass 7/7;
việc tiếp theo là chuyển config production sang Docker no-mount rồi chạy lại negative probes
trên chính config được deploy trước khi bật gateway.

**Vì sao phải có script thay vì để config ở gốc repo.** Fork có hai loader:
`cli.load_cli_config()` chấp nhận `./cli-config.yaml` làm fallback, nhưng
`hermes_cli.config.load_config()` — chỗ `hermes_cli/auth.py:1961` resolve provider, tức chỗ
runtime thật sự đọc — **chỉ** đọc `$HERMES_HOME/config.yaml`. Để config ở gốc repo thì CLI
thấy mà agent không, và triệu chứng là `No inference provider configured` dù config trông
hoàn toàn đúng. Đây là một giờ debug đã trả rồi; đừng trả lại.

Trạng thái phần còn lại (launchd, backup/restore, rollback): **stub.**
