# `scanner` — gate trước khi load, không phải audit sau khi hỏng

Quyết định chi phối: **D-15**, kèm **D-06** (memory hành vi, không fact) và **D-12** (tự do
trong vùng, gate ở biên). Workstream ⑥. Gate 2.

Self-created skill là kênh ghi truth **thứ hai và nguy hiểm hơn vault**: nó không phải note
nên `validate_vault.py` không thấy, nhưng nó được nạp thẳng vào context mỗi phiên — tức
authority thực tế **cao hơn** note approved. Và Hermes chết thì nó chết theo, trái P1.

## Luật

**Được tự ghi và tự activate** (procedural): workflow · cách dùng tool · task decomposition ·
formatting · bài học từ thất bại · quy trình verification.

**Không được tồn tại dưới dạng active instruction** (factual): giá · phần trăm và threshold ·
product claim · operational-state · company/brand policy · bất kỳ fact nào đã có canonical
home trong vault.

## Cơ chế

1. Agent ghi memory/skill vào **staging**, chưa được load.
2. Scanner chạy **trước khi** file được nạp vào context.
3. Phát hiện business fact → **tự rewrite thành vault lookup** (literal → lời gọi vault-read
   tại runtime).
4. Lint lại: pass → tự activate · rewrite thất bại → **quarantine + log** · secret / prompt
   injection / mưu toan bypass vault → **hard block**.
5. Cron hygiene chỉ để audit drift + đọc git diff, **không phải gate chính**.
6. Memory/skill dir được git-track trong repo này (không phải vault) để rollback được và để
   review nhìn 6 dòng diff thay vì đọc lại 4 file.

## Bất biến

- Một literal như `$419` trong skill/memory **active** là **error**, không phải warning: nó
  sao chép một fact có single home trong vault, và bản sao đó sẽ không đổi khi giá đổi. Chỉ
  được phép trong test fixture đã loại khỏi production loader.
- **Không có bước người duyệt memory/skill định kỳ.** Hệ tự xử lý; chỉ alert khi rewrite
  thất bại hoặc chạm red-zone.
- Gate này gate **truth**, không gate **hành vi**. Siết hành vi để vá là cách hệ trước làm
  agent rigid.

Trạng thái: **stub.**
