---
id: "0017"
title: Vá adapter Feishu — ba lỗi trên đường card
type: task
status: closed
assignee: "tech-lead"
blocked_by: []
---

## Question

Đường card là cơ chế định vị chính thức từ nay ([ADR 0002](../../architecture/decisions/0002-dinh-vi-trong-lark-va-va-adapter.md)).
Callback tới nơi và `value` giữ nguyên vẹn, nhưng ba chỗ trong `plugins/platforms/feishu/adapter.py`
làm nó không dùng được. Vá cả ba, mỗi cái một commit có test.

## Ba lỗi, đã xác minh bằng log thật

| # | Lỗi | Vị trí | Triệu chứng |
|---|---|---|---|
| 1 | `/card` không phải lệnh được đăng ký | `_handle_card_action_event` dựng `synthetic_text = f"/card {tag}"` | `Unrecognized slash command /card from feishu` — payload về rồi bị vứt |
| 2 | `message_id=token` (card id `c-…`, không phải `om_…`) | `adapter.py:3053` | `Invalid ids: [c-67998aca…]` code `99992354`; **cả fallback cũng fail** nên bot câm |
| 3 | `thread_id=None` gán cứng | `adapter.py:3042` | Agent không biết card thuộc topic nào → không trả lời về đúng topic |

## Vật liệu để vá đã có sẵn

`context` của card action event mang **`open_message_id`** (một `om_…`), cạnh `open_chat_id`
mà adapter đang đọc. Từ `open_message_id` gọi `GET /im/v1/messages/{id}` là ra `thread_id`
— đã kiểm bằng tay, API trả đúng.

## Ràng buộc

`plugins/platforms/feishu/` là **file upstream** và là file upstream sửa thường xuyên. Mỗi
commit ở đây là một điểm conflict vĩnh viễn. Nên: sửa tối thiểu, mỗi commit một lỗi, mỗi
commit một test, và **thêm dòng vào bảng "Upstream files đã sửa"** trong `gonzo/README.md`.

Test âm bắt buộc: bấm nút → agent nhận được đúng `value` của **nút đó** (không phải nút đầu),
và trả lời về **đúng topic** chứa card.

## Resolution

**Cả ba lỗi đã vá và đã xác minh trên bot thật.** Ba commit riêng, mỗi cái một test.

| Lỗi | Vá | Commit |
|---|---|---|
| `message_id` = card token `c-…` | Dùng `context.open_message_id`; uuid làm fallback (hỏng cục bộ, không hỏng ở biên API) | `5843893dd` |
| `thread_id=None` | `_resolve_thread_id_for_message()` — tra message rồi cache; topic của một card không đổi | `5843893dd` |
| `/card` không ai đăng ký | Không phát slash command nữa; click tới agent như một lượt bình thường, `value` giữ nguyên | `691efb94c` |

**Xác minh trên Lark thật** (bấm nút `Creative 2`):

| Kiểm tra | Trước | Sau |
|---|---|---|
| Lỗi `99992354` | Mọi send fail, kể cả fallback | **0 lần** |
| `thread_id` | `None` | `omt_190064f568cf194b` — đúng topic |
| Bot trả lời | Câm | 249 ký tự |
| Định vị item | Payload bị vứt | `{"item": "creative-2"}` — đúng nút |

**501 test Feishu xanh, ruff sạch.** Bảng "Upstream files đã sửa" trong `gonzo/README.md`
lên 3 dòng — thêm adapter và một test upstream (sửa để pin *ý định* thay vì pin tiền tố slash).

## Quan sát kèm theo, không phải lỗi

Một cú click tốn `tool_turns=10, api_calls=11/90` — agent đi đọc ADR, đọc file test,
`session_search`, grep. Đúng nhưng lãng phí. Ở quy mô team đây là vấn đề chi phí, và nó nối
vào [Chỗ ở của cost-cap enforcement](0019-cho-o-cua-cost-cap-enforcement.md) và
[Phạm vi của session_search](0018-pham-vi-cua-session-search.md).