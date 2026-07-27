#!/usr/bin/env python3
"""PROTOTYPE — run the governed-vault index/policy vertical slice once."""

from __future__ import annotations

import argparse
import importlib.metadata
import importlib.util
import json
import math
import resource
import sys
import tempfile
import time
from pathlib import Path
from types import ModuleType
from typing import Any

sys.dont_write_bytecode = True

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from gonzo.prototypes.vault_policy_prototype import (  # noqa: E402
    MarkdownVaultIndexEngine,
    PrototypeVaultPolicy,
    resolve_clean_git_commit,
)

PIPELINE = [
    "frontmatter_type",
    "symbolic",
    "graph",
    "semantic_fallback_rerank",
    "open_question",
    "policy",
]
FORBIDDEN_RESPONSE_KEYS = {"authority", "freshness", "status"}
DEFAULT_QUERIES = [
    "approval authority",
    "commercial price",
    "billiards low deflection shaft",
    "marketing copywriting headline",
    "marketing approval delegation open question",
]


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--vault",
        type=Path,
        default=REPO_ROOT.parent / "gonzo-vault",
    )
    parser.add_argument("--state-dir", type=Path)
    parser.add_argument(
        "--model-cache",
        type=Path,
        default=Path("/private/tmp/gonzo-vault-policy-model-cache"),
    )
    parser.add_argument("--samples", type=int, default=3)
    parser.add_argument("--query", action="append", dest="queries")
    return parser.parse_args()


