# `gonzo/tests` — hai suite độc lập, cố ý không gộp điểm

Quyết định chi phối: **D-17**. Workstream ⑦.

"Đúng" với "hay" là hai thứ khác bản chất — gộp chung một điểm số thì cái thứ hai sẽ nuốt
cái thứ nhất. Nên tách hẳn.

## ① `truth_integrity/` — invariant, không phải chỉ số

**Viết, version-control và freeze TRƯỚC Gate 1.** Chỉ dựa vào luật trong `gonzo-vault/governance/`
— **không cần biết hệ mới trông ra sao**. Viết sau khi thấy hệ chạy = viết test theo hệ, và
lúc đó nó không còn kiểm được gì.

Tối thiểu **18 case cố định**, phủ: cite đúng note approved · gặp open-question đang hiệu lực
thì nói "chưa quyết" và **dừng** · không dùng `operational-state` đã quá `review_after` ·
không biến `evidence` thành company claim · không để tên nhân sự lọt vào output khách hàng ·
`draft` không đè `approved` · không dùng `authority` để tự phân xử conflict.

Mỗi case chạy **3 lần**. Ngưỡng: **100%, zero critical failure** — đây là invariant, nên
không có "95% là ổn". Chạy regression **từ Gate 3** và sau **mọi** thay đổi retrieval /
policy / prompt.

## ② Quality benchmark — không sống ở repo này

**24 task thật** chọn trước từ lịch sử: 8 research · 8 creative · 8 review/claim-check.
**Chạy hệ cũ và lưu baseline ở Gate 2**, trước khi hệ mới hoàn thiện — nếu không thì tới lúc
so đã không còn gì để so, và người so thì đã bỏ 6 tầng công sức vào một bên.

`marketing-lead` (Sơn) chấm **mù**, paired output; `company-lead` (Trung) spot-check các task
chạm business / pricing / brand. Ngưỡng: hệ mới **win hoặc tie ≥75%** số task · điểm trung
bình **không thấp hơn** hệ cũ · **không có** output sai nghiêm trọng hoặc customer-unsafe.

Đây là đánh giá của người, không phải test tự động — nên nó không nằm trong thư mục này.

## Quy ước

- Test của module trong `gonzo/` → ở đây. Test đụng Hermes core → `tests/` của upstream,
  cạnh test upstream, vì đó là chỗ nó sẽ conflict và cần được thấy.
- Không `__init__.py` trong thư mục test — giữ `gonzo.tests` khỏi bị đóng gói vào wheel.
- Tên file test phải duy nhất trên toàn `gonzo/tests/` (pytest rootdir-based collection).

Trạng thái: **trống. `truth_integrity/` là việc chặn Gate 1 và không phụ thuộc Hermes — làm được ngay.**
