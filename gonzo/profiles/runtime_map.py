"""Validate the private runtime map used to bootstrap Gonzo Hermes profiles.

The vault owns people, roles, and company truth. This file only handles the
runtime-only mapping from platform principals/chats to Hermes profile names.
The mapping itself lives outside git (normally ``~/.hermes/gonzo-runtime.yaml``).
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Any

import yaml

from gateway.profile_routing import parse_profile_routes


_SEED_MODES = frozenset({"fresh", "clone-default"})
_ADMISSION_MODES = frozenset({"allowlist", "pairing"})
_LISTENER_ONLY_SECRET_PREFIXES = ("FEISHU_",)


def _route_is_enabled(route: dict[str, Any]) -> bool:
    return route.get("enabled", True) is True


@dataclass(frozen=True)
class RuntimeProfile:
    """One named runtime profile declared in the private map."""

    name: str
    seed: str
    description: str | None = None
    secret_keys: tuple[str, ...] = ()


@dataclass(frozen=True)
class RuntimeMap:
    """Validated profile roster and inbound routes."""

    profiles: tuple[RuntimeProfile, ...]
    profile_routes: tuple[dict[str, Any], ...]
    default_secret_keys: tuple[str, ...] = ()
    admission_mode: str = "allowlist"


def _require_mapping(value: Any, *, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a mapping")
    return value


def _secret_keys(raw: Any, *, label: str) -> tuple[str, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise ValueError(f"{label} must be a list")
    keys: list[str] = []
    for value in raw:
        key = str(value or "").strip()
        if not key or not key.replace("_", "A").isalnum() or not key[0].isalpha():
            raise ValueError(f"invalid secret key name in {label}: {value!r}")
        if key not in keys:
            keys.append(key)
    return tuple(keys)


def load_runtime_map(path: Path) -> RuntimeMap:
    """Load and validate a private runtime map."""

    try:
        mode = path.stat().st_mode & 0o777
        if mode != 0o600:
            raise ValueError(
                f"runtime map {path} must have mode 0600 (found {mode:04o})"
            )
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except ValueError:
        raise
    except OSError as exc:
        raise ValueError(f"cannot read runtime map {path}: {exc}") from exc
    data = _require_mapping(raw, label="runtime map")
    admission_mode = str(data.get("admission_mode") or "allowlist").strip().lower()
    if admission_mode not in _ADMISSION_MODES:
        raise ValueError(
            f"admission_mode must be one of {sorted(_ADMISSION_MODES)}"
        )

    raw_profiles = data.get("profiles") or []
    if not isinstance(raw_profiles, list):
        raise ValueError("profiles must be a list")
    profiles: list[RuntimeProfile] = []
    profile_names: set[str] = set()
    for index, value in enumerate(raw_profiles):
        entry = _require_mapping(value, label=f"profiles[{index}]")
        name = str(entry.get("name") or "").strip().lower()
        seed = str(entry.get("seed") or "fresh").strip().lower()
        description_raw = entry.get("description")
        description = str(description_raw).strip() if description_raw else None
        if not name:
            raise ValueError(f"profiles[{index}].name is required")
        from hermes_cli.profiles import validate_profile_name

        validate_profile_name(name)
        if name in profile_names:
            raise ValueError(f"duplicate profile name: {name}")
        if seed not in _SEED_MODES:
            raise ValueError(
                f"profiles[{index}].seed must be one of {sorted(_SEED_MODES)}"
            )
        profile_names.add(name)
        profiles.append(
            RuntimeProfile(
                name=name,
                seed=seed,
                description=description,
                secret_keys=_secret_keys(
                    entry.get("secret_keys"),
                    label=f"profiles[{index}].secret_keys",
                ),
            )
        )

    clone_default_count = sum(
        profile.seed == "clone-default" for profile in profiles
    )
    if clone_default_count > 1:
        raise ValueError("at most one clone-default profile is allowed")
    for profile in profiles:
        listener_keys = [
            key
            for key in profile.secret_keys
            if key.startswith(_LISTENER_ONLY_SECRET_PREFIXES)
        ]
        if listener_keys:
            raise ValueError(
                f"profile {profile.name!r} requests listener-only secret keys: "
                + ", ".join(sorted(listener_keys))
            )

    raw_routes = data.get("profile_routes") or []
    if not isinstance(raw_routes, list):
        raise ValueError("profile_routes must be a list")
    routes: list[dict[str, Any]] = []
    for index, value in enumerate(raw_routes):
        entry = dict(_require_mapping(value, label=f"profile_routes[{index}]"))
        if "enabled" in entry and not isinstance(entry["enabled"], bool):
            raise ValueError(f"profile_routes[{index}].enabled must be a boolean")
        target = str(entry.get("profile") or "").strip().lower()
        if target != "default" and target not in profile_names:
            raise ValueError(
                f"profile_routes[{index}] targets undeclared profile {target!r}"
            )
        entry["profile"] = target
        routes.append(entry)

    parsed = parse_profile_routes(routes)
    if len(parsed) != len(routes):
        raise ValueError("one or more profile_routes are invalid")

    for route in routes:
        if (
            str(route.get("platform") or "").strip().lower() != "feishu"
            or not route.get("principal_id")
        ):
            continue
        chat_type = str(route.get("chat_type") or "").strip().lower()
        has_location_discriminator = any(
            route.get(field) for field in ("guild_id", "chat_id", "thread_id")
        )
        if chat_type not in {"", "dm", "private", "p2p"} or has_location_discriminator:
            raise ValueError(
                "Feishu principal routes must be DM-compatible and principal-only"
            )

    feishu_principals = [
        str(route.get("principal_id") or "").strip()
        for route in routes
        if str(route.get("platform") or "").strip().lower() == "feishu"
        and route.get("principal_id")
    ]
    if len(feishu_principals) != len(set(feishu_principals)):
        raise ValueError("duplicate Feishu principal_id route")
    active_feishu_routes = [
        route
        for route in routes
        if str(route.get("platform") or "").strip().lower() == "feishu"
        and _route_is_enabled(route)
    ]
    active_feishu_principals = [
        str(route.get("principal_id") or "").strip()
        for route in active_feishu_routes
        if route.get("principal_id")
    ]
    if active_feishu_principals:
        group_fallbacks = [
            route
            for route in active_feishu_routes
            if str(route.get("chat_type") or "").strip().lower() == "group"
            and not any(
                route.get(field)
                for field in (
                    "principal_id",
                    "guild_id",
                    "chat_id",
                    "thread_id",
                )
            )
        ]
        if len(group_fallbacks) != 1:
            raise ValueError(
                "Feishu principal routes require exactly one shared group fallback"
            )
        if (
            str(group_fallbacks[0].get("profile") or "").strip().lower()
            != "shared-task"
        ):
            raise ValueError(
                "Feishu principal routes require a shared group fallback to shared-task"
            )
        has_default_principal = any(
            route.get("principal_id")
            and str(route.get("profile") or "").strip().lower() == "default"
            for route in active_feishu_routes
        )
        has_default_workspace = any(
            str(route.get("chat_type") or "").strip().lower() == "group"
            and route.get("chat_id")
            and not route.get("principal_id")
            and not route.get("thread_id")
            and str(route.get("profile") or "").strip().lower() == "default"
            for route in active_feishu_routes
        )
        if has_default_principal and not has_default_workspace:
            raise ValueError(
                "a default Feishu principal requires an exact default-profile workspace route"
            )

    return RuntimeMap(
        profiles=tuple(profiles),
        profile_routes=tuple(routes),
        default_secret_keys=_secret_keys(
            data.get("default_secret_keys"),
            label="default_secret_keys",
        ),
        admission_mode=admission_mode,
    )


def render_routes(runtime_map: RuntimeMap) -> str:
    """Render the config fragment appended to the tracked base config."""

    payload = {
        "multiplex_profiles": True,
        "profile_routes": list(runtime_map.profile_routes),
    }
    return yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)


_ENV_ASSIGNMENT_RE = re.compile(r"^(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)=(.*)$")


def _provider_secret_keys(repo_root: Path) -> tuple[str, ...]:
    source = repo_root / "gonzo" / "deploy" / "hermes-config.yaml"
    data = yaml.safe_load(source.read_text(encoding="utf-8")) or {}
    keys: list[str] = []
    for provider in data.get("custom_providers") or []:
        if not isinstance(provider, dict):
            continue
        key = str(provider.get("key_env") or "").strip()
        if key and key not in keys:
            keys.append(key)
    return tuple(keys)


def _source_env_assignments(path: Path) -> dict[str, str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ValueError(f"cannot read source env {path}: {exc}") from exc
    assignments: dict[str, str] = {}
    for line in lines:
        match = _ENV_ASSIGNMENT_RE.match(line.strip())
        if not match:
            continue
        key, value = match.groups()
        if value.strip() not in {"", "''", '\"\"'}:
            assignments[key] = f"{key}={value}"
    return assignments


def _backup_env(path: Path) -> None:
    if not path.is_file():
        return
    stamp = time.strftime("%Y%m%d%H%M%S")
    backup = path.with_name(f".env.bak-before-gonzo-bootstrap-{stamp}")
    suffix = 1
    while backup.exists():
        backup = path.with_name(
            f".env.bak-before-gonzo-bootstrap-{stamp}-{suffix}"
        )
        suffix += 1
    shutil.copy2(path, backup)


def _write_env_keys(
    target: Path,
    assignments: dict[str, str],
    keys: tuple[str, ...],
    *,
    exact: bool,
) -> None:
    missing = [key for key in keys if key not in assignments]
    if missing:
        raise ValueError(
            "source env is missing required keys: " + ", ".join(sorted(missing))
        )

    desired = {key: assignments[key] for key in keys}
    if exact:
        lines = [
            "# Managed by gonzo/profiles/runtime_map.py.",
            "# Values are copied from the operator env; key grants come from the private runtime map.",
            *desired.values(),
        ]
    else:
        try:
            current = target.read_text(encoding="utf-8").splitlines()
        except FileNotFoundError:
            current = ["# Hermes default-profile secrets."]
        lines = []
        replaced: set[str] = set()
        for line in current:
            match = _ENV_ASSIGNMENT_RE.match(line.strip())
            key = match.group(1) if match else None
            if key in desired:
                lines.append(desired[key])
                replaced.add(key)
            else:
                lines.append(line)
        lines.extend(desired[key] for key in keys if key not in replaced)

    rendered = "\n".join(lines).rstrip() + "\n"
    current_text = target.read_text(encoding="utf-8") if target.is_file() else None
    if current_text == rendered:
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    _backup_env(target)
    fd, temp_name = tempfile.mkstemp(prefix=".env.", dir=target.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(rendered)
        os.chmod(temp_name, 0o600)
        os.replace(temp_name, target)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def bootstrap_profiles(
    runtime_map: RuntimeMap,
    *,
    runtime_map_path: Path,
    hermes_root: Path,
    repo_root: Path,
    vault_root: Path,
    source_env: Path,
    write: bool,
) -> list[str]:
    """Create/sync the declared profiles and their least-privilege env files."""

    provider_keys = _provider_secret_keys(repo_root)
    source_assignments = _source_env_assignments(source_env)
    feishu_principal_ids = tuple(
        dict.fromkeys(
            str(route.get("principal_id") or "").strip()
            for route in runtime_map.profile_routes
            if str(route.get("platform") or "").strip().lower() == "feishu"
            and _route_is_enabled(route)
            and route.get("principal_id")
        )
    )
    managed_default_keys: tuple[str, ...] = ()
    has_feishu_routes = any(
        str(route.get("platform") or "").strip().lower() == "feishu"
        for route in runtime_map.profile_routes
    )
    if has_feishu_routes:
        source_assignments["FEISHU_ALLOWED_USERS"] = (
            "FEISHU_ALLOWED_USERS="
            if runtime_map.admission_mode == "pairing"
            else "FEISHU_ALLOWED_USERS=" + ",".join(feishu_principal_ids)
        )
        source_assignments["FEISHU_ALLOW_ALL_USERS"] = "FEISHU_ALLOW_ALL_USERS=false"
        managed_default_keys = (
            "FEISHU_ALLOWED_USERS",
            "FEISHU_ALLOW_ALL_USERS",
        )

    required = (
        set(provider_keys)
        | set(runtime_map.default_secret_keys)
        | set(managed_default_keys)
    )
    for profile in runtime_map.profiles:
        required.update(profile.secret_keys)
    missing = sorted(key for key in required if key not in source_assignments)
    if missing:
        raise ValueError(
            "source env is missing required keys: " + ", ".join(missing)
        )

    actions: list[str] = []
    for profile in runtime_map.profiles:
        profile_home = hermes_root / "profiles" / profile.name
        if profile_home.is_dir():
            actions.append(f"keep existing profile {profile.name}")
        else:
            actions.append(f"create {profile.name} ({profile.seed})")
    actions.append("sync tracked config for default and named profiles")
    if not write:
        return actions

    hermes_root.mkdir(parents=True, exist_ok=True)
    old_home = os.environ.get("HERMES_HOME")
    os.environ["HERMES_HOME"] = str(hermes_root)
    try:
        from hermes_cli.profiles import create_profile, seed_profile_skills

        for profile in runtime_map.profiles:
            profile_home = hermes_root / "profiles" / profile.name
            if profile_home.is_dir():
                continue
            if profile.seed == "clone-default":
                create_profile(
                    name=profile.name,
                    clone_from="default",
                    clone_config=True,
                    no_alias=True,
                    description=profile.description,
                )
            else:
                create_profile(
                    name=profile.name,
                    no_alias=True,
                    description=profile.description,
                )
                seed_profile_skills(profile_home, quiet=True)
    finally:
        if old_home is None:
            os.environ.pop("HERMES_HOME", None)
        else:
            os.environ["HERMES_HOME"] = old_home

    _write_env_keys(
        hermes_root / ".env",
        source_assignments,
        tuple(
            dict.fromkeys(
                (
                    *provider_keys,
                    *runtime_map.default_secret_keys,
                    *managed_default_keys,
                )
            )
        ),
        exact=False,
    )
    for profile in runtime_map.profiles:
        _write_env_keys(
            hermes_root / "profiles" / profile.name / ".env",
            source_assignments,
            tuple(dict.fromkeys((*provider_keys, *profile.secret_keys))),
            exact=True,
        )

    apply_config = repo_root / "gonzo" / "deploy" / "apply-config.sh"
    for target_home in [
        hermes_root,
        *(hermes_root / "profiles" / profile.name for profile in runtime_map.profiles),
    ]:
        env = os.environ.copy()
        env.pop("GONZO_RUNTIME_MAP", None)
        env.update(
            {
                "HERMES_HOME": str(target_home),
                "GONZO_VAULT_ROOT": str(vault_root),
            }
        )
        if target_home == hermes_root:
            env["GONZO_RUNTIME_MAP"] = str(runtime_map_path)
        completed = subprocess.run(
            [str(apply_config), "--write"],
            cwd=repo_root,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            raise ValueError(
                f"config deploy failed for {target_home}: {completed.stderr.strip()}"
            )
    return actions


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    render = subparsers.add_parser("render-routes")
    render.add_argument("runtime_map", type=Path)
    bootstrap = subparsers.add_parser("bootstrap")
    bootstrap.add_argument("runtime_map", type=Path)
    bootstrap.add_argument("--hermes-root", type=Path, required=True)
    bootstrap.add_argument("--repo-root", type=Path, required=True)
    bootstrap.add_argument("--vault-root", type=Path, required=True)
    bootstrap.add_argument("--source-env", type=Path, required=True)
    bootstrap.add_argument("--write", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        runtime_map = load_runtime_map(args.runtime_map)
        if args.command == "render-routes":
            sys.stdout.write(render_routes(runtime_map))
            return 0
        if args.command == "bootstrap":
            actions = bootstrap_profiles(
                runtime_map,
                runtime_map_path=args.runtime_map.resolve(),
                hermes_root=args.hermes_root.resolve(),
                repo_root=args.repo_root.resolve(),
                vault_root=args.vault_root.resolve(),
                source_env=args.source_env.resolve(),
                write=args.write,
            )
            for action in actions:
                print(action)
            if not args.write:
                print("dry-run only; pass --write to apply")
            return 0
    except ValueError as exc:
        print(f"runtime map invalid: {exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
