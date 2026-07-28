---
id: "0027"
title: Implement lark-io-broker capability boundary
type: task
status: open
assignee: ""
blocked_by: []
---

## Question

Implement production `gonzo/lark_io_broker` với bốn operation hẹp `post_message` ·
`post_card` · `patch_card` · `write_base_row`, gọi direct Lark OpenAPI qua official Python
SDK thay vì expose `larksuite/lark-openapi-mcp` cho worker/model.

## Vì sao đã đủ rõ để làm

[lark-openapi-mcp có dùng được không](0004-lark-openapi-mcp-co-dung-duoc-khong.md) đã verify
primitive Base/card tồn tại nhưng MCP upstream không có security/orchestration boundary
D-20. Fork hiện tại đã chạy thật official `lark_oapi` client cho create/reply/update
interactive message và có `BaseRequest` pattern cho endpoint chưa có typed wrapper.

## Contract bắt buộc

- worker không cầm Lark app secret;
- signed capability bind `task_id` · `owner_profile` · `topic_root_id` · allowed actions;
- capability sai action/task/topic/profile phải fail closed trước network call;
- durable ledger lưu `message_id/card_id` · task/profile/root · `content_hash`;
- idempotency + crash recovery: restart giữa send và commit không được gửi trùng;
- `post_card`/`patch_card` giữ nguyên structured payload và card addressing của ADR 0002;
- `write_base_row` chỉ nhận trạng thái D-16, không cho literal `approved`;
- app secret chỉ nằm trong gateway/broker trust domain;
- test E2E dùng fake official client + temporary state, không mock mất capability/ledger seam.

## Tiêu chí đóng

Gate 2 negative canaries pass: worker gửi card không có app secret; capability sai bị từ
chối; duplicate request/restart không tạo card/row thứ hai; callback card hiện tại vẫn route
về đúng owner task qua durable mapping.
