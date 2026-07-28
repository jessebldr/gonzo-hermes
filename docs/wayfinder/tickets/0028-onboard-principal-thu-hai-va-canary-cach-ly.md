---
id: "0028"
title: Onboard principal thứ hai và chạy canary cách ly thật
type: task
status: open
assignee: ""
blocked_by: []
---

## Question

Onboard Sơn vào bot Lark thật bằng stable Feishu `union_id`, route DM của Sơn về profile
`son`, rồi chứng minh hai principal không đọc được session/memory riêng của nhau trước khi
mở pilot cho team.

## Vì sao đây là gate vận hành

[ADR 0003](../../architecture/decisions/0003-hybrid-personal-agents-va-filesystem-boundary.md)
đã chốt profile/state isolation bằng test và canary một principal, nhưng nói rõ không được
suy phép thử hai người từ một người tự đổi topic. Ticket
[Phạm vi của session_search](0018-pham-vi-cua-session-search.md) đã sửa search boundary,
nhưng cố ý không thêm người thứ hai vào allowlist.

## Trình tự bắt buộc

1. Sơn DM bot một canary vô hại để adapter log đủ `user_id` + stable `union_id`; không lấy
   open ID làm principal nếu union ID có mặt.
2. Thêm đúng union ID đó vào private runtime map và `FEISHU_ALLOWED_USERS`; không ghi ID
   người thật vào repo.
3. Route DM principal đó về named profile `son`; không clone session/memory của `default`.
4. Restart gateway và prove route từ adapter event → profile home → session namespace.
5. Khánh và Sơn mỗi người lưu một nonce riêng qua DM, `/new`, rồi recall nonce của mình.
6. Negative canary: mỗi người hỏi nonce của người kia; phải `NOT_FOUND` qua session search,
   memory và vault-policy không được biến task marker thành company truth.
7. Group `Hermes#Test` vẫn route `default`; shared work group vẫn route `shared-task`.

## Tiêu chí đóng

- Hai DM cùng một bot đi vào hai profile/session DB/memory namespace khác nhau.
- Same-principal recall qua session mới vẫn hoạt động cho cả Khánh và Sơn.
- Cross-principal search/recall fail closed bằng log + transcript thật.
- Không secret/identity literal nào vào git; private map mode vẫn `0600`.
- Gateway restart không làm đổi route hoặc mất memory đã được approve.
