"""Contracts for the private profile/runtime mapping loader."""

from __future__ import annotations

from pathlib import Path

import pytest

from gonzo.profiles.runtime_map import load_runtime_map


def _write(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def test_runtime_map_rejects_invalid_profile_name(tmp_path):
    path = _write(
        tmp_path / "runtime.yaml",
        "profiles:\n"
        "  - name: ../escape\n"
        "    seed: fresh\n",
    )

    with pytest.raises(ValueError, match="Invalid profile name"):
        load_runtime_map(path)


def test_runtime_map_rejects_blank_principal_route(tmp_path):
    path = _write(
        tmp_path / "runtime.yaml",
        "profiles:\n"
        "  - name: personal-a\n"
        "    seed: fresh\n"
        "profile_routes:\n"
        "  - name: personal-a-dm\n"
        "    platform: feishu\n"
        "    principal_id: ''\n"
        "    profile: personal-a\n",
    )

    with pytest.raises(ValueError, match="profile_routes are invalid"):
        load_runtime_map(path)


def test_runtime_map_rejects_non_boolean_enabled_flag(tmp_path):
    path = _write(
        tmp_path / "runtime.yaml",
        "profiles:\n"
        "  - name: personal-a\n"
        "    seed: fresh\n"
        "profile_routes:\n"
        "  - name: personal-a-dm\n"
        "    platform: feishu\n"
        "    principal_id: union-personal-a\n"
        "    profile: personal-a\n"
        "    enabled: 'false'\n",
    )

    with pytest.raises(ValueError, match="enabled must be a boolean"):
        load_runtime_map(path)


@pytest.mark.parametrize(
    "extra_route_field",
    [
        "    chat_type: group\n",
        "    chat_id: oc_accidental\n",
    ],
)
def test_feishu_principal_route_must_be_dm_compatible_and_principal_only(
    tmp_path,
    extra_route_field,
):
    path = _write(
        tmp_path / "runtime.yaml",
        "profiles:\n"
        "  - name: personal-a\n"
        "    seed: fresh\n"
        "profile_routes:\n"
        "  - name: personal-a-dm\n"
        "    platform: feishu\n"
        "    principal_id: union-personal-a\n"
        "    profile: personal-a\n"
        + extra_route_field,
    )

    with pytest.raises(ValueError, match="DM-compatible and principal-only"):
        load_runtime_map(path)


def test_runtime_map_rejects_multiple_clone_default_profiles(tmp_path):
    path = _write(
        tmp_path / "runtime.yaml",
        "profiles:\n"
        "  - name: personal-a\n"
        "    seed: clone-default\n"
        "  - name: personal-b\n"
        "    seed: clone-default\n",
    )

    with pytest.raises(ValueError, match="at most one clone-default"):
        load_runtime_map(path)


def test_runtime_map_rejects_listener_secrets_on_named_profile(tmp_path):
    path = _write(
        tmp_path / "runtime.yaml",
        "profiles:\n"
        "  - name: personal-a\n"
        "    seed: fresh\n"
        "    secret_keys: [FEISHU_APP_SECRET]\n",
    )

    with pytest.raises(ValueError, match="listener-only secret"):
        load_runtime_map(path)


def test_feishu_principal_routes_require_shared_group_fallback(tmp_path):
    path = _write(
        tmp_path / "runtime.yaml",
        "profiles:\n"
        "  - name: personal-a\n"
        "    seed: fresh\n"
        "profile_routes:\n"
        "  - name: owner-dm\n"
        "    platform: feishu\n"
        "    principal_id: union-owner\n"
        "    profile: default\n"
        "  - name: personal-a-dm\n"
        "    platform: feishu\n"
        "    principal_id: union-personal-a\n"
        "    profile: personal-a\n",
    )

    with pytest.raises(ValueError, match="shared group fallback"):
        load_runtime_map(path)


def test_default_owner_principal_requires_exact_personal_workspace(tmp_path):
    path = _write(
        tmp_path / "runtime.yaml",
        "profiles:\n"
        "  - name: shared-task\n"
        "    seed: fresh\n"
        "profile_routes:\n"
        "  - name: owner-dm\n"
        "    platform: feishu\n"
        "    principal_id: union-owner\n"
        "    profile: default\n"
        "  - name: all-groups\n"
        "    platform: feishu\n"
        "    chat_type: group\n"
        "    profile: shared-task\n",
    )

    with pytest.raises(ValueError, match="exact default-profile workspace"):
        load_runtime_map(path)


def test_feishu_group_fallback_must_target_shared_task(tmp_path):
    path = _write(
        tmp_path / "runtime.yaml",
        "profiles:\n"
        "  - name: personal-a\n"
        "    seed: fresh\n"
        "profile_routes:\n"
        "  - name: personal-a-dm\n"
        "    platform: feishu\n"
        "    principal_id: union-personal-a\n"
        "    profile: personal-a\n"
        "  - name: all-groups\n"
        "    platform: feishu\n"
        "    chat_type: group\n"
        "    profile: personal-a\n",
    )

    with pytest.raises(ValueError, match="shared-task"):
        load_runtime_map(path)


def test_feishu_group_fallback_must_be_unambiguous(tmp_path):
    path = _write(
        tmp_path / "runtime.yaml",
        "profiles:\n"
        "  - name: personal-a\n"
        "    seed: fresh\n"
        "  - name: shared-task\n"
        "    seed: fresh\n"
        "profile_routes:\n"
        "  - name: personal-a-dm\n"
        "    platform: feishu\n"
        "    principal_id: union-personal-a\n"
        "    profile: personal-a\n"
        "  - name: unsafe-first-fallback\n"
        "    platform: feishu\n"
        "    chat_type: group\n"
        "    profile: personal-a\n"
        "  - name: all-groups\n"
        "    platform: feishu\n"
        "    chat_type: group\n"
        "    profile: shared-task\n",
    )

    with pytest.raises(ValueError, match="exactly one"):
        load_runtime_map(path)


def test_disabled_group_fallback_does_not_satisfy_topology(tmp_path):
    path = _write(
        tmp_path / "runtime.yaml",
        "profiles:\n"
        "  - name: shared-task\n"
        "    seed: fresh\n"
        "profile_routes:\n"
        "  - name: owner-dm\n"
        "    platform: feishu\n"
        "    principal_id: union-owner\n"
        "    profile: default\n"
        "  - name: owner-workspace\n"
        "    platform: feishu\n"
        "    chat_type: group\n"
        "    chat_id: oc_owner\n"
        "    profile: default\n"
        "  - name: all-groups\n"
        "    platform: feishu\n"
        "    chat_type: group\n"
        "    profile: shared-task\n"
        "    enabled: false\n",
    )

    with pytest.raises(ValueError, match="exactly one"):
        load_runtime_map(path)


def test_disabled_owner_workspace_does_not_satisfy_topology(tmp_path):
    path = _write(
        tmp_path / "runtime.yaml",
        "profiles:\n"
        "  - name: shared-task\n"
        "    seed: fresh\n"
        "profile_routes:\n"
        "  - name: owner-dm\n"
        "    platform: feishu\n"
        "    principal_id: union-owner\n"
        "    profile: default\n"
        "  - name: owner-workspace\n"
        "    platform: feishu\n"
        "    chat_type: group\n"
        "    chat_id: oc_owner\n"
        "    profile: default\n"
        "    enabled: false\n"
        "  - name: all-groups\n"
        "    platform: feishu\n"
        "    chat_type: group\n"
        "    profile: shared-task\n",
    )

    with pytest.raises(ValueError, match="exact default-profile workspace"):
        load_runtime_map(path)
