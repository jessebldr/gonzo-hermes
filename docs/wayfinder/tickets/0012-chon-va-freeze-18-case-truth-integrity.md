---
id: "0012"
title: Chọn và freeze 18 case truth-integrity
type: task
status: open
assignee: ""
blocked_by: []
---

## Question

D-17① đòi truth-integrity suite được **viết, version-control và freeze TRƯỚC Gate 1** —
tối thiểu 18 case cố định. 18 case đó là gì?

## Vì sao nó chặn

Nó chặn Gate 1, tức chặn mọi thứ. Và lý do phải viết *trước* là lý do thật, không phải thủ
tục: *"viết sau khi thấy hệ chạy = viết test theo hệ"*. Một suite viết sau sẽ mô tả hệ
thay vì kiểm nó.

Đây cũng là lưới an toàn bù cho việc baseline fork lấy ở HEAD chứ không phải một release
tag đã qua QA ([ADR 0001](../../architecture/decisions/0001-fork-baseline-and-branch-model.md)).
Suite không có thì đánh đổi đó chỉ còn mặt trừ.

## Ràng buộc

- Nguồn **duy nhất**: luật trong `gonzo-vault/governance/`, đặc biệt `grounding-policy.md`
  và `roles.md`. **Không** đọc code hệ mới khi viết.
- Bảy nhóm phải phủ: cite đúng note approved · gặp open-question đang hiệu lực thì nói
  "chưa quyết" và **dừng** · không dùng `operational-state` quá `review_after` · không
  biến `evidence` thành company claim · không để tên nhân sự lọt vào output khách hàng ·
  `draft` không đè `approved` · không dùng `authority` để tự phân xử conflict.
- Mỗi case chạy **3 lần**. Ngưỡng **100%, zero critical failure** — invariant, không có
  "95% là ổn".
- Nhà: `gonzo/tests/truth_integrity/`.

## Vật liệu đã có sẵn

`gonzo-vault/decisions/open/` đã có **9 open question** thật (avatar-tier-percentage,
company-values, offer-and-promo-state, who-sourced-kyperus-pricing…) — dùng chúng cho
nhóm case "chưa quyết thì dừng", đừng dựng fixture giả.

Validator vault hiện chạy sạch (59 note, no errors), nên corpus dùng làm fixture là hợp lệ.
