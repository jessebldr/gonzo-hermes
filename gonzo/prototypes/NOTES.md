# Filesystem boundary prototype — verdict

Chạy thật ngày 2026-07-27 trên fork `7aa46ca0b`, model
`ag/gemini-3.6-flash-high` qua 9router local.

## Đã chứng minh

- Local backend đọc được canary ở absolute host path: profile/process tự nó **không** là
  filesystem sandbox.
- Docker backend với `docker_mount_cwd_to_workspace: false`, `docker_volumes: []` không
  đọc được canary host và không đọc được raw
  `gonzo-vault/brands/kyperus/state/commercial-state.md`.
- Khi profile A còn sống và có file `/workspace/profile-a-only.txt`, profile B không thấy
  file đó.
- Hai lượt end-to-end đều gọi `read_file` thật. Mỗi lượt dùng 2 API calls, 1 tool call;
  local trả content, Docker trả `File not found`.
- Docker inspect xác nhận container chỉ mount skills directory của đúng profile ở chế độ
  read-only; không mount repo, sibling repo hay raw vault.

## Bug tìm thấy và đã sửa

`terminal.docker_persist_across_processes: false` từng không được honor khi environment đầu
tiên được tạo bởi `read_file`/file-tools. Trace code: `tools/file_tools.py::_get_file_ops()` không truyền
`docker_persist_across_processes`, `docker_orphan_reaper`, `docker_env`, hoặc
`docker_extra_args` vào `container_config`, trong khi đường `terminal_tool()` có truyền.

Fix gom terminal, file tools và `execute_code` về một shared container-config builder. Lượt
chạy lại pass 7/7: lifecycle teardown đúng và không còn container probe. Process-per-profile
vẫn không phải security boundary nếu dùng local backend; boundary thật là **Docker no-mount
per profile**.
