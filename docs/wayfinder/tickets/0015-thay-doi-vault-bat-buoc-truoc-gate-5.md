---
id: "0015"
title: Thay đổi vault bắt buộc trước Gate 5
type: task
status: open
assignee: ""
blocked_by: ["0006"]
---

## Question

Ba thay đổi luật vault phải xong trước Gate 5. Soạn chúng, đưa qua `vault-approver`, và
ghi thành decision record.

## Ba thay đổi

1. **`governance/grounding-policy.md`** — đổi *"it becomes doctrine only when a human
   writes it"* → *"when a human originates, materially edits, or explicitly adopts it as
   doctrine"*, kèm định nghĩa adoption event (D-13).
2. **`company/approval-authority.md`** — thêm cột path để bảng delegation join được bằng
   máy (kết quả của [Domain của một note được tính thế nào](0006-domain-cua-mot-note-duoc-tinh-the-nao.md)).
3. **`decisions/records/2026-07-25-agent-team-architecture.md`** — đang `status: draft`,
   chờ adoption event. Đưa nó qua cổng.

## Vì sao bị chặn

Thay đổi ②ban đầu chưa biết hình dạng — nó là output của ticket domain. Gộp cả ba vào một
vòng vì chúng đi qua cùng một người và cùng một decision record; tách ra là bắt
`vault-approver` duyệt ba lần cho một quyết định.

## Ràng buộc

Đây là **sửa luật vault**, nên phải đi qua chính `vault-approver` + một decision record —
**không sửa lén trong lúc build**. Và lưu ý
`decisions/records/2026-07-24-single-approval-gate.md` là immutable và nói "no
auto-approval for anyone": vòng này **không** phá điều đó, nó chỉ tách *ai quyết nội dung*
khỏi *ai đổi status*.
