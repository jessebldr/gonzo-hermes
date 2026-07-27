---
id: "0021"
title: Log rò credential của WS
type: task
status: closed
assignee: "codex"
blocked_by: []
---

## Question

`lark_oapi` in nguyên URL WebSocket ở mức INFO, kèm `access_key=…` và `ticket=…`. Vá.

## Bằng chứng

```
INFO Lark: connected to wss://msg-frontier-sg.larksuite.com/ws/v2?...&access_key=4bd99c86…&ticket=543bb205-…
```

Xuất hiện mỗi lần gateway khởi động. Đây là credential phiên kết nối, nhiều khả năng ngắn
hạn — nhưng nó nằm trong file log sẽ được cron đọc, được backup, và được agent đọc khi debug.

Trái luật số 2 của [`gonzo/README.md`](../../../gonzo/README.md): *"Không secret trong repo"* —
và tinh thần của nó rộng hơn cái repo.

## Hướng vá

Hạ log level của logger `lark_oapi.ws`, hoặc thêm filter che query string. Hermes đã có sẵn
`agent.redact.RedactingFormatter` áp lên log — nhưng rõ ràng nó **không** bắt trường hợp này
(đã kiểm: `open_id` cũng xuất hiện nguyên văn). Nên câu hỏi phụ: redactor đang che những gì,
và nó có nên che ID nền tảng không?

## Resolution

Đã vá ở **logger boundary của SDK**, không sửa `site-packages`:

- Adapter cài một filter idempotent lên logger `Lark`. Filter sửa `LogRecord` trước mọi
  handler nên che được cả stdout handler do SDK tự gắn lẫn handler Hermes nhận qua
  propagation.
- Redaction dùng `force=True, redact_url_credentials=True`: không phụ thuộc lựa chọn
  `security.redact_secrets`, vì credential kết nối không được phép xuất hiện trong log kể
  cả khi operator tắt redaction thông thường.
- Bổ sung đúng hai query credential của Lark là `access_key` và `ticket` vào strict URL
  redactor. Không blanket-redact `open_id`: platform identity không tự động là secret, và
  giữ ID vẫn cần cho admission/routing debug.
- Nếu redactor ném exception, filter fail-closed bằng cách thay toàn bộ message bằng một
  dòng omission không chứa dữ liệu SDK.

Behavioral test ở `tests/gateway/test_feishu_logging.py` pin đầu ra operator nhìn thấy:
secret biến mất; `access_key=***`, `ticket=***`; host/path và `device_id`, `aid`, `fpid`
vẫn còn. Test cố ý tắt `_REDACT_ENABLED` để chứng minh boundary bắt buộc này không bị config
preference vô hiệu hoá.

Runtime proof trên Lark tenant thật lúc 2026-07-27 13:12 (Asia/Ho_Chi_Minh): gateway kết
nối WS thành công; dòng `connected to wss://msg-frontier-sg.larksuite.com/ws/v2` in cả hai
credential là `***`, giữ các public diagnostic params. Dòng disconnect cũng được che. Tiến
trình verification đã dừng sạch sau phép thử.

Verification cuối: `586 passed` cho toàn bộ cụm `tests/gateway/test_feishu*.py` liên quan +
`tests/agent/test_redact.py`; Ruff và `git diff --check` đều pass.
