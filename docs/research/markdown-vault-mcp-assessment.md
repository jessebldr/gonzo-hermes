# Đánh giá `markdown-vault-mcp`: adopt engine, không adopt MCP surface

Ngày đánh giá: 2026-07-27

Phạm vi: Wayfinder ticket 0014, bốn tiêu chí D-04 và so sánh với `tobi/qmd` đã có
trong optional skill của Hermes.

## Kết luận

Upstream được nhắc tới gần như chắc chắn là
[`pvliesdonk/markdown-vault-mcp`](https://github.com/pvliesdonk/markdown-vault-mcp).
PyPI package chính thức `markdown-vault-mcp` trỏ ngược về đúng repository này, còn manifest
MCP dùng tên `io.github.pvliesdonk/markdown-vault-mcp`; vì vậy các repository trùng tên khác
không phải candidate canonical ([PyPI metadata](https://pypi.org/project/markdown-vault-mcp/),
[repository README, dòng 1–11](https://github.com/pvliesdonk/markdown-vault-mcp/blob/c0c68f9c74a483a6fe30b2fd90a4beaa131cdcb5/README.md#L1-L11)).

**Khuyến nghị: adopt có điều kiện dưới dạng Python library/index engine nằm *bên trong*
process host-side `gonzo/vault_policy`; không chạy hoặc khai báo MCP server upstream cho
Hermes.** Pin stable `v3.1.0`, không pin `main` hay `v3.2.0-rc.6`. Ta vẫn tự viết orchestration
D-04 và toàn bộ policy D-04a:

1. kiểm commit SHA và rebuild đồng bộ trước query;
2. symbolic → graph → semantic fallback/rerank theo đúng thứ tự;
3. đọc lại Markdown gốc và kiểm lại SHA trước khi trả;
4. tính `use_class`, open-question lane và multi-note flags;
5. chỉ expose response đã sanitize qua MCP của `vault_policy`.

Với hình thức này, candidate đạt đủ bốn tiêu chí D-04. Nếu expose MCP upstream trực tiếp,
nó **không đạt** tiêu chí 3 và phá boundary bảo mật.

## Xác định candidate và trạng thái dự án

Tìm kiếm GitHub có nhiều repository mang tên gần giống, nhưng candidate canonical là
`pvliesdonk/markdown-vault-mcp` vì:

- package metadata khai báo chính xác tên `markdown-vault-mcp`, repository, docs và issue
  tracker thuộc `pvliesdonk` ([`pyproject.toml`](https://github.com/pvliesdonk/markdown-vault-mcp/blob/c0c68f9c74a483a6fe30b2fd90a4beaa131cdcb5/pyproject.toml#L1-L34),
  [PyPI](https://pypi.org/project/markdown-vault-mcp/));
- mô tả project khớp nguyên premise của ticket: FTS5/BM25, semantic vector search,
  frontmatter-aware index và incremental reindex
  ([README, dòng 7–25](https://github.com/pvliesdonk/markdown-vault-mcp/blob/c0c68f9c74a483a6fe30b2fd90a4beaa131cdcb5/README.md#L7-L25));
- các project cùng tên còn lại không có canonical package link tương đương; một số là bản
  sao/custom hoặc có feature set khác. Không có bằng chứng local nào chỉ tới một repo khác.

Snapshot upstream khi đánh giá:

- repository không archived, hoạt động từ 2026-03-07; HEAD được kiểm là
  `c0c68f9c74a483a6fe30b2fd90a4beaa131cdcb5`;
- stable mới nhất là
  [`v3.1.0`, phát hành 2026-07-08](https://github.com/pvliesdonk/markdown-vault-mcp/releases/tag/v3.1.0);
  `main` đang ở `3.2.0-rc.6`, tức prerelease
  ([release list](https://github.com/pvliesdonk/markdown-vault-mcp/releases));
- license là MIT
  ([LICENSE](https://github.com/pvliesdonk/markdown-vault-mcp/blob/c0c68f9c74a483a6fe30b2fd90a4beaa131cdcb5/LICENSE));
- latest CodeQL trên HEAD thành công. Main CI gần nhất đỏ vì riêng Docs Prose/Vale; test
  Python 3.11–3.14, lint, type check, dependency audit và secret detection đều pass
  ([CI run `30108832517`](https://github.com/pvliesdonk/markdown-vault-mcp/actions/runs/30108832517),
  [CodeQL run `30255898922`](https://github.com/pvliesdonk/markdown-vault-mcp/actions/runs/30255898922)).

Đây là dự án sống và usable, nhưng release cadence nhanh. Pin một stable version và chỉ
nâng sau compatibility/truth suite là bắt buộc.

## Decision matrix D-04

| Tiêu chí | Kết quả | Bằng chứng và điều kiện |
|---|---|---|
| 1. Sống + license dùng được | **Đạt** | MIT; stable v3.1.0; source, PyPI, release và CI còn hoạt động. |
| 2. Symbolic **và** semantic | **Đạt về primitive, chưa đạt pipeline D-04 nếu dùng nguyên `hybrid`** | Có FTS5/BM25, title/heading/content/searchable-frontmatter, filter frontmatter, vector cosine và graph API. `hybrid` upstream chạy hai channel rồi RRF; ta phải gọi `keyword`, graph, rồi `semantic` riêng theo thứ tự D-04. |
| 3. Commit-hash + reread-original-file | **Đạt khi wrap library; không đạt khi expose MCP trực tiếp** | Public API có forced rebuild và disk read, nên policy có thể enforce contract. Upstream tự thân chỉ track SHA-256 từng file, cho phép trả `index_stale`, và MCP search/read trả raw snippet/frontmatter/file. |
| 4. Giảm code bảo trì ở ~649 note | **Đạt** | Nó thay phần scanner/chunker, FTS schema/ranking, vector persistence/provider, incremental reconcile và wikilink graph. Policy đặc thù vẫn thuộc Gonzo. Brute-force vector là đủ nhỏ cho corpus này, cần benchmark thật chứ chưa cần vector DB riêng. |

## 1. Symbolic và semantic: có đủ nguyên liệu, không dùng pipeline mặc định

### Symbolic

Upstream có các primitive phù hợp:

- SQLite FTS5 với các cột `path`, `title`, `folder`, `heading`, `content`, `summary`, dùng
  porter tokenizer và BM25 weights
  ([`fts_index.py`, dòng 132–149](https://github.com/pvliesdonk/markdown-vault-mcp/blob/c0c68f9c74a483a6fe30b2fd90a4beaa131cdcb5/src/markdown_vault_mcp/fts_index.py#L132-L149),
  [dòng 299–339](https://github.com/pvliesdonk/markdown-vault-mcp/blob/c0c68f9c74a483a6fe30b2fd90a4beaa131cdcb5/src/markdown_vault_mcp/fts_index.py#L299-L339));
- configurable title field, required frontmatter, indexed fields, searchable fields và glob
  exclusion
  ([README, dòng 182–195](https://github.com/pvliesdonk/markdown-vault-mcp/blob/c0c68f9c74a483a6fe30b2fd90a4beaa131cdcb5/README.md#L182-L195));
- parser đọc wikilink và relative link, giữ fragment/alias text
  ([`scanner.py`, dòng 977–1018](https://github.com/pvliesdonk/markdown-vault-mcp/blob/c0c68f9c74a483a6fe30b2fd90a4beaa131cdcb5/src/markdown_vault_mcp/scanner.py#L977-L1018));
- graph facet cho backlinks, outlinks và shortest path
  ([`facets/graph.py`, dòng 60–164](https://github.com/pvliesdonk/markdown-vault-mcp/blob/c0c68f9c74a483a6fe30b2fd90a4beaa131cdcb5/src/markdown_vault_mcp/facets/graph.py#L60-L164)).

Ta có thể map `title`, `tags`, `aliases` vào searchable/indexed frontmatter và áp trọng số
FTS. Exclusion boundary của vault cũng biểu diễn được bằng `EXCLUDE` cộng
`REQUIRED_FIELDS`, gồm `_templates/**`, `_inbox/**`, `outputs/**`, bookkeeping và mọi file
không có governed frontmatter. Upstream lọc excluded path trước cả hashing
([`tracker.py`, dòng 78–122](https://github.com/pvliesdonk/markdown-vault-mcp/blob/c0c68f9c74a483a6fe30b2fd90a4beaa131cdcb5/src/markdown_vault_mcp/tracker.py#L78-L122)).

Graph không tự mở rộng trong `search`; `vault_policy` phải lấy candidate symbolic rồi gọi
backlink/outlink để mở rộng. Đây đúng là phần orchestration riêng của D-04, không phải lý do
viết lại index.

### Semantic

Upstream hỗ trợ ba backend embedding: FastEmbed local, Ollama và OpenAI-compatible API;
default FastEmbed là `BAAI/bge-small-en-v1.5`
([README, dòng 212–227](https://github.com/pvliesdonk/markdown-vault-mcp/blob/c0c68f9c74a483a6fe30b2fd90a4beaa131cdcb5/README.md#L212-L227)).
Vector search là cosine similarity bằng phép nhân ma trận NumPy trên toàn bộ vector rồi
sort top-k, tức linear scan
([`vector_index.py`, dòng 338–385](https://github.com/pvliesdonk/markdown-vault-mcp/blob/c0c68f9c74a483a6fe30b2fd90a4beaa131cdcb5/src/markdown_vault_mcp/vector_index.py#L338-L385)).

Với khoảng 649 atomic notes, linear scan giúp tránh vận hành thêm vector database. Đây là
đánh giá kiến trúc, chưa phải benchmark: truth suite phải ghi p50/p95 query latency và RAM
trên corpus thật trước Gate 3.

Không dùng `mode="hybrid"` làm implementation D-04. Upstream chạy FTS và vector song song rồi
RRF
([`managers/search.py`, dòng 731–819](https://github.com/pvliesdonk/markdown-vault-mcp/blob/c0c68f9c74a483a6fe30b2fd90a4beaa131cdcb5/src/markdown_vault_mcp/managers/search.py#L731-L819));
D-04 yêu cầu symbolic trước, semantic chỉ fallback/rerank. Wrapper phải gọi các mode riêng.

Vì câu hỏi Lark có thể là tiếng Việt trong khi default embedding là model English nhỏ,
embedding model là tham số phải benchmark. Ưu tiên backend local; không gửi raw vault tới
provider bên ngoài nếu chưa có quyết định bảo mật riêng. Không giả định endpoint 9router chat
hiện tại cũng hỗ trợ embeddings.

## 2. Commit binding và reread contract

### Những gì upstream có

- mỗi file được hash SHA-256 và state lưu `path → digest`
  ([`tracker.py`, dòng 38–48](https://github.com/pvliesdonk/markdown-vault-mcp/blob/c0c68f9c74a483a6fe30b2fd90a4beaa131cdcb5/src/markdown_vault_mcp/tracker.py#L38-L48));
- forced rebuild public API: `build_index(force=True)` và
  `build_embeddings(force=True)`
  ([`facets/index.py`, dòng 130–168](https://github.com/pvliesdonk/markdown-vault-mcp/blob/c0c68f9c74a483a6fe30b2fd90a4beaa131cdcb5/src/markdown_vault_mcp/facets/index.py#L130-L168));
- `Vault.reader.read()` đọc document từ disk, không bắt buộc dùng bản content trong index
  ([`facets/reader.py`, dòng 111–127](https://github.com/pvliesdonk/markdown-vault-mcp/blob/c0c68f9c74a483a6fe30b2fd90a4beaa131cdcb5/src/markdown_vault_mcp/facets/reader.py#L111-L127));
- có library API chính thức, nên không cần đi qua MCP server upstream
  ([README, dòng 117–126](https://github.com/pvliesdonk/markdown-vault-mcp/blob/c0c68f9c74a483a6fe30b2fd90a4beaa131cdcb5/README.md#L117-L126)).

Các primitive này cho phép ta bọc contract D-04 mà không sửa/fork upstream.

### Những gì upstream không có

Không có metadata bind index với git commit SHA. State của index là hash từng file và
provenance của model/chunk/frontmatter config, không phải `git rev-parse HEAD`. Boot lifecycle
cũng submit build/reindex/embeddings bất đồng bộ rồi coi `index_stale` là trạng thái có thể
phục vụ
([`domain.py`, dòng 130–161](https://github.com/pvliesdonk/markdown-vault-mcp/blob/c0c68f9c74a483a6fe30b2fd90a4beaa131cdcb5/src/markdown_vault_mcp/domain.py#L130-L161)).

Thậm chí khi caller yêu cầu đợi pending writes, timeout mặc định vẫn trả kết quả cũ kèm
`index_stale=True`
([README, dòng 195–196](https://github.com/pvliesdonk/markdown-vault-mcp/blob/c0c68f9c74a483a6fe30b2fd90a4beaa131cdcb5/README.md#L195-L196),
[`reader.py`, dòng 74–110](https://github.com/pvliesdonk/markdown-vault-mcp/blob/c0c68f9c74a483a6fe30b2fd90a4beaa131cdcb5/src/markdown_vault_mcp/_server_tools/reader.py#L74-L110)).
Điều này trái invariant “`index_stale` không tồn tại trong production”.

Search MCP trả snippet và toàn bộ parsed frontmatter; read MCP trả raw file gồm frontmatter
([`reader.py`, dòng 87–105](https://github.com/pvliesdonk/markdown-vault-mcp/blob/c0c68f9c74a483a6fe30b2fd90a4beaa131cdcb5/src/markdown_vault_mcp/_server_tools/reader.py#L87-L105),
[dòng 139–197](https://github.com/pvliesdonk/markdown-vault-mcp/blob/c0c68f9c74a483a6fe30b2fd90a4beaa131cdcb5/src/markdown_vault_mcp/_server_tools/reader.py#L139-L197)).
Nếu Hermes gọi trực tiếp, model nhìn thấy `authority`, `status`, `freshness` và có đường đọc
raw vault — vi phạm D-04a dù server đặt `READ_ONLY=true`.

### Adapter contract bắt buộc

Một query production phải chạy trong `vault_policy` như sau:

1. lấy `HEAD` của `gonzo-vault`; so với `indexed_commit` nằm ngoài vault;
2. khác SHA → block request, `build_index(force=True)`,
   `build_embeddings(force=True)`, ghi SHA **sau khi cả hai thành công**;
3. chạy frontmatter/type filter → keyword → graph expansion → semantic fallback/rerank;
4. coi kết quả index chỉ là `{path, score, reason}` candidate; bỏ snippet và raw
   frontmatter khỏi output;
5. đọc lại từng path từ filesystem, parse governance fields, tính `use_class`, open-question
   và multi-note flags;
6. kiểm lại `HEAD` ngay trước response; nếu đổi thì bỏ kết quả và restart query;
7. chỉ trả content/citation đã sanitize qua MCP do `gonzo/vault_policy` sở hữu.

Nếu rebuild hoặc reread lỗi, fail closed; không trả cached/stale candidate.

## 3. Bảo trì và corpus ~649 note

Những phần upstream thực sự thay cho code ta phải sở hữu gồm:

- Markdown/frontmatter parser, heading chunker và link parser;
- SQLite FTS schema, BM25 scoring/weights, structured filters và snippets;
- vector provider abstraction, persistence, compatibility và cosine search;
- file hash tracker, incremental reconcile, atomic sidecar writes và concurrency;
- backlinks/outlinks/shortest-path graph.

Chỉ riêng các module tương ứng ở upstream hiện khoảng 7.7k dòng Python. Số dòng không tự
chứng minh chất lượng, nhưng cho thấy đây là một khối implementation và test surface có ý
nghĩa mà dependency thay thế. Với corpus 649 note, tự viết các cơ chế đó không tạo lợi thế
kiểm soát tương xứng.

Phần **không giảm** và vẫn phải do Gonzo bảo trì là phần quan trọng về nghiệp vụ:

- exclusion allowlist của corpus governed;
- commit binding/fail-closed freshness;
- symbolic-first orchestration và graph expansion policy;
- `use_class`, open-question lane, multi-cite flags;
- reread + sanitize + citation contract;
- truth suite và tuning artifact.

Rủi ro dependency là upstream còn trẻ và đổi nhanh. Giảm bằng cách chỉ dùng public `Vault`
facets, pin `v3.1.0`, viết contract tests quanh adapter, và không dựa vào server/tool schema.
Nếu một upgrade phá adapter, giữ version pin; dependency không được trở thành blocker Gate 3.

## 4. Deployment và security boundary

Hình dạng được phép:

```text
Hermes model
    │ MCP: chỉ tool của gonzo/vault_policy
    ▼
vault_policy process trên Mac host
    ├─ policy + commit gate + sanitize
    └─ import markdown_vault_mcp.Vault (library, private)
           ├─ raw /Users/aigonzo/Company/gonzo-vault
           └─ private index/state/embeddings ngoài vault repo
```

Không được:

- thêm `markdown-vault-mcp serve` vào MCP config của Hermes;
- expose upstream stdio/HTTP endpoint cho agent;
- mount raw vault hoặc index/state files vào Docker tool environment;
- dùng `READ_ONLY=true` như thay thế cho policy — nó chỉ chặn write tools, không chặn raw
  search/read;
- bật summarize hoặc external embedding provider mà chưa quyết việc raw note rời host.

Upstream mặc định đặt tracker state dưới source dir và index có thể giữ chunk/frontmatter;
production phải cấu hình `INDEX_PATH`, `STATE_PATH`, `EMBEDDINGS_PATH` sang private state dir
ngoài `gonzo-vault`, permission chỉ process `vault_policy` đọc được. Raw repo không bị tạo
file untracked và Hermes Docker không được mount private state dir.

## So sánh với `tobi/qmd`

Hermes đã ship optional skill cho [`tobi/qmd`](https://github.com/tobi/qmd), nên đây là
alternative cần loại trừ rõ ràng, không phải bỏ sót.

| Thuộc tính | `pvliesdonk/markdown-vault-mcp` | `tobi/qmd` |
|---|---|---|
| Runtime | Python library cùng process policy | Node 22/Bun library hoặc daemon |
| Symbolic | FTS5/BM25 + frontmatter fields/filter + heading chunks | BM25 trên filepath/title/body; collection filter |
| Graph | Wikilink/relative-link graph API | Không có vault link graph trong public store/MCP surface |
| Semantic | FastEmbed, Ollama hoặc OpenAI-compatible; vector cosine | Local GGUF embed + RRF + cross-encoder rerank + query expansion |
| Freshness | Hash reconcile nhưng có thể trả `index_stale` | `update()`/`embed()` tách riêng; status chỉ báo `needsEmbedding` |
| Reread | Public reader đọc disk | `getDocumentBody` đọc body đã lưu trong SQLite index |
| Raw bypass nếu expose MCP | `search`/`read` trả raw frontmatter/content | `get`/`multi_get` trả raw indexed content |
| Resource | Default được upstream gọi là memory-light; semantic provider thay được | Ba model mặc định khoảng 300 MB + 640 MB + 1.1 GB, chưa tính context RAM/VRAM |

QMD là công cụ search cá nhân tốt: BM25, vector, RRF/rerank, ignore glob và SDK rõ ràng
([README](https://github.com/tobi/qmd/blob/e428df76bc0274d9e93eb7ca3e95673315c42e90/README.md#L1-L39),
[`QMDStore` API](https://github.com/tobi/qmd/blob/e428df76bc0274d9e93eb7ca3e95673315c42e90/src/index.ts#L221-L317)).
Nó cũng có ignore patterns và không follow symlink khi scan
([`store.ts`, dòng 1366–1395](https://github.com/tobi/qmd/blob/e428df76bc0274d9e93eb7ca3e95673315c42e90/src/store.ts#L1366-L1395)).

Nhưng nó kém fit hơn cho governed vault:

- MCP `get` và `multi_get` trả nguyên body
  ([`server.ts`, dòng 390–535](https://github.com/tobi/qmd/blob/e428df76bc0274d9e93eb7ca3e95673315c42e90/src/mcp/server.ts#L390-L535));
- SDK retrieval lấy body từ index DB, không reread original file
  ([`index.ts`, dòng 431–437](https://github.com/tobi/qmd/blob/e428df76bc0274d9e93eb7ca3e95673315c42e90/src/index.ts#L431-L437),
  [`store.ts`, dòng 2948–2958](https://github.com/tobi/qmd/blob/e428df76bc0274d9e93eb7ca3e95673315c42e90/src/store.ts#L2948-L2958));
- update scan và embedding là hai operation riêng; query không bind với git commit
  ([`index.ts`, dòng 286–312](https://github.com/tobi/qmd/blob/e428df76bc0274d9e93eb7ca3e95673315c42e90/src/index.ts#L286-L312));
- default full pipeline tải ba GGUF model tổng khoảng 2.04 GB; code giữ model warm và
  context rerank có thể nặng đáng kể
  ([README, dòng 513–523](https://github.com/tobi/qmd/blob/e428df76bc0274d9e93eb7ca3e95673315c42e90/README.md#L513-L523),
  [`llm.ts`, dòng 570–583](https://github.com/tobi/qmd/blob/e428df76bc0274d9e93eb7ca3e95673315c42e90/src/llm.ts#L570-L583),
  [dòng 1169–1205](https://github.com/tobi/qmd/blob/e428df76bc0274d9e93eb7ca3e95673315c42e90/src/llm.ts#L1169-L1205)).

Vì vậy giữ QMD ở vai optional skill cho personal/un-governed document search. Không dùng
QMD MCP hoặc terminal command làm cửa vào company vault. Nếu sau này benchmark cho thấy
reranker của QMD vượt trội, có thể nghiên cứu riêng một rerank adapter chỉ nhận sanitized
candidate text; không thay boundary `vault_policy`.

## Quyết định đề xuất cho ticket 0014

**Adopt `pvliesdonk/markdown-vault-mcp@v3.1.0` làm private in-process index engine; tự viết
adapter + policy. Không adopt MCP server, prompts, write tools, git sync, summarize hay UI.**

Prototype kế tiếp nên chứng minh đúng năm điều trước khi giữ dependency:

1. exclusions cho corpus thật cho đúng 649 governed notes tại snapshot đã chốt;
2. commit đổi thì query block và rebuild; không bao giờ trả `index_stale`;
3. output không có raw `authority/status/freshness` và reread từ file gốc;
4. symbolic → graph → semantic chạy đúng thứ tự, truth suite pass;
5. p50/p95 latency, peak RSS và index size hợp lý trên Mac pilot.

Không đạt bất kỳ điều nào mà phải fork upstream sâu mới sửa được thì bỏ dependency và quay
về implementation nội bộ; ticket này không được trở thành blocker.
