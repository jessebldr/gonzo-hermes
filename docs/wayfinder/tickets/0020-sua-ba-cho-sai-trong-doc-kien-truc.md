---
id: "0020"
title: Sửa bốn chỗ sai trong doc kiến trúc
type: task
status: open
assignee: ""
blocked_by: []
---

## Question

Gate 0 và Gate 1 đã chứng minh bốn phát biểu trong doc là sai. Sửa chúng, mỗi cái một commit
ghi rõ bằng chứng.

| Chỗ | Doc đang viết | Sự thật |
|---|---|---|
| **§9** | *"cap thực thi được ở 9router"* | 9router chỉ có Quota Tracker để **xem**. Chi tiết → ticket [Chỗ ở của cost-cap enforcement](0019-cho-o-cua-cost-cap-enforcement.md) |
| **D-01, §6** | *"Hermes không có video-gen"* | Có: `plugins/video_gen/{deepinfra,fal,xai}`. Chi tiết → ticket [Hermes có video-gen](0008-hermes-co-video-gen-sua-d01-va-muc-6.md) |
| **D-08** | Định vị bằng `parent_id` của reply | Lark Topic-mode không có định vị theo message. Chuyển sang `card_id` → [ADR 0002](../../architecture/decisions/0002-dinh-vi-trong-lark-va-va-adapter.md) |
| **D-10, Gate 0** | Giao việc ghi Base cho `larksuite/lark-openapi-mcp` | MCP chỉ là generic OpenAPI bridge, không có capability/idempotency/inbound boundary của D-20. `lark_io_broker` phải gọi direct official SDK/OpenAPI → [lark-openapi-mcp có dùng được không](0004-lark-openapi-mcp-co-dung-duoc-khong.md) |

## Thêm một chỗ thiếu, không phải sai

Dòng 540 hứa *"chuyển **fallback UX đã định**"* khi topic-mode không pass — nhưng **không có
chỗ nào trong doc định nghĩa fallback đó**. Escape condition trỏ vào khoảng không. Hoặc định
nghĩa nó, hoặc bỏ chữ "đã định".

## Ràng buộc

Doc ở trạng thái APPROVED-DESIGN. Sửa nó là sửa thiết kế đã duyệt, nên mỗi sửa đổi phải nêu
**bằng chứng thực nghiệm** đã dẫn tới nó, không sửa vì thấy hợp lý hơn.
