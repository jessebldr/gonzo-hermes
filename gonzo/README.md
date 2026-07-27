# `gonzo/` — code công ty bên trong fork Hermes

Mọi thứ Kyperus/Gonzo tự viết sống ở đây. Upstream (`NousResearch/hermes-agent`) không
bao giờ có thư mục tên `gonzo/`, nên **không file nào trong đây có thể conflict khi
cherry-pick upstream**. Đó là toàn bộ lý do nó tồn tại.

Ngược lại: file **ngoài** `gonzo/` là file của upstream. Sửa một file như vậy tạo ra một
điểm conflict vĩnh viễn cho mọi lần sync về sau. D-19 cho phép — dispatcher, profile
routing, sandbox propagation, session routing có thể phải đụng core — nhưng có giá. Nên mỗi lần sửa file
upstream phải: (a) là một commit riêng, có test; (b) được ghi vào bảng cuối file này.

Bối cảnh đầy đủ: [`docs/architecture/hermes-vault-agent-team-architecture.md`](../docs/architecture/hermes-vault-agent-team-architecture.md).
Baseline fork + mô hình branch: [`docs/architecture/decisions/0001-fork-baseline-and-branch-model.md`](../docs/architecture/decisions/0001-fork-baseline-and-branch-model.md).

## Bản đồ — 8 thư mục production + prototype throwaway

| Thư mục | Là gì | Quyết định | Workstream | Gate |
|---|---|---|---|---|
| `profiles/` | Config personal/shared/specialist profiles; memory state tách, Docker no-mount là filesystem boundary | D-01, D-03, ADR 0003 | ① | 2 |
| `kanban_bus/` | `team_ask`, dispatcher đánh thức worker, worker inbox trên Kanban SQLite | D-02, D-03 | ② | 2 |
| `lark_io_broker/` | `post_message` · `post_card` · `patch_card` · `write_base_row` qua signed capability; routing table durable + idempotent | D-20 | ③ | 2 |
| `vault_policy/` | Retrieval 7 thành phần (symbolic → graph → semantic), read contract `use_class`, draft-write theo `status` | D-04, D-04a, D-04b | ④ | 3, 4 |
| `approval/` | Mở phiên duyệt: `content_hash` + nonce + `card_id` + expiry, render card "Adopt as doctrine" | D-14 | ⑤ | 5 |
| `publisher/` | Service **duy nhất** được ghi field `status`: verify callback → flip `approved` → `validate_vault.py` → git commit | D-05, D-13, D-14 | ⑤ | 5 |
| `scanner/` | Pre-load truth gate: staging → quét → rewrite fact thành vault lookup → activate / quarantine / hard block | D-15 | ⑥ | 2 |
| `deploy/` | launchd plist, health check, backup/restore Kanban, deploy + rollback bằng script | D-18, D-21 | ⑦ | 2, 5 |
| `tests/` | Truth-integrity suite (D-17①) + test cho các module trên | D-17 | ⑦ | 1, 3+ |
| `prototypes/` | Runner throwaway để bác/chứng minh premise bằng runtime; xoá hoặc absorb sau khi có ADR | ADR 0003 | — | — |

Trạng thái hiện tại: các thư mục production vẫn là stub; `prototypes/` đã chạy để trả lời
boundary premise nhưng không phải production code. Thứ tự build và điều kiện đậu của từng
tầng nằm ở §8 — không tầng nào được coi là xong nếu chưa qua gate của nó.

## Luật của thư mục này

1. **Không fact công ty trong code.** Vault (`gonzo-vault`) giữ truth (P1). Code ở đây
   *truy vấn* vault, không *chứa* nội dung vault. Một literal như `$419` hay một product
   claim hardcode trong `gonzo/` là bug cùng loại với thứ D-15 chặn ở memory/skill.
2. **Không secret trong repo.** Lark app secret, token, `lark_user_id → role` mapping sống
   ở runtime config ngoài git (D-14). Repo chỉ giữ schema và loader.
