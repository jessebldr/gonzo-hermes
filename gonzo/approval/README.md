# `approval` — mở phiên duyệt, không cấp phép duyệt

Quyết định chi phối: **D-14** (adoption kiểm được bằng máy), **D-13** (thế nào là
adoption event). Workstream ⑤. Gate 5.

Agent chỉ được làm đúng 2 việc khi người phát biểu một rule trong chat: ghi
`status: draft`, và **xin service này mở phiên duyệt**. Không hơn. Agent không truyền cờ
`adopted=true`, không cầm token, không gọi promote.

## Service làm gì

1. Tự tính `content_hash` của draft — không nhận hash do agent đưa.
2. Tự sinh one-time token/nonce.
3. Lưu bản ghi `{card_id, draft_path, content_hash, approver_role, expiry, used=false}`.
   Bảng này dùng chung với routing table của `lark_io_broker` (D-20) — không phải hạ tầng mới.
4. Render card "Adopt as doctrine", **bắt buộc hiện 4 thứ**: ①normalized rule ②`type`
   ③phạm vi ảnh hưởng (note nào bị đụng/supersede) ④nút **"Adopt as doctrine"** — không
   dùng nút "Approve" chung chung, vì nút chung chung là thứ người ta bấm mà không đọc.

## Bất biến

- **Gate nằm ở nội dung card, không ở cái nút.** Card không hiện normalized rule thì lần
  bấm đó không phải adoption event, dù nút có tên gì.
- "ok" / "hay" / emoji / reaction **chỉ** có thể sinh draft + card. Không có callback thì
  không có commit — đúng do **cấu trúc**, không do model ngoan.
- Doctrine agent **tự suy ra** không được lên card adopt: phải hỏi `company-lead` /
  `subject-matter-owner (<domain>)`, hoặc mở `open-question` trong vault (D-13).

Trạng thái: **stub.**
