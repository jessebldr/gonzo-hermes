---
id: "0019"
title: Chỗ ở của cost-cap enforcement
type: grilling
status: open
assignee: ""
blocked_by: []
---

## Question

9router **không** enforce cost cap. Vậy cap sống ở đâu?

## Bằng chứng

Grep toàn bộ `/opt/homebrew/lib/node_modules/9router`: các hit `quota`/`rate_limit` đều là
①dashboard **"Quota Tracker"** (quan sát) ②hiển thị `freeMonthlyQuota` free-tier của provider
③map lỗi upstream `403 insufficient_quota` / `429 rate_limit_exceeded` sang mã OpenAI.
**Không có route hay schema nào để *đặt* cap.**

Cap thật đang nằm ở **goclaw**: `external/goclaw/migrations/000071_usage_cap_policies.up.sql`,
`internal/store/pg/usage_caps.go`, ba bảng `usage_cap_policies` (47 tham chiếu) ·
`usage_cap_counters` (18) · `usage_cap_events` (12).

## Vì sao quan trọng

Doc §9 viết *"cap thực thi được **ở 9router**"* — **sai**. Hermes chỉ tracking, 9router chỉ
tracking. Nghĩa là **hệ cũ có năng lực mà hệ mới đang không có**, và cutover theo D-18 sẽ
làm **mất** nó mà không ai nhận ra, vì doc ghi là 9router lo.

Một `mkt-research` chạy cron intel hằng ngày mà loop là thứ tiêu tiền im lặng.

## Ứng viên

Một budget gate trong `gonzo/` ngay **trước** lời gọi model — đó là chỗ duy nhất biết profile
nào đang gọi. D-03 cho mỗi profile một credential riêng, nên gate ở đó cũng là chỗ duy nhất
gắn được chi phí với profile.

Cần chốt: tự viết trong `gonzo/`, port cách của goclaw, hay chấp nhận chỉ tracking ở phase 1
(và nếu vậy thì ghi rõ đó là năng lực **bị mất** khi cutover, không phải bỏ sót).
