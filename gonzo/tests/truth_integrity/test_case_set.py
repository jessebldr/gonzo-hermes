"""Structural tests over the frozen truth-integrity case set (D-17①).

These run today, before any runtime exists. They do not exercise an agent — they
protect the freeze itself: that the set is complete, that no case has drifted from
the vault rule it claims to enforce, and that nobody edited cases.yaml without
re-freezing it deliberately.

The agent-under-test layer lands at Gate 3 and is not in this file.
"""

import hashlib
import os
import re
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

HERE = Path(__file__).parent
CASES_PATH = HERE / "cases.yaml"
FREEZE_PATH = HERE / "FREEZE.md"

REQUIRED_FIELDS = ("id", "category", "source", "given", "when", "then", "never")


def _vault_root():
    """gonzo-vault lives in a sibling repo; the vault is never vendored in here (P1)."""
    env = os.environ.get("GONZO_VAULT_PATH")
    candidate = Path(env) if env else HERE.parents[2].parent / "gonzo-vault"
    return candidate if (candidate / "governance").is_dir() else None


def _flatten(text):
    """Collapse whitespace so a quote still matches across a wrapped source line."""
    return re.sub(r"\s+", " ", text).strip()


def _unmark(text):
    """Drop markdown emphasis so a heading matches the section name we recorded."""
    return _flatten(re.sub(r"[*`_]", "", text))


@pytest.fixture(scope="module")
def spec():
    return yaml.safe_load(CASES_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def cases(spec):
    return spec["cases"]


def test_meets_the_minimum_case_count(spec, cases):
    assert len(cases) >= spec["minimum_cases"], (
        f"D-17① requires at least {spec['minimum_cases']} cases; found {len(cases)}"
    )


def test_every_required_category_is_covered(spec, cases):
    covered = {c["category"] for c in cases}
    missing = sorted(set(spec["required_categories"]) - covered)
    assert not missing, f"no case covers: {missing}"


def test_case_ids_are_unique(cases):
    ids = [c["id"] for c in cases]
    assert len(ids) == len(set(ids)), "duplicate case id"


@pytest.mark.parametrize("field", REQUIRED_FIELDS)
def test_every_case_declares_every_field(cases, field):
    missing = [c.get("id", "<no id>") for c in cases if not c.get(field)]
    assert not missing, f"cases missing '{field}': {missing}"


def test_every_case_asserts_and_forbids(cases):
    """A case with only `then` teaches compliance; the `never` list is what catches drift."""
    thin = [c["id"] for c in cases if not c["never"]]
    assert not thin, f"cases with no forbidden behaviour: {thin}"


def test_thresholds_are_the_invariant_ones(spec):
    assert spec["runs_per_case"] == 3
    assert "100%" in spec["threshold"]


@pytest.mark.parametrize(
    "case", [pytest.param(c, id=c["id"]) for c in yaml.safe_load(CASES_PATH.read_text(encoding="utf-8"))["cases"]]
)
def test_quoted_rule_still_exists_in_the_vault(case):
    """The wire between this suite and the vault's rules.

    If someone edits governance/ without revisiting the cases, this goes red — which
    is the regression D-17① asks for after every policy change.
    """
    root = _vault_root()
    if root is None:
        pytest.skip("gonzo-vault not found — set GONZO_VAULT_PATH to run the wire check")

    src = root / case["source"]["file"]
    assert src.is_file(), f"{case['id']}: {case['source']['file']} does not exist in the vault"

    body = src.read_text(encoding="utf-8")
    assert _flatten(case["source"]["quote"]) in _flatten(body), (
        f"{case['id']}: quoted rule no longer appears in {case['source']['file']} — "
        f"the rule changed, or the case drifted from it"
    )

    headings = {_unmark(h) for h in re.findall(r"^#{2,4}\s+(.*)$", body, re.M)}
    assert _unmark(case["source"]["section"]) in headings, (
        f"{case['id']}: section '{case['source']['section']}' is not a heading in "
        f"{case['source']['file']}"
    )


def test_case_set_matches_its_freeze_record():
    """cases.yaml is frozen. Changing it is allowed — silently changing it is not."""
    digest = hashlib.sha256(CASES_PATH.read_bytes()).hexdigest()
    recorded = re.search(r"`sha256:([0-9a-f]{64})`", FREEZE_PATH.read_text(encoding="utf-8"))
    assert recorded, "FREEZE.md carries no sha256 for cases.yaml"
    assert digest == recorded.group(1), (
        "cases.yaml changed since it was frozen. If the change is deliberate, update "
        f"FREEZE.md with the new digest and say why:\n  sha256:{digest}"
    )
