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

`markdown-vault-mcp` là **private index engine**, không phải model-facing MCP. Dependency
khai báo bằng range có upper bound trong `pyproject.toml`; `uv.lock` hiện resolve `v3.1.0`
và giữ artifact hash cho deploy reproducible.
Production server expose đúng một stdio tool là `vault_query`; resources, prompts, raw
index và tool surface upstream không được đăng ký. Process spawn + stdio pipe là capability
boundary: không có TCP listener hay bearer credential để đoán/sai. Chỉ process Hermes có
config mới spawn được child này, và config whitelist đúng một tool.

## Pilot production hiện tại

- Entry point: `server.py`; launcher chạy locked project: `run-mcp.sh`.
- Vault source: `/Users/aigonzo/Company/gonzo-vault`.
- Persistent private state: `~/.hermes/vault-policy`; model cache:
  `~/.hermes/cache/vault-policy-model`.
- Cold build trên corpus thật: `67.83s`; process mới mở index persisted và query warm:
  `0.13s` (2026-07-27).
- Open-question lane bundle từ symbolic search, wikilink graph và `affects`. Note
  `blocking: false` vẫn được báo cho model nhưng không chặn fact đã quyết; chỉ
  `blocking: true` mới bật `blocked_by_open_question`.
- Semantic chỉ chạy fallback khi symbolic + graph chưa lấp đủ result limit; score giữa
  các channel không bị trộn như thể cùng thang đo.
- Kết quả model-facing reread raw Markdown nhưng chỉ trả excerpt liên quan, tối đa 1.600
  ký tự/note. Runtime payload giảm từ `135–159 KB` (bị Hermes truncate) xuống khoảng
  `37–50 KB` và không còn bị truncate.
- Canary thật đã trả đúng approval authority với multi-cite; canary open-question
  `who-sourced-kyperus-pricing` nói chưa biết/chưa quyết và dừng suy đoán.
- Raw vault vẫn không được mount vào Docker tool environment; `read_file` trực tiếp trả
  `File not found`.
- E2E reproducible: `scripts/run_tests.sh
  gonzo/tests/vault_policy/test_production_e2e.py -m integration -q -s` dựng temp git vault + temp
  `HERMES_HOME`, cài lockfile, build real index/embedding và gọi tool qua stdio.

Deploy trong repo này hiện **chỉ nhắm Mac pilot của owner** (launchd + Bash launcher),
không phải surface cross-platform của upstream Hermes. Nếu mở cho Windows/Linux team host,
phải thêm launcher native tương ứng trước khi dùng config này.

Prototype gốc và corpus evidence: [`../prototypes/NOTES.md`](../prototypes/NOTES.md).
Gate 3 retrieval evaluation rộng hơn vẫn là work tiếp theo; pilot seam này đã được absorb
vào production code và chạy thật.
