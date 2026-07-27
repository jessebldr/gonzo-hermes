---
id: "0025"
title: Chứng minh markdown-vault-mcp sau vault-policy
type: prototype
status: open
assignee: "codex"
blocked_by: []
---

## Question

Một vertical slice dùng `pvliesdonk/markdown-vault-mcp@v3.1.0` như private Python index
engine bên trong `gonzo/vault_policy` có giữ đủ contract D-04/D-04a trên corpus production
hay không?

## Phải chứng minh

1. Exclusion + required-frontmatter tạo đúng tập governed corpus đã chốt; `_inbox/`,
   `_templates/`, `outputs/` và bookkeeping không vào index.
2. Vault commit SHA đổi thì query block và rebuild đồng bộ; không response nào mang hoặc
   dựa trên `index_stale`.
3. Index chỉ trả candidate path/score; policy đọc lại file gốc và response không lộ raw
   `authority`, `status`, `freshness`.
4. Pipeline chạy đúng frontmatter/type → symbolic → graph → semantic fallback/rerank →
   open-question + `use_class` + multi-cite; truth-integrity cases liên quan pass.
5. Đo p50/p95 latency, peak RSS và index size trên Mac pilot + vault thật.

## Escape condition

Nếu bất kỳ invariant nào chỉ đạt bằng cách fork/sửa sâu upstream, bỏ dependency và dùng
implementation nội bộ. Ticket này không được biến thành blocker vô hạn cho Gate 3.

## Asset đầu vào

[Đánh giá `markdown-vault-mcp`: adopt engine, không adopt MCP surface](../../research/markdown-vault-mcp-assessment.md).
