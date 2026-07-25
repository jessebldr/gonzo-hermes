---
id: "0002"
title: Repo topology — hai repo hay ba
type: grilling
status: closed
assignee: "Khánh"
blocked_by: []
---

## Question

`gonzo-hermes` là fork của `NousResearch/hermes-agent`. Code công ty (vault-policy,
publisher, broker, scanner) sống ở đâu — trong fork, hay một repo `gonzo-runtime` riêng?

## Resolution

**Hai repo, không có repo thứ ba.** `gonzo-vault` giữ truth (P1); `gonzo-hermes` **là**
runtime chính thức (D-19). Repo thứ ba sẽ phải giữ hai tag khớp nhau mỗi lần deploy và làm
sống lại đúng rủi ro #7 ("implementation phân mảnh") mà D-19 sinh ra để chống.

Rủi ro thật của một repo là merge upstream đau — giải bằng **layout**: mọi code công ty
nằm dưới `gonzo/`, thư mục upstream không bao giờ có, nên không conflict được. Tám thư mục
1:1 với 7 workstream của D-21. Danh sách "upstream files đã sửa" giữ trong
[`gonzo/README.md`](../../../gonzo/README.md) — hiện có đúng 1 dòng (`pyproject.toml`).

Bằng chứng ủng hộ: phần lớn hạ tầng đã có sẵn trong fork — `plugins/platforms/feishu`
(+17 file test), `tools/kanban_tools.py`, `hermes_cli/kanban_db.py`,
`gateway/profile_routing.py`. Việc chủ yếu là config + wrap + vá, không phải viết mới.
