---
id: "0021"
title: Log rò credential của WS
type: task
status: open
assignee: ""
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
