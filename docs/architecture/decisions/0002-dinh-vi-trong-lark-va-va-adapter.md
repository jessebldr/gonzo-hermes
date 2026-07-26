# 0002 — Định vị trong Lark, và quyết định vá adapter trong fork

- **Ngày:** 2026-07-26
- **Trạng thái:** accepted
- **Thay đổi:** D-08 (cơ chế định vị). Kích hoạt rủi ro #1 và D-19.
- **Người quyết:** `tech-lead` (Khánh)

## Bối cảnh

D-08 giả định: *"User reply vào message hook nào, event mang `parent_id`/`root_id` → agent
biết chính xác đang sửa hook nào."* Giả định này chưa từng được kiểm. Phiên 2026-07-26 kiểm
nó trên một bot Lark thật, group topic-mode thật.

## Phát hiện 1 — Lark Topic-mode không có định vị theo message

Ba nguồn bằng chứng độc lập, cùng kết luận:

| Nguồn | Kết quả |
|---|---|
| Giao diện | Trong topic, nút Reply chỉ chèn `@Bot`; không có khối "Reply to…" như group thường |
| API Lark | `parent_id == root_id` ở **cả 4** message thử nghiệm, luôn bằng root của topic |
| Hành vi agent | Hỏi "cái này ý gì" sau khi Reply → agent đoán mò 3 khả năng vì không có con trỏ |

Mẫu dữ liệu thật:

```
text  : "@_user_1 cái này ý gì"        ← đã bấm Reply vào một message cụ thể
parent: om_x100b696f5a3324a0eebaf6cb32d4b26
root  : om_x100b696f5a3324a0eebaf6cb32d4b26   ← bằng nhau
thread: omt_19003986cc8f1947
```

**Đây là giới hạn của Lark, không phải của Hermes.** Adapter đọc đúng cả ba trường
(`adapter.py:3296–3300`); Lark đơn giản không điền parent riêng bên trong topic. Đổi runtime
khác không thay đổi gì.

## Quyết định 1 — D-08 chuyển từ `parent_id` sang `card_id`

Câu chữ gốc của D-08 vốn đã viết *"5 hooks = 5 message/**card** riêng"* — card đã nằm sẵn
trong thiết kế. Cái đổi là **trường định vị**: không phải `parent_id` của reply, mà `value`
+ `card_id` của card.

Đã kiểm bằng thực nghiệm: bấm nút trên card → callback tới gateway, và **`value` giữ nguyên
vẹn**. Adapter dựng thành text `/card button {"item":"creative-2"}`. Định vị hoạt động.

Phương án đã loại:

- **Dùng group thường thay group Topic** — Reply thật, `parent_id` thật, nhưng mất cấu trúc
  topic, D-07 sụp, quay lại đúng bài "DM bãi rác" mà D-08 sinh ra để giải.
- **1 topic = 1 deliverable** — topic thành địa chỉ, nhưng 5 hook = 5 topic, phá "1 task =
  1 topic".
- **Quy ước chữ** (*"sửa hook 1"*) — không có bảo đảm cấu trúc; đúng phản mẫu "gate bằng
  lời dặn" mà doc bác bỏ.

**Hệ quả phải chấp nhận: card từ "UX cho đẹp" thành hạ tầng chịu lực.** Ticket đo giới hạn
card không còn là mục kiểm tra Gate 0 — nó là thứ mô hình tương tác đứng lên. Giới hạn số
nút và kích thước payload sẽ trực tiếp chặn số deliverable trên một lượt trả lời.

## Phát hiện 2 — adapter có ba lỗi trên đường card

Callback tới nơi nhưng không dùng được, vì:

| # | Lỗi | Bằng chứng | Hệ quả |
|---|---|---|---|
| 1 | `/card` không phải lệnh được đăng ký | `Unrecognized slash command /card from feishu` | Payload về tới nơi rồi bị vứt |
| 2 | `message_id=token` — token là card id `c-…`, không phải `om_…` (`adapter.py:3053`) | `Invalid ids: [c-67998aca…]` code `99992354`, **cả fallback cũng fail** | Bot không trả lời được gì |
| 3 | `thread_id=None` gán cứng (`adapter.py:3042`) | — | Agent không biết card thuộc topic nào |

Cả ba vá được bằng dữ liệu **đã có sẵn**: `context.open_message_id` (một `om_…`) nằm trong
chính event, cạnh `open_chat_id` mà adapter đang đọc.

## Quyết định 2 — vá trong fork, không viết adapter riêng

Doc đã dự đoán chính xác tình huống này. Rủi ro #1: *"chấp nhận vá adapter 20-30% — và vá đó
là **commit trong fork** (D-19), không phải patch script bên ngoài."*

Giá phải trả, ghi rõ để sau này không ai ngạc nhiên: `plugins/platforms/feishu/` là **file
upstream**, và là file upstream sửa thường xuyên. Vá nó thêm một dòng **đắt** vào bảng
"Upstream files đã sửa" của [`gonzo/README.md`](../../../gonzo/README.md).

Phương án đã loại: **viết adapter Lark riêng trong `gonzo/`** để né conflict. Loại vì phải
bỏ đi ~17 file test và toàn bộ phần đã chạy được (WS long connection, mention gating,
allowlist, batching, dedup) chỉ để đổi lấy việc tránh giải conflict — lỗ.

## Những gì đã được chứng minh là chạy, giữ nguyên giá trị

- **WS long connection** — không cần tunnel, đúng D-20.
- **Topic → session**: hai topic → hai session key → hai agent session độc lập. **D-07 đứng
  vững, không cần vá.**
- **Session không bền**: bị evict sau ~1h nhàn rỗi. **Xác nhận giả định của D-02** — Kanban
  làm sổ cái là quyết định đúng, không phải thận trọng thừa.
- **Mô hình nhiều người dùng có sẵn**: `group_sessions_per_user` (mặc định `True`),
  `thread_sessions_per_user` (mặc định `False`) — xem `docs/session-lifecycle.md`.

## Quyết định 3 — một topic hoặc một group = một session dùng chung

Giữ `thread_sessions_per_user: false`, và **lật `group_sessions_per_user` về `false`**.
Một topic **là** một công việc (D-07), không phải một phòng chat. Tách session theo người
trong cùng một topic sẽ khiến hai người nhìn chung màn hình mà agent giữ hai câu chuyện.

Đặt ở `platforms.feishu.extra` trong config runtime.
