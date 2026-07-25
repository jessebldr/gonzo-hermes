# `gonzo/` — code công ty bên trong fork Hermes

Mọi thứ Kyperus/Gonzo tự viết sống ở đây. Upstream (`NousResearch/hermes-agent`) không
bao giờ có thư mục tên `gonzo/`, nên **không file nào trong đây có thể conflict khi
cherry-pick upstream**. Đó là toàn bộ lý do nó tồn tại.

Ngược lại: file **ngoài** `gonzo/` là file của upstream. Sửa một file như vậy tạo ra một
điểm conflict vĩnh viễn cho mọi lần sync về sau. D-19 cho phép — dispatcher, process
isolation, session routing bắt buộc phải đụng core — nhưng có giá. Nên mỗi lần sửa file
upstream phải: (a) là một commit riêng, có test; (b) được ghi vào bảng cuối file này.

Bối cảnh đầy đủ: [`docs/architecture/hermes-vault-agent-team-architecture.md`](../docs/architecture/hermes-vault-agent-team-architecture.md).
Baseline fork + mô hình branch: [`docs/architecture/decisions/0001-fork-baseline-and-branch-model.md`](../docs/architecture/decisions/0001-fork-baseline-and-branch-model.md).

## Bản đồ — 8 thư mục, 1:1 với 7 workstream của D-21

| Thư mục | Là gì | Quyết định | Workstream | Gate |
|---|---|---|---|---|
| `profiles/` | Config 4 profile (`mkt-orchestrator`, `mkt-research`, `mkt-creative`, `mkt-reviewer`), mỗi cái một process, credential riêng | D-03 | ① | 2 |
| `kanban_bus/` | `team_ask`, dispatcher đánh thức worker, worker inbox trên Kanban SQLite | D-02, D-03 | ② | 2 |
| `lark_io_broker/` | `post_message` · `post_card` · `patch_card` · `write_base_row` qua signed capability; routing table durable + idempotent | D-20 | ③ | 2 |
| `vault_policy/` | Retrieval 7 thành phần (symbolic → graph → semantic), read contract `use_class`, draft-write theo `status` | D-04, D-04a, D-04b | ④ | 3, 4 |
| `approval/` | Mở phiên duyệt: `content_hash` + nonce + `card_id` + expiry, render card "Adopt as doctrine" | D-14 | ⑤ | 5 |
| `publisher/` | Service **duy nhất** được ghi field `status`: verify callback → flip `approved` → `validate_vault.py` → git commit | D-05, D-13, D-14 | ⑤ | 5 |
| `scanner/` | Pre-load truth gate: staging → quét → rewrite fact thành vault lookup → activate / quarantine / hard block | D-15 | ⑥ | 2 |
| `deploy/` | launchd plist, health check, backup/restore Kanban, deploy + rollback bằng script | D-18, D-21 | ⑦ | 2, 5 |
| `tests/` | Truth-integrity suite (D-17①) + test cho các module trên | D-17 | ⑦ | 1, 3+ |

Trạng thái hiện tại: **tất cả đều là stub.** Thứ tự build và điều kiện đậu của từng tầng
nằm ở §8 của tài liệu kiến trúc — không tầng nào được coi là xong nếu chưa qua gate của nó.

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
