# 作業時間のカレンダー記録 実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 人の作業時間とエージェントの稼働時間をプロジェクトごとに観測し、Google カレンダーの専用カレンダーへ予定として書き込む。

**Architecture:** launchd が 60 秒ごとに `worklog.py sample` を動かし、その時点の状態を観測ログ（JSONL）へ追記する。15 分ごとに `worklog.py sync` が直近 48 時間の観測ログから区間を組み立て直し、作成済み予定の控えと突き合わせて gog CLI で作成・更新・削除する。判定と区間化は副作用のない関数に閉じ込め、外部コマンドの呼び出しは差し替え可能な引数にしてテストする。

**Tech Stack:** Python 3.9 標準ライブラリ（`/usr/bin/python3`）、unittest、gog CLI v0.43、Orca CLI 1.4、launchd、zsh

**Spec:** `docs/superpowers/specs/2026-10-04-worklog-calendar-design.md`

## Global Constraints

- 実行環境は `/usr/bin/python3`（3.9.6）。`X | None` 型注釈、`match` 文、3.10 以降の標準ライブラリ機能は使わない。外部パッケージは入れない。
- dotfiles リポジトリは公開されている。メールアドレス、カレンダー ID、プロジェクト名を git 管理のファイル（`config.json`、テスト、計画書）に書かない。テストでは `me@example.com`、`cal@example.com` を使う。
- 個人設定は `~/.config/worklog/local.json`（キーは `account`、`calendar_id`、`project_colors` のみ）。状態ファイルは `~/.local/state/worklog/`。
- しきい値（`config.json` の `thresholds`）：`active_idle_sec` 60、`reading_max_min` 30、`grace_min` 2、`sample_gap_sec` 120、`merge_gap_min` 5、`min_event_min` 3、`window_hours` 48、`retention_days` 30。
- 予定名は `人｜<プロジェクト>`・`人｜その他`・`AI｜<プロジェクト>`（区切りは全角の縦棒 `｜`）。「その他」の色は `8`（グラファイト）で固定。予定は `--transparency=transparent` で作る。
- 予定には `--private-prop=worklog_key=<kind>|<project>|<start ISO8601>` を付ける。`kind` は `human` または `agent`。
- launchd のラベルは `local.worklog.sample` と `local.worklog.sync`。
- テストは `make test-worklog`（`/usr/bin/python3 -m unittest discover -s .bin/tests -p 'test_worklog_*.py' -v`）で実行する。
- コミットはユーザーの承認を得てから行う（ユーザーのグローバル設定）。各タスクのコミット手順は、承認があった場合に実行する。

## Review Focus

- Chrome などで複数のウィンドウを開いているとき、前面のウィンドウ名が記録されること。`orca computer list-windows` の `index` が小さいほど前面という前提を置いている。Task 2 のテストで「最小の `index` で最小化されていないもの」を選ぶことを固定し、Task 6 で実機確認する。
- 日付をまたぐ作業（23:50〜0:20）が2つの観測ログファイルに分かれても、1つの予定になること。Task 1 のテストで日付をまたいだ読み込みを固定する。
- カレンダー上で予定を手で消した後も、他の予定の書き込みが止まらないこと。更新が失敗しても控えはそのまま残り、エラーログに記録され、他の操作は続く。Task 4 のテストで固定する。
- Orca を終了している間も観測が落ちず、その他の作業は記録されること。Task 2 のテストで Orca の呼び出しが失敗する場合を固定する。
- `sync` を続けて2回実行しても予定が増えないこと。Task 5 のテストで固定する。

## ファイル構成

| ファイル | 役割 |
|---|---|
| `.bin/worklog/config.json` | 共有の既定値（アプリの分類、除外パターン、しきい値、タイムゾーン、カレンダー名） |
| `.bin/worklog/wl_config.py` | `config.json` と `local.json` の読み込み |
| `.bin/worklog/wl_store.py` | 観測ログ、予定の控え、エラーログの読み書き |
| `.bin/worklog/wl_probe.py` | その時点の状態の観測（外部コマンドの呼び出しと出力の解釈） |
| `.bin/worklog/wl_timeline.py` | 人とエージェントの判定、区間化（副作用なし） |
| `.bin/worklog/wl_calendar.py` | 予定の形の決定、突き合わせ、gog の呼び出し |
| `.bin/worklog/worklog.py` | 入口（`sample` / `sync` / `init-calendar`） |
| `.bin/worklog/install.sh` | launchd への登録と解除 |
| `.bin/worklog/launchd/local.worklog.sample.plist.template` | 観測の launchd 設定のひな形 |
| `.bin/worklog/launchd/local.worklog.sync.plist.template` | 書き込みの launchd 設定のひな形 |
| `.bin/tests/worklog_fixtures.py` | テスト共通の部品（観測データの生成、偽の gog） |
| `.bin/tests/test_worklog_store.py` | `wl_config`・`wl_store` のテスト |
| `.bin/tests/test_worklog_probe.py` | `wl_probe` のテスト |
| `.bin/tests/test_worklog_timeline.py` | `wl_timeline` のテスト |
| `.bin/tests/test_worklog_calendar.py` | `wl_calendar` のテスト |
| `.bin/tests/test_worklog_cli.py` | `worklog.py` の通しテスト |
| `Makefile` | `worklog-install`・`worklog-uninstall`・`test-worklog` を追加 |

`.bin/` は `make link` の対象外なので、スクリプトは dotfiles の置き場所から直接実行される。

## データの形（全タスク共通）

観測1件（ファイルに書く形）：

```python
{"ts": "2026-10-05T10:00:05+09:00", "idle_sec": 12, "locked": False,
 "front_bundle": "com.google.Chrome", "front_app": "Google Chrome",
 "window_title": "paper - Google Scholar", "orca_project": "dotfiles2",
 "agents": [{"project": "dotfiles2", "type": "claude"}]}
```

読み込んだ観測には、解釈済みの時刻 `"_ts": datetime`（タイムゾーン付き）が加わる。

作業1分の記録（credit）：`(minute: datetime, bucket: str, detail)`。人の場合 `detail` は `str` または `None`（Orca だけを見ていた分）、エージェントの場合は `collections.Counter`（種類 → 同時数）。

区間：`{"kind": "human"|"agent", "project": str, "start": datetime, "end": datetime, "details": list}`。

予定の控え（`events.json`）：`{worklog_key: {"id": str, "start": iso, "end": iso, "description": str}}`。

---

### Task 1: 設定と状態ファイル

**Files:**
- Create: `.bin/worklog/config.json`
- Create: `.bin/worklog/wl_config.py`
- Create: `.bin/worklog/wl_store.py`
- Create: `.bin/tests/worklog_fixtures.py`
- Test: `.bin/tests/test_worklog_store.py`

**Interfaces:**
- Consumes: なし
- Produces:
  - `wl_config.load_config(repo_path=REPO_CONFIG, local_path=LOCAL_CONFIG) -> dict`
  - `wl_config.require(cfg: dict, *keys: str) -> None`（欠けていれば `ConfigError`）
  - `wl_config.ConfigError`、`wl_config.LOCAL_CONFIG: Path`
  - `wl_store.STATE_DIR: Path`
  - `wl_store.append_sample(sample: dict, state_dir=STATE_DIR) -> None`
  - `wl_store.load_samples(since: datetime, state_dir=STATE_DIR) -> (list[dict], list[str])`
  - `wl_store.load_ledger(state_dir=STATE_DIR) -> dict`、`wl_store.save_ledger(ledger: dict, state_dir=STATE_DIR) -> None`
  - `wl_store.log_error(message: str, now: datetime, state_dir=STATE_DIR) -> None`
  - `wl_store.prune_samples(before_day: date, state_dir=STATE_DIR) -> None`
  - `worklog_fixtures`：`CFG`、`BASE`、`JST`、`ORCA`、`CHROME`、`VSCODE`、`WORKLOG_DIR`、`at(minute)`、`sample(...)`、`idle_run(...)`、`stored(sample)`

- [ ] **Step 1: 共通のテスト部品を書く**

`.bin/tests/worklog_fixtures.py`：

