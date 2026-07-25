# 0001 — Baseline fork và mô hình branch

- **Ngày:** 2026-07-25
- **Trạng thái:** accepted
- **Thực thi:** D-19 của [`../hermes-vault-agent-team-architecture.md`](../hermes-vault-agent-team-architecture.md)
- **Người sở hữu:** `vault-approver` / kỹ thuật (Khánh)

Đây là decision record của **repo runtime**, không phải của vault. Nó là tri thức về
Hermes, không phải tri thức công ty — P1 nói vault phải sống sót khi runtime bị thay, nên
quyết định loại này không được ghi vào `gonzo-vault`.

## Bối cảnh

D-19 yêu cầu chọn một commit/tag upstream làm baseline và fork từ đó, vì production chỉ
được chạy release tag của fork chứ không phải working tree. Chưa chọn thì không có gì để
build lên.

Upstream `NousResearch/hermes-agent` chạy rất nhanh: **1215 commit trong 5 ngày** giữa tag
`v2026.7.20` và `main` ngày 2026-07-25. Cadence tag khoảng một tuần một lần, nên "chờ tag
kế tiếp" không phải một lựa chọn trung lập — nó là chọn tụt lại thêm ~1200 commit nữa.

## Quyết định

**1. Baseline = upstream `main` @ `9823f15f6a4e2a10b6bede6338cbe0b7682a4c4e` (2026-07-25),**
đóng dấu bằng tag của chính chúng ta: **`gonzo-baseline/2026-07-25`**.

D-19 nói "commit/tag" — thứ nó thật sự đòi là một điểm cố định, có tên, tái tạo được. Một
SHA được tự đặt tên thoả điều đó ngang một tag upstream, và không phải chờ lịch phát hành
của người khác.

**2. Không chọn `v2026.7.20`** (`3ef6bbd20`, 2026-07-20), tag mới nhất của upstream, vì
đúng hai fix mà kiến trúc này phụ thuộc đã đáp **sau** tag đó:

| Commit | Nội dung | Chạm quyết định nào |
|---|---|---|
| `a31a31826` | `fix(approval)`: nâng gateway approval timeout lên 300s, stale-tap UX trung thực, offer Always trên prompt hỗn hợp | D-09, D-14 |
| `02d8cbade` | `fix(approval)`: honor `allow_session` trên mọi button adapter | D-09, D-14 |

Card duyệt là mặt phẳng hẹp nhất và load-bearing nhất của toàn hệ (D-14: authorization
**chỉ** đi qua callback ký bởi Lark). Bắt đầu từ một baseline đã biết là thiếu hai fix ở
đúng bề mặt đó nghĩa là tự chuốc một lớp bug mà upstream đã sửa xong.

Kèm theo, `d84e11af4` (`rip out brew + pip/PyPI wheel support`) cũng nằm sau tag. Gate 1 đã
định cài bằng uv, nên lấy baseline sau commit này là đi thẳng vào thế giới uv thay vì fork
từ một thế giới pip rồi phải theo sau.

**3. Mô hình branch — hai `main`, vai khác nhau:**

| Ref | Vai | Luật |
|---|---|---|
| `main` | Gương của upstream | **Không bao giờ commit lên.** Chỉ fast-forward từ `upstream/main`. Đây là nơi để đọc và cherry-pick *từ*. |
| `gonzo/main` | Nhánh tích hợp của công ty | Mọi thứ của ta merge vào đây. Bắt đầu tại `gonzo-baseline/2026-07-25`. |
| `gonzo/<tên>` | Nhánh việc | PR vào `gonzo/main`. Tầng sau được build song song trong khi tầng trước còn sửa (D-21). |
| `gonzo-v<X.Y.Z>` | Release tag | Cắt từ `gonzo/main`. **Mac mini production chỉ checkout tag loại này.** |

**4. Đồng bộ upstream: chỉ cherry-pick có chọn lọc.** Không auto-merge `upstream/main` vào
`gonzo/main` — merge mù vào một fork đã đổi dispatcher là cách nhanh nhất để mất một tuần
(D-19). Quy trình: fast-forward `main` → đọc `git log main` → cherry-pick fix cần thiết vào
một nhánh `gonzo/*` → PR.

**5. Vẫn đúng hai repo, không có repo thứ ba.** `gonzo-vault` giữ truth (P1);
`gonzo-hermes` **là** runtime chính thức (D-19). Code công ty nằm ở `gonzo/` trong chính
fork này — xem [`gonzo/README.md`](../../../gonzo/README.md). Tách thành một
`gonzo-runtime` riêng sẽ phải giữ hai tag khớp nhau mỗi lần deploy và làm sống lại đúng rủi
ro #7 ("implementation phân mảnh") mà D-19 sinh ra để chống.

## Phương án đã cân nhắc và loại

- **`v2026.7.20`** — được cái là điểm đã qua QA phát hành của upstream. Loại vì thiếu hai
  fix approval ở trên, và vì 1215 commit khoảng cách ngay ngày đầu khiến lần sync upstream
  đầu tiên đã là một khối khổng lồ.
- **Chờ tag kế tiếp (~2026-07-27)** — loại: hoãn mọi thứ để đổi lấy một nhãn, trong khi
  điều kiện thật (một điểm cố định, có tên) đã tự tạo được.
- **`origin/main` hiện tại (`e0dfcf275`)** — chỉ kém baseline đã chọn 16 commit, và 16
  commit đó là desktop/TUI/JS formatting, không liên quan. Loại vì không có lý do gì để
  chọn điểm cũ hơn khi cả hai đều không phải tag.

## Hệ quả

- Fork bắt đầu ở HEAD của một repo chạy ~240 commit/ngày, nên **fork sẽ lệch nhanh.** Đối
  sách là kỷ luật cherry-pick ở mục 4, và giữ danh sách "upstream files đã sửa" trong
  `gonzo/README.md` **ngắn** — mỗi dòng ở đó là một conflict phải giải bằng tay mãi mãi.
- Baseline này **không phải** một điểm đã qua QA phát hành của upstream. Đổi lại, ta có
  truth-integrity suite của chính mình (D-17①) làm lưới an toàn — nhưng suite đó phải được
  viết và freeze **trước Gate 1**, nếu không thì đánh đổi này chỉ có mặt trừ.
- Đảo được rẻ **ngay bây giờ, và chỉ bây giờ**: `gonzo/main` mới có một commit doc, chưa
  push. Đổi baseline lúc này là `git branch -f`. Sau vài chục commit thì không còn vậy.

## Việc còn mở

- Tag `gonzo-baseline/2026-07-25` và nhánh `gonzo/main` hiện **chỉ có ở local**, chưa push
  lên `origin`.
- Default branch trên GitHub vẫn là `main`. Nếu `gonzo/main` là nơi làm việc thật thì nên
  đổi default branch để PR mặc định nhắm đúng chỗ — thao tác trên GitHub, cần người quyết.
- Nhánh local `gonzo/architecture-docs` giờ đã thừa: commit doc của nó đã được cherry-pick
  sang `gonzo/main` (`2d0b81ed4`).
