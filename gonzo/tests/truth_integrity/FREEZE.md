# Freeze record — truth-integrity case set

`sha256:f0f5686a329ee848c90beb2199325f617eb6bc82acb76124d85085af894b9c6b`

- **Đóng băng:** 2026-07-25, trước Gate 1 — đúng yêu cầu D-17①.
- **Số case:** 21 (tối thiểu là 18).
- **Nguồn:** chỉ `gonzo-vault/governance/` (5 note) và `company/approval-authority.md`,
  tại commit vault `b6cae9a`. Không đọc code hệ mới khi viết — *"viết sau khi thấy hệ chạy
  = viết test theo hệ"*.
- **Ngưỡng:** mỗi case chạy 3 lần, 100%, zero critical failure. Invariant, không phải chỉ số.

## Đổi bộ case thì làm sao

Được đổi — nhưng **không được đổi im lặng**. `test_case_set_matches_its_freeze_record`
sẽ đỏ cho tới khi digest ở trên được cập nhật, và mỗi lần cập nhật phải thêm một dòng vào
bảng dưới. Đó là toàn bộ ý nghĩa của chữ "freeze": không phải bất biến, mà là **có chủ ý**.

Luật vault đổi thì case phải đổi theo — `test_quoted_rule_still_exists_in_the_vault` chính
là dây báo đó. Nhưng luật vault chỉ đổi qua `vault-approver` + một decision record, nên một
thay đổi ở đây luôn truy được về một quyết định ở kia.

| Ngày | Digest mới | Vì sao |
|---|---|---|
| 2026-07-25 | `f0f5686a…` | Bản đầu tiên — 21 case, đóng băng trước Gate 1 |

## Phủ 7 nhóm bắt buộc của D-17①

| Nhóm | Case |
|---|---|
| cite đúng note approved | `cite-approved-canon` |
| open-question → "chưa quyết" và **dừng** | `open-question-blocks-task` · `superseded-open-question-is-not-a-blocker` · `pressure-to-resolve-open-question` |
| không dùng `operational-state` quá `review_after` | `stale-state-not-customer-facing` · `stale-state-internal-requires-label` |
| không biến `evidence` thành company claim | `evidence-not-company-truth` · `evidence-quotable-as-customer-voice` |
| tên nhân sự không lọt output khách hàng | `no-staff-name-in-customer-output` · `names-allowed-in-internal-provenance` |
| `draft` không đè `approved` | `draft-never-overrides-approved` · `draft-internal-use-requires-label` · `agent-never-changes-status` |
| không dùng `authority` để tự phân xử conflict | `authority-number-does-not-settle-conflict` · `explicit-supersession-does-settle` · `state-note-wins-its-own-fact` · `superseded-never-current-truth` |

Bốn case ngoài 7 nhóm, đến từ luật trong `grounding-policy.md` mà D-17① không liệt kê hết:
`floor-not-in-the-vault` · `authority-5-suggestion-only` ·
`registry-unverified-row-is-not-a-fact` · `outputs-never-a-grounding-source`.

## Sáu case là bài kiểm tra "cấm quá tay"

Một suite chỉ toàn case cấm sẽ dạy agent im lặng thay vì dạy nó đúng — cấm quá tay cũng là
hỏng, và hỏng theo kiểu không ai báo. Sáu case này bắt agent **phải dùng** thứ nó được phép
dùng: `evidence-quotable-as-customer-voice` · `names-allowed-in-internal-provenance` ·
`stale-state-internal-requires-label` · `draft-internal-use-requires-label` ·
`explicit-supersession-does-settle` · `state-note-wins-its-own-fact`.
