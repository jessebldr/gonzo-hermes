# `gonzo/` — code công ty bên trong fork Hermes

Mọi thứ Kyperus/Gonzo tự viết sống ở đây. Upstream (`NousResearch/hermes-agent`) không
bao giờ có thư mục tên `gonzo/`, nên **không file nào trong đây có thể conflict khi
cherry-pick upstream**. Đó là toàn bộ lý do nó tồn tại.

Ngược lại: file **ngoài** `gonzo/` là file của upstream. Sửa một file như vậy tạo ra một
điểm conflict vĩnh viễn cho mọi lần sync về sau. D-19 cho phép — dispatcher, profile
routing, sandbox propagation, session routing có thể phải đụng core — nhưng có giá. Nên mỗi lần sửa file
upstream phải: (a) là một commit riêng, có test; (b) được ghi vào bảng cuối file này.

Bối cảnh đầy đủ: [`docs/architecture/hermes-vault-agent-team-architecture.md`](../docs/architecture/hermes-vault-agent-team-architecture.md).
Baseline fork + mô hình branch: [`docs/architecture/decisions/0001-fork-baseline-and-branch-model.md`](../docs/architecture/decisions/0001-fork-baseline-and-branch-model.md).

## Bản đồ — 8 thư mục production + prototype throwaway

| Thư mục | Là gì | Quyết định | Workstream | Gate |
|---|---|---|---|---|
| `profiles/` | Config personal/shared/specialist profiles; memory state tách, Docker no-mount là filesystem boundary | D-01, D-03, ADR 0003 | ① | 2 |
| `kanban_bus/` | `team_ask`, dispatcher đánh thức worker, worker inbox trên Kanban SQLite | D-02, D-03 | ② | 2 |
| `lark_io_broker/` | `post_message` · `post_card` · `patch_card` · `write_base_row` qua signed capability; routing table durable + idempotent | D-20 | ③ | 2 |
| `vault_policy/` | Retrieval 7 thành phần (symbolic → graph → semantic), read contract `use_class`, draft-write theo `status` | D-04, D-04a, D-04b | ④ | 3, 4 |
| `approval/` | Mở phiên duyệt: `content_hash` + nonce + `card_id` + expiry, render card "Adopt as doctrine" | D-14 | ⑤ | 5 |
| `publisher/` | Service **duy nhất** được ghi field `status`: verify callback → flip `approved` → `validate_vault.py` → git commit | D-05, D-13, D-14 | ⑤ | 5 |
| `scanner/` | Pre-load truth gate: staging → quét → rewrite fact thành vault lookup → activate / quarantine / hard block | D-15 | ⑥ | 2 |
| `deploy/` | launchd plist, health check, backup/restore Kanban, deploy + rollback bằng script | D-18, D-21 | ⑦ | 2, 5 |
| `tests/` | Truth-integrity suite (D-17①) + test cho các module trên | D-17 | ⑦ | 1, 3+ |
| `prototypes/` | Runner throwaway để bác/chứng minh premise bằng runtime; xoá hoặc absorb sau khi có ADR | ADR 0003 | — | — |

Trạng thái hiện tại: `vault_policy/` đã thành production pilot read-only và chạy thật qua
stdio MCP hẹp; các module production còn lại phần lớn vẫn là stub. `prototypes/` giữ
evidence trước khi absorb, không phải runtime production. Thứ tự build và điều kiện đậu của
từng tầng nằm ở §8 — không tầng nào được coi là xong nếu chưa qua gate của nó.

## Luật của thư mục này

1. **Không fact công ty trong code.** Vault (`gonzo-vault`) giữ truth (P1). Code ở đây
   *truy vấn* vault, không *chứa* nội dung vault. Một literal như `$419` hay một product
   claim hardcode trong `gonzo/` là bug cùng loại với thứ D-15 chặn ở memory/skill.
2. **Không secret trong repo.** Lark app secret, token, `lark_user_id → role` mapping sống
   ở runtime config ngoài git (D-14). Repo chỉ giữ schema và loader.
3. **`encoding="utf-8"` bắt buộc.** ruff `PLW1514` bật cho `gonzo/**`. Upstream miễn trừ
   `plugins/**`, `skills/**`, `tests/**` — `gonzo/**` **không** nằm trong danh sách miễn trừ,
   và cố ý như vậy.
4. **Test đi cùng code.** Test của module ở đây → `gonzo/tests/`. Test đụng Hermes core →
   `tests/` của upstream, cạnh test upstream, vì đó là chỗ nó sẽ conflict và cần được thấy.

## Upstream files đã sửa

Mỗi dòng ở đây là một điểm conflict phải giải bằng tay ở mọi lần cherry-pick upstream.
Danh sách này ngắn là một mục tiêu, không phải tình cờ.

