---
id: "0004"
title: lark-openapi-mcp có dùng được không
type: research
status: closed
assignee: "codex"
blocked_by: []
---

## Question

`larksuite/lark-openapi-mcp` — repo còn tồn tại và còn sống không, license dùng được cho
mục đích thương mại không, và nó có phủ được `write_base_row` + card API mà D-10/D-20 cần
không?

## Vì sao nó chặn

Gate 0. D-10 giao hẳn việc ghi Base cho MCP chính chủ này. Nếu nó chết, license cấm, hoặc
thiếu API, thì `gonzo/lark_io_broker/` phải gọi thẳng Lark OpenAPI — nhiều việc hơn, nhưng
không đổi kiến trúc.

Doc tự nhận đây là "giả định có căn cứ nhưng chưa tự verify" (§9).

## Bắt đầu ở đâu

Nguồn sơ cấp: repo GitHub thật, file LICENSE thật, danh sách tool nó expose. Không tin
bài blog. Kết quả là một report markdown link từ ticket này, trả lời đủ 3 câu hỏi trên —
và nếu "không", thì nói rõ phải tự gọi những endpoint nào.

## Resolution

Report: [Đánh giá `larksuite/lark-openapi-mcp` cho D-10/D-20](../../research/lark-openapi-mcp-assessment.md).

- Repo official, public, chưa archive, nhưng vẫn Beta và gần 11.5 tháng không có
  commit/release mới tại snapshot `21920354...`: tồn tại, nhưng maintenance nguội.
- License MIT cho phép commercial use/distribute/sublicense/sell nếu giữ notice.
- Primitive API phủ đủ Base create/update/batch, interactive message create và card patch;
  CardKit/patch phải bật explicit ngoài default preset.
- MCP không có card-action receiver, signed task capability, durable routing table hay
  idempotency/recovery ledger, nên không thay được D-20 boundary.

**Quyết định:** `gonzo/lark_io_broker` tiếp tục là capability boundary do Gonzo sở hữu và
gọi direct Lark OpenAPI qua official Python SDK. Không expose generic MCP cho worker/model;
upstream MCP chỉ giữ làm reference/prototype tùy chọn.
