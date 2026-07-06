# settings.json 所有モデル

Claude Code の `settings.json` は git・orca・Claude Code の3者が関わるため、扱いを固定する。

## 3層

| 層 | キー | 所有者 | git 追跡 |
|----|------|--------|:---:|
| ① orca 注入 | hooks の `.orca/` 参照（7イベント）+ StopFailure | orca が起動時に注入 | ✕ |
| ② 個人・可変 | `model`・`agentPushNotifEnabled`・`inputNeededNotifEnabled` | Claude Code がセッションで書く | ✕ |
| ③ 恒久・意図 | `enabledPlugins`・`extraKnownMarketplaces`・非 orca hooks・`permissions`・`effortLevel` | 人が意図して決める | ○ git が正 |

## 鉄則

- **settings.json は決して symlink しない**。Claude Code も orca もアトミック書き込み（temp+rename）を使い、`rename()` がリンクを実ファイルへ置換するため、リンクは持続せず乖離する。
- `~/.claude/settings.json` は**ライブの実ファイル**（git 実体 `dotdir/.claude/settings.json` は種）。
- `make link` は settings.json を **seed-if-absent / preserve-if-present** で扱う（`link.sh` の `PRESERVE_FILES`）。既存は絶対に上書きしない。

## 恒久変更を git に取り込む

`/config` やプラグイン有効化で③の恒久変更をしたら：

    make settings-pull                # 差分を見て確認して dotdir へ書き込み（対話）
    .bin/settings-pull.sh --dry-run   # 確認のみ

`settings-pull` は orca hooks と②（model・通知・effortLevel）を自動除外する。書き込み後は `git diff` を確認してコミット。誤りは `git checkout dotdir/.claude/settings.json` で戻せる。

## 既知の制限

- `settings-pull` は追加・変更を吸い上げるが、稼働側で**キーごと削除**した変更は git に伝播しない（merge であってミラーではない）。削除を反映したい時は dotdir を直接編集する。
