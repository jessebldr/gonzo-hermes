---
id: "0005"
title: Kanban và topic↔session của Hermes có đúng docs không
type: prototype
status: closed
assignee: "tech-lead"
blocked_by: []
---

## Question

Hermes đã có Kanban và adapter Feishu sẵn. Chúng có hành xử đúng như docs mô tả không —
đặc biệt: **1 Lark topic có map thành đúng 1 session** không, và reply vào một message có
giữ được context của nhánh đó không?

## Vì sao nó chặn

Rủi ro #1 của doc, nguyên văn: *"Feishu topic↔session mapping của Hermes chưa chắc chuẩn
(issues 2026 còn rough)"*. Đây là bài test bắt buộc của Gate 1, và D-07/D-08 đứng hoàn
toàn trên nó — nếu topic không tách session, thì "mở việc mới = mở topic mới" không còn là
thật, và D-08 (5 hooks = 5 message có địa chỉ) mất đường về.

Doc đã chấp nhận trước là phải vá adapter 20-30%, và vá đó **là commit trong fork**
(D-19), không phải patch script bên ngoài.

## Bắt đầu ở đâu

`plugins/platforms/feishu`, `gateway/profile_routing.py`, `tools/kanban_tools.py`,
`hermes_cli/kanban_db.py`. Chạy thật với một group topic-mode, không đọc code rồi đoán.

**Escape condition đã định sẵn** (D-21): topic-mode không pass routing test → chuyển sang
fallback UX, không vá vô hạn để giữ một lựa chọn kỹ thuật.

## Resolution

**Topic → session mapping hoạt động đúng. Không cần vá.** Rủi ro #1 của doc được giải theo
hướng tốt; escape condition (chuyển fallback UX) không phải kích hoạt.

Bằng chứng — hai topic trong cùng một group, đo trên bot thật:

| Tin nhắn | Topic session key | Agent session |
|---|---|---|
| `alo anh bình gold phải k ạ` | `…:omt_19003986cc8f1947` | `20260726_141341_574537fb` |
| `alo hermes à sống k` | `…:omt_19004f72238f1940` | `20260726_154001_9173ea63` |

Cùng `chat_id`, khác `omt_` → hai session độc lập. Hai tin đầu có `tool_turns=0` và không
hề thấy nhau.

**Mô hình nhiều người dùng có sẵn và có công tắc** (`docs/session-lifecycle.md`):
`group_sessions_per_user` mặc định `True`, `thread_sessions_per_user` mặc định `False`.
Key ta quan sát khớp chính xác dòng *"Thread in group, shared"*.

**Session KHÔNG bền** — bị evict sau ~1h nhàn rỗi (`Agent cache idle-TTL evict … idle=3608s`).
Xác nhận giả định của D-02: Kanban làm sổ cái là quyết định đúng.

Hai thứ **không** đậu, đã tách thành ticket riêng: định vị theo message trong topic
([ADR 0002](../../architecture/decisions/0002-dinh-vi-trong-lark-va-va-adapter.md) và
[Vá adapter Feishu](0017-va-adapter-feishu-duong-card.md)), và rò rỉ xuyên topic qua
`session_search` ([ticket](0018-pham-vi-cua-session-search.md)).