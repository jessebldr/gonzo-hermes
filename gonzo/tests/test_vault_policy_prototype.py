"""Behavioral tests for the throwaway vault-policy prototype."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import yaml

from gonzo.prototypes.vault_policy_prototype import (
    MarkdownVaultIndexEngine,
    PrototypeVaultPolicy,
)


class PoisonedCandidateEngine:
    """External index boundary that deliberately returns unsafe payloads."""

    def rebuild(self) -> None:
        return None

    def keyword_search(self, query: str, *, limit: int) -> list[dict[str, object]]:
        assert query == "commercial price"
        assert limit > 0
        return [
            {
                "path": "brands/kyperus/canon/price.md",
                "score": 0.91,
                "content": "STALE INDEX CONTENT",
                "frontmatter": {
                    "authority": 1,
                    "status": "approved",
                    "freshness": "stable",
                },
            }
        ]

    def graph_neighbors(self, paths: list[str]) -> list[dict[str, object]]:
        assert paths == ["brands/kyperus/canon/price.md"]
        return []

    def semantic_search(self, query: str, *, limit: int) -> list[dict[str, object]]:
        return []

    def open_question_search(
        self, query: str, *, limit: int
    ) -> list[dict[str, object]]:
        return []


def _write_note(root: Path, relative_path: str, *, body: str) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        """---
type: canon
status: approved
authority: 1
confidence: high
scope: brand
brand: kyperus
freshness: stable
captured_at: 2026-07-27
approved_by: vault-approver
approved_at: 2026-07-27
sources:
  - "vault-approver, 2026-07-27"
tags: [kyperus, price]
---

"""
        + body,
        encoding="utf-8",
    )


def test_query_rereads_source_and_never_exposes_raw_policy_fields(tmp_path: Path) -> None:
    vault_root = tmp_path / "vault"
    _write_note(
        vault_root,
        "brands/kyperus/canon/price.md",
        body="# Commercial price\n\nFresh source truth.",
    )

    policy = PrototypeVaultPolicy(
        vault_root=vault_root,
        state_dir=tmp_path / "state",
        engine=PoisonedCandidateEngine(),
        commit_resolver=lambda: "sha-a",
    )

    response = policy.query("commercial price")

    assert response["results"] == [
        {
            "path": "brands/kyperus/canon/price.md",
            "title": "Commercial price",
            "content": "# Commercial price\n\nFresh source truth.",
            "use_class": "citable",
            "score": 0.91,
        }
    ]
    serialized = json.dumps(response)
    assert "STALE INDEX CONTENT" not in serialized
    assert "authority" not in serialized
    assert "status" not in serialized
    assert "freshness" not in serialized


class OrderedEngine(PoisonedCandidateEngine):
    def __init__(self, events: list[str]) -> None:
        self._events = events

    def rebuild(self) -> None:
        self._events.append("rebuild")

    def keyword_search(self, query: str, *, limit: int) -> list[dict[str, object]]:
        self._events.append("keyword")
        return super().keyword_search(query, limit=limit)


def test_sha_mismatch_rebuilds_synchronously_before_search(tmp_path: Path) -> None:
    vault_root = tmp_path / "vault"
    _write_note(
        vault_root,
        "brands/kyperus/canon/price.md",
        body="# Commercial price\n\nFresh source truth.",
    )
    current_commit = ["sha-a"]
    events: list[str] = []
    policy = PrototypeVaultPolicy(
        vault_root=vault_root,
        state_dir=tmp_path / "state",
        engine=OrderedEngine(events),
        commit_resolver=lambda: current_commit[0],
    )

    policy.query("commercial price")
    assert events == ["rebuild", "keyword"]

    events.clear()
    policy.query("commercial price")
    assert events == ["keyword"]

    events.clear()
    current_commit[0] = "sha-b"
    policy.query("commercial price")
    assert events == ["rebuild", "keyword"]
    assert (tmp_path / "state" / "vault-commit").read_text(encoding="utf-8") == "sha-b\n"


def test_vault_change_during_rebuild_retries_before_search(tmp_path: Path) -> None:
    vault_root = tmp_path / "vault"
    _write_note(
        vault_root,
        "brands/kyperus/canon/price.md",
        body="# Commercial price\n\nFresh source truth.",
    )
    current_commit = ["sha-a"]
    events: list[str] = []
    engine = OrderedEngine(events)
    original_rebuild = engine.rebuild

    def rebuild_and_move_head() -> None:
        original_rebuild()
        if current_commit[0] == "sha-a":
            current_commit[0] = "sha-b"

    engine.rebuild = rebuild_and_move_head  # type: ignore[method-assign]
    policy = PrototypeVaultPolicy(
        vault_root=vault_root,
        state_dir=tmp_path / "state",
        engine=engine,
        commit_resolver=lambda: current_commit[0],
    )

    policy.query("commercial price")

    assert events == ["rebuild", "rebuild", "keyword"]
    assert (tmp_path / "state" / "vault-commit").read_text(encoding="utf-8") == "sha-b\n"


class CapturingVault:
    def __init__(self, *, source_dir: Path, captured: dict[str, object], **_: object) -> None:
        self._source_dir = source_dir
        self._captured = captured
        self.index = self.Index(self)
        self.reader = self.Reader()
        self.graph = self.Graph()

    class Index:
        def __init__(self, owner: "CapturingVault") -> None:
            self._owner = owner

        def build_index(self, *, force: bool) -> None:
            assert force is True
            paths = sorted(
                path.relative_to(self._owner._source_dir).as_posix()
                for path in self._owner._source_dir.rglob("*.md")
            )
            parsed = {
                path: yaml.safe_load(
                    (self._owner._source_dir / path)
                    .read_text(encoding="utf-8")
                    .split("---", 2)[1]
                )
                for path in paths
            }
            self._owner._captured["paths"] = paths
            self._owner._captured["frontmatter"] = parsed

        def build_embeddings(self, *, force: bool) -> int:
            assert force is True
            return 1

    class Reader:
        def search(self, query: str, *, mode: str, limit: int, **_: object) -> list[object]:
            assert query == "commercial price"
            if mode == "keyword":
                return [
                    SimpleNamespace(
                        path="brands/kyperus/canon/price.md", score=0.91
                    )
                ]
            return []

    class Graph:
        def get_backlinks(self, path: str) -> list[object]:
            return []

        def get_outlinks(self, path: str) -> list[object]:
            return []


def test_rebuild_indexes_only_governed_corpus_and_normalizes_frontmatter(
    tmp_path: Path,
) -> None:
    vault_root = tmp_path / "vault"
    _write_note(
        vault_root,
        "brands/kyperus/canon/price.md",
        body="# Commercial price\n\nFresh source truth.",
    )
    weird_path = vault_root / "domains/billiards/cue-feel.md"
    weird_path.parent.mkdir(parents=True)
    weird_path.write_text(
        """---
