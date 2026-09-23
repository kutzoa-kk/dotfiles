#!/usr/bin/env python3
"""Install the repository's Codex hook boundary without changing upstream code."""

import argparse
import copy
import difflib
import json
import os
from pathlib import Path
import shlex
import sys
import tempfile


REPO_ROOT = Path(__file__).resolve().parent.parent
ADAPTER = REPO_ROOT / "dotdir/.codex/scripts/security-guidance-adapter.py"
BACKUP_NAME = "security-guidance-overlay.backup.json"
PLUGIN_NAME = "security-guidance"


def read_object(path):
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object expected: {path}")
    return value


def hook_definition():
    command = (
        f"/usr/bin/python3 {shlex.quote(str(ADAPTER))}"
        ' --plugin-root "${PLUGIN_ROOT}"'
    )

    def group(timeout, matcher=None):
        result = {"hooks": [{"type": "command", "command": command, "timeout": timeout}]}
        if matcher is not None:
            result["matcher"] = matcher
        return result

    return {"hooks": {
        "SessionStart": [group(180)],
        "UserPromptSubmit": [group(30)],
        "PostToolUse": [group(600, "Edit|Write|MultiEdit|NotebookEdit"), group(600, "Bash")],
        "Stop": [group(600)],
        "SubagentStop": [group(600)],
    }}


def is_managed_hooks(value):
    """Recognize our commands even after the dotfiles checkout has moved."""
    if not isinstance(value, dict) or not isinstance(value.get("hooks"), dict):
        return False
    value = copy.deepcopy(value)
    expected = hook_definition()
    expected_command = expected["hooks"]["SessionStart"][0]["hooks"][0]["command"]
    handlers = []
    for groups in value["hooks"].values():
        if not isinstance(groups, list):
            return False
        for group in groups:
            if not isinstance(group, dict) or not isinstance(group.get("hooks"), list):
                return False
            handlers.extend(group["hooks"])
    if not handlers:
        return False
    for handler in handlers:
        if not isinstance(handler, dict) or handler.get("type") != "command":
            return False
        if not isinstance(handler.get("command"), str):
            return False
        try:
            words = shlex.split(handler["command"])
        except ValueError:
            return False
        if (len(words) != 4 or words[0] != "/usr/bin/python3"
                or Path(words[1]).name != ADAPTER.name
                or words[2:] != ["--plugin-root", "${PLUGIN_ROOT}"]):
            return False
        handler["command"] = expected_command
    return value == expected


def ensure_within(path, root):
    if not path.resolve().is_relative_to(root):
        raise ValueError(f"Refusing a path outside {root}: {path}")


def atomic_write(path, text):
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(text)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def serialized(value):
    return json.dumps(value, indent=2, ensure_ascii=False) + "\n"


def prepare(plugin_root, codex_home, hooks):
    ensure_within(plugin_root, codex_home)
    root_manifest = plugin_root / "plugin.json"
    if root_manifest.exists():
        extensions = read_object(root_manifest).get("extensions")
        if isinstance(extensions, dict) and isinstance(extensions.get("com.openai"), dict):
            raise ValueError(f"Native root manifest takes priority over the Codex overlay: {root_manifest}")
    native_path = plugin_root / ".codex-plugin/plugin.json"
    backup_path = native_path.parent / BACKUP_NAME
    for path in (native_path, backup_path):
        ensure_within(path, plugin_root)
    upstream = read_object(plugin_root / ".claude-plugin/plugin.json")
    if upstream.get("name") != PLUGIN_NAME:
        raise ValueError(f"Unexpected plugin identity: {plugin_root}")
    for name in ("sg-python.sh", "security_reminder_hook.py", "ensure_agent_sdk.py"):
        if not (plugin_root / "hooks" / name).is_file():
            raise ValueError(f"Upstream hook entrypoint is missing: {plugin_root / 'hooks' / name}")

    original = native_path.read_text(encoding="utf-8") if native_path.exists() else None
    manifest = read_object(native_path) if original is not None else dict(upstream)
    if manifest.get("name") != PLUGIN_NAME:
        raise ValueError(f"Unexpected Codex plugin identity: {native_path}")
    if original is not None and "hooks" in manifest and not is_managed_hooks(manifest["hooks"]):
        raise ValueError(f"Existing native/custom Codex hooks are not managed by this overlay: {native_path}")
    if backup_path.exists():
        backup = read_object(backup_path)
        if (backup.get("format") != 1 or "original_manifest" not in backup
                or not isinstance(backup["original_manifest"], (str, type(None)))):
            raise ValueError(f"Invalid overlay backup: {backup_path}")

    before_hooks = manifest.get("hooks")
    if "hooks" not in manifest:
        before_hooks = read_object(plugin_root / "hooks/hooks.json")
    manifest["hooks"] = hooks
    content = serialized(manifest)
    changed = original is None or json.loads(original) != manifest
    return native_path, backup_path, original, before_hooks, content, changed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex-home", type=Path,
                        default=Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))))
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="Report missing/stale overlays without writing (exit 1 on drift).")
    mode.add_argument("--dry-run", action="store_true", help="Show the hook definition diff without writing.")
    args = parser.parse_args()
    codex_home = args.codex_home.expanduser().resolve()
    cache = codex_home / "plugins/cache/claude-plugins-official" / PLUGIN_NAME
    roots = sorted({path.resolve() for path in cache.glob("*") if path.is_dir()})
    if not roots:
        print("[codex-security-hooks] skip: security-guidance is not installed in this Codex home.")
        return 0
    if not ADAPTER.is_file():
        raise ValueError(f"Repository adapter is missing: {ADAPTER}")

    hooks = hook_definition()
    # Validate every installed version before modifying any of them.
    for root in roots:
        ensure_within(root, cache)
    plans = [prepare(root, codex_home, hooks) for root in roots]
    drift = False
    for manifest, backup, original, before_hooks, content, changed in plans:
        if not changed:
            print(f"[codex-security-hooks] current: {manifest}")
            continue
        drift = True
        if args.check:
            print(f"[codex-security-hooks] needs apply: {manifest}")
            continue
        if args.dry_run:
            print(f"[codex-security-hooks] would apply: {manifest}")
            sys.stdout.writelines(difflib.unified_diff(
                serialized(before_hooks).splitlines(keepends=True),
                serialized(hooks).splitlines(keepends=True),
                fromfile="current hook definition", tofile="Codex hook definition"))
            continue
        manifest.parent.mkdir(parents=True, exist_ok=True)
        if not backup.exists():
            atomic_write(backup, serialized({"format": 1, "original_manifest": original}))
        atomic_write(manifest, content)
        print(f"[codex-security-hooks] applied: {manifest} (backup: {backup})")
    if drift and not (args.check or args.dry_run):
        print("[codex-security-hooks] Restart Codex and review/trust the new hook definitions. Trust state was not modified.")
    return 1 if args.check and drift else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError) as error:
        print(f"[codex-security-hooks] error: {error}", file=sys.stderr)
        sys.exit(2)
