---
id: "0010"
title: schema-*.md của Kyperus đang chờ quyết gì
type: grilling
status: open
assignee: ""
blocked_by: []
---

## Question

`gonzo-vault/MIGRATION.md` ghi `brands/kyperus/`: *"CÒN TREO: schema-*.md (chờ quyết
pipeline Hermes)"*. Vault đang **chờ ta** quyết một thứ. Thứ đó là gì, và quyết nó cần
biết gì trước?

## Vì sao nó chặn

Đây là dependency đi ngược chiều so với mọi dependency khác trên map: mọi ticket khác là
runtime cần vault, ticket này là **vault cần runtime**. Migration khu 2 không đóng được
cho tới khi có câu trả lời, và migration khu 3–5 đứng sau nó trong hàng.

Nó cũng có khả năng chạm `mkt-creative`: nếu "schema" ở đây là schema của creative
output/deliverable, thì nó quyết luôn hình dạng cột của Lark Base (D-10) và bộ từ vựng
trạng thái của D-16.

## Bắt đầu ở đâu

Đọc `gonzo-vault/MIGRATION.md` và `gonzo-vault/brands/kyperus/` xem `schema-*.md` định là
những note nào. Nếu câu trả lời không nằm trong repo thì hỏi thẳng — đây là loại câu hỏi
`vault-approver` (Khánh) hoặc `marketing-lead` (Sơn) trả lời trong một phút, và đoán thì
sai cả tuần.
