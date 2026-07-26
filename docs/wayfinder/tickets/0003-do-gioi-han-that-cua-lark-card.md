---
id: "0003"
title: Đo giới hạn thật của Lark card
type: prototype
status: closed
assignee: "tech-lead"
blocked_by: []
---

## Question

Card Lark chịu được bao nhiêu: kích thước payload tối đa, số nút tối đa, và rate limit của
PATCH tại chỗ? Lark **không công bố** những số này.

## Vì sao nó chặn

Gate 0 gọi đây là thứ "sai thì gãy khung". Ba thiết kế đặt cược vào nó:

- **D-09** clarify card: 3 button option + form input, rồi PATCH tại chỗ thành "✓ đã chọn".
- **D-10** living-index card ghim đầu topic, bot PATCH mỗi lần có deliverable mới — đây là
  chỗ rate limit PATCH sẽ cắn trước tiên.
- **D-13** card "Adopt as doctrine" **bắt buộc** hiện đủ 4 thứ, trong đó có normalized rule
  và phạm vi ảnh hưởng. Nếu payload bị cắt thì gate của D-13 nằm ở nội dung card sẽ vỡ —
  và nó vỡ **im lặng**.

## Bắt đầu ở đâu

Không research được, phải bắn thật vào một group test. `plugins/platforms/feishu` trong
fork đã có sẵn đường gửi card; `tests/gateway/test_feishu_approval_buttons.py` cho thấy
hình dạng payload.

Đo tới lúc **gãy**, không đo tới lúc "chắc là đủ". Ghi lại số thật vào một report và link
từ ticket này.

## Resolution

Đo trên tenant Lark thật, group `Hermes#Test`, 2026-07-26. Đo tới lúc **gãy**, không đo tới
lúc "chắc là đủ".

| Giới hạn | Kết quả | Cách xác định |
|---|---|---|
| **Số nút / card** | ≥ **120** — không gãy | Thử 10 · 20 · 30 · 50 · 80 · 120, tất cả `code=0` |
| **Kích thước payload** | gãy giữa **130KB và 150KB** | 130KB `code=0`; 150KB → `230025 "The length of the message content reaches its limit."` |
| **Rate limit PATCH** | **không chạm được** | 30 PATCH liên tiếp trên cùng một card trong 12.8s (~2.3/giây), **0 lần bị từ chối** |

## Kết luận: card KHÔNG phải nút thắt

[ADR 0002](../../architecture/decisions/0002-dinh-vi-trong-lark-va-va-adapter.md) lo rằng
đưa card thành hạ tầng chịu lực sẽ bị giới hạn card chặn lại — *"nếu card cap ở 10 nút hoặc
payload nhỏ, nó chặn thẳng số deliverable trên một lượt trả lời"*. **Không đúng.** 120 nút,
~130KB, PATCH không bị bóp. Xa hơn mọi thứ thiết kế cần.

D-10 (living-index card, bot PATCH mỗi lần có deliverable mới) an toàn: 2.3 PATCH/giây không
bị chặn, mà nhu cầu thật là vài lần một phút.

## Cảnh báo phải ghi kèm

**API nhận ≠ dùng được.** 120 nút gửi lọt không có nghĩa là người dùng được — một card 120
nút là giao diện không ai bấm nổi. Giới hạn thật của D-08 là **con người**, không phải kỹ
thuật: bao nhiêu lựa chọn một người nhìn một lần thì còn chọn được. Con số đó phải tìm bằng
người dùng thật, không tìm bằng API.

Nên ràng buộc thiết kế đổi chỗ: không còn là *"card chịu được bao nhiêu"* mà là *"một lượt
trả lời nên đưa ra bao nhiêu lựa chọn"*. Câu đó thuộc về `marketing-lead`, không thuộc về
đo đạc.