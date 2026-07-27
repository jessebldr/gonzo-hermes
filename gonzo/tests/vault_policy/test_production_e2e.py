"""Opt-in E2E for the locked launcher and real private index dependency."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import pytest


REPO = Path(__file__).resolve().parents[3]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_locked_launcher_serves_real_commit_bound_policy(tmp_path: Path) -> None:
    vault_root = tmp_path / "vault"
    note = vault_root / "company" / "approval-authority.md"
    note.parent.mkdir(parents=True)
    note.write_text(
        """---
type: policy
status: approved
authority: 1
confidence: high
scope: company
freshness: stable
captured_at: 2026-07-27
approved_by: vault-approver
approved_at: 2026-07-27
sources:
  - "vault-approver, 2026-07-27"
tags: [approval, authority]
---

# Approval authority

Only vault-approver may approve a governed note.
""",
        encoding="utf-8",
    )
    subprocess.run(["git", "init", "-q", str(vault_root)], check=True)
    subprocess.run(["git", "-C", str(vault_root), "add", "."], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(vault_root),
            "-c",
            "user.name=Vault E2E",
            "-c",
            "user.email=vault-e2e@example.invalid",
            "commit",
            "-qm",
            "fixture",
        ],
        check=True,
    )

    hermes_home = tmp_path / "hermes-home"
    parameters = StdioServerParameters(
        command=str(REPO / "gonzo" / "vault_policy" / "run-mcp.sh"),
        args=[
            str(REPO / "gonzo" / "vault_policy" / "server.py"),
            "--vault",
            str(vault_root),
            "--state-dir",
            str(hermes_home / "vault-policy"),
            "--model-cache",
            str(hermes_home / "model-cache"),
        ],
        env={**os.environ, "HERMES_HOME": str(hermes_home)},
    )

    async with stdio_client(parameters) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools = await session.list_tools()
            result = await session.call_tool(
                "vault_query", {"query": "approval authority", "limit": 4}
            )

    assert [tool.name for tool in tools.tools] == ["vault_query"]
    assert result.isError is False
    payload = result.structuredContent
    if payload is None:
        payload = json.loads(result.content[0].text)
    assert payload["results"][0]["path"] == "company/approval-authority.md"
    assert payload["results"][0]["use_class"] == "citable"
    serialized = json.dumps(payload)
    assert "\"authority\"" not in serialized
    assert "\"status\"" not in serialized
    assert "\"freshness\"" not in serialized
