"""/understand スキル（dotdir/.claude/skills/understand）の試験。

本物の Claude は呼ばない。サーバーの返却処理と、画面側の記録の組み立てだけを確かめる。
"""

import json
import re
import subprocess
import tempfile
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SKILL_DIR = REPO / "dotdir" / ".claude" / "skills" / "understand"
SERVER_JS = SKILL_DIR / "app" / "server.js"
CONFUSIONS_JS = SKILL_DIR / "app" / "public" / "confusions.js"
URL_PATTERN = re.compile(r"http://127\.0\.0\.1:(\d+)/\?t=([0-9a-f]+)")
STARTUP_TIMEOUT_SEC = 5


def start_server(work_dir):
    """サーバーをブラウザを開かずに起動し、(proc, port, token) を返す。"""
    proc = subprocess.Popen(
        ["node", str(SERVER_JS), "--dir", str(work_dir), "--session", "test-session",
         "--cwd", str(work_dir), "--port", "0", "--no-open"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    url_file = Path(work_dir) / "url.txt"
    deadline = time.time() + STARTUP_TIMEOUT_SEC
    while time.time() < deadline:
        if url_file.exists():
            match = URL_PATTERN.match(url_file.read_text().strip())
            if match:
                return proc, int(match.group(1)), match.group(2)
        time.sleep(0.05)
    proc.kill()
    raise RuntimeError("サーバーが url.txt を書きませんでした")


def post(port, token, path, body):
    """合言葉を付けて JSON を送り、返ってきた JSON を返す。"""
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}{path}",
        data=json.dumps(body).encode(),
        method="POST",
        headers={"Content-Type": "application/json", "X-Understand-Token": token},
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as res:
            return json.loads(res.read())
    except urllib.error.HTTPError as err:
        with err:
            return json.loads(err.read())


class ServerTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.work_dir = Path(self._tmp.name)
        self.proc, self.port, self.token = start_server(self.work_dir)

    def tearDown(self):
        if self.proc.poll() is None:
            self.proc.kill()
        self.proc.wait(timeout=5)
        self._tmp.cleanup()

    def finish(self, body):
        """「メインに送って閉じる」と同じ要求を送り、サーバーが終わるのを待つ。"""
        result = post(self.port, self.token, "/api/return", body)
        self.proc.wait(timeout=5)
        return result


class ReturnTest(ServerTestCase):
    def test_return_writes_return_md(self):
        result = self.finish({"text": "テスト"})
        self.assertEqual(result, {"ok": True})
        self.assertEqual((self.work_dir / "return.md").read_text(), "テスト\n")

    def read_confusions(self):
        return json.loads((self.work_dir / "confusions.json").read_text(encoding="utf-8"))

    def test_return_writes_confusions(self):
        item = {"type": "term", "anchor": "fork-session", "question": "これは何？",
                "answer": "会話の分かれ道", "code": False, "fromSticky": True}
        self.finish({"text": "", "confusions": [item]})
        self.assertEqual(self.read_confusions(), [item])

    def test_return_without_confusions_writes_empty(self):
        self.finish({"text": "テスト"})
        self.assertEqual(self.read_confusions(), [])

    def test_return_ignores_non_list_confusions(self):
        self.finish({"text": "", "confusions": "壊れた"})
        self.assertEqual(self.read_confusions(), [])

    def test_return_sanitizes_bad_items(self):
        items = [
            {"type": "diagram", "anchor": "図"},
            "文字列だけ",
            {"type": "term", "anchor": "あ" * 5000, "question": 3, "answer": "い" * 600,
             "code": "yes", "fromSticky": True},
        ]
        self.finish({"text": "", "confusions": items})
        self.assertEqual(self.read_confusions(), [{
            "type": "term", "anchor": "あ" * 2000, "question": "", "answer": "い" * 500,
            "code": False, "fromSticky": True,
        }])

    def test_return_caps_item_count(self):
        items = [{"type": "question", "anchor": f"文{i}"} for i in range(250)]
        self.finish({"text": "", "confusions": items})
        self.assertEqual(len(self.read_confusions()), 200)

    def test_rejects_wrong_token(self):
        result = post(self.port, "0" * len(self.token), "/api/return", {"text": "テスト"})
        self.assertFalse(result.get("ok", False))
        self.assertFalse((self.work_dir / "return.md").exists())


class GitTrackingTest(unittest.TestCase):
    def test_skill_files_are_not_ignored(self):
        files = [p for p in SKILL_DIR.rglob("*") if p.is_file()]
        out = subprocess.run(
            ["git", "-C", str(REPO), "check-ignore", "--no-index", *map(str, files)],
            capture_output=True, text=True,
        )
        self.assertEqual(out.stdout.strip(), "", "git に無視されているスキルのファイルがあります")


def collect(stickies, order):
    """画面と同じ collectConfusions を Node で動かし、結果を返す。"""
    script = (
        f"const {{ collectConfusions }} = require({json.dumps(str(CONFUSIONS_JS))});"
        "const input = JSON.parse(require('fs').readFileSync(0, 'utf8'));"
        "process.stdout.write(JSON.stringify(collectConfusions(input.stickies, input.order)));"
    )
    out = subprocess.run(
        ["node", "-e", script], input=json.dumps({"stickies": stickies, "order": order}),
        capture_output=True, text=True, check=True,
    )
    return json.loads(out.stdout)


def sticky(sid, type_, anchor="分からない文", parent="main", messages=None, code=None):
    """画面の付箋と同じ形の最小限のデータを作る。"""
    return {
        "id": sid, "type": type_, "parent": parent, "anchorText": anchor, "code": code,
        "messages": messages if messages is not None else [
            {"role": "user", "text": "どういう意味？"},
            {"role": "assistant", "text": "言い換えるとこうです"},
        ],
    }


class CollectConfusionsTest(unittest.TestCase):
    def test_collect_keeps_only_three_types(self):
        stickies = {s["id"]: s for s in [
            sticky("a", "question"), sticky("b", "diagram"), sticky("c", "memo", parent=None),
        ]}
        result = collect(stickies, ["a", "b", "c"])
        self.assertEqual(result, [{
            "type": "question", "anchor": "分からない文", "question": "どういう意味？",
            "answer": "言い換えるとこうです", "code": False, "fromSticky": False,
        }])

    def test_collect_skips_graph_value(self):
        result = collect({"a": sticky("a", "term", anchor="グラフの値：x=1")}, ["a"])
        self.assertEqual(result, [])

    def test_collect_skips_empty_anchor(self):
        result = collect({"a": sticky("a", "detail", anchor="")}, ["a"])
        self.assertEqual(result, [])

    def test_collect_truncates_answer(self):
        messages = [{"role": "user", "text": "詳しく"}, {"role": "assistant", "text": "あ" * 600}]
        result = collect({"a": sticky("a", "detail", messages=messages)}, ["a"])
        self.assertEqual(len(result[0]["answer"]), 500)

    def test_collect_marks_child_and_code(self):
        result = collect({"a": sticky("a", "term", parent="st2", code=True)}, ["a"])
        self.assertTrue(result[0]["fromSticky"])
        self.assertTrue(result[0]["code"])

    def test_collect_uses_first_question_and_last_answer(self):
        messages = [
            {"role": "user", "text": "最初"}, {"role": "assistant", "text": "一つ目"},
            {"role": "user", "text": "続き"}, {"role": "assistant", "text": "二つ目"},
        ]
        result = collect({"a": sticky("a", "question", messages=messages)}, ["a"])
        self.assertEqual((result[0]["question"], result[0]["answer"]), ("最初", "二つ目"))


if __name__ == "__main__":
    unittest.main()
