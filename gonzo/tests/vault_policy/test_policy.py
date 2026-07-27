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

    def open_question_relations(
        self, paths: list[str], *, limit: int
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


def test_query_returns_a_bounded_excerpt_that_keeps_the_relevant_passage(
    tmp_path: Path,
) -> None:
    vault_root = tmp_path / "vault"
    note = vault_root / "company" / "pricing.md"
    note.parent.mkdir(parents=True)
    filler = "General background without the requested fact. " * 120
    note.write_text(
        f"""---
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

{filler}

## Approval authority

Only vault-approver may approve a governed vault note.
""",
        encoding="utf-8",
    )
    policy = VaultPolicy(
        vault_root=vault_root,
        state_dir=tmp_path / "state",
        engine=PoisonedIndex(),
        commit_resolver=lambda: "sha-a",
    )

    response = policy.query("approval authority")

    content = response["results"][0]["content"]
    assert len(content) <= 1_600
    assert "Only vault-approver may approve" in content
    assert filler not in content


class RelatedOpenQuestionIndex(PoisonedIndex):
    def open_question_relations(
        self, paths: list[str], *, limit: int
    ) -> list[dict[str, object]]:
        assert paths == ["company/pricing.md"]
        return [{"path": "decisions/open/pricing-source.md", "score": 0.4}]


def test_query_bundles_open_question_related_by_affects_without_query_match(
    tmp_path: Path,
) -> None:
    vault_root = tmp_path / "vault"
    approved = vault_root / "company" / "pricing.md"
    approved.parent.mkdir(parents=True)
    approved.write_text(
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

# Pricing

The listed price is approved.
""",
        encoding="utf-8",
    )
    question = vault_root / "decisions" / "open" / "pricing-source.md"
    question.parent.mkdir(parents=True)
    question.write_text(
        """---
type: open-question
status: draft
authority: 4
confidence: medium
scope: company
freshness: stable
captured_at: 2026-07-27
blocking: true
needs_decision_from: company-lead
affects:
  - ../../company/pricing.md
sources:
  - "vault-approver, 2026-07-27"
tags: [provenance]
---

# Source provenance

Who supplied the approved price?
""",
        encoding="utf-8",
    )
    policy = VaultPolicy(
        vault_root=vault_root,
        state_dir=tmp_path / "state",
        engine=RelatedOpenQuestionIndex(),
        commit_resolver=lambda: "sha-a",
    )

    response = policy.query("current commercial price")

    assert response["blocked_by_open_question"] is True
    assert [item["path"] for item in response["open_questions"]] == [
        "decisions/open/pricing-source.md"
    ]

    question.write_text(
        question.read_text(encoding="utf-8").replace(
            "blocking: true", "blocking: false"
        ),
        encoding="utf-8",
    )
    non_blocking_response = policy.query("current commercial price")

    assert non_blocking_response["open_questions"]
    assert non_blocking_response["blocked_by_open_question"] is False


class SemanticFallbackIndex(PoisonedIndex):
    def __init__(self) -> None:
        self.semantic_calls = 0

    def semantic_search(self, query: str, *, limit: int) -> list[dict[str, object]]:
        self.semantic_calls += 1
        return [{"path": "company/semantic.md", "score": 99.0}]


def test_semantic_search_only_fills_space_left_by_symbolic_pipeline(
    tmp_path: Path,
) -> None:
    vault_root = tmp_path / "vault"
    for relative, title in (
        ("company/pricing.md", "Pricing"),
        ("company/semantic.md", "Semantic fallback"),
    ):
        note = vault_root / relative
        note.parent.mkdir(parents=True, exist_ok=True)
        note.write_text(
            f"""---
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

# {title}
""",
            encoding="utf-8",
        )
    engine = SemanticFallbackIndex()
    policy = VaultPolicy(
        vault_root=vault_root,
        state_dir=tmp_path / "state",
        engine=engine,
        commit_resolver=lambda: "sha-a",
    )

    one_result = policy.query("pricing", limit=1)
    two_results = policy.query("pricing", limit=2)

    assert engine.semantic_calls == 1
    assert [item["path"] for item in one_result["results"]] == [
        "company/pricing.md"
    ]
    assert [item["path"] for item in two_results["results"]] == [
        "company/pricing.md",
        "company/semantic.md",
    ]


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
