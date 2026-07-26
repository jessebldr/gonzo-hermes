---
id: "0018"
title: Phạm vi của session_search
type: grilling
status: open
assignee: ""
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
