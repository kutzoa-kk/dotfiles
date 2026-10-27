#!/usr/bin/env python3
"""git(dotdir) の settings.json にあるプラグインと取得元を、このマシンの Claude Code へ反映する。

make link は稼働中の ~/.claude/settings.json を上書きしないため、別のマシンで増減したプラグインはここで反映する。
- 取得元の追加、プラグインの導入、有効・無効の切り替え、取得元の autoUpdate の設定だけを行う。削除はしない。
- このマシンにだけあるプラグイン・取得元は表示するだけにする。
- プラグイン一覧から入れたもの（@anthropic-plugin-directory）は取得元が無いため、名前だけで install する。
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


REPO_ROOT = Path(__file__).resolve().parent.parent
GIT_SETTINGS = REPO_ROOT / "dotdir/.claude/settings.json"
RUNTIME_SETTINGS = Path.home() / ".claude/settings.json"
DIRECTORY = "anthropic-plugin-directory"
# 対話の Claude Code を初めて起動したときに自動で追加される取得元
BUILTIN_MARKETPLACES = {"claude-plugins-official"}


def cli_json(claude: str, *args: str) -> list:
    result = subprocess.run([claude, "plugin", *args, "--json"], check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def known_marketplaces(claude: str) -> set:
    return {m["name"] for m in cli_json(claude, "marketplace", "list")}


def installed_plugins(claude: str) -> dict:
    return {p["id"]: p["enabled"] for p in cli_json(claude, "list") if p.get("scope") == "user"}


def marketplace_arg(entry: dict) -> str | None:
    source = entry.get("source", {})
    return source.get("repo") or source.get("url") or source.get("path")


def plan(git: dict, runtime: dict, known: set, installed: dict) -> tuple[list, list]:
    """(実行する操作, 表示だけの情報) を返す。操作は (説明, 種類, 値) の組。"""
    actions, notes = [], []
    want_mkts = git.get("extraKnownMarketplaces", {})
    want_plugins = git.get("enabledPlugins", {})

    for name, entry in want_mkts.items():
        if name in known:
            continue
        arg = marketplace_arg(entry)
        if arg:
            actions.append((f"取得元を追加: {name}（{arg}）", "marketplace-add", (name, arg)))
        else:
            notes.append(f"取得元 {name} は追加の仕方が分からないため飛ばします: {entry}")
    for name in BUILTIN_MARKETPLACES - known:
        notes.append(f"取得元 {name} がありません。対話の Claude Code を一度起動すると自動で追加されます")

    for pid, enabled in want_plugins.items():
        name, _, mkt = pid.rpartition("@")
        if pid not in installed:
            if enabled:
                target = name if mkt == DIRECTORY else pid
                actions.append((f"導入: {pid}", "install", (pid, target)))
        elif installed[pid] != enabled:
            verb = "enable" if enabled else "disable"
            actions.append((f"{'有効' if enabled else '無効'}にする: {pid}", verb, (pid, pid)))

    runtime_mkts = runtime.get("extraKnownMarketplaces", {})
    for name, entry in want_mkts.items():
        if "autoUpdate" in entry and runtime_mkts.get(name, {}).get("autoUpdate") != entry["autoUpdate"]:
            actions.append((f"取得元 {name} の autoUpdate を {entry['autoUpdate']} にする", "auto-update", (name, entry)))

    for pid in sorted(set(installed) - set(want_plugins)):
        notes.append(f"このマシンにだけあるプラグイン: {pid}（git に残すなら make settings-pull）")
    for name in sorted(known - set(want_mkts) - BUILTIN_MARKETPLACES):
        notes.append(f"このマシンにだけある取得元: {name}")
    return actions, notes


def write_auto_update(runtime_p: Path, name: str, entry: dict) -> None:
    """稼働中の settings.json の extraKnownMarketplaces.<name>.autoUpdate だけを書き換える（一時ファイル + rename）。"""
    runtime = json.loads(runtime_p.read_text(encoding="utf-8"))
    mkts = runtime.setdefault("extraKnownMarketplaces", {})
    mkts[name] = {**mkts.get(name, {"source": entry["source"]}), "autoUpdate": entry["autoUpdate"]}
    fd, tmp = tempfile.mkstemp(dir=runtime_p.parent, prefix=".settings.", suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(runtime, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, runtime_p)


def apply(actions: list, claude: str, runtime_p: Path, assume_yes: bool) -> int:
    failures = 0
    for label, kind, value in actions:
        if kind == "marketplace-add":
            cmd = [claude, "plugin", "marketplace", "add", value[1]]
        elif kind == "install":
            mkt = value[0].rpartition("@")[2]
            if mkt != DIRECTORY and mkt not in known_marketplaces(claude):
                print(f"飛ばしました（取得元 {mkt} がありません）: {label}")
                failures += 1
                continue
            cmd = [claude, "plugin", "install", value[1]] + (["-y"] if assume_yes else [])
        elif kind in ("enable", "disable"):
            cmd = [claude, "plugin", kind, value[1]]
        else:
            write_auto_update(runtime_p, *value)
            print(f"完了: {label}")
            continue
        print(f"実行: {' '.join(cmd)}")
        if subprocess.run(cmd).returncode != 0:
            print(f"失敗しました: {label}")
            failures += 1
    return failures


def confirm() -> bool:
    try:
        with open("/dev/tty", encoding="utf-8") as tty:
            sys.stderr.write("\nこの内容で反映しますか? [y/N]: ")
            sys.stderr.flush()
            return tty.readline().strip().lower() in ("y", "yes")
    except OSError:
        print("確認の入力を受け取れません。--yes を付けて実行してください。")
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--git", type=Path, default=GIT_SETTINGS, help="基準にする git 側の settings.json")
    parser.add_argument("--runtime", type=Path, default=RUNTIME_SETTINGS, help="稼働中の settings.json")
    parser.add_argument("--claude", default="claude", help="claude コマンドのパス（テスト用）")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="やることを表示するだけで実行しない")
    mode.add_argument("--yes", action="store_true", help="確認せずに実行する。取得元が導入時に実行を宣言している命令も確認なしで受け入れる（install -y）")
    args = parser.parse_args()

    git = json.loads(args.git.read_text(encoding="utf-8"))
    runtime = json.loads(args.runtime.read_text(encoding="utf-8"))
    actions, notes = plan(git, runtime, known_marketplaces(args.claude), installed_plugins(args.claude))

    for note in notes:
        print(f"[情報] {note}")
    if not actions:
        print("差分なし。git 側のプラグインと取得元はすべて反映済みです。")
        return 0
    print("\n反映する内容:")
    for label, _, _ in actions:
        print(f"  - {label}")
    if args.dry_run:
        print("\n[dry-run] 実行しませんでした。")
        return 0
    if not args.yes and not confirm():
        print("中止しました。")
        return 0

    failures = apply(actions, args.claude, args.runtime, args.yes)
    print("\nClaude Code を再起動するか、/reload-plugins を実行すると反映されます。")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
