# `vault_policy` — cửa duy nhất vào vault

Quyết định chi phối: **D-04** (retrieval đầy đủ), **D-04a** (read contract),
**D-04b** (hợp đồng draft-write). Workstream ④. Gate 3 (read) và Gate 4 (write).

## Đọc — trả *quyền dùng*, không trả nguyên liệu suy luận

Bảy thành phần, **chạy đúng thứ tự này**, symbolic trước semantic — không đảo:

1. lọc frontmatter / `type` → 2. title, heading, tag, alias → 3. BM25/full-text →
4. mở rộng theo wikilink + relative-link graph → 5. semantic embedding
(**fallback/rerank**, luôn sau symbolic) → 6. bundling open-question (lane riêng) →
7. `use_class` + multi-note flags.

## Bất biến — mỗi cái là một test, không phải một lời dặn

- **Model không bao giờ thấy `authority`, `status`, `freshness` ở dạng thô.** Mỗi kết quả
  mang đúng một `use_class`: `citable` · `suggestion-only` · `unverified` · `stale` ·
  `undecided` · `historical-only`.
- **Index không phải source of truth.** Index chỉ tìm ứng viên; policy layer đọc lại file
  Markdown gốc trước khi trả. Index gắn git commit hash — commit hiện tại khác commit đã
  index thì **rebuild trước khi phục vụ query**. `index_stale` không được phép tồn tại
  trên production.
- **Open-question là lane riêng.** Lọc `approved`-only sẽ giết `decisions/open/` và agent
  sẽ lấp khoảng trống bằng suy luận. Task phụ thuộc open-question đang hiệu lực → agent
  nói "chưa quyết" và **dừng**.
- **Chặn gộp im lặng.** Từ 2 note approved materially relevant trở lên: trả riêng từng
  note kèm `multiple_relevant_notes` + `requires_multi_cite`. Đây *không* phải conflict
  detection — cái thật để Gate 6.
- **Draft-write gate theo `status`, không theo path.** Draft sinh thẳng vào folder
  canonical theo `type`; không có `_drafts/`; không thêm key mới vào frontmatter; và
  **không bao giờ ghi field `status`**, kể cả ghi lại đúng giá trị cũ.

## Ngoài phạm vi

Promote (`draft` → `approved`) không nằm ở đây — đó là `gonzo/publisher/`, service duy
nhất được ghi field `status`.

`markdown-vault-mcp` **không phải dependency bắt buộc**. Prototype trên corpus production
đã pass điều kiện adopt `v3.1.0` như private index engine sau policy; xem
[`../prototypes/NOTES.md`](../prototypes/NOTES.md). Không expose MCP upstream. Production
Gate 3 vẫn phải absorb seam + tests và chạy retrieval evaluation.

Trạng thái: **stub.**
