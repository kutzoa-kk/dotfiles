#!/bin/bash
# SDD Holdout Hook (PreToolUse → Bash)
# holdout 関連引数を検出し、gate condition 達成をチェック
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

# holdout 関連引数がなければスキップ
if ! echo "$command" | grep -qE '\-\-holdout|\-\-phase[= ]holdout|holdout[= ]true|holdout[= ]True'; then
  exit 0
fi

# --- SDD プロジェクト判定 ---
if [ ! -f "docs/specs/00_HYPOTHESES.md" ]; then
  exit 0
fi

METRICS_FILE="docs/specs/02_METRICS.md"
RUNS_DIR="data/processed/runs"

# --- Gate condition の確認 ---
# 02_METRICS.md から gate condition を抽出
if [ ! -f "$METRICS_FILE" ]; then
  echo "[SDD Hook] INFO: 02_METRICS.md が見つかりません。holdout を許可します。" >&2
  exit 0
fi

# gate / Gate / GATE を含む行からメトリクス閾値を抽出
gate_lines=$(grep -iE 'gate|threshold' "$METRICS_FILE" 2>/dev/null || echo "")
if [ -z "$gate_lines" ]; then
  echo "[SDD Hook] INFO: gate condition が定義されていません。holdout を許可します。" >&2
  exit 0
fi

# --- CV 結果の確認 ---
if [ ! -d "$RUNS_DIR" ]; then
  cat >&2 <<EOF
[SDD Hook] holdout 実行がブロックされました。
CV の実験結果ディレクトリが存在しません: $RUNS_DIR
gate condition を確認するための CV 結果が必要です。

定義された gate condition:
$gate_lines
EOF
  exit 2
fi

# CV run の存在確認（phase=cv のタグを持つ run を探す）
cv_runs_found=false
for run_file in "$RUNS_DIR"/*.json; do
  [ -f "$run_file" ] || continue
  phase=$(jq -r '.tags.phase // .phase // ""' "$run_file" 2>/dev/null || echo "")
  if [ "$phase" = "cv" ] || [ "$phase" = "cross_validation" ]; then
    cv_runs_found=true
    break
  fi
done

if [ "$cv_runs_found" = false ]; then
  cat >&2 <<EOF
[SDD Hook] holdout 実行がブロックされました。
CV phase の実験結果が見つかりません。
holdout 評価の前に CV で gate condition を達成する必要があります。

定義された gate condition:
$gate_lines
EOF
  exit 2
fi

# gate の数値チェック（02_METRICS.md から閾値抽出、CV 結果と比較）
# メトリクス名と閾値を抽出（例: "accuracy >= 0.85", "AUC > 0.80"）
gate_met=true
while IFS= read -r line; do
  # パターン: metric_name >= threshold or metric_name > threshold
  metric=$(echo "$line" | grep -oE '[a-zA-Z_]+\s*[><=]+\s*[0-9.]+' | head -1)
  [ -z "$metric" ] && continue

  metric_name=$(echo "$metric" | grep -oE '^[a-zA-Z_]+')
  threshold=$(echo "$metric" | grep -oE '[0-9.]+$')
  [ -z "$metric_name" ] || [ -z "$threshold" ] && continue

  # CV runs から該当メトリクスの最良値を取得
  best_value=""
  for run_file in "$RUNS_DIR"/*.json; do
    [ -f "$run_file" ] || continue
    phase=$(jq -r '.tags.phase // .phase // ""' "$run_file" 2>/dev/null || echo "")
    [ "$phase" = "cv" ] || [ "$phase" = "cross_validation" ] || continue

    value=$(jq -r ".metrics.${metric_name} // .metrics.\"mean_${metric_name}\" // empty" "$run_file" 2>/dev/null || echo "")
    [ -z "$value" ] && continue

    if [ -z "$best_value" ]; then
      best_value="$value"
    else
      # 大きい方を採用（awk で比較）
      best_value=$(awk "BEGIN {print ($value > $best_value) ? $value : $best_value}")
    fi
  done

  if [ -z "$best_value" ]; then
    echo "[SDD Hook] WARNING: メトリクス '$metric_name' の CV 結果が見つかりません。" >&2
    continue
  fi

  # 閾値比較
  met=$(awk "BEGIN {print ($best_value >= $threshold) ? 1 : 0}")
  if [ "$met" -eq 0 ]; then
    echo "[SDD Hook] GATE 未達成: $metric_name = $best_value (閾値: >= $threshold)" >&2
    gate_met=false
  fi
done <<<"$gate_lines"

if [ "$gate_met" = false ]; then
  cat >&2 <<EOF

[SDD Hook] holdout 実行がブロックされました。
上記の gate condition が未達成です。
CV の結果を改善してから holdout 評価を実行してください。
EOF
  exit 2
fi

echo "[SDD Hook] INFO: gate condition 確認済み。holdout を許可します。" >&2
exit 0
