---
id: "0006"
title: Domain của một note được tính thế nào
type: grilling
status: open
assignee: ""
blocked_by: []
---

## Question

D-14 điều kiện ⑤ đòi publisher kiểm `user_id` map được sang role có quyền **trong domain
của note đó**. Publisher lấy domain của một note ở đâu ra?

## Vì sao nó chặn

Hiện tại **không lấy được** — điều kiện ⑤ không implement được như đang viết:

- `KNOWN_KEYS` trong `gonzo-vault/tools/validate_vault.py` **không có key `domain`**. Có
  `brand`; có `scope` (enum `vault·company·brand·domain`) nhưng nó nói *bán kính ảnh
  hưởng*, không nói *domain nào*.
- Bảng delegation trong `company/approval-authority.md` là **văn xuôi**: "Marketing, ads,
  creative, customer research, e-commerce execution".

Máy không join được "note này nói về ads" → `marketing-lead`. Thiếu cái này thì Gate 5
không có test âm ② ("đúng card nhưng sai `user_id`") để mà chạy.

## Hướng đề xuất — bác được thì bác

**Suy domain từ path**, không thêm key frontmatter (giữ nguyên D-04b): vault đã dùng path
làm ngữ nghĩa sẵn — `TYPE_HOME` ép folder theo `type`, và `domains/billiards/` đã tồn tại.
Đại khái `domains/<x>/` → `subject-matter-owner (<x>)` · `marketing/` + `brands/<b>/` →
`marketing-lead` · `company/` + `decisions/records/` → `company-lead` · `governance/` +
`tools/` → `vault-approver` · còn lại → dòng catch-all đã có sẵn.

Chỗ nó **phải** sống: một **cột path trong `approval-authority.md`**, file tự tuyên bố là
chỗ duy nhất ghi delegation. Nhét vào publisher runtime config = một fact hai nhà = đúng
con bug vault sinh ra để diệt.

Kiểm tra cùng lúc: cách này có sống được khi thêm domain mới (media, 3D) không — validator
đã nhận `subject-matter-owner (<bất kỳ>)` qua `SMO_RE`, nên phần role thì sống; phần path
cần một quy ước rõ.
