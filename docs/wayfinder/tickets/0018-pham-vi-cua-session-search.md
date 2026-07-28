---
id: "0018"
title: Phạm vi của session_search
type: grilling
status: closed
assignee: "codex"
blocked_by: []
---

## Question

`session_search` đọc xuyên topic và xuyên profile, **không có một tham chiếu `user_id` nào**
trong toàn bộ `tools/session_search_tool.py`. Cho nó thấy tới đâu?

## Bằng chứng

Quan sát trực tiếp: hỏi ở topic 2 *"tôi vừa hỏi gì ở topic kia"* → agent trả lời đúng nội
dung topic 1, và đọc được cả **tên** topic kia. Cơ chế là tool, không phải context — hai tin
nhắn đầu có `tool_turns=0` và hoàn toàn không thấy nhau.

`_resolve_profile_db()` còn cho phép mở `state.db` của **profile khác** ở chế độ read-only —
đó là tính năng có chủ đích, không phải lỗ hổng.

## Vì sao quan trọng

- **Gate 2 tiêu chí ⑥** (*"draft/memory/skill không bleed giữa profiles"*) không thể pass khi
  tool này còn mounted.
- **D-20** mất khả năng thực thi: nội dung deliverable không đi qua context orchestrator,
  nhưng đi qua tool này thì vẫn tới.
- Đây là **kênh truth thứ ba** — sau vault và self-created skill (D-15). Hội thoại của người
  khác: không provenance, không `use_class`, `validate_vault.py` không thấy.

## Ba mức

| | Phạm vi | Được | Mất |
|---|---|---|---|
| a | Chỉ session hiện tại | Tắt bằng config (`disabled_toolsets`), không đụng core | Agent không nhớ hội thoại cũ — mất cảm giác personal-AI |
| b | Hội thoại **của chính người hỏi**, trong **cùng profile** | Giữ personal-AI, chặn xuyên người và xuyên profile | Phải vá fork (thêm `WHERE user_id`), cần test âm |
| c | Giữ nguyên | — | Gate 2 ⑥ fail |

Khuyến nghị đã nêu: **(a) trước, (b) sau** — vì đang ở Gate 1, chưa có 4 profile chạy song
song và truth suite chưa chạy thật (chỉ từ Gate 3), nên vá bây giờ là vá thứ chưa có lưới
nào bắt nếu vá sai.

Cần chốt: (b) có đáng làm không, và nếu có thì phạm vi theo **người**, theo **topic**, hay cả hai.

## Cập nhật 2026-07-26 — hoãn có điều kiện, kèm mốc kích hoạt chính xác

Đo lại trọng số sau khi đọc kỹ hơn. Ba kịch bản **không** ngang nhau:

| Kịch bản | Hại thật | Khi nào |
|---|---|---|
| Topic 2 đọc topic 1 | **Thấp** — cả hai là không gian chung, ai trong group cũng cuộn lên đọc được. Agent nhắc lại không lộ gì mới | ngay |
| **Group đọc nội dung DM** | **Thật, và im lặng** — người ta DM vì tưởng riêng tư | lần đầu có người thứ hai dùng bot |
| Profile A đọc kho profile B | Chặn Gate 2 ⑥ | ở Gate 2 |

Lần trước tôi nhấn vào dòng đầu, mà đó đúng là chuyện nhỏ. Cái đáng lo là dòng giữa.

**Hôm nay rủi ro bằng không theo cấu trúc:** `FEISHU_ALLOW_ALL_USERS=false` và
`FEISHU_ALLOWED_USERS` chỉ có một người → không ai khác gọi được bot, kể cả DM. Không có DM
của người khác để mà rò.

> **MỐC KÍCH HOẠT:** khi thêm người thứ hai vào `FEISHU_ALLOWED_USERS`, phải chốt (a) hoặc
> (b) **trước** đó. Đó là dòng duy nhất trong `.env` mở cửa cho rủi ro này.

**Chi phí của (b) cao hơn ước tính ban đầu.** `search_messages` có sẵn `source_filter` nhưng
nó lọc theo `sessions.source`, mà cột đó chỉ chứa tên nền tảng (`cli`, `feishu`) — quá thô.
Lọc theo người phải thêm tham số vào `search_messages` + `_search_messages_impl` + nhánh
trigram + nhánh CJK — **bốn chỗ trong `hermes_state.py`**, file lõi 8000+ dòng, đắt hơn
adapter nhiều. Cộng thêm: cùng một người đang tồn tại dưới **hai** `user_id`
(`1d13c1ff` tenant-scoped và `ou_d8ae…` open_id), nên bộ lọc phải xử lý cả hai dạng.

## Resolution — 2026-07-28

**Chọn (b), nhưng tách semantics theo loại hội thoại:**

- DM: cùng platform + cùng profile + cùng principal. Principal là giao của `user_id` và
  `user_id_alt`; Feishu dùng stable `union_id` trong `user_id_alt`, nên đổi giữa các dạng
  tenant/open ID không làm Khánh mất recall của chính Khánh.
- Group/channel/topic: chỉ exact `chat_id` + `thread_id`. Người trong cùng topic chia sẻ
  context của topic đó; topic khác không được search chéo.
- Messaging runtime không được chọn profile khác. `profile` đã bị gỡ khỏi model schema;
  cả `profile=` lẫn link embedded `profile/id` đều bị từ chối trước khi mở DB khác.
- CLI/admin direct calls giữ hành vi cũ. Boundary chỉ được bật bởi hai agent execution
  path qua trusted `enforce_scope=True`; model không điều khiển cờ này.
- Thiếu active session, thiếu row hoặc gateway identity hỏng thì fail closed. Không fallback
  scan profile khác khi boundary đang bật.

Implementation đi theo ba seam:

1. `hermes_state.py` schema v24 lưu `user_id_alt`, backfill từ `origin_json`, giữ identity
   qua conflict enrichment/compression và áp scope vào FTS, CJK, trigram, LIKE, Latin
   fallback, deferred-gap scan và browse (`e9e41852d`).
2. `session_search` kiểm ownership cho discover/browse/read/scroll và bỏ profile khỏi model
   surface (`263f051e3`).
3. Gateway + lazy agent-session creation persist đủ `user_id`, `user_id_alt`, session/chat/
   thread metadata; cả hai runtime tool path ép scope (`706736351`).

Evidence: 728 focused tests pass với writable temporary `HERMES_HOME`, gồm positive recall
của cùng principal, negative cross-principal/cross-topic/cross-profile, malformed metadata,
CJK/trigram/LIKE/Latin fallback, migration và gateway persistence. Compile và Ruff pass.

Tripwire cũ đã được giải ở code boundary. Chỉ được thêm user thứ hai sau khi deploy ba
commit trên vào pilot và chạy canary hai principal thật; việc thêm allowlist không nằm trong
ticket này. Automatic memory và skill learning không bị sửa bởi thay đổi này.
