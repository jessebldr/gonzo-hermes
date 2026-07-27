# `kanban_bus` — kênh phối hợp durable giữa task owner và specialists

Quyết định chi phối: **D-02** (Kanban là xương sống điều phối), **D-03** và ADR 0003.
Workstream ②. Gate 2.

Delegation nền của Hermes không sống qua restart; Kanban (SQLite, worker lanes, reviewer
gate) thì có. Quy tắc: **việc bền = thẻ Kanban có assignee**; delegation chỉ dùng fan-out
ngắn trong một phiên chat đang sống.

Personal/shared task profiles và specialists dùng chung một Kanban durable làm bus — task,
dependency, comment, block, structured handoff. **Không shared context, không shared memory
trực tiếp.**

## `team_ask`

Wrapper để agent A hỏi agent B: tạo một **child task**, chờ kết quả hoặc đi tiếp async.
Hỏi nhau là một thẻ, không phải một lời nhắn trong context chung.

## Bất biến

- **Kanban là sổ nội bộ của agents, không phải giao diện duyệt của người.** Fresh reviewer
  gate ở boundary factual/public/irreversible. Người thật duyệt ở card Lark và adoption
  flow của vault.
- **Kanban subtask KHÔNG tạo thêm Lark session riêng** (D-07): 1 topic = 1 session
  task owner + N subtask.
- **Backup là tiêu chí đậu Gate 2, không phải tuỳ chọn** — từ Gate 2 nó đã là sổ cái thật.
  Dùng SQLite online backup API hoặc `VACUUM INTO` (**không** copy file DB đang chạy),
  ≥1 bản **off-device**, có retention + **restore test tự động**. Schema/config git-track ở
  repo này; dữ liệu backup không chứa secret. Xem `gonzo/deploy/`.
- Cron cho việc định kỳ, và **mỗi cron job chạy trong một profile cụ thể** (fresh session):
  intel → research specialist, vault hygiene → reviewer specialist.

## Nền tảng có sẵn

Hermes upstream đã có Kanban: `tools/kanban_tools.py`, `hermes_cli/kanban_db.py`,
`hermes_cli/kanban.py`, `gateway/kanban_watchers.py`, `plugins/kanban`. Việc ở đây phần lớn
là wrap + dispatcher + `team_ask`, không phải viết Kanban mới.

Trạng thái: **stub.**
