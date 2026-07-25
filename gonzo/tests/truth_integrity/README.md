# `truth_integrity` — 21 case, đã đóng băng

Xem `gonzo/tests/truth_integrity/../README.md` §① cho luật đầy đủ và ngưỡng.

| File | Là gì |
|---|---|
| `cases.yaml` | Bộ case **đã đóng băng**. 21 case, phủ 7 nhóm bắt buộc của D-17① + 4 nhóm nữa. |
| `FREEZE.md` | Digest sha256 của `cases.yaml`, ngày đóng băng, và bảng lịch sử mỗi lần đổi. |
| `test_case_set.py` | Tầng chạy **hôm nay**: kiểm chính bộ case, không gọi agent nào. |

## Hai tầng, và vì sao tách

**Tầng A — chạy hôm nay** (`test_case_set.py`, 34 test): kiểm bộ case đủ 18, phủ hết 7 nhóm,
mọi case đều có cả `then` lẫn `never`, digest khớp `FREEZE.md`, và — quan trọng nhất — **21
wire check** xác nhận từng `source.quote` vẫn xuất hiện nguyên văn trong file governance mà
nó viện dẫn. Sửa luật vault mà không sửa case thì suite đỏ. Đó chính là regression mà D-17①
đòi sau mọi thay đổi policy.

**Tầng B — từ Gate 3**: chạy thật 21 case qua agent, mỗi case 3 lần, ngưỡng 100%. Chưa tồn
tại vì chưa có runtime để chạy vào.

## Vì sao case không trỏ vào file vault cụ thể

Mỗi case khai báo **hình dạng vault nó cần** (`given`), không phải một path. Hai lý do, cả
hai đều đo được:

1. **Vault đang nở.** Hôm nay 59 note; `MIGRATION.md` cho thấy đích ~690. Một suite đóng
   băng mà hardcode `cite brands/kyperus/brand.md` sẽ vỡ vì corpus lớn lên — vỡ vì lý do
   không liên quan gì tới thứ nó canh.
2. **Vài hình dạng chưa tồn tại.** Vault hiện **không có note stale nào**: cả hai
   `operational-state` đều `freshness: event-driven`, mà theo `freshness-policy.md` thì
   loại đó **không có** `review_after`. Nên `stale-state-*` chưa có fixture thật, và hai
   note approved mâu thuẫn nhau cũng vậy.

Vật chất hoá `given` bằng vault thật hay bằng fixture là câu hỏi của Gate 3 — nó phụ thuộc
quyết định corpus. Đó là một ticket riêng, không phải việc của lần đóng băng này.

## Chạy

```bash
pytest gonzo/tests/truth_integrity/          # cần pyyaml
GONZO_VAULT_PATH=../gonzo-vault pytest ...   # mặc định đã dò sibling repo
```

Không tìm thấy vault → 21 wire check **skip** kèm lý do, 13 test còn lại vẫn chạy.
