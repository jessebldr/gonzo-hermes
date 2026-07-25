# `profiles` — 4 vai, 4 process, không hơn

Quyết định chi phối: **D-01** (4 vai), **D-03** (process-per-profile). Workstream ①. Gate 2.

Thư mục config, không phải package Python — cố ý không có `__init__.py`.

| Profile | Nhiệm vụ | Được phép | KHÔNG được phép |
|---|---|---|---|
| `mkt-orchestrator` | Nhận brief, tạo thẻ cha + con, gán lane, ráp output, trả lời thread. **Đồng thời host Lark gateway.** | Kanban full, vault read | Tự làm deliverable, ghi vault |
| `mkt-research` | Evidence ngoài + tri thức approved → memo gắn vào thẻ | Vault read, web, draft-write | Đưa memo chưa duyệt thành "fact" |
| `mkt-creative` | Brief + memo → hooks/scripts/variants, ghi vào Base | Vault read, Base write, image/video tools | Dùng note `status: draft` làm tri thức nền |
| `mkt-reviewer` | Soi từng claim với note approved, viết publication-candidate (draft), gửi card adopt | Vault read + draft-write, gọi adoption card | **Promote.** Và không đưa doctrine tự suy lên card adopt |

## Bất biến

- Mỗi profile có **session, memory, skills, staging, scanner và credential riêng.**
  Credential riêng là thứ biến audit log từ "Hermes ghi cái này" thành "`mkt-reviewer` ghi
  cái này lúc X" — đúng chất lượng provenance mà vault được dựng lên để có.
- **Không shared context, không shared memory.** Phối hợp đi qua `gonzo/kanban_bus/`.
- Tiêu chí đậu Gate 2: ghi một fact đặc trưng vào memory `mkt-research` → `mkt-creative`
  **phải không biết**; và audit log chỉ đúng profile đã thực hiện từng hành động.
- Thêm vai = thêm một process nữa, không redesign (P6). Profile thứ 5 `ops` là mở rộng đã dự trù.

## Chưa chốt

RAM thực tế của 4 process trên Mac mini — **đo ở Gate 2**, không đoán. Cost cap per-profile
thực thi ở 9router (Hermes chỉ tracking) — chốt cấu hình ở Gate 1.

Trạng thái: **stub.**
