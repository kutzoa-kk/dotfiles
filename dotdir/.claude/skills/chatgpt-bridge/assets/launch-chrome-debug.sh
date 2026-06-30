#!/usr/bin/env bash
# launch-chrome-debug.sh — chatgpt-bridge skill 用に remote-debugging Chrome を冪等起動する。
# Chrome 136+ はデフォルト profile での remote-debugging を無効化するため、専用 --user-data-dir を使う。
set -euo pipefail

PORT="${CHATGPT_BRIDGE_PORT:-9222}"
PROFILE_DIR="${CHATGPT_BRIDGE_PROFILE:-$HOME/.cache/chatgpt-bridge-chrome}"
CHROME_BIN="${CHATGPT_BRIDGE_CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
HEALTH_URL="http://127.0.0.1:${PORT}/json/version"

# 既に up なら冪等にスキップ
if curl -sf "$HEALTH_URL" >/dev/null 2>&1; then
  echo "[chatgpt-bridge] Chrome debug endpoint already up on :${PORT}"
  exit 0
fi

if [ ! -x "$CHROME_BIN" ]; then
  echo "[chatgpt-bridge] ERROR: Chrome binary not found at: $CHROME_BIN" >&2
  echo "[chatgpt-bridge] Set CHATGPT_BRIDGE_CHROME to your Chrome path." >&2
  exit 1
fi

mkdir -p "$PROFILE_DIR"

echo "[chatgpt-bridge] launching Chrome (port ${PORT}, profile ${PROFILE_DIR})"
"$CHROME_BIN" \
  --remote-debugging-port="$PORT" \
  --user-data-dir="$PROFILE_DIR" \
  --no-first-run \
  --no-default-browser-check \
  >/dev/null 2>&1 &

# 起動待ち（最大 ~10s）
for _ in $(seq 1 20); do
  if curl -sf "$HEALTH_URL" >/dev/null 2>&1; then
    echo "[chatgpt-bridge] ready on :${PORT}"
    echo "[chatgpt-bridge] 初回は開いた Chrome で https://chatgpt.com にログインしてください（profile に永続）。"
    exit 0
  fi
  sleep 0.5
done

echo "[chatgpt-bridge] ERROR: endpoint did not come up within timeout on :${PORT}" >&2
exit 1
