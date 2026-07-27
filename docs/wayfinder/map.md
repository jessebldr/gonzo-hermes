# Map — Triển khai agent team Hermes + gonzo-vault

<!-- wayfinder:map -->

Đích: đưa kiến trúc trong
[hermes-vault-agent-team-architecture.md](../architecture/hermes-vault-agent-team-architecture.md)
qua Gate 0→6, theo 7 workstream của D-21.

Frontier: `python3 docs/wayfinder/frontier.py` · Quy ước tracker:
[docs/agents/issue-tracker.md](../agents/issue-tracker.md)

## Notes

**Hai repo, cả hai đều cần đọc.** `gonzo-hermes` = runtime (fork của
`NousResearch/hermes-agent`, code công ty ở [`gonzo/`](../../gonzo/README.md)) ·
`gonzo-vault` = truth (Markdown + git, độc lập mọi runtime — P1). Hệ cũ đang chạy
production là **goclaw**, ở `~/Company/gonzo-brands`.

**Thiết kế đã approve — đừng grill lại.** D-01…D-21 đã qua một vòng grill (2026-07-25) và
ở trạng thái APPROVED-DESIGN. Map này chart cái **chưa quyết**, không mở lại cái đã quyết.
Muốn bác một D-xx thì bác thẳng bằng bằng chứng, đừng bác bằng sở thích.

**Skill nên gọi mỗi session:** `/grilling` và `/domain-modeling` cho ticket loại grilling ·
`/research` cho research · `/prototype` cho prototype · `/tdd` khi ticket đẻ ra code ·
`/code-review` trước khi merge.

**Standing preferences.**

- Viết bằng tiếng Việt, trừ code và commit message.
- **Bất biến phải thành test, không thành lời dặn.** Doc này gọi "gate bằng lời dặn" là
  phản mẫu — mọi ràng buộc chốt được thì chốt bằng một test âm.
- **Sửa luật vault đi qua `vault-approver` + một decision record.** Không sửa lén trong
  lúc build. Decision record của *runtime* thì ở `docs/architecture/decisions/`, không vào
  vault (P1).
- **Không patch tay ngoài repo**; mọi sửa đổi là một commit có test (D-19).
- Sửa file **ngoài** `gonzo/` thì ghi thêm một dòng vào bảng "Upstream files đã sửa" trong
  [`gonzo/README.md`](../../gonzo/README.md).

## Decisions so far

- [Baseline fork và mô hình branch](tickets/0001-baseline-fork-va-mo-hinh-branch.md) —
  baseline là upstream `main` @ `9823f15f6` (tag `gonzo-baseline/2026-07-25`), không phải
  `v2026.7.20`, vì hai fix approval mà D-09/D-14 cần đáp sau tag đó; `main` là gương
  upstream, `gonzo/main` là nhánh công ty, production chỉ chạy tag `gonzo-v*`.
- [Repo topology — hai repo hay ba](tickets/0002-repo-topology-hai-repo-hay-ba.md) —
  hai repo, không có `gonzo-runtime`; fork **là** runtime chính thức (D-19), code công ty
  nằm dưới `gonzo/` để upstream không conflict được.
- [Chọn và freeze 18 case truth-integrity](tickets/0012-chon-va-freeze-18-case-truth-integrity.md) —
  21 case đóng băng ở `gonzo/tests/truth_integrity/cases.yaml` (digest ở `FREEZE.md`); case
  khai báo *hình dạng vault* chứ không trỏ file, nên suite không vỡ khi vault nở lên ~690
  note; 34 test cấu trúc chạy được hôm nay, trong đó 21 wire check nối thẳng vào văn bản
  governance nên sửa luật vault mà quên sửa case thì suite đỏ.
- [Kanban và topic↔session của Hermes có đúng docs không](tickets/0005-kanban-va-card-behavior-cua-hermes-co-dung-docs-khong.md) —
  **có, không cần vá**: hai topic → hai session key → hai agent session độc lập; rủi ro #1
  được giải theo hướng tốt. Kèm hai xác nhận: session **không bền** (evict sau ~1h, đúng
  giả định D-02), và mô hình nhiều người dùng có sẵn qua `group_sessions_per_user` /
  `thread_sessions_per_user`.
