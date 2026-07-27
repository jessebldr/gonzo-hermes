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

# Vault-policy index prototype — verdict

Chạy thật ngày 2026-07-27 trên `gonzo-vault`
`a93d693ccc1ffedc9d23dd02a8e7f204ab31f800`, dùng
`markdown-vault-mcp==3.1.0` + FastEmbed `BAAI/bge-small-en-v1.5`.

## Verdict

**Giữ dependency theo quyết định adopt có điều kiện**, nhưng chỉ như private Python index
engine phía sau `gonzo/vault_policy`. Không expose MCP upstream và không đưa raw vault hay
private index vào agent Docker. Prototype không cần fork/sửa upstream; phần wrapper còn
lại là luật riêng D-04/D-04a mà upstream không thể sở hữu thay.

Prototype vẫn là throwaway, chưa phải Gate 3 production service. Khi absorb, giữ behavioral
tests và seam; bỏ runner/TUI-ish measurement shell sau khi production evaluation thay thế.

## Đã chứng minh

- Corpus match **665/665** note governed theo validator + exclusion contract; không có note
  governed nào bị skip. `_inbox/`, `_templates/`, `outputs/`, `.github/` và ba file
  bookkeeping root đều không vào index.
- Raw upstream parser làm rơi **7 note production** vì chuỗi quote hợp lệ theo flat schema
  của vault nhưng không hợp lệ với PyYAML. Index-only normalized mirror giải được mà không
  sửa vault; policy vẫn reread Markdown gốc trước khi trả.
- Query fail-closed nếu working tree bẩn. SHA mismatch rebuild đồng bộ; nếu HEAD đổi trong
  lúc build thì retry tối đa ba lần rồi fail, không phục vụ response từ index chưa bind.
- Engine adapter chỉ trả `path` + `score`. Payload đã reread không có raw `authority`,
  `status`, `freshness`; `use_class` phủ `citable`, `suggestion-only`, `unverified`, `stale`,
  `undecided`, `historical-only`.
- Pipeline quan sát được: frontmatter/type → symbolic → graph → semantic fallback/rerank →
  open-question → policy. Open-question bị loại khỏi result lane chính và bundle riêng;
  hai approved note liên quan bật `multiple_relevant_notes` + `requires_multi_cite`.
- 6 behavioral tests của prototype + 34 test frozen truth-integrity pass: **40/40**.

## Số đo Mac pilot

- Cold query gồm full FTS + embedding build: **67.6 s**.
- Forced SHA-mismatch rebuild: **68.1 s**.
- 15 warm query: **p50 31.5 ms**, **p95 35.6 ms**.
- Peak RSS: **817,496,064 bytes** (~780 MiB).
- SQLite + vector/state: **22,974,731 bytes** (~21.9 MiB).
- Normalized index-only mirror: **3,346,061 bytes** (~3.2 MiB).

RAM/build time là chi phí đáng kể nhưng nằm ở một host-side vault service dùng chung, không
nhân theo profile. Gate 3 vẫn phải tune relevance/false-blocker bằng retrieval evaluation;
prototype này chứng minh contract và feasibility, không chứng minh chất lượng top-k cuối.
