---
id: "0017"
title: Vá adapter Feishu — ba lỗi trên đường card
type: task
status: open
assignee: ""
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