| File | Vì sao | Commit |
|---|---|---|
| `pyproject.toml` | Đăng ký package `gonzo` vào `packages.find`, thêm `gonzo/tests` vào `testpaths` | khung ban đầu |
| `docs/architecture/hermes-vault-agent-team-architecture.md` | Runtime evidence supersede D-01/D-03 bằng hybrid personal agents + Docker filesystem boundary | pending — ADR 0003 |
| `docs/architecture/decisions/0003-hybrid-personal-agents-va-filesystem-boundary.md` | Decision record cho topology và boundary đã test thật; file fork-owned, không có upstream counterpart | pending — ADR 0003 |
| `docs/wayfinder/map.md` | Ghi decision ADR 0003, credential-log boundary, pilot Docker/Lark, corpus retrieval và cập nhật fog | pending — ADR 0003 + WS log fix + pilot/retrieval closure |
| `docs/wayfinder/tickets/0022-profile-khong-phai-filesystem-boundary.md` | Đóng prototype ticket bằng runtime evidence | pending — ADR 0003 |
| `docs/wayfinder/tickets/0023-file-tools-lam-roi-docker-lifecycle-config.md` | Đóng config propagation bug bằng tests + runtime probe 7/7 | pending — lifecycle fix |
| `tools/terminal_tool.py` | Một shared container-config builder cho mọi environment creation path | pending — lifecycle fix |
| `tools/file_tools.py` | File-first environment creation dùng full container contract | pending — lifecycle fix |
| `tools/code_execution_tool.py` | Execute-first environment creation dùng full container contract | pending — lifecycle fix |
| `tests/tools/test_file_tools_container_config.py` | Pin exact file-first container contract bằng non-default values | pending — lifecycle fix |
| `tests/tools/test_code_execution_container_config.py` | Pin exact execute-first container contract bằng non-default values | pending — lifecycle fix |
| `tests/tools/test_docker_network_config.py` | Thay AST change-detector bằng behavioral contract trên shared builder | pending — lifecycle fix |
| `agent/redact.py` | Strict URL boundary nhận diện `access_key` và authentication `ticket`; default URL behavior không đổi | `test_redact.py` + `test_feishu_logging.py` |
| `plugins/platforms/feishu/adapter.py` | Card action: dùng `context.open_message_id` thay cho card token (`c-…`), resolve `thread_id` của topic, và không phát `/card` (lệnh không ai đăng ký). Bắt buộc vì Lark Topic-mode không có định vị theo message — [ADR 0002](../docs/architecture/decisions/0002-dinh-vi-trong-lark-va-va-adapter.md). Logger boundary ép che credential WS do SDK tự in. Allowlist/group/card callback giữ đủ `open_id`/`user_id`/`union_id` để stable principal hoạt động end-to-end | `test_feishu_card_action_addressing.py` + `test_feishu_logging.py` + `486256633` |
| `tests/gateway/test_feishu_approval_buttons.py` | Pin click card tới được agent, `value` sống sót và authorization bằng `union_id` qua cả synchronous callback lẫn async re-check | chính nó + `486256633` |
| `tests/gateway/test_feishu_bot_admission.py` | Pin stable `union_id` đi xuyên group admission tới shared-profile routing | `486256633` |
| `tests/gateway/test_feishu_logging.py` | Pin invariant log WS thật: credential bị che, endpoint và public diagnostic params còn nguyên, không phụ thuộc redaction preference | chính nó |
| `website/docs/user-guide/messaging/feishu.md` | Ghi granular scope nhận DM/group @mention, cách xử lý case group chạy nhưng DM im lặng và allowlist nhận stable `union_id` ngoài `open_id`/`user_id` | pending — pilot closure + `486256633` |
| `docs/profile-routing.md` | Document DM principal route, normalized chat type, specificity và shared-group fallback | `486256633` |
| `gateway/config.py` | Mở schema/doc config profile route cho `principal_id` và `chat_type` | `486256633` |
| `gateway/platforms/base.py` | Khai báo runner back-reference cho mọi adapter để inbound profile routing không còn Discord-only | `486256633` |
| `gateway/profile_routing.py` | Route DM theo stable principal, normalize chat type và giữ principal route khỏi group/topic | `486256633` |
| `gateway/authz_mixin.py` | Cho lớp authorization thứ hai match cùng tập sender identity (`user_id` + stable `user_id_alt`) mà adapter admission, profile routing và session keying đã dùng; sửa DM Feishu có typing rồi bị drop khi allowlist lưu `union_id` | commit này |
| `gateway/run.py` | Truyền principal/chat type vào matcher và resolve đúng profile home dưới multiplex gate | `486256633` |
| `tests/gateway/test_unauthorized_dm_behavior.py` | Pin Feishu `union_id` hợp lệ qua gateway auth và giữ negative canary cho union ID lạ | commit này |
| `tests/gateway/test_profile_resolution.py` | E2E adapter → route → profile home → profile-scoped session namespace trên temporary `HERMES_HOME` | `486256633` |
| `tests/gateway/test_profile_routing.py` | Pin specificity, DM-only principal matching, chat-type fallback và config parsing | `486256633` |
| `website/docs/user-guide/multi-profile-gateways.md` | Document one-gateway principal/workspace/shared-group topology | `486256633` |
| `docs/wayfinder/tickets/0021-log-ro-credential-cua-ws.md` | Ghi root cause, boundary và runtime proof của credential-log fix | ticket này |
| `docs/wayfinder/tickets/0024-docker-no-mount-pilot-va-bat-hermes-test.md` | Theo dõi deploy Docker boundary vào pilot và phép thử Lark thật trước khi nối vault-policy | ticket này |
| `docs/wayfinder/tickets/0009-retrieval-thiet-ke-tren-corpus-nao.md` | Chốt Gate 3 trên corpus production gần hoàn chỉnh và phân biệt corpus thật với fixture edge-case | ticket này |
| `docs/research/markdown-vault-mcp-assessment.md` | Đánh giá upstream index theo 4 tiêu chí D-04 và so với `qmd`; chốt chỉ dùng library sau policy | pending — vault index research |
| `docs/wayfinder/tickets/0014-markdown-vault-mcp-adopt-hay-tu-viet.md` | Chốt adopt có điều kiện private index engine, không expose MCP surface upstream | ticket này |
| `docs/wayfinder/tickets/0025-chung-minh-markdown-vault-mcp-sau-vault-policy.md` | Prototype gate trước khi giữ dependency index cho Gate 3 | ticket này |
| `docs/wayfinder/tickets/0026-absorb-vault-policy-va-noi-pilot-hermes.md` | Absorb read-only policy seam, deploy stdio MCP hẹp và ghi runtime canary của pilot | ticket này |
| `docs/research/lark-openapi-mcp-assessment.md` | Verify repo/license/Base/card primitives và chốt direct official SDK sau D-20 broker thay vì generic MCP surface | pending — Lark MCP research |
| `docs/wayfinder/tickets/0004-lark-openapi-mcp-co-dung-duoc-khong.md` | Đóng Gate 0 premise bằng primary-source report pinned upstream SHA | ticket này |
| `docs/wayfinder/tickets/0020-sua-ba-cho-sai-trong-doc-kien-truc.md` | Thêm correction D-10/Gate 0 đã được research chứng minh | pending — doc reconciliation |
| `docs/wayfinder/tickets/0027-implement-lark-io-broker-capability-boundary.md` | Task implement direct-SDK capability/idempotency boundary cho workstream ③ | ticket này |
| `hermes_state.py` | Schema v24 lưu alternate principal ID và áp recall scope vào toàn bộ browse/FTS/CJK/trigram/LIKE/fallback paths; preserve alias khi gateway update thiếu trường | `e9e41852d`, `1da2e470b` |
| `tests/test_hermes_state.py` | Pin migration, principal scope, identity inheritance qua compression và preserve-on-NULL | `e9e41852d`, `1da2e470b` |
| `tests/test_fts_cjk_bigram.py` | Pin recall scope trên CJK và Latin fallback indexes | `e9e41852d` |
| `tools/session_search_tool.py` | Enforce ownership cho browse/discover/read/scroll; bỏ model-controlled profile selector | `263f051e3` |
| `tests/tools/test_session_search.py` | Positive same-principal recall và negative cross-principal/topic/profile/fail-closed contracts | `263f051e3` |
| `agent/tool_executor.py` | Bật trusted recall scope ở sequential tool execution path | `706736351` |
| `agent/agent_runtime_helpers.py` | Bật trusted recall scope ở helper/runtime tool execution path | `706736351` |
| `gateway/session.py` | Persist `user_id_alt` qua create/reset/recovery để principal identity không mất | `706736351` |
| `run_agent.py` | Lazy DB session creation giữ gateway principal/chat/thread metadata | `706736351` |
| `tests/gateway/test_session.py` | Pin alternate principal ID qua gateway recovery persistence | `706736351` |
| `tests/run_agent/test_860_dedup.py` | Pin gateway metadata khi agent tạo DB session muộn | `706736351` |
| `docs/wayfinder/tickets/0018-pham-vi-cua-session-search.md` | Chốt và ghi evidence cho principal-scoped session recall | ticket này |
