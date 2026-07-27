"""Test-only stdio process around the production MCP server factory."""

from __future__ import annotations

from gonzo.vault_policy.server import create_mcp_server


class FixturePolicy:
    def query(self, query: str, *, limit: int = 8) -> dict[str, object]:
        return {
            "query": query,
            "limit": limit,
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


if __name__ == "__main__":
    create_mcp_server(FixturePolicy()).run(transport="stdio")
