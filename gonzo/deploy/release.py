"""Pure helpers for reproducible launchd release deployment.

The mutation/orchestration layer can build on these functions while keeping
the contracts easy to exercise without touching a user's launchd service.
"""

from __future__ import annotations

import plistlib
import re
import shutil
import subprocess
import time
from pathlib import Path


_PID_RE = re.compile(r'\"PID\"\s*=\s*(\d+)\s*;')
_PROGRAM_RE = re.compile(r'\"Program\"\s*=\s*\"([^\"]+)\"\s*;')


def validate_release_root(release_root: Path) -> bool:
    """Check the minimum filesystem contract for a deployable release."""
    root = Path(release_root).expanduser()
    python = root / ".venv" / "bin" / "python"
    return root.is_dir() and python.is_file() and python.stat().st_mode & 0o111 != 0


def render_launchd_plist(*, release_root: Path, hermes_home: Path) -> bytes:
    """Render the gateway plist pinned to a release worktree runtime."""
    release_root = Path(release_root).expanduser().resolve()
    hermes_home = Path(hermes_home).expanduser().resolve()
    python = release_root / ".venv" / "bin" / "python"
    payload = {
        "Label": "ai.hermes.gateway",
        "ProgramArguments": [
            str(python),
            "-m",
            "hermes_cli.main",
            "gateway",
            "run",
            "--replace",
        ],
        "WorkingDirectory": str(hermes_home),
        "EnvironmentVariables": {
            "HERMES_HOME": str(hermes_home),
            "PYTHONPATH": str(release_root),
        },
        "RunAtLoad": True,
        "KeepAlive": True,
        "ProcessType": "Interactive",
        "StandardOutPath": str(hermes_home / "logs" / "gateway.log"),
        "StandardErrorPath": str(hermes_home / "logs" / "errors.log"),
    }
    return plistlib.dumps(payload, fmt=plistlib.FMT_XML, sort_keys=False)


def parse_launchctl_status(text: str) -> dict[str, int | str]:
    """Extract the PID and executable path from ``launchctl list`` output."""
    pid_match = _PID_RE.search(text)
    program_match = _PROGRAM_RE.search(text)
    if not pid_match or not program_match:
        raise ValueError("launchctl status must contain PID and Program")
    return {"pid": int(pid_match.group(1)), "program": program_match.group(1)}


def gateway_log_is_healthy(text: str) -> bool:
    """Return true only when fresh logs show gateway and both Lark WS signals."""
    required = (
        "Gateway running with ",
        "[Feishu] Connected in websocket mode (lark)",
        "connected to wss://msg-frontier-sg.larksuite.com/ws/v2",
    )
    return all(signal in text for signal in required)


def install_launchd_plist(
    *,
    plist_path: Path,
    payload: bytes,
    launchctl: str = "launchctl",
    launchd_domain: str = "gui/501",
    dry_run: bool = False,
) -> Path | None:
    """Install and load a plist, retaining a recoverable backup.

    Returns the backup path when an existing plist was replaced.  The actual
    service mutation is deliberately kept here (rather than at import time)
    so callers can dry-run and test the rendering independently.
    """
    plist_path = Path(plist_path).expanduser()
    backup = plist_path.with_suffix(plist_path.suffix + ".gonzo-backup")
    if dry_run:
        return backup if plist_path.exists() else None
    plist_path.parent.mkdir(parents=True, exist_ok=True)
    if plist_path.exists():
        shutil.copy2(plist_path, backup)
        subprocess.run([launchctl, "bootout", f"{launchd_domain}/ai.hermes.gateway"], check=False)
    temporary = plist_path.with_suffix(plist_path.suffix + ".tmp")
    temporary.write_bytes(payload)
    temporary.replace(plist_path)
    try:
        subprocess.run([launchctl, "load", str(plist_path)], check=True)
    except Exception:
        if backup.exists():
            shutil.copy2(backup, plist_path)
            subprocess.run([launchctl, "load", str(plist_path)], check=False)
        raise
    return backup if backup.exists() else None


def rollback_launchd_plist(
    *,
    plist_path: Path,
    launchctl: str = "launchctl",
    launchd_domain: str = "gui/501",
    dry_run: bool = False,
) -> bool:
    """Restore the last plist backup and load it."""
    plist_path = Path(plist_path).expanduser()
    backup = plist_path.with_suffix(plist_path.suffix + ".gonzo-backup")
    if not backup.exists():
        return False
    if dry_run:
        return True
    subprocess.run([launchctl, "bootout", f"{launchd_domain}/ai.hermes.gateway"], check=False)
    shutil.copy2(backup, plist_path)
    subprocess.run([launchctl, "load", str(plist_path)], check=True)
    return True


def wait_for_gateway_health(
    *,
    expected_program: str,
    status_reader,
    log_reader,
    timeout: float = 60.0,
    interval: float = 1.0,
) -> dict[str, int | str]:
    """Wait for launchd identity and fresh gateway/Lark connection signals."""
    deadline = time.monotonic() + timeout
    last_status = ""
    while time.monotonic() < deadline:
        last_status = status_reader()
        try:
            status = parse_launchctl_status(last_status)
        except ValueError:
            time.sleep(interval)
            continue
        if status["program"] != expected_program or not gateway_log_is_healthy(log_reader()):
            time.sleep(interval)
            continue
        return status
    raise TimeoutError(f"gateway health check timed out; last status: {last_status!r}")


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Deploy or roll back the Hermes gateway release plist")
    parser.add_argument("action", choices=("render", "install", "rollback"))
    parser.add_argument("--release-root", type=Path)
    parser.add_argument("--hermes-home", type=Path, default=Path.home() / ".hermes")
    parser.add_argument("--plist", type=Path, default=Path.home() / "Library/LaunchAgents/ai.hermes.gateway.plist")
    parser.add_argument("--launchd-domain", default="gui/501")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.action == "rollback":
        return 0 if rollback_launchd_plist(
            plist_path=args.plist,
            launchd_domain=args.launchd_domain,
            dry_run=args.dry_run,
        ) else 1
    if args.release_root is None:
        parser.error("--release-root is required for render/install")
    if not validate_release_root(args.release_root):
        parser.error(f"release worktree is not ready: {args.release_root}")
    payload = render_launchd_plist(release_root=args.release_root, hermes_home=args.hermes_home)
    if args.action == "render":
        print(payload.decode())
        return 0
    install_launchd_plist(
        plist_path=args.plist,
        payload=payload,
        launchd_domain=args.launchd_domain,
        dry_run=args.dry_run,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