type: canon
status: approved
authority: 4
confidence: medium
scope: domain
freshness: stable
captured_at: 2026-07-13
approved_by: vault-approver
approved_at: 2026-07-25
sources:
  - "agent correction — restored the source's "probably" hedge"
tags: [billiards, cue]
---

# Cue feel
""",
        encoding="utf-8",
    )
    for excluded in (
        "README.md",
        "_templates/note.md",
        "_inbox/raw.md",
        "outputs/kyperus/answer.md",
        ".github/pull_request_template.md",
    ):
        path = vault_root / excluded
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# excluded\n", encoding="utf-8")

    captured: dict[str, object] = {}
    state_dir = tmp_path / "state"
    engine = MarkdownVaultIndexEngine(
        vault_root=vault_root,
        state_dir=state_dir,
        vault_factory=lambda **kwargs: CapturingVault(captured=captured, **kwargs),
        embedding_provider=object(),
    )
    policy = PrototypeVaultPolicy(
        vault_root=vault_root,
        state_dir=state_dir,
        engine=engine,
        commit_resolver=lambda: "sha-a",
    )

    policy.query("commercial price")

    assert captured["paths"] == [
        "brands/kyperus/canon/price.md",
        "domains/billiards/cue-feel.md",
    ]
    assert captured["frontmatter"]["domains/billiards/cue-feel.md"]["sources"] == [
        'agent correction — restored the source\'s "probably" hedge'
    ]


class PolicyPipelineEngine:
    def __init__(self) -> None:
        self.events: list[str] = []

    def rebuild(self) -> None:
        self.events.append("rebuild")

    def keyword_search(self, query: str, *, limit: int) -> list[dict[str, object]]:
        self.events.append("symbolic")
        return [
            {"path": "company/rule-a.md", "score": 0.9},
            {"path": "decisions/open/pricing.md", "score": 0.85},
        ]

    def graph_neighbors(self, paths: list[str]) -> list[dict[str, object]]:
        self.events.append("graph")
        return []

    def semantic_search(self, query: str, *, limit: int) -> list[dict[str, object]]:
        self.events.append("semantic")
        return [{"path": "company/rule-b.md", "score": 0.8}]

    def open_question_search(
        self, query: str, *, limit: int
    ) -> list[dict[str, object]]:
        self.events.append("open_question")
        return [{"path": "decisions/open/pricing.md", "score": 0.95}]


def _write_custom_note(root: Path, relative_path: str, frontmatter: str, body: str) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{frontmatter}---\n\n{body}", encoding="utf-8")


def test_pipeline_bundles_open_question_and_requires_multi_cite(tmp_path: Path) -> None:
    vault_root = tmp_path / "vault"
    approved = """type: policy
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
"""
    _write_custom_note(vault_root, "company/rule-a.md", approved, "# Rule A\n\nA.")
    _write_custom_note(vault_root, "company/rule-b.md", approved, "# Rule B\n\nB.")
    _write_custom_note(
        vault_root,
        "decisions/open/pricing.md",
        """type: open-question