def _load_validator(vault_root: Path) -> ModuleType:
    validator_path = vault_root / "tools" / "validate_vault.py"
    spec = importlib.util.spec_from_file_location("gonzo_vault_validator", validator_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load validator: {validator_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _expected_governed_paths(validator: ModuleType) -> tuple[list[str], dict[str, str]]:
    paths: list[str] = []
    errors: dict[str, str] = {}
    root = Path(validator.ROOT)
    for raw_path in validator.walk():
        path = Path(raw_path)
        relative = path.relative_to(root).as_posix()
        if relative in validator.EXEMPT_FILES or relative.startswith("_templates/"):
            continue
        parsed, error = validator.parse_frontmatter(path.read_text(encoding="utf-8"))
        if error:
            errors[relative] = error
            continue
        if parsed is not None:
            paths.append(relative)
    return sorted(paths), errors


def _response_keys(value: object) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        keys.update(str(key) for key in value)
        for item in value.values():
            keys.update(_response_keys(item))
    elif isinstance(value, list):
        for item in value:
            keys.update(_response_keys(item))
    return keys


def _assert_reread(response: dict[str, Any], validator: ModuleType) -> None:
    root = Path(validator.ROOT)
    for result in [*response["results"], *response["open_questions"]]:
        source = (root / result["path"]).read_text(encoding="utf-8")
        parsed, error = validator.parse_frontmatter(source)
        if error or parsed is None:
            raise AssertionError(f"validator cannot reread {result['path']}: {error}")
        _, body, _ = parsed
        if result["content"] != body.strip():
            raise AssertionError(f"response did not reread source: {result['path']}")


def _percentile(samples: list[float], percentile: float) -> float:
    ordered = sorted(samples)
    index = max(0, math.ceil(percentile * len(ordered)) - 1)
    return ordered[index]


def _directory_bytes(root: Path, *, excluded_parts: set[str] | None = None) -> int:
    excluded_parts = excluded_parts or set()
    return sum(
        path.stat().st_size
        for path in root.rglob("*")
        if path.is_file() and not excluded_parts.intersection(path.relative_to(root).parts)
    )


def _peak_rss_bytes() -> int:
    raw = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(raw if sys.platform == "darwin" else raw * 1024)


def _run(vault_root: Path, state_dir: Path, model_cache: Path, queries: list[str], samples: int) -> dict[str, Any]:
    from markdown_vault_mcp.providers import FastEmbedProvider

    validator = _load_validator(vault_root)
    expected_paths, validator_errors = _expected_governed_paths(validator)
    if validator_errors:
        raise AssertionError(f"vault validator parser errors: {validator_errors}")

    provider = FastEmbedProvider(cache_dir=str(model_cache))
    engine = MarkdownVaultIndexEngine(
        vault_root=vault_root,
        state_dir=state_dir,
        embedding_provider=provider,
    )
    policy = PrototypeVaultPolicy(
        vault_root=vault_root,
        state_dir=state_dir,
        engine=engine,
        commit_resolver=lambda: resolve_clean_git_commit(vault_root),
    )

    first_started = time.perf_counter()
    first_response = policy.query(queries[0])
    first_query_with_build_seconds = time.perf_counter() - first_started
    indexed_paths = sorted(engine.corpus_report["included_paths"])
    if indexed_paths != expected_paths:
        missing = sorted(set(expected_paths) - set(indexed_paths))
        extra = sorted(set(indexed_paths) - set(expected_paths))
        raise AssertionError(f"governed corpus mismatch: missing={missing}, extra={extra}")
    if engine.corpus_report["skipped"]:
        raise AssertionError(f"prototype skipped governed notes: {engine.corpus_report['skipped']}")

    responses = [first_response]
    for response in responses:
        if response["pipeline"] != PIPELINE:
            raise AssertionError(f"pipeline order drifted: {response['pipeline']}")
        leaked = FORBIDDEN_RESPONSE_KEYS.intersection(_response_keys(response))
        if leaked:
            raise AssertionError(f"raw policy fields leaked: {sorted(leaked)}")
        _assert_reread(response, validator)

    (state_dir / "vault-commit").write_text("forced-mismatch\n", encoding="utf-8")
    mismatch_started = time.perf_counter()
    mismatch_response = policy.query(queries[0])
    mismatch_seconds = time.perf_counter() - mismatch_started
    if engine.rebuild_count != 2:
        raise AssertionError("SHA mismatch did not synchronously rebuild")
    responses.append(mismatch_response)

    latencies: list[float] = []
    query_summaries: dict[str, dict[str, object]] = {}
    for _ in range(samples):
        for query in queries:
            started = time.perf_counter()
            response = policy.query(query)
            latencies.append(time.perf_counter() - started)
            if response["pipeline"] != PIPELINE:
                raise AssertionError(f"pipeline order drifted: {response['pipeline']}")
            leaked = FORBIDDEN_RESPONSE_KEYS.intersection(_response_keys(response))
            if leaked:
                raise AssertionError(f"raw policy fields leaked: {sorted(leaked)}")
            _assert_reread(response, validator)
            query_summaries[query] = {
                "result_count": len(response["results"]),
                "open_question_count": len(response["open_questions"]),
                "use_classes": sorted(
                    {result["use_class"] for result in response["results"]}
                ),
                "multiple_relevant_notes": response["multiple_relevant_notes"],
                "requires_multi_cite": response["requires_multi_cite"],
                "blocked_by_open_question": response["blocked_by_open_question"],
            }

    index_bytes = _directory_bytes(
        state_dir,
        excluded_parts={"index-source", "model-cache"},
    )
    mirror_bytes = _directory_bytes(state_dir / "index-source")
    return {
        "prototype": "markdown-vault-mcp behind vault-policy",
        "dependency_version": importlib.metadata.version("markdown-vault-mcp"),
        "vault_commit": resolve_clean_git_commit(vault_root),
        "governed_corpus": {
            "expected_count": len(expected_paths),
            "indexed_count": len(indexed_paths),
            "exact_match": indexed_paths == expected_paths,
            "excluded_boundaries": [
                ".github/",
                "_inbox/",
                "_templates/",
                "outputs/",
                "README.md",
                "CLAUDE.md",
                "MIGRATION.md",
            ],
        },
        "freshness_gate": {
            "forced_mismatch_rebuilt": engine.rebuild_count == 2,
            "rebuild_count": engine.rebuild_count,
            "forced_mismatch_seconds": mismatch_seconds,
            "indexed_commit": (state_dir / "vault-commit").read_text(encoding="utf-8").strip(),
        },
        "contract": {
            "pipeline": PIPELINE,
            "candidate_keys": ["path", "score"],
            "source_reread_verified": True,
            "raw_policy_keys_absent": True,
            "query_summaries": query_summaries,
        },
        "performance": {
            "first_query_with_build_seconds": first_query_with_build_seconds,
            "last_rebuild_seconds": engine.last_rebuild_seconds,
            "warm_samples": len(latencies),
            "warm_latency_p50_ms": _percentile(latencies, 0.50) * 1000,
            "warm_latency_p95_ms": _percentile(latencies, 0.95) * 1000,
            "peak_rss_bytes": _peak_rss_bytes(),
            "index_state_bytes": index_bytes,
            "normalized_mirror_bytes": mirror_bytes,
        },
    }


def main() -> int:
    args = _arguments()
    vault_root = args.vault.resolve()
    queries = args.queries or DEFAULT_QUERIES
    if args.samples < 1:
        raise SystemExit("--samples must be >= 1")
    if args.state_dir:
        state_dir = args.state_dir.resolve()
        state_dir.mkdir(parents=True, exist_ok=True)
        report = _run(vault_root, state_dir, args.model_cache, queries, args.samples)
    else:
        with tempfile.TemporaryDirectory(prefix="gonzo-vault-policy-") as scratch:
            report = _run(
                vault_root,
                Path(scratch),
                args.model_cache,
                queries,
                args.samples,
            )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