3. **`encoding="utf-8"` bắt buộc.** ruff `PLW1514` bật cho `gonzo/**`. Upstream miễn trừ
   `plugins/**`, `skills/**`, `tests/**` — `gonzo/**` **không** nằm trong danh sách miễn trừ,
   và cố ý như vậy.
4. **Test đi cùng code.** Test của module ở đây → `gonzo/tests/`. Test đụng Hermes core →
   `tests/` của upstream, cạnh test upstream, vì đó là chỗ nó sẽ conflict và cần được thấy.

## Upstream files đã sửa

Mỗi dòng ở đây là một điểm conflict phải giải bằng tay ở mọi lần cherry-pick upstream.
Danh sách này ngắn là một mục tiêu, không phải tình cờ.

| File | Vì sao | Commit |
|---|---|---|
| `pyproject.toml` | Đăng ký package `gonzo` vào `packages.find`, thêm `gonzo/tests` vào `testpaths` | khung ban đầu |
| `docs/architecture/hermes-vault-agent-team-architecture.md` | Runtime evidence supersede D-01/D-03 bằng hybrid personal agents + Docker filesystem boundary | pending — ADR 0003 |
| `docs/architecture/decisions/0003-hybrid-personal-agents-va-filesystem-boundary.md` | Decision record cho topology và boundary đã test thật; file fork-owned, không có upstream counterpart | pending — ADR 0003 |
| `docs/wayfinder/map.md` | Ghi decision ADR 0003, credential-log boundary và cập nhật fog RAM/topology | pending — ADR 0003 + WS log fix |
| `docs/wayfinder/tickets/0022-profile-khong-phai-filesystem-boundary.md` | Đóng prototype ticket bằng runtime evidence | pending — ADR 0003 |
| `docs/wayfinder/tickets/0023-file-tools-lam-roi-docker-lifecycle-config.md` | Đóng config propagation bug bằng tests + runtime probe 7/7 | pending — lifecycle fix |
| `tools/terminal_tool.py` | Một shared container-config builder cho mọi environment creation path | pending — lifecycle fix |
| `tools/file_tools.py` | File-first environment creation dùng full container contract | pending — lifecycle fix |
| `tools/code_execution_tool.py` | Execute-first environment creation dùng full container contract | pending — lifecycle fix |
| `tests/tools/test_file_tools_container_config.py` | Pin exact file-first container contract bằng non-default values | pending — lifecycle fix |
| `tests/tools/test_code_execution_container_config.py` | Pin exact execute-first container contract bằng non-default values | pending — lifecycle fix |
| `tests/tools/test_docker_network_config.py` | Thay AST change-detector bằng behavioral contract trên shared builder | pending — lifecycle fix |
| `agent/redact.py` | Strict URL boundary nhận diện `access_key` và authentication `ticket`; default URL behavior không đổi | `test_redact.py` + `test_feishu_logging.py` |
| `plugins/platforms/feishu/adapter.py` | Card action: dùng `context.open_message_id` thay cho card token (`c-…`), resolve `thread_id` của topic, và không phát `/card` (lệnh không ai đăng ký). Bắt buộc vì Lark Topic-mode không có định vị theo message — [ADR 0002](../docs/architecture/decisions/0002-dinh-vi-trong-lark-va-va-adapter.md). Logger boundary ép che credential WS do SDK tự in | `test_feishu_card_action_addressing.py` + `test_feishu_logging.py` |
| `tests/gateway/test_feishu_approval_buttons.py` | Một test pin hành vi `/card` cũ; sửa để pin **ý định** (click tới được agent, `value` sống sót) thay vì tiền tố slash | chính nó |
| `tests/gateway/test_feishu_logging.py` | Pin invariant log WS thật: credential bị che, endpoint và public diagnostic params còn nguyên, không phụ thuộc redaction preference | chính nó |
| `docs/wayfinder/tickets/0021-log-ro-credential-cua-ws.md` | Ghi root cause, boundary và runtime proof của credential-log fix | ticket này |
