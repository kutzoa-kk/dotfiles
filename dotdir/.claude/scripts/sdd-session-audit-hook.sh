#!/bin/bash
# SDD Session Audit Hook (Stop)
# セッション終了時に experiment_audit.py を実行し、macOS 通知で結果表示
# Stop hook のためブロック不可。常に exit 0。

# --- SDD プロジェクト判定 ---
if [ ! -f "docs/specs/00_HYPOTHESES.md" ]; then
  exit 0
fi

# --- experiment_audit.py のパス解決 ---
AUDIT_SCRIPT="$HOME/.claude/skills/sdd-experiment-audit/scripts/experiment_audit.py"
if [ ! -f "$AUDIT_SCRIPT" ]; then
  exit 0
fi

# --- experiment_audit.py 実行（タイムアウト 10 秒） ---
audit_output=$(timeout 10 python3 "$AUDIT_SCRIPT" --project-dir "$PWD" --backend local 2>&1) || {
  exit_code=$?
  if [ $exit_code -eq 124 ]; then
    # タイムアウト
    osascript -e 'display notification "Audit がタイムアウトしました (10s)" with title "SDD Session Audit" sound name "Basso"' 2>/dev/null || true
    exit 0
  fi

  # チェック失敗 — 警告通知
  # 出力から要約行を抽出
  summary=$(echo "$audit_output" | tail -5 | head -3)
  osascript -e "display notification \"$summary\" with title \"SDD Audit: 要確認\" sound name \"Basso\"" 2>/dev/null || true
  exit 0
}

# 全チェック通過
osascript -e 'display notification "全チェック通過" with title "SDD Audit: OK" sound name "Glass"' 2>/dev/null || true
exit 0
