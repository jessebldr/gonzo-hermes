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
        cwd=REPO,
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
