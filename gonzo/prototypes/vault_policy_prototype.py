"""PROTOTYPE — prove the D-04/D-04a vault read contract with a private index.

Question: can markdown-vault-mcp remain only a candidate generator while this
host-side policy owns source rereads and the model-facing response?
"""

from __future__ import annotations

import shutil
import subprocess
import time
from collections.abc import Callable
from datetime import date
from pathlib import Path
from typing import Any

import yaml


_EXCLUDED_PARTS = {
    ".git",
    ".github",
    ".obsidian",
    "_inbox",
    "_templates",
    "node_modules",
    "outputs",
}
_EXCLUDED_ROOT_FILES = {"CLAUDE.md", "MIGRATION.md", "README.md"}
_BASE_REQUIRED = {
    "authority",
    "captured_at",
    "confidence",
    "freshness",
    "scope",
    "sources",
    "status",
    "tags",
    "type",
}


def resolve_clean_git_commit(vault_root: Path) -> str:
    """Return HEAD only when every governed source file is committed."""
    status = subprocess.run(
        [
            "git",
            "-C",
            str(vault_root),
            "status",
            "--porcelain",
            "--untracked-files=all",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    if status.stdout.strip():
        raise RuntimeError("vault working tree is dirty; refusing commit-bound query")
    commit = subprocess.run(
        ["git", "-C", str(vault_root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return commit.stdout.strip()


class MarkdownVaultIndexEngine:
    """Private markdown-vault-mcp adapter; never exposes its MCP surface."""

    def __init__(
        self,
        *,
        vault_root: Path,
        state_dir: Path,
        embedding_provider: object,
        vault_factory: Callable[..., object] | None = None,
    ) -> None:
        self._vault_root = vault_root.resolve()
        self._state_dir = state_dir.resolve()
        self._embedding_provider = embedding_provider
        self._vault_factory = vault_factory
        self._vault: Any = None
        self.corpus_report: dict[str, object] = {}
        self.rebuild_count = 0
        self.last_rebuild_seconds = 0.0

    def rebuild(self) -> None:
        started = time.perf_counter()
        if self._vault is not None and hasattr(self._vault, "close"):
            self._vault.close()
        mirror_root = self._state_dir / "index-source"
        if mirror_root == self._vault_root:
            raise ValueError("index mirror must not overwrite the source vault")
        if mirror_root.exists():
            shutil.rmtree(mirror_root)
        mirror_root.mkdir(parents=True)

        included: list[str] = []
        skipped: dict[str, str] = {}
        for source_path in sorted(self._vault_root.rglob("*.md")):
            relative = source_path.relative_to(self._vault_root)
            relative_path = relative.as_posix()
            if (
                relative_path in _EXCLUDED_ROOT_FILES
                or any(part in _EXCLUDED_PARTS for part in relative.parts)
            ):
                continue
            try:
                frontmatter, body = _parse_flat_frontmatter(
                    source_path.read_text(encoding="utf-8")
                )
            except (OSError, UnicodeError, ValueError) as exc:
                skipped[relative_path] = str(exc)
                continue
            missing = sorted(_BASE_REQUIRED - frontmatter.keys())
            if missing:
                skipped[relative_path] = f"missing frontmatter: {missing}"
                continue

            mirror_path = mirror_root / relative
            mirror_path.parent.mkdir(parents=True, exist_ok=True)
            normalized = yaml.safe_dump(
                frontmatter,
                allow_unicode=True,
                sort_keys=False,
            )
            mirror_path.write_text(
                f"---\n{normalized}---\n{body}", encoding="utf-8"
            )
            included.append(relative_path)

        factory = self._vault_factory or _load_vault_factory()
        self._vault = factory(
            source_dir=mirror_root,
            index_path=self._state_dir / "index.sqlite",
            embeddings_path=self._state_dir / "embeddings",
            embedding_provider=self._embedding_provider,
            read_only=True,
            state_path=self._state_dir / "upstream-state.json",
            indexed_frontmatter_fields=[
                "type",
                "status",
                "authority",
                "freshness",
                "tags",
                "affects",
            ],
            required_frontmatter=sorted(_BASE_REQUIRED),
            exclude_patterns=[],
        )
        index_stats = self._vault.index.build_index(force=True)
        embedded_chunks = self._vault.index.build_embeddings(force=True)
        self.corpus_report = {
            "included_count": len(included),
            "included_paths": included,
            "skipped": skipped,
            "index_stats": _plain_object(index_stats),
            "embedded_chunks": embedded_chunks,
        }
        self.rebuild_count += 1
        self.last_rebuild_seconds = time.perf_counter() - started

    def keyword_search(self, query: str, *, limit: int) -> list[dict[str, object]]:
        return self._search(query, mode="keyword", limit=limit)

    def semantic_search(self, query: str, *, limit: int) -> list[dict[str, object]]:
        return self._search(query, mode="semantic", limit=limit)

    def open_question_search(
        self, query: str, *, limit: int
    ) -> list[dict[str, object]]:
        return self._search(
            query,
            mode="keyword",
            limit=limit,
            filters={"type": "open-question"},
        )

    def _search(
        self,
        query: str,
        *,
        mode: str,
        limit: int,
        filters: dict[str, str] | None = None,
    ) -> list[dict[str, object]]:
        if self._vault is None:
            raise RuntimeError("index engine has not been built")
        hits = self._vault.reader.search(
            query,
            mode=mode,
            limit=limit,
            filters=filters,
            chunks_per_file=1,
            snippet_words=0,
        )
        return [
            {"path": str(hit.path), "score": float(hit.score)} for hit in hits
        ]

    def graph_neighbors(self, paths: list[str]) -> list[dict[str, object]]:
        if self._vault is None:
            raise RuntimeError("index engine has not been built")
        neighbors: dict[str, float] = {}
        for path in paths:
            for backlink in self._vault.graph.get_backlinks(path):
                neighbors[str(backlink.source_path)] = 0.2
            for outlink in self._vault.graph.get_outlinks(path):
                if outlink.exists:
                    neighbors[str(outlink.target_path)] = 0.2
        return [
            {"path": path, "score": score} for path, score in neighbors.items()
        ]


def _load_vault_factory() -> Callable[..., object]:
    from markdown_vault_mcp import Vault

    return Vault


def _plain_object(value: object) -> object:
    if value is None or isinstance(value, (bool, float, int, str)):
        return value
    if hasattr(value, "__dict__"):
        return {
            key: _plain_object(item)
            for key, item in vars(value).items()
            if not key.startswith("_")
        }
    return str(value)


class PrototypeVaultPolicy:
    """Throwaway public seam exercised by the vault-policy prototype."""

    def __init__(
        self,
        *,
        vault_root: Path,
        state_dir: Path,
        engine: Any,
        commit_resolver: Callable[[], str],
    ) -> None:
        self._vault_root = vault_root.resolve()
        self._state_dir = state_dir
        self._engine = engine
        self._commit_resolver = commit_resolver

    def query(self, query: str, *, limit: int = 8) -> dict[str, Any]:
        """Return only reread, policy-classified source content."""
        self._ensure_fresh()
        pipeline = ["frontmatter_type"]
        symbolic = self._engine.keyword_search(query, limit=limit)
        pipeline.append("symbolic")
        paths = [str(candidate["path"]) for candidate in symbolic]
        graph = self._engine.graph_neighbors(paths)
        pipeline.append("graph")
        semantic = self._engine.semantic_search(query, limit=limit)
        pipeline.append("semantic_fallback_rerank")
        open_question_candidates = self._engine.open_question_search(
            query, limit=limit
        )
        pipeline.append("open_question")

        candidates: dict[str, float] = {}
        for candidate in [*symbolic, *graph, *semantic]:
            path = str(candidate["path"])
            score = float(candidate.get("score", 0.0))
            candidates[path] = max(score, candidates.get(path, float("-inf")))

        classified_results = [
            self._reread(path, score)
            for path, score in sorted(
                candidates.items(), key=lambda item: item[1], reverse=True
            )
        ]
        results = [
            _public_result(result)
            for result in classified_results
            if result["_note_type"] != "open-question"
        ][:limit]
        classified_open_questions = [
            self._reread(str(candidate["path"]), float(candidate.get("score", 0.0)))
            for candidate in open_question_candidates
        ]
        open_questions = [
            _public_result(result)
            for result in classified_open_questions
            if result["_note_type"] == "open-question"
        ]
        pipeline.append("policy")
        approved_relevant = sum(
            result["use_class"] in {"citable", "stale", "suggestion-only"}
            for result in results
        )
        return {
            "pipeline": pipeline,
            "results": results,
            "open_questions": open_questions,
            "multiple_relevant_notes": approved_relevant >= 2,
            "requires_multi_cite": approved_relevant >= 2,
            "blocked_by_open_question": any(
                result["use_class"] == "undecided" for result in open_questions
            ),
        }

    def _ensure_fresh(self) -> None:
        commit_path = self._state_dir / "vault-commit"
        indexed_commit = (
            commit_path.read_text(encoding="utf-8").strip()
            if commit_path.exists()
            else None
        )
        for _ in range(3):
            target_commit = self._commit_resolver()
            if indexed_commit == target_commit:
                return

            self._engine.rebuild()
            if self._commit_resolver() != target_commit:
                indexed_commit = None
                continue

            self._state_dir.mkdir(parents=True, exist_ok=True)
            pending_path = self._state_dir / "vault-commit.pending"
            pending_path.write_text(f"{target_commit}\n", encoding="utf-8")
            pending_path.replace(commit_path)
            return
        raise RuntimeError("vault changed during three consecutive synchronous rebuilds")

    def _reread(self, relative_path: str, score: float) -> dict[str, Any]:
        source_path = (self._vault_root / relative_path).resolve()
        source_path.relative_to(self._vault_root)
        frontmatter, body = _parse_flat_frontmatter(
            source_path.read_text(encoding="utf-8")
        )
        title = _first_heading(body) or source_path.stem.replace("-", " ").title()
        return {
            "path": relative_path,
            "title": title,
            "content": body.strip(),
            "use_class": _use_class(frontmatter),
            "score": score,
            "_note_type": str(frontmatter.get("type", "")),
        }


def _parse_flat_frontmatter(text: str) -> tuple[dict[str, object], str]:
    """Parse the flat subset used by gonzo-vault without exposing it downstream."""
    if not text.startswith("---\n"):
        raise ValueError("note has no frontmatter")
    end = text.find("\n---\n", 3)
    if end == -1:
        raise ValueError("frontmatter is not closed")

    frontmatter: dict[str, object] = {}
    active_key: str | None = None
    for line in text[4 : end + 1].splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith("  - "):
            if active_key is None:
                raise ValueError("frontmatter list item has no key")
            item = line[4:].strip()
            if len(item) > 1 and item[0] == item[-1] and item[0] in "\"'":
                item = item[1:-1]
            value = frontmatter.setdefault(active_key, [])
            if not isinstance(value, list):
                raise ValueError(f"frontmatter field is not a list: {active_key}")
            value.append(item)
            continue
        active_key, separator, raw_value = line.partition(":")
        if not separator:
            raise ValueError(f"invalid frontmatter line: {line}")
        active_key = active_key.strip()
        raw_value = raw_value.strip()
        if raw_value.startswith("[") and raw_value.endswith("]"):
            frontmatter[active_key] = [
                value.strip() for value in raw_value[1:-1].split(",") if value.strip()
            ]
        elif raw_value:
            if (
                len(raw_value) > 1
                and raw_value[0] == raw_value[-1]
                and raw_value[0] in "\"'"
            ):
                raw_value = raw_value[1:-1]
            frontmatter[active_key] = raw_value
        else:
            frontmatter[active_key] = []
    return frontmatter, text[end + 5 :]


def _first_heading(body: str) -> str | None:
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return None


def _public_result(classified: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in classified.items() if not key.startswith("_")}


def _use_class(frontmatter: dict[str, object]) -> str:
    status = str(frontmatter.get("status", ""))
    note_type = str(frontmatter.get("type", ""))
    if note_type == "open-question":
        return "historical-only" if status == "superseded" else "undecided"
    if status == "superseded":
        return "historical-only"
    if status != "approved":
        return "unverified"
    if str(frontmatter.get("authority")) == "5":
        return "suggestion-only"
    review_after = frontmatter.get("review_after")
    if note_type == "operational-state" and review_after:
        try:
            if date.fromisoformat(str(review_after)) < date.today():
                return "stale"
        except ValueError:
            return "stale"
    return "citable"
