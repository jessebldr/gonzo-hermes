---
id: "0012"
title: Chọn và freeze 18 case truth-integrity
type: task
status: closed
assignee: "tech-lead"
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

## Resolution

**21 case, đóng băng 2026-07-25** ở `gonzo/tests/truth_integrity/cases.yaml`, digest ghi ở
`FREEZE.md`. Phủ đủ 7 nhóm bắt buộc, cộng 4 nhóm nữa mà `grounding-policy.md` đòi và D-17①
không liệt kê hết: the floor · authority-5 gate · registry `UNVERIFIED` · `outputs/` bị loại
khỏi grounding.

**Quyết định thiết kế: case khai báo *hình dạng vault*, không trỏ file thật.** Vault đang nở
từ 59 lên ~690 note, nên một suite đóng băng mà hardcode path sẽ vỡ vì corpus lớn lên — vỡ vì
lý do không liên quan tới thứ nó canh. Vật chất hoá `given` là việc của Gate 3 →
[Vật chất hoá `given` và adapter cho truth suite](0016-vat-chat-hoa-given-va-adapter-cho-truth-suite.md).

**Hai tầng.** Tầng A chạy hôm nay: 34 test cấu trúc, **34/34 xanh, 0 skip**. Trong đó 21 là
*wire check* — mỗi case trích một câu luật nguyên văn và test xác nhận câu đó vẫn còn trong
file governance nó viện dẫn. Đã kiểm chứng không xanh rỗng: đổi một chữ trong câu trích thì
test đỏ. Sửa luật vault mà quên sửa case → suite đỏ, đúng regression D-17① đòi. Tầng B (chạy
thật qua agent, 3 lần/case, ngưỡng 100%) là việc của Gate 3.

**Sáu case là bài kiểm tra "cấm quá tay"** — bắt agent *phải dùng* thứ nó được phép dùng
(evidence làm tiếng nói khách hàng, tên người trong provenance nội bộ, state stale có nhãn,
draft có nhãn, supersession được phép resolve, state note thắng fact của chính nó). Một suite
toàn case cấm sẽ dạy agent im lặng thay vì dạy nó đúng, và hỏng kiểu đó không ai báo.

**Phát hiện phụ:** vault hôm nay **không có note stale nào** — cả hai `operational-state` đều
`freshness: event-driven`, mà loại đó theo `freshness-policy.md` **không có** `review_after`.
Nên nhóm case stale chưa có fixture thật; đã ghi vào ticket 0016.
