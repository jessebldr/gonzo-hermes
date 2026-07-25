---
id: "0016"
title: Vật chất hoá `given` và adapter cho truth suite
type: grilling
status: open
assignee: ""
blocked_by: ["0009"]
---

## Question

21 case trong `gonzo/tests/truth_integrity/cases.yaml` khai báo **hình dạng vault** chúng
cần (`given`), không trỏ file. Gate 3 phải biến mỗi `given` thành một vault chạy được, và
phải có một adapter để gọi agent-under-test. Hai thứ đó trông thế nào?

## Vì sao bị chặn

Câu trả lời phụ thuộc quyết định corpus — xem
[Retrieval thiết kế trên corpus nào](0009-retrieval-thiet-ke-tren-corpus-nao.md). Chạy suite
trên vault thật hay trên fixture là hai thiết kế khác nhau, và chọn sai thì hoặc suite vỡ khi
vault nở lên ~690 note, hoặc suite kiểm một thứ không phải vault thật.

## Ràng buộc đã biết

- **Ba hình dạng chưa tồn tại trong vault thật**, nên riêng chúng buộc phải có fixture:
  ①một `operational-state` stale — hiện cả hai note state đều `event-driven`, mà loại đó
  theo `freshness-policy.md` **không có** `review_after`, nên không note nào stale được
  ②hai note approved mâu thuẫn thật, không có quan hệ supersede ③một `registry` có dòng
  `UNVERIFIED`.
- Fixture nào cũng phải **pass `tools/validate_vault.py`** — fixture sai schema thì nó đang
  kiểm một vault không tồn tại.
- Adapter phải để **`skip` thành ồn**: hiện 21 wire check skip lặng khi không thấy vault.
  Khi adapter đã cấu hình thì **không case nào được phép skip** — cần một test canh chính
  điều đó, nếu không một suite "100% pass" có thể là 100% của con số không.

## Ràng buộc không được phá

`cases.yaml` **đã đóng băng** (`FREEZE.md`). Ticket này làm cách *chạy* chúng, không sửa
*nội dung* chúng. Cần sửa case thì phải qua đường của FREEZE.md — cập nhật digest, ghi lý do
vào bảng lịch sử — và nếu lý do là luật vault đổi thì luật đó phải đổi qua `vault-approver`
+ một decision record trước.
