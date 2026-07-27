"""Pure verdict logic for the throwaway filesystem-boundary prototype."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Expectation(str, Enum):
    EXPOSED = "exposed"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class Observation:
    name: str
    expectation: Expectation
    tool_called: bool
    canary_seen: bool
    access_error_seen: bool
    note: str = ""


@dataclass(frozen=True)
class Verdict:
    name: str
    passed: bool
    reason: str


def evaluate(observation: Observation) -> Verdict:
    """Evaluate one probe without performing any I/O."""
    if not observation.tool_called:
        return Verdict(observation.name, False, "không có bằng chứng tool đã chạy")

    if observation.expectation is Expectation.EXPOSED:
        if observation.canary_seen:
            return Verdict(observation.name, True, "control xác nhận host đang đọc được")
        return Verdict(observation.name, False, "control local không đọc được canary")

    if observation.canary_seen:
        return Verdict(observation.name, False, "canary lọt qua boundary")
    if observation.access_error_seen:
        return Verdict(observation.name, True, "tool chạy nhưng filesystem từ chối/không thấy path")
    return Verdict(observation.name, False, "không thấy canary nhưng cũng không có lỗi truy cập rõ ràng")


def all_security_boundaries_pass(verdicts: list[Verdict]) -> bool:
    """The intentionally exposed local control is included and must also behave as expected."""
    return bool(verdicts) and all(verdict.passed for verdict in verdicts)
