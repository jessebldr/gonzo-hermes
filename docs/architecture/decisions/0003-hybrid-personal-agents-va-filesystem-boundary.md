# 0003 — Hybrid personal agents, specialist escalation và filesystem boundary

- **Ngày:** 2026-07-27
- **Trạng thái:** accepted
- **Thay đổi:** D-01, D-03; bổ sung điều kiện trước Gate 2/3
- **Người quyết:** `tech-lead` (Khánh)

## Bối cảnh

Thiết kế cũ chọn bốn functional profile cố định (`orchestrator`, `research`, `creative`,
`reviewer`) và coi process-per-profile là isolation boundary. Hai tiền đề đó đến từ đọc
code và suy luận kiến trúc, chưa chạy vertical slice.

Mục tiêu thật rộng hơn marketing pipeline: mỗi người cần một personal agent tự học riêng,
nhưng task khó vẫn cần specialist và independent review. Lark chỉ là cửa vào; DM hoặc một
group topic-mode chỉ có người đó + bot phải dùng được như personal workspace có context
được chia theo topic.

## Bằng chứng runtime

### 1. Hermes có agency đủ để làm default end-to-end

Prompt thật: *“Biên lợi nhuận Kyperus tháng này là bao nhiêu?”* trên fork hiện tại qua
`ag/gemini-3.6-flash-high`/9router.

Hermes không bịa số; tự kiểm dữ liệu, xác định thiếu revenue/COGS/ad spend/fees, đề xuất
Shopify + ads + payment/accounting connectors và minimum read-only permissions. Lượt chạy
dùng 5 API calls, 10 tool calls. Như vậy specialist pipeline cố định cho mọi task sẽ lặp
lại khả năng agent gốc đã có.

### 2. Profile memory tách thật ở tầng state

Profile A dùng `memory` lưu preference nonce `FORMAT-PINE-7C92`. Session mới của A recall
đúng; profile B cùng model/config trả `UNKNOWN`. Trên đĩa, nonce chỉ tồn tại trong
`personal-a/memories/USER.md`; B không có `USER.md`. State DB cũng tách: A có tool call
`memory`, B không có.

### 3. Profile/process không phải filesystem sandbox

Local backend cho model dùng raw `search_files`/`read_file` đi từ repo sang sibling
`gonzo-vault` và đọc nội dung note thật. Tài liệu upstream cũng nói profile chỉ tách
`HERMES_HOME`; local tools có toàn bộ quyền filesystem của Unix user.

Prototype [`gonzo/prototypes/filesystem_boundary_probe.py`](../../../gonzo/prototypes/filesystem_boundary_probe.py)
đã chạy control + negative probes:

- local đọc được absolute host canary;
- Docker với `docker_mount_cwd_to_workspace: false`, `docker_volumes: []` không đọc được
  canary host hoặc raw `gonzo-vault`;
- khi profile A còn sống và có `/workspace/profile-a-only.txt`, profile B không đọc được;
- model end-to-end gọi `read_file` thật ở cả hai lượt: local trả content, Docker trả
  `File not found`.

Docker inspect chỉ thấy skills directory của đúng profile mount read-only; không mount
repo, sibling repo hoặc raw vault.

Prototype cũng tìm thấy bug lifecycle riêng: file-tools từng không honor
`docker_persist_across_processes: false`. Follow-up đã gom ba đường terminal/file/
`execute_code` về một container-config contract và runtime probe nay pass 7/7, gồm teardown
không còn container. Bằng chứng tại ticket
[`File-tools làm rơi Docker lifecycle config`](../../wayfinder/tickets/0023-file-tools-lam-roi-docker-lifecycle-config.md).

### 4. Lark topic là session boundary dùng được

ADR 0002 đã chứng minh hai topic sinh hai session độc lập. Lark Topic-mode không có
`parent_id` riêng cho từng message, nên deliverable-level addressing phải dùng card button
`card_id`/payload. Kết quả này phù hợp với personal workspace: một group riêng có nhiều
topic, mỗi topic là một task/context.

