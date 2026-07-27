---
id: "0009"
title: Retrieval thiết kế trên corpus nào
type: grilling
status: closed
assignee: "codex"
blocked_by: []
---

## Question

Vault hôm nay có **59 note**. `MIGRATION.md` cho thấy còn 3 khu chưa bắt đầu:
`intel/kyperus/`, `marketing/canon/` (~178 note), `domains/billiards/` (~449 note) —
tức corpus đích khoảng **~690 note, gấp hơn 10 lần**. Thiết kế và tune retrieval (D-04)
trên corpus nào?

## Vì sao nó chặn

Gate 3 nghiệm thu bằng "agent trả lời có cite đúng note" — kết quả đó phụ thuộc corpus.
Tune symbolic-trước-semantic, BM25, và ngưỡng rerank trên 59 note rồi gặp 690 note là đúng
loại việc vỡ khi scale, và vỡ **sau khi** đã đậu gate.

Hai chi tiết làm nó gai hơn:

- **`domains/billiards/` (~449 note) là bulk-copy, không duyệt từng note** — đó là quyết
  định đã ghi trong `MIGRATION.md`. Vậy 449 note đó mang `status` gì, và `use_class` của
  chúng ra sao khi qua read contract (D-04a)? Nếu chúng vào thẳng `approved` thì hai phần
  ba vault là tri thức chưa ai đọc.
- `brands/kyperus/` còn treo `schema-*.md` **chờ quyết pipeline Hermes** — xem ticket
  [schema-*.md của Kyperus đang chờ quyết gì](0010-schema-md-cua-kyperus-dang-cho-quyet-gi.md).

## Phải chốt được

1. Gate 3 chạy trên corpus nào — 59 note hiện tại, hay chờ migrate xong?
2. Nếu chạy sớm: cái gì trong thiết kế retrieval **không được** phụ thuộc kích thước
   corpus, và cái gì phải tune lại sau migration (và ai nhớ làm việc đó)?
3. 449 note billiards vào vault ở `status` nào, và `use_class` tương ứng.

## Resolution

Premise 59-note đã bị migration vượt qua. Snapshot vault thật ngày 2026-07-27 trên commit
`096e44f` có **649 note governed có frontmatter** sau khi loại `_templates/`, `_inbox/`,
`outputs/` và các file bookkeeping (`README.md`, `MIGRATION.md`, `CLAUDE.md`, PR template):

- 484 `approved`;
- 160 `draft`;
- 5 `superseded`.

Trong đó `domains/billiards/` đã migrate đủ 450 note, còn `marketing/canon/` đã có 142
note và toàn bộ vẫn là draft. Vault-approver xác nhận vault đã gần hoàn chỉnh. Vì vậy
**Gate 3 thiết kế, tune và nghiệm thu trên corpus thật hiện tại**; không dựng một baseline
59-note và không chờ phần migration còn lại mới bắt đầu.

Fixture chỉ dùng để tạo những failure shape mà vault production cố ý không chứa, ví dụ:
hai approved note mâu thuẫn không có quan hệ supersede, operational-state stale, hoặc một
registry có row `UNVERIFIED`. Fixture phải pass cùng validator và read contract như vault
thật; nó không thay thế phép thử retrieval trên corpus thật.

### Bất biến không phụ thuộc kích thước corpus

- Exclusion boundary: không index `_inbox/`, `outputs/`, template hay bookkeeping.
- Frontmatter/type filter, symbolic trước semantic, open-question lane riêng.
- Index chỉ tìm candidate, policy đọc lại Markdown gốc và index phải gắn vault commit.
- `use_class` do policy tính; model không thấy raw `authority`, `status`, `freshness`.
- Nhiều note materially relevant phải trả riêng với multi-cite flags, không gộp im lặng.

### Phần được tune và cách tránh phụ thuộc trí nhớ người

BM25 field weights, candidate count, graph expansion depth, embedding model, semantic
threshold, rerank weights và bundle/token budget là tham số thực nghiệm. Mỗi kết quả tune
phải version-control cùng vault commit/fingerprint và kết quả evaluation. Thay retrieval,
policy, prompt, embedding model hoặc corpus lớn phải chạy lại retrieval evaluation + truth
suite trước release; đây là release gate tự động/ghi trong artifact, không phải việc ai đó
phải nhớ bằng miệng.

### Billiards

Premise “449 note bulk-copy chưa được kiểm” cũng không còn đúng ở snapshot hiện tại. Corpus
có 450 note: **447 `approved`** sau batch promotion, fidelity audit ba vòng và 46 correction
được vault-approver adopt; **3 `draft`** (index/audit-supporting material). Qua D-04a:

- approved canon authority 4 → `use_class: citable`, nhưng phải giữ attribution thật của
  speaker/source và không được biến thành Kyperus/company truth;
- draft → `use_class: unverified`;
- authority vẫn chỉ dùng nội bộ để rank, không trả raw cho model.

Quyết định này mở khoá việc đánh giá `markdown-vault-mcp` và vật chất hoá adapter/fixture
cho truth suite. Phần intel còn lại là corpus growth bình thường, không còn là blocker cho
thiết kế retrieval.
