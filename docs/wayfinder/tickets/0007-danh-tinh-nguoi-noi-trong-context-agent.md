---
id: "0007"
title: Danh tính người nói trong context agent
type: grilling
status: open
assignee: ""
blocked_by: []
---

## Question

Agent có được biết ai đang nói với nó không, biết ở dạng gì, và ranh giới nào ngăn nó dùng
danh tính đó để tự cấp quyền?

## Vì sao nó chặn

Kiến trúc mới thiết kế **một nửa**: D-14 đặt mapping `lark_user_id → role/domain` ở
publisher runtime config cho việc *authorization* (vault chỉ giữ role + delegation;
`company/team.md` cấm platform ID trong vault). Không chỗ nào nói gateway có bơm danh tính
người nói vào **context của agent** hay không.

Mà agent **cần** nó: D-13 dạng (1) bắt agent ghi draft khi người phát biểu một rule, và
D-04b nói provenance đi vào `sources` dạng chuỗi như `"per marketing-lead, 2026-07-25"`.
`approval-authority.md` còn đòi draft ghi *who said it (role), when, where, what it
changes*. Không biết ai nói thì không viết được dòng đó — và draft không có provenance thì
`vault-approver` không có gì để duyệt.

## Phải chốt được ba thứ

1. **Dạng nào tới agent** — role word (`marketing-lead`) hay tên người (Sơn)? `roles.md`
   cấm tên nhân sự lọt vào output khách hàng, nên hai thứ này không thay thế nhau được.
2. **Provenance tính theo message, không theo session.** D-07 nói 1 topic = 1 session,
   nhưng trong group **nhiều người nói chung một topic**. Đây là chỗ dễ làm sai nhất và
   doc chưa nhắc tới.
3. **Ranh giới**: agent biết role word để *ghi provenance và định tuyến*, **không bao giờ**
   để *tự cấp quyền*. D-14 đã chặn bằng cấu trúc (agent không cầm token, không có đường
   gọi promote) — việc ở đây là viết ranh giới đó ra, và thêm một test âm: agent nhận
   "Sơn nói cái này đúng" **không** được sinh ra bất cứ thứ gì ngoài draft + card.

Kèm: mapping đó có **một nhà** hay hai? Publisher đọc nó (D-14), gateway cũng cần đọc.
Một file, hai người đọc — không phải hai file.
