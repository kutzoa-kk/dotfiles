#!/bin/bash
# SDD Spec Drift Hook (PostToolUse → Write/Edit/MultiEdit)
# docs/specs/*.md の変更を検出し、deviation_checker.py で警告
# PostToolUse のためブロック不可。警告のみ。

set -euo pipefail

# --- JSON 入力の読み取り ---
input=$(cat)
tool_name=$(echo "$input" | jq -r '.tool_name' 2>/dev/null || echo "")

# Write/Edit/MultiEdit 以外は無視
case "$tool_name" in
  Write|Edit|MultiEdit) ;;
  *) exit 0 ;;
esac

# --- file_path の抽出 ---
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty' 2>/dev/null || echo "")
if [ -z "$file_path" ]; then
  exit 0
fi

# docs/specs/ 配下の .md ファイルでなければスキップ
case "$file_path" in
  */docs/specs/*.md) ;;
  *) exit 0 ;;
esac

# --- SDD プロジェクト判定 ---
# file_path から project root を推定（docs/specs/ の親ディレクトリ）
project_root="${file_path%/docs/specs/*}"
if [ ! -f "${project_root}/docs/specs/00_HYPOTHESES.md" ]; then
  exit 0
fi

# --- deviation_checker.py のパス解決 ---
CHECKER_SCRIPT="$HOME/.claude/skills/sdd-experiment-audit/scripts/deviation_checker.py"
if [ ! -f "$CHECKER_SCRIPT" ]; then
  echo "[SDD Hook] WARNING: deviation_checker.py が見つかりません: $CHECKER_SCRIPT" >&2
  exit 0
fi

# --- deviation_checker.py 実行 ---
checker_output=$(python3 "$CHECKER_SCRIPT" --project-dir "$project_root" 2>&1) || {
  filename=$(basename "$file_path")
  cat >&2 <<EOF
[SDD Hook] Spec 変更検出: $filename
Deviation Log に未記録の変更がある可能性があります。

$checker_output

docs/specs/00_HYPOTHESES.md の Deviation Log セクションに
変更内容を記録してください。
EOF
  exit 0
}

exit 0
