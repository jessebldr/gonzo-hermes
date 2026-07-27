# Throwaway prototypes

Các file trong thư mục này là **PROTOTYPE — xoá sau khi câu hỏi đã được trả lời**.
Chúng không phải production runtime và không được import bởi `gonzo/`.

## Filesystem boundary probe

Câu hỏi: profile/process của Hermes có thực sự ngăn agent đọc filesystem của host và
workspace của profile khác không, hay chỉ tách state trong `HERMES_HOME`?

Chạy một lệnh:

```bash
.venv/bin/python gonzo/prototypes/filesystem_boundary_probe.py
```

Probe tạo canary trong một thư mục tạm, chạy đúng file tools của fork ở local và Docker,
sau đó chạy hai lượt `hermes chat` thật qua provider trong `gonzo/deploy/hermes-config.yaml`.
Mặc định scratch bị xoá. Dùng `--keep` chỉ khi cần giữ trace để audit.

Điều kiện mong đợi:

- local backend đọc được canary host — đây là control **đỏ có chủ ý**;
- Docker không mount không đọc được canary host hoặc raw `gonzo-vault`;
- profile Docker B không đọc được file nằm trong `/workspace` của profile A;
- chính model phải gọi tool thật, không được chỉ đoán `BLOCKED`.
