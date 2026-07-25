---
id: "0014"
title: markdown-vault-mcp — adopt hay tự viết
type: research
status: open
assignee: ""
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
