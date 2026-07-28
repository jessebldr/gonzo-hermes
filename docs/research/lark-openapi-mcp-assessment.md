# Đánh giá `larksuite/lark-openapi-mcp` cho D-10/D-20

Ngày đánh giá: 2026-07-28

Snapshot upstream: [`21920354ec6e3966b52e89152620c5085e496b55`](https://github.com/larksuite/lark-openapi-mcp/commit/21920354ec6e3966b52e89152620c5085e496b55)

Phạm vi: Wayfinder ticket **“lark-openapi-mcp có dùng được không”** — xác minh dự án còn
tồn tại/sống, license có dùng thương mại được không, và có phủ `write_base_row` cùng card
API mà D-10/D-20 cần không.

## Kết luận

`larksuite/lark-openapi-mcp` là MCP chính chủ, public và chưa archive. License MIT cho phép
dùng, sửa, phân phối, sublicense và bán trong sản phẩm thương mại nếu giữ copyright +
permission notice. Về primitive API, nó **có đủ** để tạo/cập nhật dòng Base, gửi interactive
card và PATCH card đã gửi.

Nhưng nó **không phải implementation của D-20**. Đây là generic OpenAPI bridge với catalog
rất rộng; nó không có signed capability theo `task_id`/`owner_profile`/`topic_root_id`,
không có durable routing table, content-hash ledger, idempotency/recovery, hay receiver cho
card-action callback. Cho worker/model gọi MCP này trực tiếp sẽ phá narrow capability
boundary dù chỉ bật một số tool.

**Quyết định triển khai:** giữ `gonzo/lark_io_broker` là boundary do Gonzo sở hữu. Broker
gọi trực tiếp Lark OpenAPI qua official Python SDK `lark_oapi`, tái dùng connection/client
pattern mà Feishu adapter hiện tại đã chạy thật. Không thêm MCP process vào production
path ở Gate 2. Official MCP chỉ giữ làm reference catalog/prototype tùy chọn, không là
dependency kiến trúc.

Điều này sửa premise cũ của D-10: deliverable vẫn sống ở Base, nhưng `write_base_row` đi
qua capability broker — không “giao hẳn việc ghi Base” cho MCP upstream.

## 1. Dự án còn tồn tại và sống không?

Repo tự nhận là “Feishu/Lark official OpenAPI MCP” và vẫn public, không archive
([README, dòng 15–17](https://github.com/larksuite/lark-openapi-mcp/blob/21920354ec6e3966b52e89152620c5085e496b55/README.md#L15-L17)).

Tín hiệu maintenance tại snapshot:

- HEAD là `21920354...`, commit cuối ngày 2025-08-14
  ([commit](https://github.com/larksuite/lark-openapi-mcp/commit/21920354ec6e3966b52e89152620c5085e496b55));
- release mới nhất là `v0.5.1`, phát hành 2025-08-06
  ([release](https://github.com/larksuite/lark-openapi-mcp/releases/tag/v0.5.1));
- README vẫn ghi **Beta** và cảnh báo feature/API có thể đổi
  ([README, dòng 15](https://github.com/larksuite/lark-openapi-mcp/blob/21920354ec6e3966b52e89152620c5085e496b55/README.md#L15));
- tới ngày đánh giá đã gần 11.5 tháng không có commit/release mới.

Kết luận chính xác là: **không chết, không bị tuyên bố abandoned, nhưng maintenance nguội
và chưa có cơ sở gọi là actively maintained**. Pin version/SHA và không đặt security
boundary của Gonzo lên hành vi beta của nó.

## 2. License có dùng thương mại được không?

Có. Repo và package khai MIT
([LICENSE](https://github.com/larksuite/lark-openapi-mcp/blob/21920354ec6e3966b52e89152620c5085e496b55/LICENSE),
[`package.json`, dòng 2–10](https://github.com/larksuite/lark-openapi-mcp/blob/21920354ec6e3966b52e89152620c5085e496b55/package.json#L2-L10)).

MIT cho phép “use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies”
([LICENSE, dòng 3–7](https://github.com/larksuite/lark-openapi-mcp/blob/21920354ec6e3966b52e89152620c5085e496b55/LICENSE#L3-L7)).

Điều kiện cần giữ:

- copyright notice và permission notice trong mọi copy/substantial portion;
- chấp nhận software “AS IS”, không warranty/liability
  ([LICENSE, dòng 7–9](https://github.com/larksuite/lark-openapi-mcp/blob/21920354ec6e3966b52e89152620c5085e496b55/LICENSE#L7-L9)).

License source code không thay thế điều khoản dịch vụ Lark: app credentials, tenant
entitlement và API scopes vẫn phải cấu hình đúng.

## 3. Tool catalog hoạt động thế nào?

Catalog là registry TypeScript generate sẵn, không phải runtime discovery từ OpenAPI:

- các nhóm `bitableV1Tools`, `cardkitV1Tools`, `imV1Tools`, ... được ghép vào `GenTools`
  ([generated index, dòng 177–210](https://github.com/larksuite/lark-openapi-mcp/blob/21920354ec6e3966b52e89152620c5085e496b55/src/mcp-tool/tools/en/gen-tools/index.ts#L177-L210));
- `AllTools` ghép generated tools và builtin tools
  ([tools index, dòng 1–11](https://github.com/larksuite/lark-openapi-mcp/blob/21920354ec6e3966b52e89152620c5085e496b55/src/mcp-tool/tools/index.ts#L1-L11));
- không truyền `-t` thì server dùng default tool names
  ([`mcp-tool.ts`, dòng 45–55](https://github.com/larksuite/lark-openapi-mcp/blob/21920354ec6e3966b52e89152620c5085e496b55/src/mcp-tool/mcp-tool.ts#L45-L55));
- truyền `-t` thì danh sách đó trở thành allowlist sau khi expand preset và dedupe
  ([`init.ts`, dòng 19–35](https://github.com/larksuite/lark-openapi-mcp/blob/21920354ec6e3966b52e89152620c5085e496b55/src/mcp-server/shared/init.ts#L19-L35));
- từng tool còn lại được đăng ký vào MCP server bằng schema + handler
  ([`mcp-tool.ts`, dòng 170–176](https://github.com/larksuite/lark-openapi-mcp/blob/21920354ec6e3966b52e89152620c5085e496b55/src/mcp-tool/mcp-tool.ts#L170-L176)).

Preset và individual tool có thể kết hợp
([preset docs, dòng 31–49](https://github.com/larksuite/lark-openapi-mcp/blob/21920354ec6e3966b52e89152620c5085e496b55/docs/reference/tool-presets/presets.md#L31-L49)).
Tuy nhiên README nói API ngoài preset chưa qua compatibility testing
([README, dòng 159–183](https://github.com/larksuite/lark-openapi-mcp/blob/21920354ec6e3966b52e89152620c5085e496b55/README.md#L159-L183)).

## 4. Có phủ `write_base_row` không?

Có. Generated catalog có đủ primitive cần thiết:

| Nhu cầu | Tool/API | Bằng chứng |
|---|---|---|
| Tạo một dòng | `bitable.v1.appTableRecord.create` | [`bitable_v1.ts`, dòng 1512–1526](https://github.com/larksuite/lark-openapi-mcp/blob/21920354ec6e3966b52e89152620c5085e496b55/src/mcp-tool/tools/en/gen-tools/zod/bitable_v1.ts#L1512-L1526) |
| Sửa một dòng | `bitable.v1.appTableRecord.update` | [`bitable_v1.ts`, dòng 1742–1768](https://github.com/larksuite/lark-openapi-mcp/blob/21920354ec6e3966b52e89152620c5085e496b55/src/mcp-tool/tools/en/gen-tools/zod/bitable_v1.ts#L1742-L1768) |
| Tạo batch | `bitable.v1.appTableRecord.batchCreate` | [`bitable_v1.ts`, dòng 1384–1402](https://github.com/larksuite/lark-openapi-mcp/blob/21920354ec6e3966b52e89152620c5085e496b55/src/mcp-tool/tools/en/gen-tools/zod/bitable_v1.ts#L1384-L1402) |
| Sửa batch | `bitable.v1.appTableRecord.batchUpdate` | [`bitable_v1.ts`, dòng 1473–1492](https://github.com/larksuite/lark-openapi-mcp/blob/21920354ec6e3966b52e89152620c5085e496b55/src/mcp-tool/tools/en/gen-tools/zod/bitable_v1.ts#L1473-L1492) |

Single create/update nằm trong `preset.default`/`preset.base.default`; batch operations
nằm trong preset riêng
([preset matrix, dòng 53–69](https://github.com/larksuite/lark-openapi-mcp/blob/21920354ec6e3966b52e89152620c5085e496b55/docs/reference/tool-presets/presets.md#L53-L69)).

## 5. Có phủ card API không?

Có cho outbound:

- `im.v1.message.create` gửi được `msg_type: interactive`
  ([`im_v1.ts`, dòng 1615–1639](https://github.com/larksuite/lark-openapi-mcp/blob/21920354ec6e3966b52e89152620c5085e496b55/src/mcp-tool/tools/en/gen-tools/zod/im_v1.ts#L1615-L1639));
- `im.v1.message.patch` cập nhật card đã gửi theo `message_id`; source giới hạn rõ cho
  interactive card
  ([`im_v1.ts`, dòng 1823–1845](https://github.com/larksuite/lark-openapi-mcp/blob/21920354ec6e3966b52e89152620c5085e496b55/src/mcp-tool/tools/en/gen-tools/zod/im_v1.ts#L1823-L1845));
- CardKit v1 có create/update/batch update/settings, element create/delete/patch/update và
  streaming text
  ([tool catalog, dòng 343–355](https://github.com/larksuite/lark-openapi-mcp/blob/21920354ec6e3966b52e89152620c5085e496b55/docs/reference/tool-presets/tools-en.md#L343-L355)).

CardKit và `im.v1.message.patch` không thuộc default preset; phải bật explicit bằng `-t`.

Không có inbound Feishu event/card-action receiver. HTTP surface của project chỉ là MCP,
legacy SSE/messages và OAuth callback
([streamable routes, dòng 43–80](https://github.com/larksuite/lark-openapi-mcp/blob/21920354ec6e3966b52e89152620c5085e496b55/src/mcp-server/transport/streamable.ts#L43-L80),
[SSE routes, dòng 43–72](https://github.com/larksuite/lark-openapi-mcp/blob/21920354ec6e3966b52e89152620c5085e496b55/src/mcp-server/transport/sse.ts#L43-L72),
[OAuth callback, dòng 95–99](https://github.com/larksuite/lark-openapi-mcp/blob/21920354ec6e3966b52e89152620c5085e496b55/src/auth/handler/handler.ts#L95-L99)).

Hermes Feishu gateway hiện tại vẫn phải nhận button click, authorize operator, resolve
`card_id`/topic và route về đúng profile/task.

## 6. Vì sao không dùng MCP trực tiếp trong production path?

MCP upstream giải quyết **API invocation**, còn D-20 giải quyết **authority + delivery
semantics**. Các phần bắt buộc của D-20 mà upstream không có:

- signed capability giới hạn action theo task/owner/topic;
- worker không cầm app secret;
- durable map `card_id/message_id ↔ task_id ↔ owner_profile ↔ content_hash`;
- idempotency key và recovery sau crash để không gửi trùng;
- policy chỉ cho bốn operation hẹp;
- inbound callback nối lại đúng Kanban inbox/profile.

Đặt generic MCP sau broker vẫn khả thi, nhưng thêm Node process, MCP transport và một beta
dependency mà không xóa phần khó nào của broker. Fork đã có official Python SDK, create /
reply / update interactive message chạy production và `BaseRequest` pattern cho endpoint
chưa có typed wrapper. Direct SDK/OpenAPI là footprint nhỏ hơn và dễ khóa bằng contract test.

## 7. Endpoint contract cho `lark_io_broker`

Broker production chỉ cần map bốn API nội bộ sang official OpenAPI primitives:

| Broker action | Lark primitive |
|---|---|
| `post_message` | IM message create/reply |
| `post_card` | IM message create với `msg_type=interactive` |
| `patch_card` | IM message patch theo `message_id` |
| `write_base_row` | Bitable app-table-record create/update; batch variant khi cần |

Implementation phải giữ raw payload qua broker nhưng tự thêm capability verification,
idempotency và durable routing ledger trước khi gọi API. App secret chỉ tồn tại trong
gateway/broker trust domain, không forward vào personal/specialist profile.

## Quyết định Gate 0

Tiền đề đã verify:

- repo tồn tại: **có**;
- commercial license: **có, MIT**;
- Base + outbound card primitive: **có**;
- thay được `lark_io_broker`: **không**;
- dependency production nên chọn: **official SDK/OpenAPI trực tiếp**, không MCP upstream.

Gate 0 không còn bị ticket này chặn. Work tiếp theo của workstream ③ là implement broker
contract + negative capability/idempotency tests, không phải cài MCP cho Hermes model.
