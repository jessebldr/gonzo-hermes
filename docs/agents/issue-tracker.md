# Issue tracker của repo này

Tracker là **local-markdown**, sống trong `docs/wayfinder/`. Không dùng GitHub Issues:
`jessebldr/gonzo-hermes` là fork nên GitHub tắt Issues mặc định, và D-21 đòi "một coding
agent đọc repo là tiếp tục debug được" — ticket nằm trong git, đi theo release tag, thì
đúng yêu cầu đó hơn một cái tab trên web.

## Wayfinding operations

| Khái niệm | Ở đây là gì |
|---|---|
| Map | `docs/wayfinder/map.md` (tương đương label `wayfinder:map`) |
| Ticket | Một file `docs/wayfinder/tickets/NNNN-<slug>.md` |
| Child-of-map | Mọi file trong `tickets/` đều là con của map — không có quan hệ nào khác |
| Label `wayfinder:<type>` | Trường `type:` trong frontmatter: `research` · `prototype` · `grilling` · `task` |
| Claim | Trường `assignee:` khác rỗng. Ticket open + `assignee:` rỗng = chưa ai nhận |
| Blocking | Trường `blocked_by: [NNNN, ...]` — tracker này không có quan hệ native |
| Đóng | `status: closed` + thêm mục `## Resolution` vào cuối file |
| Frontier | `python3 docs/wayfinder/frontier.py` — open, `assignee` rỗng, mọi `blocked_by` đã closed |

## Frontmatter của ticket

```yaml
---
id: "0007"
title: <tiêu đề — đây là TÊN của ticket, luôn gọi bằng tên, không gọi bằng số>
type: research | prototype | grilling | task
status: open | closed
assignee: ""
blocked_by: []
---
```

## Luật

- **Gọi ticket bằng tên, không bằng số.** `0007, 0008, 0009` không đọc được; tên thì đọc
  được ngay. Số chỉ để máy tra.
- **Map là index, không phải kho.** Một quyết định sống ở đúng một chỗ — ticket của nó.
  Map chỉ gist một dòng + link. Không chép lại nội dung.
- **Ticket open không được liệt kê trong map** — chúng là kết quả của `frontier.py`.
- **Một session resolve tối đa một ticket.**
- Asset sinh ra khi resolve (report, prototype, ADR) được **link** từ ticket, không paste vào.
