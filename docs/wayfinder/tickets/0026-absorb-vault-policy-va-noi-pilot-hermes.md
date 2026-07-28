---
id: "0026"
title: Absorb vault-policy và nối pilot Hermes
type: task
status: closed
assignee: "codex"
blocked_by: ["0025"]
---

## Question

Biến prototype đã pass thành read-only `gonzo/vault_policy` production seam tối thiểu,
expose đúng một surface hẹp cho Hermes trong Docker và nối profile pilot để Khánh hỏi vault
thật qua Lark như thế nào?

## Phải hoàn thành

1. Absorb commit gate, normalized private index, symbolic-first pipeline, source reread,
   open-question lane, `use_class` và multi-cite vào `gonzo/vault_policy`; production không
   import từ `gonzo/prototypes/`.
2. Expose surface hẹp, capability-gated và service-gated; không expose MCP/tool surface
   của `markdown-vault-mcp`, raw vault, raw index hay raw policy fields. Với stdio local,
   quyền spawn + pipe thay network authentication; không mở listener/credential surface.
3. Hermes host agent gọi seam bằng stdio child; Docker no-mount tool environment không gọi
   hoặc đọc raw vault. Config runtime ngoài git; secret vẫn chỉ ở `.env`.
4. Behavioral + transport + opt-in production E2E tests pass; negative probe chứng minh
   raw vault vẫn không đọc được. Thay test “sai credential” bằng invariant mạnh hơn cho
   stdio: không có remote request surface nếu process không được Hermes spawn.
5. Deploy vào đúng profile pilot hiện tại, health check pass, rồi chạy canary thật từ Lark
   trả kết quả có citation từ `gonzo-vault`.

## Không làm trong ticket này

- Không vật chất hoá toàn bộ 21 truth-integrity `given` — ticket
  [Vật chất hoá `given` và adapter cho truth suite](0016-vat-chat-hoa-given-va-adapter-cho-truth-suite.md).
- Không làm draft-write, publisher/adoption hoặc thêm user Lark thứ hai.
- Không mount raw vault/index vào agent Docker và không thêm core model tool.

## Runtime evidence đến hiện tại

- `hermes mcp test gonzo_vault`: connected, discover đúng một tool `vault_query`.
- Cold query thật build index `67.83s`; process mới query warm `0.13s`. Index/state persist
  dưới `~/.hermes/vault-policy` và reopen không rebuild.
- Payload full-note ban đầu `135–159 KB` bị Hermes truncate. Policy đổi sang query-relevant
  excerpt tối đa 1.600 ký tự/note; payload thật còn khoảng `37–50 KB`, không truncate.
- CLI session `20260727_215437_15071d`: trả đúng status gate, multi-cite và bundle
  `marketing-approval-delegation` như open-question **không blocking** thay vì false-stop.
- CLI session `20260727_213754_d5922f`: câu hỏi ai cung cấp giá Kyperus được chặn đúng bởi
  `decisions/open/who-sourced-kyperus-pricing.md` và trả “chưa biết/chưa quyết”.
- Negative probe session `20260727_213630_683dbc`: `read_file` raw sibling vault trả
  `File not found`; Docker volume args không chứa vault.
- Opt-in production E2E chạy qua canonical runner: temp git vault → locked launcher → real
  dependency/index/embedding → stdio MCP → sanitized cited result, `1/1` pass.
- Feishu WS connected và startup register `mcp__gonzo_vault__vault_query`. Claim cũ rằng
  gateway đã chuyển sang launchd chưa được verify: plist tồn tại nhưng
  `launchctl print gui/501/ai.hermes.gateway` không tìm thấy service; pilot process thực tế
  từng là orphan dưới PID 1. Launchd bootstrap/KeepAlive được tách thành việc deploy riêng.

## Resolution

**Pass — production read seam đã absorb và Lark pilot dùng vault thật end-to-end.**

Live owner canary ngày 2026-07-28 đi trọn Feishu DM → existing DM session → stdio policy
tool → Feishu outbound:

- `06:56:35` inbound `Ai có quyền approve 1 vault not` vào session
  `20260727_154211_410d00e9`;
- agent gọi `mcp__gonzo_vault__vault_query` hai lần (`0.24s` + `0.07s`);
- `06:56:43` response ready sau `8.0s`, 3 API calls, 853 ký tự; owner xác nhận đã nhận và
  tiếp tục hỏi nhiều câu thật;
- `billiards`, `Kyperus`, một đoạn claim dài và cấu trúc creative ads đều gọi vault tool,
  warm latency mỗi call khoảng `0.07–0.10s`, rồi outbound thành công;
- reply vào một message riêng tạo session định vị riêng
  `20260728_070114_d5a8130e`, đúng contract Feishu card/message addressing của ADR 0002.

Dashboard đang chạy ở Tailscale `100.79.40.55:9119`; trang Sessions hiển thị transcript,
tool-call count, tên + arguments từng `vault_query` và tool-result messages; trang Logs cho
lọc `agent`, `gateway`, `errors`. Đây là operator surface đủ để trace pilot hiện tại.

Raw vault vẫn không mount vào Docker, model chỉ thấy reread excerpts + `use_class`. stdio
spawn/pipe là capability boundary thay cho một network credential giả tạo. Locked runtime,
behavioral/transport/truth tests và production E2E đều pass; gateway chạy dưới launchd.

Tripwire giữ nguyên: chưa thêm user Lark thứ hai trước khi scope hoặc disable
`session_search`, vì implementation hiện không lọc `user_id` và còn hỗ trợ cross-profile
lookup.
