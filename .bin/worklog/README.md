# worklog

人が作業していた時間と、AI エージェント（Claude Code・Codex）が動いていた時間を、Google カレンダーの専用カレンダー「作業ログ（人）」と「作業ログ（AI）」に分けて記録する。AI の予定名は Claude Code のタスク名になる。1分ごとに画面の状態を観測し、15分ごとに予定を作成・延長する。仕組みと判定規則は [設計書](../../docs/superpowers/specs/2026-10-04-worklog-calendar-design.md) を参照。

## 別の PC で使い始める手順

カレンダーは最初の PC で作成済みなので、2台目以降の PC では作らずに同じものを使う。

### 1. 前提をそろえる

dotfiles をクローンして `make link` と `make brew` まで済ませる（gog は `.Brewfile` の `gogcli` で入る）。Orca は `.Brewfile` に入っていないので、`brew install --cask orca` で入れて起動したままにする。プロジェクトの作業時間は、Orca で選んでいるプロジェクトから判定するためである。

### 2. gog に Google の認証を登録する

最初の PC で使った OAuth クライアントの JSON ファイル（Google Cloud の「mac-orca」アプリの「クライアント」からダウンロードしたもの）をこの PC にコピーし、gog に読み込ませてからログインする。

```bash
gog auth credentials <ダウンロードした JSON ファイルのパス>
gog auth add <Google アカウント> --services calendar
gog auth doctor --check
```

最後のコマンドが `status ok` で終われば認証は済んでいる。OAuth アプリの公開ステータスが「テスト中」だと、ログインが7日ごとに切れる。Google Cloud の「Google Auth Platform」→「対象」で「本番環境」になっていることを確かめておく。

### 3. 個人設定ファイルを作る

アカウントとカレンダー ID は公開リポジトリに入れないため、PC ごとに `~/.config/worklog/local.json` を作る（フォルダは `mkdir -m 700 -p ~/.config/worklog` で、自分だけが開けるように作る）。カレンダー ID は、次のコマンドの出力から「作業ログ（人）」と「作業ログ（AI）」の行を探して確かめる。

```bash
gog calendar calendars --account=<Google アカウント>
```

```json
{
  "account": "me@example.com",
  "calendar_id": "xxxxxxxx@group.calendar.google.com",
  "agent_calendar_id": "yyyyyyyy@group.calendar.google.com",
  "project_colors": {}
}
```

`project_colors` には、予定の色をプロジェクトごとに `"dotfiles2": "9"` の形で書ける（1〜11。8 は「その他」用）。書かなければ名前から自動で決まる。`calendar_id` には人の、`agent_calendar_id` には AI のカレンダーの ID を書く。`worklog.py init-calendar` は ID が未設定のカレンダーを新しく作るコマンドなので、2台目以降では実行しない。

### 4. launchd に登録する

```bash
make worklog-install
launchctl print gui/$(id -u)/local.worklog.sample | grep 'last exit code'
```

`last exit code = 0` なら観測が動いている。15分ほど作業してから、書き込みの結果とエラーを確かめる。

```bash
tail -3 ~/.local/state/worklog/launchd-sync.log
tail -3 ~/.local/state/worklog/errors.log
```

`sync: N actions, 0 failed` が出ていて、2つのカレンダーに予定が入っていれば完了。

## 日々の扱い

作業の分類（どのアプリをプロジェクト作業・その他に数えるか）、除外するウィンドウ名、判定のしきい値は `config.json` で変える。変更すると次の書き込みで直近48時間の予定が組み直される。

観測ログ・予定の控え・エラーログは `~/.local/state/worklog/` にあり、観測ログは30日で消える。止めたいときは `make worklog-uninstall` で launchd から外す。テストは `make test-worklog` で実行する。

ログインが切れると、`errors.log` に gog のエラーが残り、予定の書き込みが止まる。`gog auth add <Google アカウント> --services calendar` でログインし直せば、直近48時間の分はまとめて書き込まれる。
