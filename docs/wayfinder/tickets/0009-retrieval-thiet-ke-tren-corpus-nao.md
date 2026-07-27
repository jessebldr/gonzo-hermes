---
id: "0009"
title: Retrieval thiết kế trên corpus nào
type: grilling
status: open
assignee: "codex"
blocked_by: []
---

## Question

Vault hôm nay có **59 note**. `MIGRATION.md` cho thấy còn 3 khu chưa bắt đầu:
`intel/kyperus/`, `marketing/canon/` (~178 note), `domains/billiards/` (~449 note) —
tức corpus đích khoảng **~690 note, gấp hơn 10 lần**. Thiết kế và tune retrieval (D-04)
trên corpus nào?

## Vì sao nó chặn

Gate 3 nghiệm thu bằng "agent trả lời có cite đúng note" — kết quả đó phụ thuộc corpus.
Tune symbolic-trước-semantic, BM25, và ngưỡng rerank trên 59 note rồi gặp 690 note là đúng
loại việc vỡ khi scale, và vỡ **sau khi** đã đậu gate.

Hai chi tiết làm nó gai hơn:

- **`domains/billiards/` (~449 note) là bulk-copy, không duyệt từng note** — đó là quyết
  định đã ghi trong `MIGRATION.md`. Vậy 449 note đó mang `status` gì, và `use_class` của
  chúng ra sao khi qua read contract (D-04a)? Nếu chúng vào thẳng `approved` thì hai phần
  ba vault là tri thức chưa ai đọc.
- `brands/kyperus/` còn treo `schema-*.md` **chờ quyết pipeline Hermes** — xem ticket
  [schema-*.md của Kyperus đang chờ quyết gì](0010-schema-md-cua-kyperus-dang-cho-quyet-gi.md).

## Phải chốt được

1. Gate 3 chạy trên corpus nào — 59 note hiện tại, hay chờ migrate xong?
2. Nếu chạy sớm: cái gì trong thiết kế retrieval **không được** phụ thuộc kích thước
   corpus, và cái gì phải tune lại sau migration (và ai nhớ làm việc đó)?
3. 449 note billiards vào vault ở `status` nào, và `use_class` tương ứng.
