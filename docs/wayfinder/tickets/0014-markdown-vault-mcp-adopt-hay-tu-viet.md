---
id: "0014"
title: markdown-vault-mcp — adopt hay tự viết
type: research
status: closed
assignee: "codex"
blocked_by: ["0009"]
---

## Question

`markdown-vault-mcp` có đạt đủ **4 tiêu chí** của D-04 không: ①sống + license dùng được
②đủ symbolic **và** semantic ③không cản ràng buộc commit-hash ④thật sự **giảm** lượng code
phải bảo trì?

## Vì sao bị chặn

Tiêu chí ④ chỉ trả lời được khi biết corpus đích — xem
[Retrieval thiết kế trên corpus nào](0009-retrieval-thiet-ke-tren-corpus-nao.md). Một
index ngoài "giảm code" ở 59 note nhưng có thể thành gánh nặng ở 690 note, hoặc ngược lại.

## Ghi nhớ khi resolve

Doc nói rõ đây là **đánh giá tuỳ chọn, không phải tiền đề** — nó đã bị rút khỏi Gate 0.
Không đạt → dùng implementation nội bộ, *vốn đã đủ*. Đừng biến ticket này thành nút thắt.

Và dù adopt hay không, phần *có ý nghĩa* của seam vẫn là luật riêng của vault này: read
contract `use_class`, lane open-question, chặn gộp im lặng, đọc lại file gốc trước khi
trả. Thứ một MCP ngoài cung cấp chỉ còn là cái index.

## Resolution

Research đầy đủ: [Đánh giá `markdown-vault-mcp`: adopt engine, không adopt MCP
surface](../../research/markdown-vault-mcp-assessment.md).

Candidate canonical là
[`pvliesdonk/markdown-vault-mcp`](https://github.com/pvliesdonk/markdown-vault-mcp), xác
nhận qua package metadata PyPI và MCP manifest. Quyết định:

- **Adopt có điều kiện** stable `v3.1.0` như private Python library/index engine nằm trong
  process host-side `gonzo/vault_policy`.
- **Không expose MCP server upstream** cho Hermes. Search/read upstream trả raw snippet,
  frontmatter và file; model sẽ thấy `authority/status/freshness` và bypass D-04a.
- Tự viết adapter/orchestration D-04: commit gate fail-closed, symbolic → graph → semantic,
  reread Markdown gốc, `use_class`, open-question lane, multi-cite và sanitize.
- Pin version; upgrade chỉ sau contract tests + truth suite. Không fork upstream sâu để
  giữ dependency.

Đối chiếu bốn tiêu chí:

1. **Sống + license:** đạt — MIT, stable release và CI/source còn active.
2. **Symbolic + semantic:** đạt về primitive — FTS5/BM25, frontmatter filters, wikilink
   graph, vector search; không dùng hybrid RRF mặc định vì D-04 yêu cầu symbolic-first.
3. **Commit-hash contract:** upstream không có sẵn nhưng không cản wrapper — public library
   API cho forced rebuild và disk reread. Adapter phải block query khi SHA lệch; trạng thái
   `index_stale` không được phép trả production.
4. **Giảm maintenance:** đạt — thay scanner/chunker, FTS/ranking, vector persistence,
   incremental reconcile và graph; phần policy đặc thù Gonzo vẫn tự sở hữu.

`tobi/qmd` giữ vai optional skill cho personal/un-governed document search; không dùng làm
company-vault seam vì thiếu graph/frontmatter fit, retrieval đọc từ index và full pipeline
mang khoảng 2 GB model.

Dependency chỉ được giữ sau prototype
[Chứng minh markdown-vault-mcp sau vault-policy](0025-chung-minh-markdown-vault-mcp-sau-vault-policy.md)
pass năm invariant trên corpus production. Fail mà cần fork sâu → bỏ dependency, quay về
implementation nội bộ; không block Gate 3.
