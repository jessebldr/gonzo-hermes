---
id: "0025"
title: Chứng minh markdown-vault-mcp sau vault-policy
type: prototype
status: closed
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

## Resolution

**Pass — giữ `markdown-vault-mcp==3.1.0` làm private index engine sau `vault_policy`.**
Không cần fork/sửa upstream; tuyệt đối không expose MCP surface. Runtime proof và số đo:
[Vault-policy index prototype — verdict](../../../gonzo/prototypes/NOTES.md#vault-policy-index-prototype--verdict).

Trên vault `a93d693` ngày 2026-07-27, normalized index-only mirror match đúng **665/665**
note governed, gồm cả 7 note mà parser PyYAML upstream làm rơi nếu đọc raw; mọi exclusion
đã chốt đều đúng. Commit gate fail-closed với dirty tree, forced SHA mismatch rebuild đồng
bộ, và HEAD đổi giữa build gây retry trước search. Candidate chỉ có path/score; policy
reread source và payload không có raw `authority/status/freshness`.

Pipeline symbolic-first + graph + semantic + open-question lane + policy pass behavioral
tests; open-question không lọt result lane chính, multi-cite/use-class pass. Tổng 6 test
prototype + 34 truth-integrity = **40/40**. Mac pilot: cold/rebuild ~68 s, warm p50 31.5 ms,
p95 35.6 ms, peak RSS ~780 MiB, index/state ~21.9 MiB, mirror ~3.2 MiB.

Đây là feasibility/contract proof, không phải production Gate 3. Retrieval evaluation vẫn
phải tune relevance và false blocker khi absorb seam; prototype giữ dependency cô lập khỏi
`pyproject.toml`.
