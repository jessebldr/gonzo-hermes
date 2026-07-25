---
id: "0013"
title: Cost cap per-profile ở 9router
type: research
status: open
assignee: ""
blocked_by: []
---

## Question

Hermes chỉ **tracking** chi phí, không enforce. 9router (provider production) có enforce
được cap **theo từng profile** không, và cấu hình thế nào?

## Vì sao nó chặn

§9 để ngỏ và hẹn "chốt cấu hình ở Gate 1". Sau D-03 thì 4 profile là 4 process với
credential riêng — nếu cap enforce được ở 9router theo credential thì nó rơi đúng vào
thiết kế sẵn có, không cần thêm gì. Nếu không, phương án thay thế là script cảnh báo, mà
doc đã nói rõ cảnh báo **không phải** enforcement.

Một `mkt-research` chạy cron intel hàng ngày mà loop là thứ tiêu tiền im lặng.

## Việc cụ thể

Cấu hình 9router qua `custom_providers` là đường production đã chốt (Gate 1). Xác minh:
cap theo key/credential có tồn tại không · granularity tới đâu · hành vi khi chạm cap (từ
chối, hay degrade) · agent nhìn thấy gì khi bị từ chối.

Antigravity **không** thuộc ticket này — doc đã đẩy nó ra khỏi đường tới hạn, đánh giá lại
sau Gate 6.
