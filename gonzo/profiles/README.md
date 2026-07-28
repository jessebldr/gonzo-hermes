# `profiles` — personal-first, specialist khi cần

Quyết định chi phối: [ADR 0003](../../docs/architecture/decisions/0003-hybrid-personal-agents-va-filesystem-boundary.md).
Workstream ①. Gate 2.

Thư mục config, không phải package Python — cố ý không có `__init__.py`.

## Topology

| Profile class | Sở hữu | Mặc định làm gì | Khi nào tách process |
|---|---|---|---|
| Personal — một người một profile | session, memory, USER, skills, preference | Làm task end-to-end; DM + personal workspace cùng route vào đây | Có thể multiplex cùng gateway khi cùng trust domain |
| Shared task | session/topic và state công việc chung | Phục vụ shared group/topic; không route theo người nói | Theo crash/resource domain của workload |
| `research` specialist | web/data connectors, research procedure | Escalation khi cần evidence sâu hoặc parallelism | Credential riêng → process riêng |
| `creative` specialist | creative procedure + media tools | Escalation khi cần chuyên môn/media | Tool/resource riêng → process riêng |
| `reviewer` specialist | fresh context + vault-policy read | Independent review ở biên factual/public/irreversible | Quyền/audit riêng → process riêng |

Lark bot là transport/front door, không phải một agent. Một bot route DM/personal workspace
về personal profile, shared topic về shared task profile; specialist làm việc qua
coordination bus, không cần xuất hiện thành nhiều bot trong group.

## Bất biến đã có bằng chứng runtime

- Profile A ghi preference vào `USER.md`, session mới của A recall đúng; profile B cùng
  model/config trả `UNKNOWN`.
- Profile chỉ tách state; **không** sandbox filesystem trên local backend.
- Security boundary cho raw file/terminal tools là Docker no-mount theo profile:
  `docker_mount_cwd_to_workspace: false`, `docker_volumes` allowlist tối thiểu, không mount
  raw `gonzo-vault`.
- Terminal, file tools và `execute_code` dùng chung container-config contract; full runtime
  probe pass 7/7, gồm lifecycle teardown không để lại container.
- Raw vault chỉ tới agent qua `vault-policy` read contract; process separation không được
  dùng thay cho negative probe filesystem.
- Không shared memory live. Chia sẻ knowledge qua artifact đúng loại: personal memory,
  shared-skill draft, vault draft+approval, hoặc Kanban/Base.

## Gate 2 phải chứng minh

1. Hai personal profile route đúng và memory/session không bleed.
2. Shared topic dùng một shared task session, không tách theo speaker.
3. Personal agent tự hoàn tất task bình thường; escalation specialist chỉ khi contract yêu
   cầu.
4. Fresh reviewer chạy ở boundary đã định, không phải mọi lượt creative.
5. Host-vault và cross-profile absolute-path probes fail trong sandbox.
6. Credential/audit log đúng profile thực hiện action.
7. Trước người thứ hai trong `FEISHU_ALLOWED_USERS`, chạy canary hai principal thật trên
   bản `session_search` đã scope theo người/profile/topic.

## Đã có pilot

- Default profile `~/.hermes` dùng tracked config Docker no-mount; file/terminal/
  `execute_code` negative probes trên raw vault pass ngày 2026-07-27.
- `session_search` đã scope theo principal/profile/topic; canary một principal qua `/new`
  và hai topic thật đã pass ngày 2026-07-28.
- Core router nhận `principal_id` cho **DM only**. Nó match `user_id_alt`/`user_id` nhưng
  fail group/topic theo cấu trúc, nên một người nói trong shared group không kéo turn vào
  personal profile.
- `runtime_map.py` + `bootstrap.sh` dựng profile từ private runtime map, apply cùng tracked
  Docker/vault config cho từng profile và chỉ cấp provider key cho named profile. Lark app
  credentials ở default listener, không bị clone sang personal profile. Chỉ default config
  bật multiplex/routes; named config luôn giữ `multiplex_profiles: false` để không thể mở
  nhầm multiplexer thứ hai.

## Bootstrap runtime map

Vault giữ roster/role; runtime map giữ platform ID → profile. Hai thứ cố ý không nhập làm
một. Copy example ra ngoài git:

```bash
cp gonzo/profiles/runtime-map.example.yaml ~/.hermes/gonzo-runtime.yaml
chmod 600 ~/.hermes/gonzo-runtime.yaml
$EDITOR ~/.hermes/gonzo-runtime.yaml
```

Dry-run trước, rồi mới ghi:

```bash
./gonzo/profiles/bootstrap.sh
./gonzo/profiles/bootstrap.sh --write
```

Trong pilot hiện tại, giữ owner trên built-in `default` để lịch sử session cũ vẫn recall
được. `clone-default` chỉ copy config, curated `USER.md`/`MEMORY.md` và skills; nó **không**
copy `state.db`/session history. Chỉ dùng mode đó khi chấp nhận một session cutover riêng.
Người thứ hai trở đi luôn `seed: fresh`; nếu clone default cho họ thì memory và
self-created skills của owner sẽ bị copy sang.

Named profiles nhận các `key_env` cần cho model từ operator `.env`; extra credential chỉ
được cấp khi liệt kê trong `profiles[].secret_keys`. Default listener nhận các key name ở
`default_secret_keys`. Mọi `FEISHU_*` key bị cấm ở named profile. Khi map có Feishu
principal routes, bootstrap tự sinh `FEISHU_ALLOWED_USERS` đúng bằng tập principal đó và
ép `FEISHU_ALLOW_ALL_USERS=false`; admission và DM routing vì thế dùng cùng một nguồn.
Map đồng thời phải có đúng một catch-all `chat_type: group` tới `shared-task`, còn
owner+bot workspace phải có exact `chat_id` override về `default`. Script không in secret
value và giữ `.env` mode 600.

Route `enabled: false` vẫn được render để staging nhưng không được tính vào allowlist và
không thỏa các invariant bắt buộc ở trên. `enabled` phải là YAML boolean thật, không phải
chuỗi `"false"`.

## Chưa build

- Chưa deploy named profiles thật trên pilot và chưa chạy canary hai principal thật.
- Chưa có Lark principal ID của người thứ hai trong private runtime map.
- Coordination bus và credential grants cho specialist.
