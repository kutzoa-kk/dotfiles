#!/bin/bash
# SDD Pre-Train Hook (PreToolUse → Bash)
# python.*train コマンドを検出し、pre_train_guard.py でチェック
# exit 0 = 許可, exit 2 = ブロック

set -euo pipefail

# --- JSON 入力の読み取り ---
input=$(cat)
tool_name=$(echo "$input" | jq -r '.tool_name' 2>/dev/null || echo "")
command=$(echo "$input" | jq -r '.tool_input.command' 2>/dev/null || echo "")

# Bash 以外は無視
if [ "$tool_name" != "Bash" ]; then
  exit 0
fi

# python.*train パターンにマッチしなければスキップ
if ! echo "$command" | grep -qE 'python[23]?\s+.*train'; then
  exit 0
fi

# --- SDD プロジェクト判定 ---
if [ ! -f "docs/specs/00_HYPOTHESES.md" ]; then
  exit 0
fi

# --- pre_train_guard.py のパス解決 ---
GUARD_SCRIPT="$HOME/.claude/skills/sdd-pre-train-guard/scripts/pre_train_guard.py"
if [ ! -f "$GUARD_SCRIPT" ]; then
  echo "[SDD Hook] WARNING: pre_train_guard.py が見つかりません: $GUARD_SCRIPT" >&2
  exit 0
fi

# --- training script の自動検出 ---
# コマンドから python <script> を抽出
training_script=$(echo "$command" | grep -oE 'python[23]?\s+[^ ]+' | head -1 | sed 's/python[23]*\s*//')

GUARD_ARGS=(--project-dir "$PWD")
if [ -n "$training_script" ] && [ -f "$training_script" ]; then
  GUARD_ARGS+=(--training-script "$training_script")
fi

# --- pre_train_guard.py 実行 ---
guard_output=$(python3 "$GUARD_SCRIPT" "${GUARD_ARGS[@]}" 2>&1) || {
  exit_code=$?
  if [ $exit_code -eq 1 ]; then
    cat >&2 <<EOF
[SDD Hook] 学習前チェックが失敗しました。
以下の問題を修正してから再実行してください:

$guard_output
EOF
    exit 2
  fi
  # その他のエラー（スクリプト自体の問題）は警告のみ
  echo "[SDD Hook] WARNING: pre_train_guard.py が異常終了しました (exit $exit_code)" >&2
  exit 0
}

# チェック通過
exit 0
