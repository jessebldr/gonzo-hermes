"""Behavior contracts for release-tag gateway deployment."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import plistlib


REPO = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO / "gonzo" / "deploy" / "release.py"
SPEC = importlib.util.spec_from_file_location("gonzo_release_deploy", MODULE_PATH)
assert SPEC and SPEC.loader
release = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release)


def test_launchd_plist_runs_only_from_release_worktree(tmp_path):
    release_root = tmp_path / "releases" / "gonzo-v0.19.0-pilot.1"
    hermes_home = tmp_path / "hermes"

    payload = plistlib.loads(
        release.render_launchd_plist(
            release_root=release_root,
            hermes_home=hermes_home,
        )
    )

    assert payload["ProgramArguments"] == [
        str(release_root / ".venv" / "bin" / "python"),
        "-m",
        "hermes_cli.main",
        "gateway",
        "run",
        "--replace",
    ]
    assert payload["WorkingDirectory"] == str(hermes_home)
    assert payload["EnvironmentVariables"]["HERMES_HOME"] == str(hermes_home)
    assert payload["EnvironmentVariables"]["PYTHONPATH"] == str(release_root)


def test_parse_launchctl_status_requires_pid_and_release_program():
    status = release.parse_launchctl_status(
        '''{
            "PID" = 54489;
            "Program" = "/srv/releases/gonzo-v1/.venv/bin/python";
        };'''
    )

    assert status == {
        "pid": 54489,
        "program": "/srv/releases/gonzo-v1/.venv/bin/python",
    }


def test_gateway_log_health_requires_gateway_and_lark_connection():
    assert release.gateway_log_is_healthy(
        "Gateway running with 1 platform(s)\n"
        "[Feishu] Connected in websocket mode (lark)\n"
        "connected to wss://msg-frontier-sg.larksuite.com/ws/v2?ticket=***\n"
    )
    assert not release.gateway_log_is_healthy(
        "Gateway running with 1 platform(s)\n"
        "[Feishu] Connecting...\n"
    )


def test_validate_release_root_requires_release_python(tmp_path):
    release_root = tmp_path / "release"
    release_root.mkdir()
    assert not release.validate_release_root(release_root)

    python = release_root / ".venv" / "bin" / "python"
    python.parent.mkdir(parents=True)
    python.write_text("#!/bin/sh\n")
    python.chmod(0o755)
    assert release.validate_release_root(release_root)
