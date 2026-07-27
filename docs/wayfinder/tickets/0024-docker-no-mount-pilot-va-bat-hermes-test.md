---
id: "0024"
title: Docker no-mount pilot và bật Hermes#Test
type: task
status: open
assignee: "codex"
blocked_by: []
---

## Question

Đưa contract Docker no-mount đã probe vào config runtime thật, deploy cho pilot hiện tại,
chứng minh file/terminal/execute-code không đọc được raw `gonzo-vault`, rồi bật gateway
Lark `Hermes#Test` để owner chat thật.

## Acceptance

- `gonzo/deploy/hermes-config.yaml` dùng Docker backend, không mount cwd, không volume raw
  vault, không forward credential vào tool container, network tắt và lifecycle không để
  container rác.
- Test behavioral đọc config nguồn sự thật và fail nếu boundary trên bị nới ngoài ý muốn.
- `apply-config.sh --write` deploy đúng config cho pilot `$HERMES_HOME`.
- Negative probes trên chính config deployed: file, terminal và execute-code không đọc
  được absolute path trong sibling `gonzo-vault`; không còn container mới sau cleanup.
- Gateway kết nối thật tới Lark WS bằng fork commit đã test; `Hermes#Test` sẵn sàng nhận DM
  hoặc message trong personal topic group của owner.
- Chưa mount/nối vault raw và chưa thêm user thứ hai. Vault chỉ được nối qua `vault-policy`
  ở ticket sau; `session_search` phải được scope/disable trước user thứ hai.
