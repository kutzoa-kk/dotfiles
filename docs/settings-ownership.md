# settings.json 所有モデル

Claude Code の `settings.json` は git・orca・Claude Code の3者が関わるため、扱いを固定する。

## 3層

| 層 | キー | 所有者 | git 追跡 |
|----|------|--------|:---:|
| ① orca 注入 | hooks の `.orca/` 参照（7イベント）+ StopFailure | orca が起動時に注入 | ✕ |
| ② 個人・可変 | `model`・`agentPushNotifEnabled`・`inputNeededNotifEnabled`・`autoMode`（`/auto-mode-setup` が書くマシンごとの自動モード設定） | Claude Code が書く | ✕ |
| ③ 恒久・意図 | `enabledPlugins`・`extraKnownMarketplaces`・非 orca hooks・`permissions`・`effortLevel`・`modelSettings`・`advisorModel` | 人が意図して決める | ○ git が正 |

## 鉄則

- **settings.json は決して symlink しない**。Claude Code も orca もアトミック書き込み（temp+rename）を使い、`rename()` がリンクを実ファイルへ置換するため、リンクは持続せず乖離する。
- `~/.claude/settings.json` は**ライブの実ファイル**（git 実体 `dotdir/.claude/settings.json` は種）。
- `make link` は settings.json を **seed-if-absent / preserve-if-present** で扱う（`link.sh` の `PRESERVE_FILES`）。既存は絶対に上書きしない。

## 恒久変更を git に取り込む

`/config` やプラグイン有効化で③の恒久変更をしたら：

    make settings-pull                # 差分を見て確認して dotdir へ書き込み（対話）
    .bin/settings-pull.sh --dry-run   # 確認のみ

`settings-pull` は orca hooks と②（model・通知・autoMode）を自動除外する。トップレベルの `effortLevel` はセッション中の切り替えが逆流しないよう git の値を保持する。モデルごとの effort（`/effort` が書く `modelSettings`）と `advisorModel`（`/advisor` が書く）は既定値の保存なので吸い上げる。書き込み後は `git diff` を確認してコミット。誤りは `git checkout dotdir/.claude/settings.json` で戻せる。

## 別のマシンのプラグインの増減を反映する

`git pull` のあと：

    make plugins-sync                        # やることを見て確認して反映（対話）
    python3 .bin/plugins-sync.py --dry-run   # 確認のみ

git 側の `enabledPlugins` と `extraKnownMarketplaces` を基準に、足りない取得元の追加、プラグインの導入、有効・無効の切り替え、取得元の `autoUpdate` の設定を `claude plugin` で行う。削除はせず、このマシンにだけあるものは表示するだけ。プラグイン一覧から入れたもの（`@anthropic-plugin-directory`）は名前だけで導入する。反映後は Claude Code を再起動する。`--yes` は確認を省くだけでなく、取得元が導入時に実行を宣言している命令も確認なしで受け入れる（`claude plugin install -y`）ため、ふだんは対話で使う。

Claude Code は、settings.json に書かれた取得元がまだ無いときだけ、起動後にそれを追加して有効なプラグインを取得する。取得元が既にあるマシンで新しく有効にしたプラグインは取得されず `not cached` になると読めるため、この手順で明示的に入れる（出典：<https://code.claude.com/docs/en/plugins/loading.md> の「Plugins and marketplaces that aren't on disk at session start」、2026-10-27 確認）。

## 既知の制限

- `settings-pull` は git を土台に、稼働側の値でトップレベルのキーを丸ごと置き換える。そのため `enabledPlugins` の1件のようなキーの中の項目の削除は git に伝わる（2026-10-26 のプラグイン整理で確認）。稼働側で**トップレベルのキーそのもの**（`permissions` など）を消した変更は伝わらず、git の値が残る。これを反映したい時は dotdir を直接編集する。
- 逆向きも伝播しない。dotdir だけを編集しても、既存マシンの稼働側は preserve-if-present のため変わらない（2026-07-06 のプラグイン無効化が稼働側に届かず、2026-09-26 まで有効のまま残った）。プラグインと取得元は `make plugins-sync` で反映する。それ以外の③を変える時は稼働側と dotdir の両方を編集する。
