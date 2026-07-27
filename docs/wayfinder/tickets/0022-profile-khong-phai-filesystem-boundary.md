---
id: "0022"
title: Profile không phải filesystem boundary
type: prototype
status: closed
assignee: "codex"
blocked_by: []
---

## Question

Profile/process của Hermes có ngăn personal agent đọc raw `gonzo-vault` và filesystem của
profile khác không? Nếu không, boundary nhỏ nhất nào pass bằng runtime evidence?

## Resolution

Local backend fail: model đọc được absolute host path và raw sibling vault. Profile chỉ
tách state trong `HERMES_HOME`.

Docker no-mount pass các negative probe host canary, raw vault và cross-profile workspace.
Profile memory A/B cũng tách đúng: A recall preference nonce, B trả `UNKNOWN`.

Giữ kết luận tại [ADR 0003](../../architecture/decisions/0003-hybrid-personal-agents-va-filesystem-boundary.md)
và runner throwaway tại
[`gonzo/prototypes/filesystem_boundary_probe.py`](../../../gonzo/prototypes/filesystem_boundary_probe.py).

Một bug lifecycle riêng được tách thành ticket
[`File-tools làm rơi Docker lifecycle config`](0023-file-tools-lam-roi-docker-lifecycle-config.md).