```python
"""Shared builders for worklog tests."""
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

WORKLOG_DIR = Path(__file__).resolve().parents[1] / "worklog"
sys.path.insert(0, str(WORKLOG_DIR))

JST = timezone(timedelta(hours=9))
BASE = datetime(2026, 10, 5, 10, 0, tzinfo=JST)
ORCA = "com.stablyai.orca"
CHROME = "com.google.Chrome"
VSCODE = "com.microsoft.VSCode"

CFG = {
    "timezone": "Asia/Tokyo",
    "calendar_name": "作業ログ",
    "project_apps": [ORCA, CHROME],
    "other_apps": [VSCODE],
    "exclude_title_patterns": ["YouTube"],
    "thresholds": {
        "active_idle_sec": 60, "reading_max_min": 30, "grace_min": 2,
        "sample_gap_sec": 120, "merge_gap_min": 5, "min_event_min": 3,
        "window_hours": 48, "retention_days": 30,
    },
    "account": "me@example.com",
    "calendar_id": "cal@example.com",
    "project_colors": {"dotfiles2": "9"},
}


def at(minute):
    return BASE + timedelta(minutes=minute)


def sample(minute, idle=0, locked=False, bundle=ORCA, app="Orca", title="Orca",
           project="dotfiles2", agents=()):
    ts = at(minute) + timedelta(seconds=5)
    return {"ts": ts.isoformat(), "_ts": ts, "idle_sec": idle, "locked": locked,
            "front_bundle": bundle, "front_app": app, "window_title": title,
            "orca_project": project, "agents": list(agents)}


def idle_run(first, last, since_minute, **kw):
    """Idle samples for minutes first..last; the last input was at since_minute."""
    return [sample(m, idle=(m - since_minute) * 60, **kw) for m in range(first, last + 1)]


def stored(s):
    """The sample as written to disk (without the parsed _ts)."""
    return {k: v for k, v in s.items() if k != "_ts"}
```

- [ ] **Step 2: 失敗するテストを書く**

`.bin/tests/test_worklog_store.py`：

```python
"""wl_config and wl_store: settings merge and state files."""
import json
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from worklog_fixtures import BASE, sample, stored

import wl_config
import wl_store


class ConfigTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.shared = self.tmp / "config.json"
        self.shared.write_text(json.dumps({"timezone": "Asia/Tokyo"}), encoding="utf-8")
        self.local = self.tmp / "local.json"

    def test_local_values_override_defaults(self):
        self.local.write_text(json.dumps({"account": "me@example.com"}), encoding="utf-8")
        cfg = wl_config.load_config(self.shared, self.local)
        self.assertEqual(cfg["timezone"], "Asia/Tokyo")
        self.assertEqual(cfg["account"], "me@example.com")
        self.assertEqual(cfg["calendar_id"], "")
        self.assertEqual(cfg["project_colors"], {})

    def test_missing_local_file_gives_empty_personal_values(self):
        cfg = wl_config.load_config(self.shared, self.local)
        self.assertEqual(cfg["account"], "")

    def test_unknown_local_key_is_rejected(self):
        self.local.write_text(json.dumps({"acount": "typo"}), encoding="utf-8")
        with self.assertRaises(wl_config.ConfigError):
            wl_config.load_config(self.shared, self.local)

    def test_require_names_missing_keys(self):
        with self.assertRaisesRegex(wl_config.ConfigError, "calendar_id"):
            wl_config.require({"account": "a", "calendar_id": ""}, "account", "calendar_id")


class StoreTest(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())

    def test_samples_round_trip_across_midnight(self):
        before = sample(-11)  # 2026-10-05 09:49
        late = dict(stored(sample(0)), ts="2026-10-04T23:59:05+09:00")
        wl_store.append_sample(late, self.dir)
        wl_store.append_sample(stored(before), self.dir)
        self.assertEqual(sorted(p.name for p in self.dir.iterdir()),
                         ["samples-2026-10-04.jsonl", "samples-2026-10-05.jsonl"])
        loaded, errors = wl_store.load_samples(BASE - timedelta(days=1), self.dir)
        self.assertEqual(errors, [])
        self.assertEqual([s["ts"] for s in loaded], [late["ts"], before["ts"]])
        self.assertEqual(loaded[1]["_ts"], before["_ts"])

    def test_samples_before_since_are_skipped(self):
        for m in (0, 10):
            wl_store.append_sample(stored(sample(m)), self.dir)
        loaded, _ = wl_store.load_samples(BASE + timedelta(minutes=5), self.dir)
        self.assertEqual(len(loaded), 1)

    def test_broken_lines_are_reported_and_skipped(self):
        wl_store.append_sample(stored(sample(0)), self.dir)
        with open(self.dir / "samples-2026-10-05.jsonl", "a", encoding="utf-8") as f:
            f.write('{"ts": "2026-10-05T10:01\n42\n')
        loaded, errors = wl_store.load_samples(BASE, self.dir)
        self.assertEqual(len(loaded), 1)
        self.assertEqual(len(errors), 2)
        self.assertIn("samples-2026-10-05.jsonl:2", errors[0])

    def test_ledger_round_trip_and_missing_file(self):
        self.assertEqual(wl_store.load_ledger(self.dir), {})
        ledger = {"human|dotfiles2|x": {"id": "ev1", "start": "s", "end": "e", "description": ""}}
        wl_store.save_ledger(ledger, self.dir)
        self.assertEqual(wl_store.load_ledger(self.dir), ledger)

    def test_prune_samples_deletes_old_days_only(self):
        for day in ("2026-09-01", "2026-10-05"):
            (self.dir / f"samples-{day}.jsonl").write_text("", encoding="utf-8")
        wl_store.prune_samples(date(2026, 9, 5), self.dir)
        self.assertEqual([p.name for p in self.dir.iterdir()], ["samples-2026-10-05.jsonl"])

    def test_log_error_appends_with_timestamp(self):
        wl_store.log_error("first", BASE, self.dir)
        wl_store.log_error("second", BASE, self.dir)
        lines = (self.dir / "errors.log").read_text(encoding="utf-8").splitlines()
        self.assertEqual(lines, ["2026-10-05T10:00:00+09:00 first", "2026-10-05T10:00:00+09:00 second"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: テストが失敗することを確かめる**

Run: `/usr/bin/python3 -m unittest discover -s .bin/tests -p 'test_worklog_store.py' -v`
Expected: `ModuleNotFoundError: No module named 'wl_config'`

- [ ] **Step 4: 設定ファイルと2つのモジュールを書く**

`.bin/worklog/config.json`：

```json
{
  "timezone": "Asia/Tokyo",
  "calendar_name": "作業ログ",
  "project_apps": [
    "com.stablyai.orca",
    "com.google.Chrome",
    "com.apple.Safari",
    "com.apple.Preview",
    "com.microsoft.Word",
    "com.adobe.Acrobat.Pro",
    "com.adobe.Reader",
    "md.obsidian"
  ],
  "other_apps": [
    "com.microsoft.VSCode",
    "com.microsoft.Powerpoint",
    "com.microsoft.Excel"
  ],
  "exclude_title_patterns": [
    "YouTube",
    "TVer",
    "Netflix",
    "Prime Video",
    "ABEMA",
    "U-NEXT",
    "Disney+"
  ],
  "thresholds": {
    "active_idle_sec": 60,
    "reading_max_min": 30,
    "grace_min": 2,
    "sample_gap_sec": 120,
    "merge_gap_min": 5,
    "min_event_min": 3,
    "window_hours": 48,
    "retention_days": 30
  }
}
```

`.bin/worklog/wl_config.py`：

```python
"""Settings: shared defaults in config.json (git) plus per-PC local.json."""
import json
from pathlib import Path

REPO_CONFIG = Path(__file__).resolve().parent / "config.json"
LOCAL_CONFIG = Path.home() / ".config/worklog/local.json"
# The dotfiles repo is public: personal values live only in local.json.
LOCAL_DEFAULTS = {"account": "", "calendar_id": "", "project_colors": {}}


class ConfigError(Exception):
    pass


def load_config(repo_path=REPO_CONFIG, local_path=LOCAL_CONFIG):
    shared = json.loads(Path(repo_path).read_text(encoding="utf-8"))
    local_path = Path(local_path)
    local = json.loads(local_path.read_text(encoding="utf-8")) if local_path.exists() else {}
    unknown = sorted(set(local) - set(LOCAL_DEFAULTS))
    if unknown:
        raise ConfigError(f"unknown keys in {local_path}: {unknown}")
    return {**shared, **LOCAL_DEFAULTS, **local}


def require(cfg, *keys):
    missing = [key for key in keys if not cfg.get(key)]
    if missing:
        raise ConfigError(f"set {', '.join(missing)} in {LOCAL_CONFIG}")
```

`.bin/worklog/wl_store.py`：

```python
"""Files under ~/.local/state/worklog: samples, event ledger, error log."""
import json
from datetime import datetime
from pathlib import Path

STATE_DIR = Path.home() / ".local/state/worklog"
SAMPLE_PREFIX = "samples-"
LEDGER_NAME = "events.json"


def _sample_day(path):
    return path.stem[len(SAMPLE_PREFIX):]


def append_sample(sample, state_dir=STATE_DIR):
    state_dir.mkdir(parents=True, exist_ok=True)
    line = json.dumps(sample, ensure_ascii=False) + "\n"
    # One write per line keeps a concurrent reader from seeing half a record.
    with open(state_dir / f"{SAMPLE_PREFIX}{sample['ts'][:10]}.jsonl", "a", encoding="utf-8") as f:
        f.write(line)


