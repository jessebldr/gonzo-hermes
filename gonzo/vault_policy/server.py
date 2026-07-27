#!/usr/bin/env python3
"""Narrow stdio MCP surface for the governed read-only vault policy."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Protocol

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from mcp.server.fastmcp import FastMCP

from gonzo.vault_policy.policy import (
    MarkdownVaultIndexEngine,
    VaultPolicy,
    resolve_clean_git_commit,
)


class QueryPolicy(Protocol):
    def query(self, query: str, *, limit: int = 8) -> dict[str, object]: ...


def create_mcp_server(policy: QueryPolicy) -> FastMCP:
    """Expose exactly one model tool; no raw index/file operations."""
    server = FastMCP(
        "gonzo-vault-policy",
        instructions=(
            "Use vault_query for company, brand, operational, or policy facts. "
            "Cite returned paths. Respect use_class. If blocked_by_open_question "
            "is true, say the matter is undecided and stop."
        ),
    )

    @server.tool(name="vault_query")
    def vault_query(query: str, limit: int = 8) -> dict[str, object]:
        """Search the governed vault and return reread, policy-safe cited results."""
        normalized_query = query.strip()
        if not normalized_query:
            raise ValueError("query must not be empty")
        if not 1 <= limit <= 12:
            raise ValueError("limit must be between 1 and 12")
        return policy.query(normalized_query, limit=limit)

    return server


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault", type=Path, required=True)
    parser.add_argument("--state-dir", type=Path, required=True)
    parser.add_argument("--model-cache", type=Path, required=True)
    parser.add_argument(
        "--embedding-model",
        default="BAAI/bge-small-en-v1.5",
    )
    return parser.parse_args()


def main() -> int:
    args = _arguments()
    from markdown_vault_mcp.providers import FastEmbedProvider

    vault_root = args.vault.resolve()
    state_dir = args.state_dir.expanduser().resolve()
    model_cache = args.model_cache.expanduser().resolve()
    provider = FastEmbedProvider(
        model_name=args.embedding_model,
        cache_dir=str(model_cache),
    )
    engine = MarkdownVaultIndexEngine(
        vault_root=vault_root,
        state_dir=state_dir,
        embedding_provider=provider,
    )
    policy = VaultPolicy(
        vault_root=vault_root,
        state_dir=state_dir,
        engine=engine,
        commit_resolver=lambda: resolve_clean_git_commit(vault_root),
    )
    create_mcp_server(policy).run(transport="stdio")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
