"""End-to-end MCP transport tests for the narrow vault-policy surface."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@pytest.mark.asyncio
async def test_stdio_server_exposes_only_vault_query_and_returns_structured_policy() -> None:
    fixture_server = Path(__file__).with_name("stdio_fixture_server.py")
    parameters = StdioServerParameters(
        command=sys.executable,
        args=[str(fixture_server)],
    )

    async with stdio_client(parameters) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools = await session.list_tools()
            result = await session.call_tool(
                "vault_query", {"query": "pricing", "limit": 4}
            )

    assert [tool.name for tool in tools.tools] == ["vault_query"]
    assert result.isError is False
    payload = result.structuredContent
    if payload is None:
        payload = json.loads(result.content[0].text)
    assert payload == {
        "query": "pricing",
        "limit": 4,
        "results": [
            {
                "path": "company/pricing.md",
                "title": "Pricing",
                "content": "Grounded result.",
                "use_class": "citable",
                "score": 0.9,
            }
        ],
    }
