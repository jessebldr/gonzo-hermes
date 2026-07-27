"""Regression tests for Docker config propagation in execute_code."""

import threading

import tools.code_execution_tool as code_execution_tool
import tools.terminal_tool as terminal_tool


def test_execute_code_first_environment_honors_docker_lifecycle_options(monkeypatch):
    """execute_code must not weaken Docker config when it creates the sandbox first."""
    captured = {}
    sentinel = object()
    config = {
        "env_type": "docker",
        "docker_image": "test-image:latest",
        "cwd": "/workspace",
        "host_cwd": None,
        "timeout": 180,
        "modal_mode": "direct",
        "container_cpu": 2,
        "container_memory": 4096,
        "container_disk": 20480,
        "container_persistent": False,
        "docker_volumes": [],
        "docker_mount_cwd_to_workspace": False,
        "docker_forward_env": ["MY_SECRET"],
        "docker_env": {"PROBE_MODE": "strict"},
        "docker_run_as_host_user": False,
        "docker_extra_args": ["--cap-drop=ALL"],
        "docker_network": False,
        "docker_persist_across_processes": False,
        "docker_orphan_reaper": False,
    }

    def fake_create_environment(**kwargs):
        captured.update(kwargs)
        return sentinel

    monkeypatch.setattr(terminal_tool, "_get_env_config", lambda: config)
    monkeypatch.setattr(terminal_tool, "_active_environments", {})
    monkeypatch.setattr(terminal_tool, "_last_activity", {})
    monkeypatch.setattr(terminal_tool, "_creation_locks", {})
    monkeypatch.setattr(terminal_tool, "_creation_locks_lock", threading.Lock())
    monkeypatch.setattr(terminal_tool, "_task_env_overrides", {})
    monkeypatch.setattr(terminal_tool, "_create_environment", fake_create_environment)
    monkeypatch.setattr(terminal_tool, "_start_cleanup_thread", lambda: None)

    env, env_type = code_execution_tool._get_or_create_env("execute-first")

    assert env is sentinel
    assert env_type == "docker"
    assert captured["container_config"] == {
        "container_cpu": 2,
        "container_memory": 4096,
        "container_disk": 20480,
        "container_persistent": False,
        "modal_mode": "direct",
        "docker_volumes": [],
        "docker_mount_cwd_to_workspace": False,
        "docker_forward_env": ["MY_SECRET"],
        "docker_env": {"PROBE_MODE": "strict"},
        "docker_run_as_host_user": False,
        "docker_extra_args": ["--cap-drop=ALL"],
        "docker_network": False,
        "docker_persist_across_processes": False,
        "docker_orphan_reaper": False,
    }
