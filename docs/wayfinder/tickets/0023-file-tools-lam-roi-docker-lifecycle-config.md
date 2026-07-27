---
id: "0023"
title: File-tools làm rơi Docker lifecycle config
type: task
status: closed
assignee: "codex"
blocked_by: []
---

## Question

Vì sao `terminal.docker_persist_across_processes: false` vẫn để container sống khi
environment đầu tiên được tạo bởi `read_file`?

## Reproduction

Chạy:

```bash
.venv/bin/python gonzo/prototypes/filesystem_boundary_probe.py
```

Sáu data-isolation probe pass, assertion cuối fail với hai container còn chạy. Prototype
cleanup exact container của nó trong `finally`, nên sau lệnh không còn rác.

## Line-level cause

`tools/file_tools.py::_get_file_ops()` dựng `container_config` nhưng không truyền:

- `docker_persist_across_processes`;
- `docker_orphan_reaper`;
- `docker_env`;
- `docker_extra_args`.

`tools/code_execution_tool.py::_get_or_create_environment()` cũng thiếu ít nhất lifecycle
keys. Trong khi đường tạo environment của `terminal_tool()` truyền đủ các key này. Giá trị
missing rơi về default `persist_across_processes=True`, nên `cleanup()` cố ý no-op.

## Acceptance

- Viết regression test ở `tests/tools/` pin cùng một `container_config` cho mọi creation
  path: terminal, file tools và execute_code.
- `docker_persist_across_processes: false` → file-tool-created container bị stop + remove
  khi process cleanup.
- `docker_orphan_reaper: false`, `docker_env`, `docker_extra_args`, network và mount config
  không drift giữa ba path.
- Chạy prototype: lifecycle assertion pass và `docker ps -a --filter
  label=hermes-agent=1` không còn container mới.
- Đây là sửa file upstream: commit riêng + test + thêm dòng vào `gonzo/README.md`.

## Resolution

Ba đường tạo environment (`terminal`, file tools, `execute_code`) nay dùng chung
`tools.terminal_tool._build_container_config()`. File-first và execute-first không còn làm
rơi lifecycle, mount, forwarded env, explicit env, extra args, network hoặc orphan-reaper
policy.

Regression tests dùng giá trị không-default để pin exact container contract ở cả file tools
và `execute_code`; test network cũ được đổi từ soi AST/source shape sang behavior contract.

Full runtime probe qua `ag/gemini-3.6-flash-high` + 9router + Docker pass 7/7, bao gồm
`docker_persist_across_processes=false` teardown đúng và không còn container probe sau khi
process kết thúc.
