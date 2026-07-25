---
id: "0001"
title: Baseline fork và mô hình branch
type: grilling
status: closed
assignee: "tech-lead"
blocked_by: []
---

## Question

D-19 đòi chọn một commit/tag upstream làm baseline vì production chỉ chạy release tag của
fork. Chọn điểm nào, và fork tổ chức branch ra sao để cherry-pick upstream không thành
việc mất một tuần?

## Resolution

Baseline = upstream `main` @ `9823f15f6` (2026-07-25), đóng dấu bằng tag của ta:
`gonzo-baseline/2026-07-25`. **Không** chọn `v2026.7.20` — nó đã 1215 commit phía sau, và
hai fix approval mà D-09/D-14 phụ thuộc (`a31a31826`, `02d8cbade`) đáp **sau** tag đó.

Branch: `main` = gương upstream (không commit, chỉ fast-forward) · `gonzo/main` = nhánh
công ty · `gonzo/<tên>` = nhánh việc · `gonzo-v*` = release tag, production chỉ checkout
loại này. Upstream chỉ cherry-pick có chọn lọc, không auto-merge.

Chi tiết + phương án đã loại: [ADR 0001](../../architecture/decisions/0001-fork-baseline-and-branch-model.md).