## Quyết định

### 1. Topology hybrid, không ép mọi task qua bốn vai

- **Một người = một personal profile.** Profile sở hữu memory, USER, skills, session và
  preference của người đó.
- Personal agent **tự làm end-to-end mặc định**. Nó escalation sang specialist khi cần
  chuyên môn sâu, parallelism, credential khác hoặc independent review.
- `research`, `creative`, `reviewer` là **specialist profiles dùng chung**, không phải ba
  cửa bắt buộc của mọi task.
- Shared group/topic thuộc về **công việc**, không thuộc người đang nói. Nó dùng shared
  task profile/session; không route sang personal profile theo speaker.

### 2. Một Lark bot là front door mặc định

- DM và personal workspace (group chỉ có owner + bot) route về cùng personal profile.
- Mỗi topic trong personal workspace là một task/session riêng nhưng dùng chung memory và
  skills của owner.
- Shared work group/topic route về shared task profile.
- Specialist escalation đi qua coordination bus; không đặt 8 bot functional vào group.

Personal profiles có thể multiplex trong một gateway **chỉ khi cùng trust domain**. Đây
là lựa chọn vận hành, không phải security boundary. Specialist profile có credential hoặc
quyền khác chạy process riêng để giới hạn crash/credential/audit domain.

### 3. Filesystem boundary là Docker no-mount, không phải process

Mọi profile production có raw file/terminal tools phải chạy trong execution sandbox:

- `terminal.backend: docker`;
- `docker_mount_cwd_to_workspace: false` mặc định;
- `docker_volumes` là allowlist tối thiểu, không bao giờ mount raw `gonzo-vault`;
- raw vault chỉ đi qua `vault-policy` service/MCP với read contract `use_class`;
- credential chỉ forward theo allowlist của đúng specialist;
- negative probe host-vault và cross-profile phải pass trước Gate 2/3.

Process separation vẫn có giá trị cho crash domain, resource cap, credential và audit,
nhưng **không được dùng làm bằng chứng data isolation** nếu các process cùng Unix user hoặc
cùng host mounts.

### 4. Independent review là boundary-driven

Personal agent tự review trong vùng bình thường. Fresh reviewer bắt buộc trước:

- factual claim ra customer/public;
- thay đổi vault truth/doctrine;
- hành động khó đảo ngược hoặc đụng tiền/quyền.

Người vẫn là approval cuối ở những biên đã định. Không thêm reviewer chỉ để tạo cảm giác
“nhiều agent hơn”.

### 5. Knowledge sharing phải đi qua artifact đúng loại

- preference cá nhân → personal memory;
- procedure tái dùng → shared-skill draft, promote nhẹ;
- company fact/rule → vault draft + approval;
- task-only context → Kanban/Base;
- không copy memory live từ người A sang người B.

## Điều kiện an toàn còn mở

Tripwire `session_search` đã được giải ngày 2026-07-28: DM recall chỉ cùng
platform/profile/principal; group/topic chỉ exact `chat_id + thread_id`; messaging runtime
không còn model-controlled cross-profile search. Canary một principal + hai topic đã pass.

Trước khi thêm người thứ hai vào `FEISHU_ALLOWED_USERS`, phần còn lại là deploy hai named
profiles, route DM bằng stable principal ID và chạy negative canary **hai principal thật**.
Không được suy canary này từ unit test hoặc từ một người tự đổi topic.

## Hệ quả

- D-01 “4 vai, không nhiều hơn” bị supersede bằng personal-first + specialist escalation.
- D-03 “process-per-profile là isolation boundary” bị supersede. Process topology và
  security topology là hai quyết định khác nhau.
- Gate 2 phải chứng minh hai personal profiles + shared specialist, memory/session
  isolation và Docker negative probes; không cần dựng pipeline bốn vai trước khi một
  personal agent làm được vertical slice hữu ích.
- Vault-policy không chỉ là quality layer; nó là **đường duy nhất** agent được thấy raw
  company truth khi raw vault đã bị loại khỏi filesystem mounts.
