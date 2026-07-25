---
id: "0003"
title: Đo giới hạn thật của Lark card
type: prototype
status: open
assignee: ""
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
