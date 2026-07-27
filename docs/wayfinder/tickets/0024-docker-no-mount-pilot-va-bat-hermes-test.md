---
id: "0024"
title: Docker no-mount pilot và bật Hermes#Test
type: task
status: closed
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

## Resolution

Đã deploy `gonzo/deploy/hermes-config.yaml` vào pilot thật và chạy gateway bằng launchd trên
host. Agent core + Lark WS chạy trên Mac; `file`, `terminal` và `execute_code` dùng chung
Docker sandbox với `docker_mount_cwd_to_workspace: false`, `docker_volumes: []`, không
forward credential và `docker_network: false`.

Negative probes trên config deployed đều không đọc được raw sibling
`/Users/aigonzo/Company/gonzo-vault` qua cả ba đường file, terminal và execute-code. Raw
vault chưa được mount hoặc nối; đường production duy nhất vẫn là `vault-policy` read-only ở
ticket sau.

Lifecycle runtime cũng đạt contract. Lượt DM có tool calls tạo một container Hermes lúc
15:42:18; container được giữ trong cửa sổ idle 300 giây để tái sử dụng, rồi cleanup lúc
15:47:53. `docker ps -a --filter label=hermes-agent` sau cleanup trả về rỗng — không có
container rác.

Lark live proof trên app `Hermes#00`:

- Group `Hermes#Test` nhận cả message có @mention lẫn không @mention theo pilot config và
  trả lời end-to-end.
- DM ban đầu im lặng dù gateway/model/allowlist đều khỏe. Root cause là app Lark thiếu
  scope server-side `im:message.p2p_msg:readonly`; app khi đó chỉ nhận được group @mention
  qua `im:message.group_at_msg:readonly`.
- Sau khi grant scope P2P, publish/approve version và restart gateway, canary
  `DM-P2P-GREEN` đi trọn raw event → session
  `agent:main:feishu:dm:<chat_id>` → agent (6 API calls) → send response. Owner nhận được
  `Received DM-P2P-GREEN.` trong Lark.
- Docs Feishu đã ghi hai granular receive scopes và case “group chạy nhưng DM im lặng”.

Canary này chứng minh transport + sandbox deployment, **không** chứng minh Hermes đã tự chủ
hoặc biết dùng company truth. Thực tế response còn tự gọi `session_search`/file search cho
một ping đơn giản; mức chủ động và vault retrieval phải được test sau khi nối policy seam.

Giữ nguyên hai tripwire: chưa thêm user thứ hai; trước khi thêm entry thứ hai vào
`FEISHU_ALLOWED_USERS`, phải scope hoặc disable `session_search` vì hiện nó có thể đọc xuyên
topic/profile mà không lọc `user_id`.
