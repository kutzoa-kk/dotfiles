#!/usr/bin/env bash
# llm-worker.sh — Codex/agy 統一ヘッドレスラッパー（Opus Fable 級化基盤 L1）
# 使い方: echo "プロンプト" | llm-worker.sh <codex|agy|both> [--role reviewer|researcher] [--timeout SEC] [--cd DIR]
# 出力: worker ごとに「===== <worker> (Ns) =====」ヘッダー + 本文。障害時は FAILED ヘッダー。
# 終了コード: 0=少なくとも1つ成功 / 1=全 worker 失敗 / 2=引数エラー
set -u

usage() {
  echo "usage: echo PROMPT | llm-worker.sh <codex|agy|both> [--role reviewer|researcher] [--timeout SEC] [--cd DIR]" >&2
  exit 2
}

WORKER="${1:-}"
[ $# -gt 0 ] && shift
case "$WORKER" in codex|agy|both) ;; *) usage ;; esac

ROLE=""
TIMEOUT=300
WORKDIR="$PWD"
while [ $# -gt 0 ]; do
  case "$1" in
    --role)    ROLE="${2:?--role に値がありません}"; shift 2 ;;
    --timeout) TIMEOUT="${2:?--timeout に値がありません}"; shift 2 ;;
    --cd)      WORKDIR="${2:?--cd に値がありません}"; shift 2 ;;
    *) usage ;;
  esac
done

PROMPT="$(cat)"
[ -n "$PROMPT" ] || { echo "error: stdin からプロンプトを渡してください" >&2; exit 2; }

case "$ROLE" in
  reviewer) PROMPT="あなたは敵対的レビュアーです。対象を反証する視点で検証し、問題点を重大度順に根拠付きで指摘してください。反証できなければ「反証失敗」と明記してください。

$PROMPT" ;;
  researcher) PROMPT="あなたは調査担当です。事実と推測を明確に分け、事実には根拠を示し、不確かな点は不確かと明記してください。

$PROMPT" ;;
  "") ;;
  *) usage ;;
esac

LOG_DIR="$HOME/.claude/logs/llm-worker"
mkdir -p "$LOG_DIR"
STAMP="$(date +%Y%m%d-%H%M%S)-$$"

run_one() {
  local name="$1" out rc start end
  start=$(date +%s)
  case "$name" in
    codex) out=$(cd "$WORKDIR" && timeout "$TIMEOUT" codex exec --sandbox read-only "$PROMPT" 2>"$LOG_DIR/$STAMP-codex.err") ;;
    agy)   out=$(cd "$WORKDIR" && timeout "$TIMEOUT" agy --print "$PROMPT" --model "Gemini 3.1 Pro (High)" 2>"$LOG_DIR/$STAMP-agy.err") ;;
  esac
  rc=$?
  end=$(date +%s)
  printf '%s' "$out" > "$LOG_DIR/$STAMP-$name.out"
  if [ "$rc" -eq 0 ] && [ -n "$out" ]; then
    printf '===== %s (%ss) =====\n%s\n' "$name" "$((end - start))" "$out"
    return 0
  fi
  printf '===== %s FAILED (rc=%s, %ss) — stderr: %s =====\n' "$name" "$rc" "$((end - start))" "$LOG_DIR/$STAMP-$name.err"
  return 1
}

case "$WORKER" in
  codex) run_one codex; exit $? ;;
  agy)   run_one agy; exit $? ;;
  both)
    TMP_C="$(mktemp)" TMP_A="$(mktemp)"
    run_one codex >"$TMP_C" 2>&1 & PID_C=$!
    run_one agy   >"$TMP_A" 2>&1 & PID_A=$!
    RC_C=0; RC_A=0
    wait "$PID_C" || RC_C=1
    wait "$PID_A" || RC_A=1
    cat "$TMP_C" "$TMP_A"
    rm -f "$TMP_C" "$TMP_A"
    if [ "$RC_C" -ne 0 ] && [ "$RC_A" -ne 0 ]; then exit 1; fi
    exit 0
    ;;
esac
