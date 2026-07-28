"""Behavioral contract for the tracked Hermes pilot deployment config."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess

import yaml


REPO = Path(__file__).resolve().parents[2]


def test_deployed_pilot_config_enforces_docker_no_mount_boundary(tmp_path):
    """Deploying the tracked config cannot expose host files to agent tools."""
    pilot_home = tmp_path / "pilot-home"
    vault_root = tmp_path / "gonzo-vault"
    vault_root.mkdir()
    env = os.environ.copy()
    env["HERMES_HOME"] = str(pilot_home)
    env["GONZO_VAULT_ROOT"] = str(vault_root)

    completed = subprocess.run(
        [str(REPO / "gonzo" / "deploy" / "apply-config.sh"), "--write"],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    config = yaml.safe_load(
        (pilot_home / "config.yaml").read_text(encoding="utf-8")
    )
    assert config["terminal"] == {
        "backend": "docker",
        "cwd": "/workspace",
        "docker_image": "python:3.11-slim",
        "docker_mount_cwd_to_workspace": False,
        "docker_volumes": [],
        "docker_forward_env": [],
        "docker_env": {},
        "docker_network": False,
        "container_persistent": False,
        "docker_persist_across_processes": False,
        "docker_orphan_reaper": True,
        "container_cpu": 1,
        "container_memory": 512,
        "container_disk": 0,
    }
    launcher = pilot_home / "bin" / "gonzo-vault-policy-mcp"
    assert launcher.is_file()
    assert os.access(launcher, os.X_OK)
    assert config["mcp_servers"] == {
        "gonzo_vault": {
            "command": str(launcher),
            "args": [
                str(REPO / "gonzo" / "vault_policy" / "server.py"),
                "--vault",
                str(vault_root),
                "--state-dir",
                str(pilot_home / "vault-policy"),
                "--model-cache",
                str(pilot_home / "cache" / "vault-policy-model"),
            ],
            "enabled": True,
            "timeout": 180,
            "connect_timeout": 180,
            "supports_parallel_tool_calls": False,
            "tools": {
                "include": ["vault_query"],
                "resources": False,
                "prompts": False,
            },
        }
    }


def test_private_runtime_map_enables_principal_routes_without_committing_ids(tmp_path):
    pilot_home = tmp_path / "pilot-home"
    vault_root = tmp_path / "gonzo-vault"
    vault_root.mkdir()
    runtime_map = tmp_path / "runtime-map.yaml"
    runtime_map.write_text(
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
        "  - name: all-groups\n"
        "    platform: feishu\n"
        "    chat_type: group\n"
        "    profile: shared-task\n",
        encoding="utf-8",
    )
    runtime_map.chmod(0o600)
    env = os.environ.copy()
    env["HERMES_HOME"] = str(pilot_home)
    env["GONZO_VAULT_ROOT"] = str(vault_root)
    env["GONZO_RUNTIME_MAP"] = str(runtime_map)

    completed = subprocess.run(
        [str(REPO / "gonzo" / "deploy" / "apply-config.sh"), "--write"],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    config = yaml.safe_load(
        (pilot_home / "config.yaml").read_text(encoding="utf-8")
    )
    assert config["multiplex_profiles"] is True
    assert config["profile_routes"] == [
        {
            "name": "personal-a-dm",
            "platform": "feishu",
            "principal_id": "union-personal-a",
            "profile": "personal-a",
        },
        {
            "name": "all-groups",
            "platform": "feishu",
            "chat_type": "group",
            "profile": "shared-task",
        },
    ]


def test_profile_bootstrap_preserves_only_clone_default_memory_and_scopes_secrets(tmp_path):
    hermes_root = tmp_path / "hermes-home"
    hermes_root.mkdir()
    (hermes_root / "memories").mkdir()
    (hermes_root / "memories" / "USER.md").write_text(
        "owner preference marker\n",
        encoding="utf-8",
    )
    vault_root = tmp_path / "gonzo-vault"
    vault_root.mkdir()
    source_env = tmp_path / "source.env"
    source_env.write_text(
        "GONZO_9ROUTER_KEY=model-secret\n"
        "FEISHU_APP_ID=app-id\n"
        "FEISHU_APP_SECRET=app-secret\n",
        encoding="utf-8",
    )
    runtime_map = tmp_path / "runtime-map.yaml"
    runtime_map.write_text(
        "default_secret_keys:\n"
        "  - FEISHU_APP_ID\n"
        "  - FEISHU_APP_SECRET\n"
        "profiles:\n"
        "  - name: personal-a\n"
        "    seed: clone-default\n"
        "  - name: personal-b\n"
        "    seed: fresh\n"
        "  - name: shared-task\n"
        "    seed: fresh\n"
        "profile_routes:\n"
        "  - name: personal-a-dm\n"
        "    platform: feishu\n"
        "    principal_id: union-personal-a\n"
        "    profile: personal-a\n"
        "  - name: personal-b-dm-disabled\n"
        "    platform: feishu\n"
        "    principal_id: union-personal-b\n"
        "    profile: personal-b\n"
        "    enabled: false\n"
        "  - name: all-groups\n"
        "    platform: feishu\n"
        "    chat_type: group\n"
        "    profile: shared-task\n",
        encoding="utf-8",
    )
    runtime_map.chmod(0o600)

    completed = subprocess.run(
        [
            str(REPO / ".venv" / "bin" / "python"),
            str(REPO / "gonzo" / "profiles" / "runtime_map.py"),
            "bootstrap",
            str(runtime_map),
            "--hermes-root",
            str(hermes_root),
            "--repo-root",
            str(REPO),
            "--vault-root",
            str(vault_root),
            "--source-env",
            str(source_env),
            "--write",
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    personal_a = hermes_root / "profiles" / "personal-a"
    personal_b = hermes_root / "profiles" / "personal-b"
    shared_task = hermes_root / "profiles" / "shared-task"
    assert (personal_a / "memories" / "USER.md").read_text(
        encoding="utf-8"
    ) == "owner preference marker\n"
    assert not (personal_b / "memories" / "USER.md").exists()

    root_env = (hermes_root / ".env").read_text(encoding="utf-8")
    assert "GONZO_9ROUTER_KEY=model-secret" in root_env
    assert "FEISHU_APP_SECRET=app-secret" in root_env
    assert "FEISHU_ALLOWED_USERS=union-personal-a" in root_env
    assert "union-personal-b" not in root_env
    assert "FEISHU_ALLOW_ALL_USERS=false" in root_env
    root_config = yaml.safe_load(
        (hermes_root / "config.yaml").read_text(encoding="utf-8")
    )
    assert root_config["multiplex_profiles"] is True
    assert root_config["profile_routes"][0]["principal_id"] == "union-personal-a"
    for profile_home in (personal_a, personal_b, shared_task):
        profile_env = (profile_home / ".env").read_text(encoding="utf-8")
        assert "GONZO_9ROUTER_KEY=model-secret" in profile_env
        assert "FEISHU_APP_ID" not in profile_env
        assert "FEISHU_APP_SECRET" not in profile_env
        config = yaml.safe_load(
            (profile_home / "config.yaml").read_text(encoding="utf-8")
        )
        assert config["multiplex_profiles"] is False
        assert config["profile_routes"] == []
        assert (profile_home / "bin" / "gonzo-vault-policy-mcp").is_file()
