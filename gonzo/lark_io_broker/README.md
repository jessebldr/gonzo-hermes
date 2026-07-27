# `lark_io_broker` — inbound tập trung, outbound qua capability

Quyết định chi phối: **D-20**. Kèm **D-07** (topic ↔ session), **D-08** (message có địa
chỉ), **D-09** (clarify card), **D-10/D-16** (Base + từ vựng trạng thái). Workstream ③. Gate 2.

Một bot identity, một WS gateway/router nhận **toàn bộ** inbound rồi route về personal hoặc
shared task profile. Specialist không kết nối Lark và không dùng shared memory/context live;
task owner nhận artifact theo contract.

## API — hẹp, cố ý

`post_message` · `post_card` · `patch_card` · `write_base_row`. Không có gì khác.

**Outbound:** worker gọi broker bằng **signed capability** gắn với `task_id` ·
`owner_profile` · `topic_root_id` · danh sách action được phép. Broker kiểm capability, gửi
**nguyên payload**, ghi lại `{message_id/card_id, task_id, owner_profile, root_id,
content_hash}`.

**Inbound:** gateway route topic theo `root_id`/`thread_id`; card button định vị deliverable
theo `card_id` + payload → tra routing table ra `task_id` + `owner_profile` → ghi event vào
**Kanban inbox** của profile sở hữu task → dispatcher đánh thức đúng worker process. Trong
Topic-mode, `parent_id == root_id`; không dùng nó làm per-message pointer (ADR 0002).

## Bất biến

- **Worker không bao giờ cầm Lark app secret.**
- **Routing table durable**, backup **cùng Kanban** (D-02), và **idempotent** — kill broker
  giữa chừng rồi restart thì **không được gửi trùng card**.
- Bảng này dùng chung với ánh xạ `card_id ↔ content_hash` mà D-14 vốn đã cần.
- **`approved` là từ của vault, không ai khác được mượn** (D-16). Trạng thái Base dùng bộ
  riêng, không giao nhau: `working` · `review-ready` · `cleared-for-use` · `needs-edit` ·
  `retired`. Phải áp **trước dòng Base đầu tiên** — sau đó cả team đã quen mồm, không sửa được.

## Tiêu chí đậu Gate 2

Worker gửi được card **không** cầm app secret; capability sai `task_id`/action → **từ chối**;
kill broker giữa chừng rồi restart → **không gửi trùng card**.

Trạng thái: **stub.** Card limits đã đo thật; `larksuite/lark-openapi-mcp` vẫn là tiền đề
Gate 0 chưa resolve.
