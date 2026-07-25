---
id: "0011"
title: 24 task benchmark và cách chạy baseline trên goclaw
type: task
status: open
assignee: ""
blocked_by: []
---

## Question

D-17② đòi **24 task thật** (8 research · 8 creative · 8 review/claim-check) chọn trước từ
lịch sử, và **chạy hệ cũ để lưu baseline ở Gate 2** — trước khi hệ mới hoàn thiện. Hệ cũ
là gì, chạy nó thế nào, và 24 task đó là những task nào?

## Vì sao nó chặn

Doc nói thẳng lý do phải làm sớm: *"nếu không thì tới lúc so đã không còn gì để so, và
người so thì đã bỏ 6 tầng công sức vào một bên."* Đây là cửa sổ **đóng lại theo thời
gian** — mọi ticket khác chờ được, ticket này thì không.

## Cái đã biết

Hệ cũ là **goclaw**, workspace sống ở `~/Company/gonzo-brands` (theo
`gonzo-vault/MIGRATION.md`: *"Repo cũ là workspace SỐNG của goclaw production"*). Nó dựa
trên Claude Code (`.claude/`), và có sẵn `media-producer-*`, `goclaw-runtime-auditor`,
`cron/`, `functions/`.

## Việc cụ thể

1. Chốt 24 task: lấy từ lịch sử thật, không bịa. Cân đủ 8/8/8.
2. Chạy chúng trên goclaw, **lưu output nguyên văn** + ngày chạy + cấu hình. Đây là
   baseline, nó phải bất biến.
3. Ghi lại **cách chạy** goclaw đủ chi tiết để lặp lại được sau 3 tháng — D-18 giữ legacy
   chạy thêm 4 tuần sau cutover và cần một routing flag kéo task về nó.
4. Chấm là việc của người (`marketing-lead` chấm mù, `company-lead` spot-check) — ticket
   này chỉ chuẩn bị vật liệu, không chấm.
