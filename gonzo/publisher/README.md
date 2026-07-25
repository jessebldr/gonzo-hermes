# `publisher` — service duy nhất được ghi field `status`

Quyết định chi phối: **D-05** (tách khỏi draft-writer), **D-13** (human-originated hoặc
explicitly adopted), **D-14** (6 điều kiện callback). Workstream ⑤. Gate 5.

Publisher **thực thi** quyết định của domain approver. Nó không phải người quyết.

## Promote là thao tác tại chỗ

Không move, không rename — giữ nguyên path ⇒ không vỡ relative link nào, kể cả các link
`## Based on` đang trỏ tới chính nó. Trình tự: đối chiếu `content_hash` của bản người đã
duyệt trên card với file trên đĩa → thêm `approved_by` + `approved_at` (+ `supersedes` nếu
có) → chạy `tools/validate_vault.py` của vault → git commit.

## Promote khi và chỉ khi callback thoả **toàn bộ** 6 điều kiện (D-14)

①event/chữ ký hợp lệ từ Lark ②`card_id` + token khớp bản ghi ③`content_hash` của file
trên đĩa chưa đổi ④button đúng là `Adopt as doctrine` ⑤`user_id` map được sang role có
quyền **trong domain của note đó** ⑥token chưa dùng và chưa hết hạn.

Thiếu một điều kiện → từ chối, ghi log, báo lại người duyệt. Hash lệch → **không tự
promote**. Reject → note ở lại `draft` kèm lý do.

## Hai chữ ký, hai vai

`vault-approver` (Khánh) là cổng kỹ thuật duy nhất đổi `status`, nhưng **không** phải
người quyết nội dung của mọi domain. Thẩm quyền nội dung phân tán theo domain — bảng
delegation sống ở `company/approval-authority.md` trong vault. Mapping
`lark_user_id → role/domain` sống trong **runtime config của publisher**, không vào vault
(`company/team.md` cấm platform ID trong vault). Hai bảng, join bằng role word.

## Test âm bắt buộc ở Gate 5 — mỗi cái phải **từ chối + log**

①callback giả mạo/không chữ ký ②đúng card nhưng sai `user_id` (không có quyền trong domain)
③hash stale — draft bị sửa sau khi card được tạo ④replay: bấm lại token đã dùng
⑤token hết hạn ⑥"ok"/emoji/card thiếu normalized rule.

Trạng thái: **stub.**
