---
id: "0008"
title: Hermes có video-gen — xác minh và sửa D-01 với §6
type: task
status: open
assignee: ""
blocked_by: []
---

## Question

Doc nói *"Hermes không có video-gen"* ở hai chỗ (D-01 và §6). Fork có
`plugins/video_gen/{deepinfra,fal,xai}`. Cái nào đúng, và sửa doc lại cho khớp.

## Vì sao nó chặn

Không chặn gate nào, nhưng nó đang **đẩy video ra một pipeline riêng không cần thiết**:
D-01 giao cho `mkt-creative` "video qua pipeline Veo (MCP/script riêng)", §6 nhắc lại. Nếu
ba plugin kia dùng được thì đó là công sức thừa, và ai đó sẽ build theo doc trước khi phát
hiện ra.

Đáng lưu ý: hệ cũ goclaw ở `~/Company/gonzo-brands` có sẵn `media-producer-*` (nhiều
version), nên video/media không phải chuyện giả thuyết — nó là thứ đang chạy.

## Việc cụ thể

1. Đọc `plugins/video_gen/{deepinfra,fal,xai}` xem chúng thật sự gen video hay chỉ là
   wrapper rỗng, và model nào chạy được (fal có đường tới Veo).
2. Sửa D-01 và §6 của `docs/architecture/hermes-vault-agent-team-architecture.md` cho khớp
   sự thật — **một commit riêng**, ghi rõ vì sao đổi.
3. Nếu plugin dùng được thì nói rõ pipeline Veo hiện có ở goclaw còn cần giữ không.
