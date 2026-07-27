---
id: "0026"
title: Absorb vault-policy và nối pilot Hermes
type: task
status: open
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
2. Expose surface hẹp, authenticated và service-gated; không expose MCP/tool surface của
   `markdown-vault-mcp`, raw vault, raw index hay raw policy fields.
3. Hermes Docker no-mount gọi được seam qua host; credential/config ở runtime ngoài git.
4. Behavioral + transport tests pass; negative probe chứng minh raw vault vẫn không đọc
   được và request thiếu/sai credential bị từ chối.
5. Deploy vào đúng profile pilot hiện tại, health check pass, rồi chạy canary thật từ Lark
   trả kết quả có citation từ `gonzo-vault`.

## Không làm trong ticket này

- Không vật chất hoá toàn bộ 21 truth-integrity `given` — ticket
  [Vật chất hoá `given` và adapter cho truth suite](0016-vat-chat-hoa-given-va-adapter-cho-truth-suite.md).
- Không làm draft-write, publisher/adoption hoặc thêm user Lark thứ hai.
- Không mount raw vault/index vào agent Docker và không thêm core model tool.