def load_samples(since, state_dir=STATE_DIR):
    """Return (samples at or after `since` sorted by time, messages for broken lines)."""
    samples, errors = [], []
    first_day = since.date().isoformat()
    for path in sorted(state_dir.glob(f"{SAMPLE_PREFIX}*.jsonl")):
        if _sample_day(path) < first_day:
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            try:
                raw = json.loads(line)
                ts = datetime.fromisoformat(raw["ts"])
            except (ValueError, KeyError, TypeError) as exc:
                errors.append(f"{path.name}:{number}: {exc!r}")
                continue
            if ts >= since:
                samples.append({**raw, "_ts": ts})
    return sorted(samples, key=lambda s: s["_ts"]), errors


def load_ledger(state_dir=STATE_DIR):
    path = state_dir / LEDGER_NAME
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_ledger(ledger, state_dir=STATE_DIR):
    state_dir.mkdir(parents=True, exist_ok=True)
    tmp = state_dir / (LEDGER_NAME + ".tmp")
    tmp.write_text(json.dumps(ledger, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    tmp.replace(state_dir / LEDGER_NAME)


def log_error(message, now, state_dir=STATE_DIR):
    state_dir.mkdir(parents=True, exist_ok=True)
    with open(state_dir / "errors.log", "a", encoding="utf-8") as f:
        f.write(f"{now.isoformat(timespec='seconds')} {message}\n")


def prune_samples(before_day, state_dir=STATE_DIR):
    """Delete sample files dated before `before_day`."""
    for path in state_dir.glob(f"{SAMPLE_PREFIX}*.jsonl"):
        if _sample_day(path) < before_day.isoformat():
            path.unlink()
```

- [ ] **Step 5: テストが通ることを確かめる**

Run: `/usr/bin/python3 -m unittest discover -s .bin/tests -p 'test_worklog_store.py' -v`
Expected: 10 tests, `OK`

- [ ] **Step 6: コミット（承認後）**

```bash
git add .bin/worklog/config.json .bin/worklog/wl_config.py .bin/worklog/wl_store.py .bin/tests/worklog_fixtures.py .bin/tests/test_worklog_store.py
git commit -m "feat: worklog の設定と状態ファイルの読み書きを追加する"
```

---

### Task 2: その時点の状態の観測

**Files:**
- Create: `.bin/worklog/wl_probe.py`
- Test: `.bin/tests/test_worklog_probe.py`

**Interfaces:**
- Consumes: なし
- Produces:
  - `wl_probe.run(cmd: list[str], timeout=10) -> bytes | None`（失敗時 `None`）
  - `wl_probe.ProbeError`
  - `wl_probe.parse_idle_sec(ioreg_out: bytes) -> int`
  - `wl_probe.parse_locked(root_plist: bytes) -> bool`
  - `wl_probe.parse_lsappinfo(out: bytes) -> dict`
  - `wl_probe.parse_orca_ps(out: bytes) -> (str | None, list[dict])`
  - `wl_probe.parse_window_title(out: bytes) -> str | None`
  - `wl_probe.collect_sample(now: datetime, runner=run) -> dict`（観測1件。`_ts` は含まない）

- [ ] **Step 1: 失敗するテストを書く**

`.bin/tests/test_worklog_probe.py`：

```python
"""wl_probe: parsing command output and assembling one sample."""
import json
import plistlib
import unittest

from worklog_fixtures import BASE, CHROME

import wl_probe

ASN = "ASN:0x0-0x2c02c:"
ORCA_PS = {"result": {"worktrees": [
    {"repo": "dotfiles2", "isActive": True, "agents": [
        {"agentType": "claude", "state": "working"},
        {"agentType": "claude", "state": "done"}]},
    {"repo": "proj-b", "isActive": False, "agents": [
        {"agentType": "codex", "state": "working"}]},
    {"repo": "proj-c", "isActive": False},
]}}
WINDOWS = {"result": {"windows": [
    {"index": 1, "isMinimized": False, "title": "Background"},
    {"index": 2, "isMinimized": True, "title": "Minimized"},
    {"index": 0, "isMinimized": False, "title": "paper - Google Scholar"},
]}}


def fake_runner(orca_up=True):
    outputs = {
        ("ioreg", "-c", "IOHIDSystem"): b'    | |   "HIDIdleTime" = 13231015208\n',
        ("ioreg", "-n", "Root", "-d1", "-a"): plistlib.dumps({"IOConsoleUsers": [{"kCGSSessionOnConsoleKey": True}]}),
        ("lsappinfo", "front"): (ASN + "\n").encode(),
        ("lsappinfo", "info", "-only", "bundleid", ASN): b'"CFBundleIdentifier"="com.google.Chrome"\n',
        ("lsappinfo", "info", "-only", "name", ASN): b'"LSDisplayName"="Google Chrome"\n',
        ("orca", "worktree", "ps", "--json"): json.dumps(ORCA_PS).encode() if orca_up else None,
        ("orca", "computer", "list-windows", "--app", CHROME, "--json"):
            json.dumps(WINDOWS).encode() if orca_up else None,
    }
    return lambda cmd: outputs[tuple(cmd)]


class ParseTest(unittest.TestCase):
    def test_idle_is_whole_seconds(self):
        self.assertEqual(wl_probe.parse_idle_sec(b'"HIDIdleTime" = 13231015208'), 13)

    def test_idle_missing_raises(self):
        with self.assertRaises(wl_probe.ProbeError):
            wl_probe.parse_idle_sec(b"nothing")

    def test_locked_only_when_flag_present(self):
        locked = plistlib.dumps({"IOConsoleUsers": [{"CGSSessionScreenIsLocked": True}]})
        unlocked = plistlib.dumps({"IOConsoleUsers": [{"kCGSSessionOnConsoleKey": True}]})
        self.assertTrue(wl_probe.parse_locked(locked))
        self.assertFalse(wl_probe.parse_locked(unlocked))

    def test_lsappinfo_pairs(self):
        self.assertEqual(wl_probe.parse_lsappinfo(b'"LSDisplayName"="Google Chrome"\n'),
                         {"LSDisplayName": "Google Chrome"})

    def test_orca_ps_active_project_and_working_agents(self):
        project, agents = wl_probe.parse_orca_ps(json.dumps(ORCA_PS).encode())
        self.assertEqual(project, "dotfiles2")
        self.assertEqual(agents, [{"project": "dotfiles2", "type": "claude"},
                                  {"project": "proj-b", "type": "codex"}])

    def test_window_title_is_front_visible_window(self):
        self.assertEqual(wl_probe.parse_window_title(json.dumps(WINDOWS).encode()),
                         "paper - Google Scholar")

    def test_empty_title_becomes_none(self):
        out = json.dumps({"result": {"windows": [{"index": 0, "isMinimized": False, "title": ""}]}})
        self.assertIsNone(wl_probe.parse_window_title(out.encode()))


class CollectTest(unittest.TestCase):
    def test_collects_one_sample(self):
        s = wl_probe.collect_sample(BASE, fake_runner())
        self.assertEqual(s, {
            "ts": "2026-10-05T10:00:00+09:00", "idle_sec": 13, "locked": False,
            "front_bundle": CHROME, "front_app": "Google Chrome",
            "window_title": "paper - Google Scholar", "orca_project": "dotfiles2",
            "agents": [{"project": "dotfiles2", "type": "claude"},
                       {"project": "proj-b", "type": "codex"}],
        })

    def test_orca_down_leaves_orca_fields_empty(self):
        s = wl_probe.collect_sample(BASE, fake_runner(orca_up=False))
        self.assertEqual((s["orca_project"], s["agents"], s["window_title"]), (None, [], None))
        self.assertEqual(s["front_bundle"], CHROME)

    def test_missing_system_output_raises(self):
        def broken(cmd):
            return None if cmd[0] == "ioreg" else fake_runner()(cmd)
        with self.assertRaises(wl_probe.ProbeError):
            wl_probe.collect_sample(BASE, broken)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: テストが失敗することを確かめる**

Run: `/usr/bin/python3 -m unittest discover -s .bin/tests -p 'test_worklog_probe.py' -v`
Expected: `ModuleNotFoundError: No module named 'wl_probe'`

- [ ] **Step 3: 実装を書く**

`.bin/worklog/wl_probe.py`：

```python
"""Observe the desk right now: input idle time, screen lock, front app, Orca state."""
import json
import plistlib
import re
import subprocess

IDLE_RE = re.compile(rb'"HIDIdleTime" = (\d+)')
LSAPPINFO_RE = re.compile(r'"(\w+)"="([^"]*)"')
NANOS_PER_SEC = 1_000_000_000


class ProbeError(Exception):
    pass


def run(cmd, timeout=10):
    """Return stdout, or None when the command fails (e.g. Orca is not running)."""
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return result.stdout if result.returncode == 0 else None


def _required(runner, cmd):
    out = runner(cmd)
    if out is None:
        raise ProbeError(f"command failed: {' '.join(cmd)}")
    return out


def parse_idle_sec(ioreg_out):
    match = IDLE_RE.search(ioreg_out)
    if not match:
        raise ProbeError("HIDIdleTime not found in ioreg output")
    return int(match.group(1)) // NANOS_PER_SEC


def parse_locked(root_plist):
    # The lock flag only appears while the screen is locked.
    users = plistlib.loads(root_plist).get("IOConsoleUsers", [])
    return any(user.get("CGSSessionScreenIsLocked") for user in users)


def parse_lsappinfo(out):
    return dict(LSAPPINFO_RE.findall(out.decode("utf-8")))


def parse_orca_ps(out):
    """Return (selected project, working agents) from `orca worktree ps --json`."""
    active, agents = None, []
    for worktree in json.loads(out)["result"]["worktrees"]:
        if worktree.get("isActive"):
            active = worktree["repo"]
        agents += [{"project": worktree["repo"], "type": agent.get("agentType") or "unknown"}
                   for agent in worktree.get("agents", []) if agent.get("state") == "working"]
    return active, agents


def parse_window_title(out):
    """Title of the front window: the lowest index that is not minimized."""
    windows = [w for w in json.loads(out)["result"]["windows"] if not w.get("isMinimized")]
    if not windows:
        return None
    return min(windows, key=lambda w: w.get("index", 0)).get("title") or None


def collect_sample(now, runner=run):
    idle_sec = parse_idle_sec(_required(runner, ["ioreg", "-c", "IOHIDSystem"]))
    locked = parse_locked(_required(runner, ["ioreg", "-n", "Root", "-d1", "-a"]))
    asn = _required(runner, ["lsappinfo", "front"]).decode("utf-8").strip()
    bundle = parse_lsappinfo(_required(runner, ["lsappinfo", "info", "-only", "bundleid", asn])).get("CFBundleIdentifier")
    app = parse_lsappinfo(_required(runner, ["lsappinfo", "info", "-only", "name", asn])).get("LSDisplayName")
    ps = runner(["orca", "worktree", "ps", "--json"])
    project, agents = parse_orca_ps(ps) if ps else (None, [])
    windows = runner(["orca", "computer", "list-windows", "--app", bundle, "--json"]) if ps and bundle else None
    return {
        "ts": now.isoformat(timespec="seconds"),
        "idle_sec": idle_sec,
        "locked": locked,
        "front_bundle": bundle,
        "front_app": app,
        "window_title": parse_window_title(windows) if windows else None,
        "orca_project": project,
        "agents": agents,
    }
```

- [ ] **Step 4: テストが通ることを確かめる**

Run: `/usr/bin/python3 -m unittest discover -s .bin/tests -p 'test_worklog_probe.py' -v`
Expected: 10 tests, `OK`

- [ ] **Step 5: 実機で1回観測して形を確かめる**

Run: `/usr/bin/python3 -c 'import sys; sys.path.insert(0, ".bin/worklog"); import json, datetime, wl_probe; print(json.dumps(wl_probe.collect_sample(datetime.datetime.now().astimezone()), ensure_ascii=False))'`
Expected: 1行の JSON。`front_bundle` が前面のアプリ、`orca_project` が Orca で選んでいるプロジェクト名、`idle_sec` が数秒程度。

- [ ] **Step 6: コミット（承認後）**

```bash
git add .bin/worklog/wl_probe.py .bin/tests/test_worklog_probe.py
git commit -m "feat: worklog の観測処理を追加する"
```

---

### Task 3: 判定と区間化

**Files:**
- Create: `.bin/worklog/wl_timeline.py`
- Test: `.bin/tests/test_worklog_timeline.py`

**Interfaces:**
- Consumes: 観測（`_ts` 付き、Task 1 の `load_samples` の戻り値）、設定 `cfg`（Task 1）
- Produces:
  - `wl_timeline.OTHER = "その他"`、`wl_timeline.ORCA_BUNDLE = "com.stablyai.orca"`
  - `wl_timeline.classify(sample: dict, cfg: dict) -> (str, str | None) | None`
  - `wl_timeline.human_minutes(samples: list, cfg: dict) -> list[(datetime, str, str | None)]`
  - `wl_timeline.agent_minutes(samples: list) -> list[(datetime, str, Counter)]`
  - `wl_timeline.build_intervals(kind: str, credits: list, cfg: dict) -> list[dict]`

- [ ] **Step 1: 失敗するテストを書く**

`.bin/tests/test_worklog_timeline.py`：

```python
"""wl_timeline: which minutes count as work, and how they become intervals."""
import unittest
from collections import Counter

from worklog_fixtures import CFG, CHROME, VSCODE, at, idle_run, sample

from wl_timeline import OTHER, agent_minutes, build_intervals, human_minutes


def human_spans(samples):
    return [(i["project"], i["start"], i["end"])
            for i in build_intervals("human", human_minutes(samples, CFG), CFG)]


def active(first, last, **kw):
    return [sample(m, **kw) for m in range(first, last + 1)]


class ReadingGapTest(unittest.TestCase):
    def test_resumed_in_same_window_counts_the_gap(self):
        s = active(0, 4) + idle_run(5, 14, 4) + [sample(15)]
        self.assertEqual(human_spans(s), [("dotfiles2", at(0), at(16))])

    def test_gap_of_exactly_30_minutes_counts(self):
        s = [sample(0)] + idle_run(1, 29, 0) + [sample(30)]
        self.assertEqual(human_spans(s), [("dotfiles2", at(0), at(31))])

    def test_gap_over_30_minutes_keeps_only_grace(self):
        s = [sample(0)] + idle_run(1, 30, 0) + [sample(31)]
        self.assertEqual(human_spans(s), [("dotfiles2", at(0), at(3))])

    def test_lock_keeps_only_grace(self):
        s = active(0, 4) + idle_run(5, 7, 4) + idle_run(8, 20, 4, locked=True) + [sample(21)]
        self.assertEqual(human_spans(s), [("dotfiles2", at(0), at(7))])

    def test_resume_in_other_window_keeps_only_grace(self):
        s = active(0, 4) + idle_run(5, 14, 4) + active(15, 19, title="Other")
        self.assertEqual(human_spans(s), [("dotfiles2", at(0), at(7)), ("dotfiles2", at(15), at(20))])

    def test_unresolved_gap_at_end_keeps_only_grace(self):
        s = active(0, 4) + idle_run(5, 12, 4)
        self.assertEqual(human_spans(s), [("dotfiles2", at(0), at(7))])

    def test_sleep_gap_is_not_counted(self):
        s = active(0, 4) + active(30, 34)
        self.assertEqual(human_spans(s), [("dotfiles2", at(0), at(5)), ("dotfiles2", at(30), at(35))])


class ClassifyTest(unittest.TestCase):
    def test_excluded_title_is_not_counted(self):
        s = active(0, 9, bundle=CHROME, app="Google Chrome", title="Cats - youtube")
        self.assertEqual(human_spans(s), [])

    def test_other_apps_count_without_orca(self):
        s = active(0, 4, bundle=VSCODE, app="Code", title="main.py", project=None)
        intervals = build_intervals("human", human_minutes(s, CFG), CFG)
        self.assertEqual([(i["project"], i["start"], i["end"]) for i in intervals], [(OTHER, at(0), at(5))])
        self.assertEqual(set(intervals[0]["details"]), {"Code: main.py"})

    def test_project_app_needs_orca_project(self):
        self.assertEqual(human_spans(active(0, 9, bundle=CHROME, project=None)), [])

    def test_unlisted_app_is_not_counted(self):
        self.assertEqual(human_spans(active(0, 9, bundle="com.apple.Terminal")), [])

    def test_orca_minutes_have_no_detail_but_other_windows_do(self):
        s = active(0, 2) + active(3, 5, bundle=CHROME, app="Google Chrome", title="paper")
        details = build_intervals("human", human_minutes(s, CFG), CFG)[0]["details"]
        self.assertEqual(Counter(details), Counter({None: 3, "Google Chrome: paper": 3}))


class MergeTest(unittest.TestCase):
    def test_gap_under_5_minutes_merges(self):
        self.assertEqual(human_spans(active(0, 4) + active(8, 12)), [("dotfiles2", at(0), at(13))])

    def test_gap_of_5_minutes_splits(self):
        self.assertEqual(human_spans(active(0, 4) + active(10, 14)),
                         [("dotfiles2", at(0), at(5)), ("dotfiles2", at(10), at(15))])

    def test_intervals_under_3_minutes_are_dropped(self):
        self.assertEqual(human_spans(active(0, 1)), [])


class AgentTest(unittest.TestCase):
    def test_parallel_projects_are_separate_intervals(self):
        agents = [{"project": "dotfiles2", "type": "claude"}, {"project": "proj-b", "type": "codex"}]
        s = active(0, 4, agents=agents, idle=600)
        intervals = build_intervals("agent", agent_minutes(s), CFG)
        self.assertEqual([(i["project"], i["start"], i["end"]) for i in intervals],
                         [("dotfiles2", at(0), at(5)), ("proj-b", at(0), at(5))])

    def test_same_project_agents_share_one_interval(self):
        agents = [{"project": "dotfiles2", "type": "claude"}] * 2
        intervals = build_intervals("agent", agent_minutes(active(0, 4, agents=agents)), CFG)
        self.assertEqual(len(intervals), 1)
        self.assertEqual(intervals[0]["details"][0], Counter({"claude": 2}))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: テストが失敗することを確かめる**

Run: `/usr/bin/python3 -m unittest discover -s .bin/tests -p 'test_worklog_timeline.py' -v`
Expected: `ModuleNotFoundError: No module named 'wl_timeline'`

- [ ] **Step 3: 実装を書く**

`.bin/worklog/wl_timeline.py`：

```python
"""Decide which minutes count as work and turn them into intervals (no side effects).

Rules: docs/superpowers/specs/2026-10-04-worklog-calendar-design.md
"""
from collections import Counter, defaultdict
from datetime import timedelta

OTHER = "その他"
ORCA_BUNDLE = "com.stablyai.orca"
ONE_MIN = timedelta(minutes=1)


def _minute(sample):
    return sample["_ts"].replace(second=0, microsecond=0)


def _context(sample):
    return sample.get("front_bundle"), sample.get("window_title")


def _is_active(sample, cfg):
    return sample["idle_sec"] < cfg["thresholds"]["active_idle_sec"] and not sample["locked"]


def classify(sample, cfg):
    """Return (bucket, detail) when the front window counts as work, else None."""
    title = sample.get("window_title") or ""
    if any(pattern.lower() in title.lower() for pattern in cfg["exclude_title_patterns"]):
        return None
    bundle = sample.get("front_bundle")
    app = sample.get("front_app") or bundle
    detail = f"{app}: {title}" if title else app
    if bundle in cfg["other_apps"]:
        return OTHER, detail
    if bundle in cfg["project_apps"] and sample.get("orca_project"):
        return sample["orca_project"], (None if bundle == ORCA_BUNDLE else detail)
    return None


def _idle_run_credits(last_active, run, resumed, cfg):
    """Credit an idle stretch: all of it when reading resumed in the same window, else a grace."""
    if last_active is None or not run:
        return []
    bucket = classify(last_active, cfg)
    if bucket is None:
        return []
    t = cfg["thresholds"]
    last_input = run[0]["_ts"] - timedelta(seconds=run[0]["idle_sec"])
    reading = (resumed is not None
               and not any(s["locked"] for s in run)
               and _context(resumed) == _context(last_active)
               and resumed["_ts"] - last_input <= timedelta(minutes=t["reading_max_min"]))
    limit = None if reading else last_input + timedelta(minutes=t["grace_min"])
    return [(_minute(s),) + bucket for s in run if limit is None or s["_ts"] <= limit]


def human_minutes(samples, cfg):
    gap = timedelta(seconds=cfg["thresholds"]["sample_gap_sec"])
    credits, last_active, run, previous = [], None, [], None
    for s in samples:
        if previous is not None and s["_ts"] - previous > gap:
            credits += _idle_run_credits(last_active, run, None, cfg)
            last_active, run = None, []
        previous = s["_ts"]
        if _is_active(s, cfg):
            credits += _idle_run_credits(last_active, run, s, cfg)
            bucket = classify(s, cfg)
            if bucket is not None:
                credits.append((_minute(s),) + bucket)
            last_active, run = s, []
        else:
            run = run + [s]
    return credits + _idle_run_credits(last_active, run, None, cfg)


def agent_minutes(samples):
    credits = []
    for s in samples:
        per_project = defaultdict(Counter)
        for agent in s.get("agents", []):
            per_project[agent["project"]][agent["type"]] += 1
        credits += [(_minute(s), project, counts) for project, counts in per_project.items()]
    return credits


def build_intervals(kind, credits, cfg):
    t = cfg["thresholds"]
    merge_gap = timedelta(minutes=t["merge_gap_min"])
    min_length = timedelta(minutes=t["min_event_min"])
    by_bucket = defaultdict(lambda: defaultdict(list))
    for minute, bucket, detail in credits:
        by_bucket[bucket][minute].append(detail)
    intervals = []
    for bucket, minutes in by_bucket.items():
        groups = []
        for minute in sorted(minutes):
            if groups and minute - (groups[-1][-1] + ONE_MIN) < merge_gap:
                groups[-1].append(minute)
            else:
                groups.append([minute])
        for group in groups:
            start, end = group[0], group[-1] + ONE_MIN
            if end - start < min_length:
                continue
            details = [detail for minute in group for detail in minutes[minute]]
            intervals.append({"kind": kind, "project": bucket, "start": start, "end": end, "details": details})
    return sorted(intervals, key=lambda i: (i["start"], i["project"]))
```

- [ ] **Step 4: テストが通ることを確かめる**

Run: `/usr/bin/python3 -m unittest discover -s .bin/tests -p 'test_worklog_timeline.py' -v`
Expected: 17 tests, `OK`

- [ ] **Step 5: コミット（承認後）**

```bash
git add .bin/worklog/wl_timeline.py .bin/tests/test_worklog_timeline.py
git commit -m "feat: worklog の作業判定と区間化を追加する"
```

---

### Task 4: 予定の形と突き合わせ

**Files:**
- Create: `.bin/worklog/wl_calendar.py`
- Modify: `.bin/tests/worklog_fixtures.py`（末尾に `FakeGog` を追加）
- Test: `.bin/tests/test_worklog_calendar.py`

**Interfaces:**
- Consumes: 区間（Task 3 の `build_intervals` の戻り値）、`wl_timeline.OTHER`、設定 `cfg`
- Produces:
  - `wl_calendar.GogError`、`wl_calendar.AUTO_COLORS`
  - `wl_calendar.interval_key(interval) -> str`、`summary(interval) -> str`、`color(project, cfg) -> str`、`describe(interval) -> str`
  - `wl_calendar.plan_actions(intervals, ledger, window_start) -> list[(action, key, interval | None)]`
  - `wl_calendar.apply_actions(actions, ledger, gog, cfg) -> (dict, list[str])`
  - `wl_calendar.prune_ledger(ledger, before: datetime) -> dict`
  - `wl_calendar.Gog(account, calendar_id, runner=subprocess.run)`：`create(summary, start, end, description, color, key) -> str`、`update(event_id, end, description)`、`delete(event_id)`、`create_calendar(name, timezone) -> str`
  - `worklog_fixtures.FakeGog(fail_on=())`：`calls` に呼び出しを記録し、`fail_on` に含む操作名で `GogError` を投げる

- [ ] **Step 1: 偽の gog をテスト部品に足す**

`.bin/tests/worklog_fixtures.py` の末尾に追加：

```python


class FakeGog:
    """Records calls instead of talking to Google; fails on the named operations."""

    def __init__(self, fail_on=()):
        self.calls, self.fail_on, self.created = [], set(fail_on), 0

    def _record(self, name, *args):
        self.calls.append((name,) + args)
        if name in self.fail_on:
            from wl_calendar import GogError
            raise GogError(f"{name} failed")

    def create(self, summary, start, end, description, color, key):
        self._record("create", summary, start, end, description, color, key)
        self.created += 1
        return f"ev{self.created}"

    def update(self, event_id, end, description):
        self._record("update", event_id, end, description)

    def delete(self, event_id):
        self._record("delete", event_id)
```

- [ ] **Step 2: 失敗するテストを書く**

`.bin/tests/test_worklog_calendar.py`：

```python
"""wl_calendar: event shape, reconciliation with the ledger, gog command lines."""
import unittest
from collections import Counter
from types import SimpleNamespace

from worklog_fixtures import CFG, FakeGog, at

import wl_calendar
from wl_timeline import OTHER


def interval(kind="human", project="dotfiles2", start=0, end=10, details=None):
    return {"kind": kind, "project": project, "start": at(start), "end": at(end),
            "details": [] if details is None else details}


def ledger_entry(iv, event_id="ev1"):
    return {"id": event_id, "start": iv["start"].isoformat(), "end": iv["end"].isoformat(),
            "description": wl_calendar.describe(iv)}


class ShapeTest(unittest.TestCase):
    def test_summary(self):
        self.assertEqual(wl_calendar.summary(interval()), "人｜dotfiles2")
        self.assertEqual(wl_calendar.summary(interval(project=OTHER)), "人｜その他")
        self.assertEqual(wl_calendar.summary(interval(kind="agent", project="proj-b")), "AI｜proj-b")

    def test_color(self):
        self.assertEqual(wl_calendar.color("dotfiles2", CFG), "9")
        self.assertEqual(wl_calendar.color(OTHER, CFG), "8")
        auto = wl_calendar.color("proj-b", CFG)
        self.assertIn(auto, wl_calendar.AUTO_COLORS)
        self.assertEqual(auto, wl_calendar.color("proj-b", CFG))

    def test_describe_agent_peak_concurrency(self):
        iv = interval(kind="agent", details=[Counter(claude=1), Counter(claude=2, codex=1)])
        self.assertEqual(wl_calendar.describe(iv), "claude ×2, codex ×1")

    def test_describe_human_top_windows(self):
        iv = interval(details=["Chrome: paper", "Chrome: paper", None, "Preview: a.pdf"])
        self.assertEqual(wl_calendar.describe(iv), "Chrome: paper（2分）\nPreview: a.pdf（1分）")

    def test_key(self):
        self.assertEqual(wl_calendar.interval_key(interval()), "human|dotfiles2|2026-10-05T10:00:00+09:00")


class PlanTest(unittest.TestCase):
    window_start = at(-60)

    def test_new_interval_is_created(self):
        iv = interval()
        self.assertEqual(wl_calendar.plan_actions([iv], {}, self.window_start),
                         [("create", wl_calendar.interval_key(iv), iv)])

    def test_unchanged_interval_needs_nothing(self):
        iv = interval()
        ledger = {wl_calendar.interval_key(iv): ledger_entry(iv)}
        self.assertEqual(wl_calendar.plan_actions([iv], ledger, self.window_start), [])

    def test_longer_interval_is_updated(self):
        old, new = interval(end=10), interval(end=20)
        ledger = {wl_calendar.interval_key(old): ledger_entry(old)}
        self.assertEqual(wl_calendar.plan_actions([new], ledger, self.window_start),
                         [("update", wl_calendar.interval_key(new), new)])

    def test_vanished_interval_is_deleted(self):
        iv = interval()
        ledger = {wl_calendar.interval_key(iv): ledger_entry(iv)}
        self.assertEqual(wl_calendar.plan_actions([], ledger, self.window_start),
                         [("delete", wl_calendar.interval_key(iv), None)])

    def test_outside_window_is_left_alone(self):
        old = interval(start=-120, end=-110)
        ledger = {wl_calendar.interval_key(old): ledger_entry(old)}
        self.assertEqual(wl_calendar.plan_actions([old], {}, self.window_start), [])
        self.assertEqual(wl_calendar.plan_actions([], ledger, self.window_start), [])


class ApplyTest(unittest.TestCase):
    def test_create_records_event_id(self):
        iv = interval()
        key = wl_calendar.interval_key(iv)
        gog = FakeGog()
        ledger, errors = wl_calendar.apply_actions([("create", key, iv)], {}, gog, CFG)
        self.assertEqual(errors, [])
        self.assertEqual(ledger[key]["id"], "ev1")
        self.assertEqual(gog.calls[0], ("create", "人｜dotfiles2", iv["start"].isoformat(),
                                        iv["end"].isoformat(), "", "9", key))

    def test_failed_update_keeps_ledger_and_continues(self):
        old, other = interval(end=10), interval(project="proj-b")
        ledger = {wl_calendar.interval_key(old): ledger_entry(old)}
        actions = [("update", wl_calendar.interval_key(old), interval(end=20)),
                   ("create", wl_calendar.interval_key(other), other)]
        result, errors = wl_calendar.apply_actions(actions, ledger, FakeGog(fail_on={"update"}), CFG)
        self.assertEqual(result[wl_calendar.interval_key(old)], ledger[wl_calendar.interval_key(old)])
        self.assertIn(wl_calendar.interval_key(other), result)
        self.assertEqual(len(errors), 1)

    def test_delete_removes_entry_without_touching_input(self):
        iv = interval()
        key = wl_calendar.interval_key(iv)
        ledger = {key: ledger_entry(iv)}
        result, _ = wl_calendar.apply_actions([("delete", key, None)], ledger, FakeGog(), CFG)
        self.assertEqual(result, {})
        self.assertIn(key, ledger)

    def test_prune_ledger_by_start(self):
        old, new = interval(start=-100, end=-90), interval()
        ledger = {"old": ledger_entry(old), "new": ledger_entry(new)}
        self.assertEqual(list(wl_calendar.prune_ledger(ledger, at(-50))), ["new"])


class GogTest(unittest.TestCase):
    def make(self, stdout='{"id": "ev9"}', returncode=0):
        calls = []

        def runner(cmd, **kwargs):
            calls.append(cmd)
            return SimpleNamespace(returncode=returncode, stdout=stdout, stderr="boom")
        return wl_calendar.Gog("me@example.com", "cal@example.com", runner), calls

    def test_create_command_line(self):
        gog, calls = self.make()
        event_id = gog.create("人｜dotfiles2", "s", "e", "d", "9", "human|dotfiles2|s")
        self.assertEqual(event_id, "ev9")
        self.assertEqual(calls[0], [
            "gog", "calendar", "create", "cal@example.com", "--summary=人｜dotfiles2",
            "--from=s", "--to=e", "--description=d", "--event-color=9",
            "--private-prop=worklog_key=human|dotfiles2|s", "--transparency=transparent",
            "--account=me@example.com", "--json", "--no-input"])

    def test_nested_id_is_found(self):
        gog, _ = self.make(stdout='{"event": {"id": "ev7"}}')
        self.assertEqual(gog.create("t", "s", "e", "d", "1", "k"), "ev7")

    def test_missing_id_raises(self):
        gog, _ = self.make(stdout="{}")
        with self.assertRaises(wl_calendar.GogError):
            gog.create("t", "s", "e", "d", "1", "k")

    def test_nonzero_exit_raises(self):
        gog, _ = self.make(returncode=1)
        with self.assertRaisesRegex(wl_calendar.GogError, "boom"):
            gog.delete("ev1")

    def test_update_and_delete_command_lines(self):
        gog, calls = self.make(stdout="")
        gog.update("ev1", "e", "d")
        gog.delete("ev1")
        self.assertEqual(calls[0][:6], ["gog", "calendar", "update", "cal@example.com", "ev1", "--to=e"])
        self.assertEqual(calls[1][:6], ["gog", "calendar", "delete", "cal@example.com", "ev1", "--force"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: テストが失敗することを確かめる**

Run: `/usr/bin/python3 -m unittest discover -s .bin/tests -p 'test_worklog_calendar.py' -v`
Expected: `ModuleNotFoundError: No module named 'wl_calendar'`

- [ ] **Step 4: 実装を書く**

`.bin/worklog/wl_calendar.py`：

```python
"""Map intervals to calendar events and reconcile them through the gog CLI."""
import json
import subprocess
import zlib
from collections import Counter
from datetime import datetime

from wl_timeline import OTHER

OTHER_COLOR = "8"  # graphite
AUTO_COLORS = ("1", "2", "3", "4", "5", "6", "7", "9", "10", "11")
MAX_DETAIL_LINES = 5
GOG_TIMEOUT_SEC = 60


class GogError(Exception):
    pass


def interval_key(interval):
    return f"{interval['kind']}|{interval['project']}|{interval['start'].isoformat()}"


def summary(interval):
    who = "人" if interval["kind"] == "human" else "AI"
    return f"{who}｜{interval['project']}"


def color(project, cfg):
    if project == OTHER:
        return OTHER_COLOR
    configured = cfg["project_colors"].get(project)
    return configured or AUTO_COLORS[zlib.crc32(project.encode("utf-8")) % len(AUTO_COLORS)]


def describe(interval):
    if interval["kind"] == "agent":
        peak = Counter()
        for counts in interval["details"]:
            for agent_type, n in counts.items():
                peak[agent_type] = max(peak[agent_type], n)
        return ", ".join(f"{agent_type} ×{n}" for agent_type, n in sorted(peak.items()))
    windows = Counter(detail for detail in interval["details"] if detail)
    return "\n".join(f"{detail}（{n}分）" for detail, n in windows.most_common(MAX_DETAIL_LINES))


def plan_actions(intervals, ledger, window_start):
    wanted = {interval_key(i): i for i in intervals if i["start"] >= window_start}
    actions = []
    for key, interval in sorted(wanted.items()):
        record = ledger.get(key)
        if record is None:
            actions.append(("create", key, interval))
        elif (record["end"], record["description"]) != (interval["end"].isoformat(), describe(interval)):
            actions.append(("update", key, interval))
    for key, record in sorted(ledger.items()):
        if key not in wanted and datetime.fromisoformat(record["start"]) >= window_start:
            actions.append(("delete", key, None))
    return actions


def _record(event_id, interval):
    return {"id": event_id, "start": interval["start"].isoformat(),
            "end": interval["end"].isoformat(), "description": describe(interval)}


def apply_actions(actions, ledger, gog, cfg):
    """Return (new ledger, error messages). A failed action leaves its entry as it was."""
    result, errors = dict(ledger), []
    for action, key, interval in actions:
        try:
            if action == "create":
                event_id = gog.create(summary(interval), interval["start"].isoformat(),
                                      interval["end"].isoformat(), describe(interval),
                                      color(interval["project"], cfg), key)
                result[key] = _record(event_id, interval)
            elif action == "update":
                gog.update(ledger[key]["id"], interval["end"].isoformat(), describe(interval))
                result[key] = _record(ledger[key]["id"], interval)
            else:
                gog.delete(ledger[key]["id"])
                result = {k: v for k, v in result.items() if k != key}
        except GogError as exc:
            errors.append(f"{action} {key}: {exc}")
    return result, errors


def prune_ledger(ledger, before):
    return {k: v for k, v in ledger.items() if datetime.fromisoformat(v["start"]) >= before}


def _find_id(payload, nested):
    for candidate in (payload, payload.get(nested)):
        if isinstance(candidate, dict) and candidate.get("id"):
            return candidate["id"]
    raise GogError(f"no id in gog output (keys: {sorted(payload)})")


class Gog:
    def __init__(self, account, calendar_id, runner=subprocess.run):
        self.account, self.calendar_id, self.runner = account, calendar_id, runner

    def _call(self, *args):
        cmd = ["gog", "calendar", *args, f"--account={self.account}", "--json", "--no-input"]
        result = self.runner(cmd, capture_output=True, text=True, timeout=GOG_TIMEOUT_SEC, check=False)
        if result.returncode != 0:
            raise GogError(f"{args[0]}: {(result.stderr or result.stdout).strip()}")
        return json.loads(result.stdout) if result.stdout.strip() else {}

    def create(self, summary, start, end, description, color, key):
        payload = self._call("create", self.calendar_id, f"--summary={summary}", f"--from={start}",
                             f"--to={end}", f"--description={description}", f"--event-color={color}",
                             f"--private-prop=worklog_key={key}", "--transparency=transparent")
        return _find_id(payload, "event")

    def update(self, event_id, end, description):
        self._call("update", self.calendar_id, event_id, f"--to={end}", f"--description={description}")

    def delete(self, event_id):
        self._call("delete", self.calendar_id, event_id, "--force")

    def create_calendar(self, name, timezone):
        return _find_id(self._call("create-calendar", name, f"--timezone={timezone}"), "calendar")
```

- [ ] **Step 5: テストが通ることを確かめる**

Run: `/usr/bin/python3 -m unittest discover -s .bin/tests -p 'test_worklog_calendar.py' -v`
Expected: 19 tests, `OK`

- [ ] **Step 6: コミット（承認後）**

```bash
git add .bin/worklog/wl_calendar.py .bin/tests/worklog_fixtures.py .bin/tests/test_worklog_calendar.py
git commit -m "feat: worklog の予定の突き合わせと gog 連携を追加する"
```

---

### Task 5: 入口、launchd 登録、Makefile

**Files:**
- Create: `.bin/worklog/worklog.py`
- Create: `.bin/worklog/install.sh`
- Create: `.bin/worklog/launchd/local.worklog.sample.plist.template`
- Create: `.bin/worklog/launchd/local.worklog.sync.plist.template`
- Modify: `Makefile`（末尾に3つの目標を追加）
- Test: `.bin/tests/test_worklog_cli.py`

**Interfaces:**
- Consumes: Task 1〜4 のすべての公開関数
- Produces:
  - `worklog.cmd_sample(now, state_dir=wl_store.STATE_DIR, runner=wl_probe.run) -> None`
  - `worklog.cmd_sync(now, cfg, gog, state_dir=wl_store.STATE_DIR) -> int`（実行した操作の数）
  - `worklog.cmd_init_calendar(now, cfg, gog) -> str`（作成したカレンダー ID）
  - `worklog.main(argv=None) -> int`

- [ ] **Step 1: 失敗するテストを書く**

`.bin/tests/test_worklog_cli.py`：

```python
"""worklog.py: sample and sync end to end with a fake calendar."""
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from worklog_fixtures import CFG, WORKLOG_DIR, FakeGog, at, sample, stored

import wl_store

spec = importlib.util.spec_from_file_location("worklog", WORKLOG_DIR / "worklog.py")
worklog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worklog)


class SyncTest(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        agents = [{"project": "proj-b", "type": "codex"}]
        for m in range(10):
            wl_store.append_sample(stored(sample(m, agents=agents)), self.dir)

    def test_first_sync_creates_human_and_agent_events(self):
        gog = FakeGog()
        self.assertEqual(worklog.cmd_sync(at(30), CFG, gog, self.dir), 2)
        self.assertEqual(sorted(call[1] for call in gog.calls), ["AI｜proj-b", "人｜dotfiles2"])
        self.assertEqual(len(wl_store.load_ledger(self.dir)), 2)

    def test_second_sync_changes_nothing(self):
        worklog.cmd_sync(at(30), CFG, FakeGog(), self.dir)
        gog = FakeGog()
        self.assertEqual(worklog.cmd_sync(at(45), CFG, gog, self.dir), 0)
        self.assertEqual(gog.calls, [])

    def test_failures_go_to_error_log(self):
        worklog.cmd_sync(at(30), CFG, FakeGog(fail_on={"create"}), self.dir)
        self.assertEqual(wl_store.load_ledger(self.dir), {})
        log = (self.dir / "errors.log").read_text(encoding="utf-8")
        self.assertEqual(log.count("create failed"), 2)

    def test_sample_appends_one_line(self):
        with mock.patch.object(worklog.wl_probe, "collect_sample", return_value=stored(sample(10))):
            worklog.cmd_sample(at(10), self.dir)
        loaded, _ = wl_store.load_samples(at(-1), self.dir)
        self.assertEqual(len(loaded), 11)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: テストが失敗することを確かめる**

Run: `/usr/bin/python3 -m unittest discover -s .bin/tests -p 'test_worklog_cli.py' -v`
Expected: `FileNotFoundError`（`worklog.py` がまだない）

- [ ] **Step 3: 入口を書く**

`.bin/worklog/worklog.py`：

```python
#!/usr/bin/env python3
"""Record human and agent working time to Google Calendar.

Design: docs/superpowers/specs/2026-10-04-worklog-calendar-design.md
"""
import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import wl_calendar  # noqa: E402
import wl_config  # noqa: E402
import wl_probe  # noqa: E402
import wl_store  # noqa: E402
import wl_timeline  # noqa: E402

# Read a little before the window so intervals that start inside it are never truncated.
LOOKBACK_MARGIN = timedelta(hours=2)


def cmd_sample(now, state_dir=wl_store.STATE_DIR, runner=wl_probe.run):
    wl_store.append_sample(wl_probe.collect_sample(now, runner), state_dir)


def cmd_sync(now, cfg, gog, state_dir=wl_store.STATE_DIR):
    t = cfg["thresholds"]
    window_start = now - timedelta(hours=t["window_hours"])
    samples, broken = wl_store.load_samples(window_start - LOOKBACK_MARGIN, state_dir)
    intervals = (wl_timeline.build_intervals("human", wl_timeline.human_minutes(samples, cfg), cfg)
                 + wl_timeline.build_intervals("agent", wl_timeline.agent_minutes(samples), cfg))
    ledger = wl_store.load_ledger(state_dir)
    actions = wl_calendar.plan_actions(intervals, ledger, window_start)
    ledger, failed = wl_calendar.apply_actions(actions, ledger, gog, cfg)
    retention = timedelta(days=t["retention_days"])
    wl_store.save_ledger(wl_calendar.prune_ledger(ledger, now - retention), state_dir)
    wl_store.prune_samples((now - retention).date(), state_dir)
    for message in broken + failed:
        wl_store.log_error(message, now, state_dir)
    print(f"{now.isoformat(timespec='seconds')} sync: {len(actions)} actions, {len(failed)} failed")
    return len(actions)


def cmd_init_calendar(now, cfg, gog):
    if cfg["calendar_id"]:
        raise wl_config.ConfigError(f"calendar_id is already set in {wl_config.LOCAL_CONFIG}")
    calendar_id = gog.create_calendar(cfg["calendar_name"], cfg["timezone"])
    print(f"created {cfg['calendar_name']!r}: {calendar_id}")
    print(f'add "calendar_id": "{calendar_id}" to {wl_config.LOCAL_CONFIG}')
    return calendar_id


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=["sample", "sync", "init-calendar"])
    command = parser.parse_args(argv).command
    now = datetime.now().astimezone()
    try:
        if command == "sample":
            cmd_sample(now)
            return 0
        cfg = wl_config.load_config()
        if command == "sync":
            wl_config.require(cfg, "account", "calendar_id")
            cmd_sync(now, cfg, wl_calendar.Gog(cfg["account"], cfg["calendar_id"]))
        else:
            wl_config.require(cfg, "account")
            cmd_init_calendar(now, cfg, wl_calendar.Gog(cfg["account"], ""))
    except Exception as exc:
        # launchd has no terminal: leave a trace in errors.log, then fail loudly.
        wl_store.log_error(f"{command}: {exc!r}", now)
        raise
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: テストが通ることを確かめる**

Run: `/usr/bin/python3 -m unittest discover -s .bin/tests -p 'test_worklog_cli.py' -v`
Expected: 4 tests, `OK`

- [ ] **Step 5: launchd のひな形と登録スクリプトを書く**

`.bin/worklog/launchd/local.worklog.sample.plist.template`：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>local.worklog.sample</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/python3</string>
    <string>__WORKLOG__/worklog.py</string>
    <string>sample</string>
  </array>
  <key>StartInterval</key>
  <integer>60</integer>
  <key>RunAtLoad</key>
  <true/>
  <key>ProcessType</key>
  <string>Background</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key>
    <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
  </dict>
  <key>StandardOutPath</key>
  <string>__HOME__/.local/state/worklog/launchd-sample.log</string>
  <key>StandardErrorPath</key>
  <string>__HOME__/.local/state/worklog/launchd-sample.log</string>
</dict>
</plist>
```

`.bin/worklog/launchd/local.worklog.sync.plist.template`：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>local.worklog.sync</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/python3</string>
    <string>__WORKLOG__/worklog.py</string>
    <string>sync</string>
  </array>
  <key>StartInterval</key>
  <integer>900</integer>
  <key>RunAtLoad</key>
  <true/>
  <key>ProcessType</key>
  <string>Background</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key>
    <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
  </dict>
  <key>StandardOutPath</key>
  <string>__HOME__/.local/state/worklog/launchd-sync.log</string>
  <key>StandardErrorPath</key>
  <string>__HOME__/.local/state/worklog/launchd-sync.log</string>
</dict>
</plist>
```

`.bin/worklog/install.sh`：

```zsh
#!/bin/zsh
# launchd に worklog の観測（毎分）と書き込み（15分ごと）を登録・解除する。
# パスはひな形に直接書かず、ここでその PC の値を埋め込む。
set -euo pipefail

WORKLOG_DIR="$(cd "$(dirname "$0")" && pwd)"
AGENTS_DIR="$HOME/Library/LaunchAgents"
STATE_DIR="$HOME/.local/state/worklog"
LABELS=(local.worklog.sample local.worklog.sync)
DOMAIN="gui/$(id -u)"

case "${1:-}" in
  install)
    mkdir -p "$AGENTS_DIR" "$STATE_DIR"
    for label in $LABELS; do
      dest="$AGENTS_DIR/$label.plist"
      # 再登録に備えて外す。未登録なら失敗するので結果は見ない。
      launchctl bootout "$DOMAIN/$label" 2>/dev/null || true
      sed -e "s|__HOME__|$HOME|g" -e "s|__WORKLOG__|$WORKLOG_DIR|g" \
        "$WORKLOG_DIR/launchd/$label.plist.template" > "$dest"
      plutil -lint "$dest"
      launchctl bootstrap "$DOMAIN" "$dest"
      echo "installed: $label"
    done
    ;;
  uninstall)
    for label in $LABELS; do
      launchctl bootout "$DOMAIN/$label" 2>/dev/null || true
      rm -f "$AGENTS_DIR/$label.plist"
      echo "removed: $label"
    done
    ;;
  *)
    echo "usage: $0 install|uninstall" >&2
    exit 2
    ;;
esac
```

Run: `chmod +x .bin/worklog/install.sh .bin/worklog/worklog.py`

- [ ] **Step 6: Makefile に目標を足す**

`Makefile` の末尾に追加する（レシピの行頭はタブ文字にする）：

```make

# Record human/agent working time to Google Calendar (see .bin/worklog)
.PHONY: worklog-install worklog-uninstall test-worklog
worklog-install:
	@.bin/worklog/install.sh install

worklog-uninstall:
	@.bin/worklog/install.sh uninstall

test-worklog:
	@/usr/bin/python3 -m unittest discover -s .bin/tests -p 'test_worklog_*.py' -v
```

- [ ] **Step 7: 全テストと手動の観測を確かめる**

Run: `make test-worklog`
Expected: 60 tests, `OK`

Run: `/usr/bin/python3 .bin/worklog/worklog.py sample && tail -1 ~/.local/state/worklog/samples-$(date +%F).jsonl`
Expected: 今の時刻の観測が1行表示される。

Run: `/usr/bin/python3 .bin/worklog/worklog.py sync; echo "exit=$?"; tail -1 ~/.local/state/worklog/errors.log`
Expected: `local.json` がまだないので `ConfigError`（`set account, calendar_id in ...`）で終了し、`exit=1`。エラーログにも同じ内容が1行残る。

- [ ] **Step 8: コミット（承認後）**

```bash
git add .bin/worklog/worklog.py .bin/worklog/install.sh .bin/worklog/launchd Makefile .bin/tests/test_worklog_cli.py
git commit -m "feat: worklog の入口と launchd 登録を追加する"
```

---

### Task 6: 実機での接続と確認（ユーザーの操作を含む）

**Files:**
- Create（git の外）: `~/.config/worklog/local.json`
- Modify（形が違った場合のみ）: `.bin/worklog/wl_calendar.py`、`.bin/worklog/wl_probe.py` と対応するテスト

**Interfaces:**
- Consumes: Task 5 の `worklog.py`、`install.sh`
- Produces: 稼働中の launchd ジョブ2つと、カレンダー上の予定

- [ ] **Step 1: gog の Google 認証（ユーザーが実行）**

この Mac の gog は未設定（`gog auth list` が `No tokens stored`、`config_exists false`）。ユーザーに次の実行を依頼する。ブラウザでの Google ログインを伴う。

```text
! gog auth setup
! gog auth add <Google アカウント> --services calendar
```

確認：`gog auth list` に対象アカウントが表示される。

- [ ] **Step 2: 個人設定を書く**

`~/.config/worklog/local.json`（git の外。アカウントはユーザーに確認して書く）：

```json
{
  "account": "<Step 1 のアカウント>",
  "project_colors": {}
}
```

- [ ] **Step 3: 専用カレンダーを作る**

Run: `/usr/bin/python3 .bin/worklog/worklog.py init-calendar`
Expected: `created '作業ログ': <カレンダー ID>` と表示される。表示された ID を `local.json` の `calendar_id` に書く。

`no id in gog output` で失敗した場合は、カレンダー自体は作られている。`gog calendar calendars --account=<アカウント> --json` で「作業ログ」の ID を確かめて `local.json` に書き、出力の形に合わせて `create_calendar` の `_find_id` の第2引数を直し、`GogTest` に実際の形のテストを1つ足す。

- [ ] **Step 4: 観測と書き込みを登録し、10分ほど溜める**

Run: `make worklog-install`
Expected: `installed: local.worklog.sample`、`installed: local.worklog.sync`

Run: `launchctl print gui/$(id -u)/local.worklog.sample | grep -E 'state|last exit'`
Expected: `last exit code = 0`

10分後、Run: `wc -l ~/.local/state/worklog/samples-$(date +%F).jsonl`
Expected: 登録後の分数とほぼ同じ行数（手動で動かした分を含む）。

- [ ] **Step 5: 書き込みを手動で1回動かし、予定の形を確かめる**

Run: `/usr/bin/python3 .bin/worklog/worklog.py sync`
Expected: `sync: N actions, 0 failed`（N は 1 以上）

`errors.log` に `no id in gog output` が出た場合は、予定自体は作られている。Google カレンダーで重複した予定を消し、`gog calendar create` の出力の形に合わせて `create` の `_find_id` の第2引数を直し、テストを足してから再実行する。

Google カレンダーで「作業ログ」を開き、次を目で確かめる。
- `人｜<Orca で選んでいるプロジェクト>` の予定が、登録してからの作業時間に合っている
- 別プロジェクトでエージェントを動かしていれば、`AI｜<プロジェクト>` が横に並んでいる
- 予定が「予定なし」として表示される

- [ ] **Step 6: 前面ウィンドウの判定を確かめる**

Chrome で2つのウィンドウを開き、片方ずつ前面にして1分以上待つ。観測ログの `window_title` が、そのとき前面にあったウィンドウの題名になっているかを `tail -3 ~/.local/state/worklog/samples-$(date +%F).jsonl` で確かめる。合っていなければ `parse_window_title` の選び方（`index` の向き）を直し、テストを実際の並びに合わせる。

- [ ] **Step 7: 1日動かして見比べる**

翌日、前日の予定と実際の作業を見比べる。特に、文書を読んでいた時間が抜けていないか、離席が作業になっていないかを確かめる。ずれていれば `config.json` の `reading_max_min`・`grace_min` を調整する。観測ログは残っているので、調整後の `sync` で直近 48 時間の予定が組み直される。

- [ ] **Step 8: コミット（Step 3・5・6 でコードを直した場合のみ、承認後）**

```bash
git add .bin/worklog/wl_calendar.py .bin/worklog/wl_probe.py .bin/tests/test_worklog_calendar.py .bin/tests/test_worklog_probe.py
git commit -m "fix: worklog を実機の gog と Orca の出力に合わせる"
```
