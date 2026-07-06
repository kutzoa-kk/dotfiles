#!/bin/bash
# Claude 環境の月次監査 — env-audit Workflow をヘッドレス実行し docs/reports/ へ保存する
# launchd (com.kkmclab.claude-env-audit) から毎月1日 9:17 に起動される。手動実行も可。
# 導入手順:
#   cp .bin/com.kkmclab.claude-env-audit.plist ~/Library/LaunchAgents/
#   launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.kkmclab.claude-env-audit.plist
set -euo pipefail

REPO="$HOME/dotfiles"
DATE="$(date +%Y-%m-%d)"
OUT="docs/reports/env-audit-${DATE}.md"
LOG="/tmp/claude-env-audit-${DATE}.log"
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
# GateGuard(ecc) は無人実行では対話応答できないため、公式案内の変数で当スクリプトに限り外す
# （env-audit は読み取り専用監査 + レポート1ファイル保存のみ）
export ECC_DISABLED_HOOKS="pre:bash:gateguard-fact-force,pre:edit-write:gateguard-fact-force"

cd "$REPO"
claude -p "Workflow ツールで名前 'env-audit'、args: { \"date\": \"${DATE}\" } を実行し、返り値の findings を重大度順の日本語 Markdown レポートに整形して ${OUT} に保存してください。保存後、所見の総数と severity 内訳を1行で出力して終了。" \
  --model sonnet \
  --allowedTools "Workflow" "Read" "Write" "Glob" "Grep" "Bash" \
  >"$LOG" 2>&1

# レポートが生成されたことを確認（無ければ非0終了で launchd 側のログに残る）
test -s "$REPO/$OUT"
echo "env-audit ${DATE}: OK -> $OUT"
