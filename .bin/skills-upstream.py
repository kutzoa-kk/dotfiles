#!/usr/bin/env python3
"""外部から取り込んだスキルの取得元と版を、.bin/skills-upstream.json の記録と比べる。

- check: 取得元のパスに触れた最新の commit と記録を比べ、該当パスの中身が変わっていれば差分を表示する。
  比較は両方の版のファイル一覧（内容の指紋）で行い、属性だけの変更は「変化なし」とみなす。
- sync <名前>: 置き方が mirror（無改変の写し）のものだけ、指定の版（既定は最新）で置き先を丸ごと置き換え、記録を進める。
  adapted（手を入れた写し）は差分を見て人が取り込むため、置き換えない。
取得には gh api を使う（gh の認証が必要）。
"""

from __future__ import annotations

import argparse
import difflib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import quote


DEFAULT_CONFIG = Path(__file__).resolve().parent / "skills-upstream.json"
RAW = "Accept: application/vnd.github.raw"


class Upstream:
    def __init__(self, gh: str) -> None:
        self.gh = gh

    def api(self, endpoint: str, raw: bool = False) -> str:
        args = [self.gh, "api", *(["-H", RAW] if raw else []), endpoint]
        try:
            result = subprocess.run(args, capture_output=True, text=True)
        except FileNotFoundError:
            sys.exit(f"{self.gh} コマンドが見つかりません（取得元の更新は確認できていません）")
        if result.returncode != 0:
            sys.exit(f"gh api {endpoint} が失敗しました（取得元の更新は確認できていません）: {result.stderr.strip()}")
        return result.stdout

    def latest(self, repo: str, path: str) -> str:
        commits = json.loads(self.api(f"repos/{repo}/commits?path={quote(path)}&per_page=1"))
        return commits[0]["sha"]

    def blobs(self, repo: str, sha: str, path: str) -> dict[str, str]:
        """その版で path 以下にあるファイルと、内容の指紋（blob の sha）。"""
        tree = json.loads(self.api(f"repos/{repo}/git/trees/{sha}?recursive=1"))["tree"]
        return {t["path"]: t["sha"] for t in tree if t["type"] == "blob" and under(t["path"], path)}

    def content(self, repo: str, path: str, sha: str) -> str:
        return self.api(f"repos/{repo}/contents/{quote(path)}?ref={sha}", raw=True)

    def changed_files(self, repo: str, path: str, old: str, new: str) -> list[dict]:
        """中身が変わったファイルだけを、手元で作った差分つきで返す（属性だけの変更は含めない）。"""
        before, after = self.blobs(repo, old, path), self.blobs(repo, new, path)
        changed = []
        for name in sorted(before.keys() | after.keys()):
            if before.get(name) == after.get(name):
                continue
            status = "added" if name not in before else "removed" if name not in after else "modified"
            old_text = self.content(repo, name, old) if name in before else ""
            new_text = self.content(repo, name, new) if name in after else ""
            diff = difflib.unified_diff(old_text.splitlines(keepends=True), new_text.splitlines(keepends=True),
                                        fromfile=f"{old[:12]}/{name}", tofile=f"{new[:12]}/{name}")
            changed.append({"filename": name, "status": status, "patch": "".join(diff)})
        return changed


def under(filename: str, path: str) -> bool:
    return filename == path or filename.startswith(path.rstrip("/") + "/")


def check(skills: list[dict], up: Upstream) -> list[dict]:
    report = []
    for s in skills:
        latest = up.latest(s["repo"], s["path"])
        files = up.changed_files(s["repo"], s["path"], s["commit"], latest) if latest != s["commit"] else []
        report.append({"name": s["name"], "mode": s["mode"], "repo": s["repo"], "recorded": s["commit"],
                       "latest": latest, "status": "behind" if files else "current", "files": files})
    return report


def print_report(report: list[dict]) -> None:
    for r in report:
        if r["status"] == "current":
            print(f"{r['name']}: 変化なし（{r['repo']} @ {r['recorded'][:12]}）")
            continue
        action = f"make skills-sync NAME={r['name']} で取り込めます" if r["mode"] == "mirror" else "差分を見て手で反映してください"
        print(f"{r['name']}: 取得元が進んでいます {r['recorded'][:12]} → {r['latest'][:12]}（{action}）")
        for f in r["files"]:
            print(f"=== {f['filename']} ({f['status']})")
            print(f["patch"])


def sync(entry: dict, ref: str | None, root: Path, up: Upstream) -> str:
    if entry["mode"] != "mirror":
        sys.exit(f"{entry['name']} は adapted（手を入れた写し）なので置き換えません。check の差分を見て手で反映してください。")
    sha = ref or up.latest(entry["repo"], entry["path"])
    with tempfile.TemporaryDirectory() as tmp:
        staging = Path(tmp) / "skill"
        prefix = entry["path"].rstrip("/") + "/"
        for path in up.blobs(entry["repo"], sha, entry["path"]):
            write(staging / path[len(prefix):], up.content(entry["repo"], path, sha))
        if entry.get("license"):
            write(staging / "LICENSE", up.content(entry["repo"], entry["license"], sha))
        dest = root / entry["dest"]
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(staging, dest)
    return sha


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG, help="取り込み元の記録（置き先はこのファイルの2つ上を基準にする）")
    parser.add_argument("--gh", default="gh", help="gh コマンドのパス（テスト用）")
    sub = parser.add_subparsers(dest="command", required=True)
    p_check = sub.add_parser("check", help="記録と取得元の最新の版を比べる")
    p_check.add_argument("--json", action="store_true", help="機械向けに JSON で出す")
    p_sync = sub.add_parser("sync", help="mirror の置き先を取得元の版で置き換える")
    p_sync.add_argument("name")
    p_sync.add_argument("--ref", help="取得する commit（既定は最新）")
    args = parser.parse_args()

    config = json.loads(args.config.read_text())
    up = Upstream(args.gh)
    if args.command == "check":
        report = check(config["skills"], up)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print_report(report)
        return

    entry = next((s for s in config["skills"] if s["name"] == args.name), None)
    if entry is None:
        sys.exit(f"{args.name} は記録にありません: {[s['name'] for s in config['skills']]}")
    sha = sync(entry, args.ref, args.config.resolve().parent.parent, up)
    entry["commit"] = sha
    args.config.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n")
    print(f"{entry['name']} を {sha[:12]} に置き換えました: {entry['dest']}")


if __name__ == "__main__":
    main()