- [Cost cap per-profile ở 9router](tickets/0013-cost-cap-per-profile-o-9router.md) —
  **không làm được**; 9router chỉ tracking. Cap thật đang ở goclaw và sẽ mất khi cutover.
- [ADR 0002 — Định vị trong Lark](../architecture/decisions/0002-dinh-vi-trong-lark-va-va-adapter.md) —
  Lark Topic-mode **không có** định vị theo message (`parent_id == root_id` luôn luôn), nên
  D-08 chuyển từ `parent_id` sang `card_id`; và chốt **vá adapter trong fork** thay vì viết
  adapter riêng.
- [ADR 0003 — Hybrid personal agents và filesystem boundary](../architecture/decisions/0003-hybrid-personal-agents-va-filesystem-boundary.md) —
  personal agent làm end-to-end mặc định, specialist chỉ escalation; profile memory A/B
  tách thật nhưng process/local backend không sandbox filesystem. Boundary production là
  Docker no-mount per profile; raw vault chỉ qua policy seam. Config lifecycle của
  terminal/file/execute-code đã dùng chung contract và full runtime probe pass 7/7.
- [Log rò credential của WS](tickets/0021-log-ro-credential-cua-ws.md) — logger boundary
  của SDK Lark ép strict-redact `access_key`/`ticket` bất kể config preference; runtime WS
  thật xác nhận secret bị che còn endpoint và public diagnostic params vẫn dùng được.
- [Docker no-mount pilot và bật Hermes#Test](tickets/0024-docker-no-mount-pilot-va-bat-hermes-test.md) —
  pilot host+Docker chạy thật: ba đường tool không đọc được raw vault, idle cleanup về 0
  container, group và DM Lark đều end-to-end; DM cần scope P2P riêng của app.
- [Retrieval thiết kế trên corpus nào](tickets/0009-retrieval-thiet-ke-tren-corpus-nao.md) —
  Gate 3 dùng corpus production gần hoàn chỉnh hiện tại (649 note governed); fixture chỉ
  tạo failure shape cố ý không tồn tại, còn tuning phải gắn vault fingerprint + evaluation.

## Fog

- **RAM thật của hybrid topology trên Mac mini** — personal profiles cùng trust domain có
  thể multiplex; specialist có thể tách process. Đo ở Gate 2 trên topology chạy thật,
  không đóng đinh “4 process” trước dữ liệu.
- **Media/3D thành domain + profile riêng** — không còn là giả thuyết: goclaw đã có
  `media-producer-*` đang chạy, và validator vault đã nhận `subject-matter-owner (<domain>)`.
  Chưa rõ nó vào như profile thứ 5 hay như một workstream riêng.
- **Ngưỡng cảnh báo cho 5 chỉ số của Gate 5** (card/người/tuần, queue age, tỷ lệ
  approve/reject, tỷ lệ approve không chỉnh sửa gì, note lẽ ra nên ở evidence) — doc nói
  rõ: chạy thật 2 tuần rồi mới đặt ngưỡng, **không chốt trước**.
- **Conflict detection thật** ở Gate 6 — supersedes graph, single-home, mâu thuẫn ngữ
  nghĩa — thay cho `multiple_relevant_notes` của v1.
- **Cutover mechanics** (D-18): routing flag kéo toàn bộ task về goclaw trông thế nào, và
  "ngừng giao task mới" thực thi ở tầng nào.
- **Base vs Doc cho deliverable** — mặc định Base; đổi nếu team chê UX. Chờ người dùng thật.
- **Shopify phase 1 read-only** và **MCP ads-read (Meta)** — mở rộng đã dự trù (§6), chưa
  tới lượt.
- **Antigravity** — đã bị đẩy ra khỏi đường tới hạn; đánh giá lại sau Gate 6.
