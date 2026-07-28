"""Docker E2E for multiplexed profile attachment isolation.

Run explicitly with ``HERMES_RUN_DOCKER_E2E=1`` on a host with Docker.  The
normal unit suite skips this because it creates real containers.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest


pytestmark = pytest.mark.skipif(
    os.environ.get("HERMES_RUN_DOCKER_E2E") != "1",
    reason="set HERMES_RUN_DOCKER_E2E=1 to run real Docker isolation tests",
)


@pytest.fixture
def docker_shared_tmp_path():
    # Colima/Docker Desktop share /Users by default but not macOS's
    # /private/var pytest temp root.  Keep the fixture inside the checkout so
    # the daemon sees the same attachment bytes the host test created.
    with tempfile.TemporaryDirectory(
        prefix=".docker-profile-e2e-", dir=Path.cwd()
    ) as tmp:
        yield Path(tmp)


def test_named_profiles_mount_only_their_own_attachment_cache(
    docker_shared_tmp_path: Path,
):
    from gateway.run import _profile_runtime_scope
    from gateway.session_context import clear_session_vars, set_session_vars
    from tools.environments.docker import DockerEnvironment
    from tools.terminal_tool import _resolve_container_task_id

    son_home = docker_shared_tmp_path / "profiles" / "son"
    shared_home = docker_shared_tmp_path / "profiles" / "shared-task"
    son_documents = son_home / "cache" / "documents"
    shared_documents = shared_home / "cache" / "documents"
    son_documents.mkdir(parents=True)
    shared_documents.mkdir(parents=True)
    (son_documents / "canary.xlsx").write_bytes(b"son-private-workbook")

    environments: list[DockerEnvironment] = []
    try:
        with _profile_runtime_scope(son_home):
            tokens = set_session_vars(profile="son")
            try:
                son_key = _resolve_container_task_id("default")
                son_env = DockerEnvironment(
                    image="python:3.11-slim",
                    task_id=son_key,
                    network=False,
                    persistent_filesystem=False,
                    persist_across_processes=False,
                )
                environments.append(son_env)
                son_result = son_env.execute(
                    "python -c \"from pathlib import Path; "
                    "print(Path('/root/.hermes/cache/documents/canary.xlsx').read_text())\""
                )
            finally:
                clear_session_vars(tokens)

        with _profile_runtime_scope(shared_home):
            tokens = set_session_vars(profile="shared-task")
            try:
                shared_key = _resolve_container_task_id("default")
                shared_env = DockerEnvironment(
                    image="python:3.11-slim",
                    task_id=shared_key,
                    network=False,
                    persistent_filesystem=False,
                    persist_across_processes=False,
                )
                environments.append(shared_env)
                shared_result = shared_env.execute(
                    "python -c \"from pathlib import Path; "
                    "print(Path('/root/.hermes/cache/documents/canary.xlsx').exists())\""
                )
            finally:
                clear_session_vars(tokens)

        assert son_key == "default:son"
        assert shared_key == "default:shared-task"
        assert son_key != shared_key
        assert son_result["returncode"] == 0, son_result
        assert son_result["output"].strip() == "son-private-workbook"
        assert shared_result["returncode"] == 0, shared_result
        assert shared_result["output"].strip() == "False"
    finally:
        for environment in reversed(environments):
            environment.cleanup(force_remove=True)
