---
id: "0013"
title: Cost cap per-profile ở 9router
type: research
status: closed
assignee: "tech-lead"
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

## Resolution

**Không. 9router không enforce được cost cap** — nó chỉ tracking.

Grep toàn bộ package: mọi hit `quota`/`rate_limit` đều là dashboard "Quota Tracker" (quan
sát), hiển thị free-tier quota của provider, hoặc map lỗi upstream `403 insufficient_quota` /
`429 rate_limit_exceeded` sang mã OpenAI. Không có route hay schema nào để **đặt** cap.

Cap thật đang nằm ở **goclaw** (`migrations/000071_usage_cap_policies`, `usage_caps.go`,
ba bảng, 77 tham chiếu tổng) — tức **hệ cũ có năng lực mà hệ mới không có**, và cutover sẽ
làm mất nó.

Doc §9 sai ở chỗ này → [Sửa ba chỗ sai trong doc](0020-sua-ba-cho-sai-trong-doc-kien-truc.md).
Câu hỏi "vậy cap sống ở đâu" → [Chỗ ở của cost-cap enforcement](0019-cho-o-cua-cost-cap-enforcement.md).

Thông tin kèm theo, đã xác minh: 9router = npm `9router@0.5.40` bọc CLIProxyAPI, endpoint
`http://localhost:20128/v1`, OpenAI-compatible, **không đòi auth**, 166 model.