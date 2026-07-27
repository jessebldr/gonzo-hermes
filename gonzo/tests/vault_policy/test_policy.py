"""Behavioral contract for the production read-only vault policy seam."""

from __future__ import annotations

import json
from pathlib import Path

from gonzo.vault_policy.policy import VaultPolicy


class PoisonedIndex:
    def rebuild(self) -> None:
        return None

    def keyword_search(self, query: str, *, limit: int) -> list[dict[str, object]]:
        return [
            {
                "path": "company/pricing.md",
                "score": 0.9,
                "content": "stale index payload",
                "frontmatter": {
                    "authority": 1,
                    "status": "approved",
                    "freshness": "stable",
                },
            }
        ]

    def graph_neighbors(self, paths: list[str]) -> list[dict[str, object]]:
        return []

    def semantic_search(self, query: str, *, limit: int) -> list[dict[str, object]]:
        return []

    def open_question_search(
        self, query: str, *, limit: int
    ) -> list[dict[str, object]]:
        return []


def test_query_rereads_markdown_and_returns_only_model_safe_policy(tmp_path: Path) -> None:
    vault_root = tmp_path / "vault"
    note = vault_root / "company" / "pricing.md"
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
tags: [pricing]
---

# Pricing rule

Fresh source truth.
""",
        encoding="utf-8",
    )
    policy = VaultPolicy(
        vault_root=vault_root,
        state_dir=tmp_path / "state",
        engine=PoisonedIndex(),
        commit_resolver=lambda: "sha-a",
    )

    response = policy.query("pricing")

    assert response["results"] == [
        {
            "path": "company/pricing.md",
            "title": "Pricing rule",
            "content": "# Pricing rule\n\nFresh source truth.",
            "use_class": "citable",
            "score": 0.9,
        }
    ]
    serialized = json.dumps(response)
    assert "stale index payload" not in serialized
    assert "authority" not in serialized
    assert "status" not in serialized
    assert "freshness" not in serialized


class RestartedIndex(PoisonedIndex):
    def __init__(self) -> None:
        self.is_ready = False
        self.events: list[str] = []

    def open(self) -> None:
        self.events.append("open")
        self.is_ready = True

    def rebuild(self) -> None:
        self.events.append("rebuild")
        self.is_ready = True

    def keyword_search(self, query: str, *, limit: int) -> list[dict[str, object]]:
        if not self.is_ready:
            raise RuntimeError("engine was searched before warm open")
        self.events.append("search")
        return super().keyword_search(query, limit=limit)


def test_process_restart_opens_matching_persistent_index_without_rebuild(
    tmp_path: Path,
) -> None:
    vault_root = tmp_path / "vault"
    note = vault_root / "company" / "pricing.md"
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
tags: [pricing]
---

# Pricing rule
""",
        encoding="utf-8",
    )
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    (state_dir / "vault-commit").write_text("sha-a\n", encoding="utf-8")
    engine = RestartedIndex()
    policy = VaultPolicy(
        vault_root=vault_root,
        state_dir=state_dir,
        engine=engine,
        commit_resolver=lambda: "sha-a",
    )

    policy.query("pricing")

    assert engine.events == ["open", "search"]