status: draft
authority: 4
confidence: medium
scope: company
freshness: stable
captured_at: 2026-07-27
blocking: true
needs_decision_from: vault-approver
affects:
  - company/rule-a.md
sources:
  - "vault-approver, 2026-07-27"
tags: [pricing]
""",
        "# Pricing question\n\nWhich rule applies?",
    )
    engine = PolicyPipelineEngine()
    policy = PrototypeVaultPolicy(
        vault_root=vault_root,
        state_dir=tmp_path / "state",
        engine=engine,
        commit_resolver=lambda: "sha-a",
    )

    response = policy.query("pricing")

    assert engine.events == [
        "rebuild",
        "symbolic",
        "graph",
        "semantic",
        "open_question",
    ]
    assert response["pipeline"] == [
        "frontmatter_type",
        "symbolic",
        "graph",
        "semantic_fallback_rerank",
        "open_question",
        "policy",
    ]
    assert [result["path"] for result in response["results"]] == [
        "company/rule-a.md",
        "company/rule-b.md",
    ]
    assert {result["use_class"] for result in response["results"]} == {"citable"}
    assert response["multiple_relevant_notes"] is True
    assert response["requires_multi_cite"] is True
    assert response["blocked_by_open_question"] is True
    assert response["open_questions"] == [
        {
            "path": "decisions/open/pricing.md",
            "title": "Pricing question",
            "content": "# Pricing question\n\nWhich rule applies?",
            "use_class": "undecided",
            "score": 0.95,
        }
    ]
    serialized = json.dumps(response)
    assert "authority" not in serialized
    assert "status" not in serialized
    assert "freshness" not in serialized


class ClassificationEngine(PoisonedCandidateEngine):
    def keyword_search(self, query: str, *, limit: int) -> list[dict[str, object]]:
        return [
            {"path": "notes/draft.md", "score": 0.9},
            {"path": "notes/stale.md", "score": 0.8},
            {"path": "notes/external.md", "score": 0.7},
            {"path": "notes/history.md", "score": 0.6},
        ]

    def graph_neighbors(self, paths: list[str]) -> list[dict[str, object]]:
        return []


def test_policy_computes_use_class_without_returning_raw_inputs(tmp_path: Path) -> None:
    vault_root = tmp_path / "vault"
    common = """type: canon
authority: 2
confidence: high
scope: company
freshness: stable
captured_at: 2026-07-27
sources:
  - "vault-approver, 2026-07-27"
tags: [classification]
"""
    _write_custom_note(
        vault_root,
        "notes/draft.md",
        "status: draft\n" + common,
        "# Draft",
    )
    _write_custom_note(
        vault_root,
        "notes/stale.md",
        """type: operational-state
status: approved
authority: 2
confidence: high
scope: company
freshness: volatile
captured_at: 2026-01-01
last_verified: 2026-01-01
review_after: 2026-01-02
approved_by: vault-approver
approved_at: 2026-01-01
sources:
  - "vault-approver, 2026-01-01"
tags: [classification]
""",
        "# Stale",
    )
    _write_custom_note(
        vault_root,
        "notes/external.md",
        "type: canon\nstatus: approved\nauthority: 5\n"
        + "\n".join(common.splitlines()[2:])
        + "\napproved_by: vault-approver\napproved_at: 2026-07-27\n",
        "# External",
    )
    _write_custom_note(
        vault_root,
        "notes/history.md",
        "status: superseded\n"
        + common
        + "superseded_by: notes/replacement.md\n",
        "# History",
    )
    policy = PrototypeVaultPolicy(
        vault_root=vault_root,
        state_dir=tmp_path / "state",
        engine=ClassificationEngine(),
        commit_resolver=lambda: "sha-a",
    )

    response = policy.query("classification")

    assert {
        result["path"]: result["use_class"] for result in response["results"]
    } == {
        "notes/draft.md": "unverified",
        "notes/stale.md": "stale",
        "notes/external.md": "suggestion-only",
        "notes/history.md": "historical-only",
    }
