---
id: "0005"
title: Kanban và topic↔session của Hermes có đúng docs không
type: prototype
status: open
assignee: ""
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
