#!/bin/zsh
# launchd に worklog の観測（毎分）と書き込み（15分ごと）を登録・解除する。
# パスはひな形に直接書かず、ここでその PC の値を埋め込む。
set -euo pipefail

WORKLOG_DIR="$(cd "$(dirname "$0")" && pwd)"
AGENTS_DIR="$HOME/Library/LaunchAgents"
STATE_DIR="$HOME/.local/state/worklog"
LABELS=(local.worklog.sample local.worklog.sync)
DOMAIN="gui/$(id -u)"

case "${1:-}" in
  install)
    mkdir -p "$AGENTS_DIR" "$STATE_DIR"
    for label in $LABELS; do
      dest="$AGENTS_DIR/$label.plist"
      # 再登録に備えて外す。未登録なら失敗するので結果は見ない。
      launchctl bootout "$DOMAIN/$label" 2>/dev/null || true
      sed -e "s|__HOME__|$HOME|g" -e "s|__WORKLOG__|$WORKLOG_DIR|g" \
        "$WORKLOG_DIR/launchd/$label.plist.template" > "$dest"
      plutil -lint "$dest"
      launchctl bootstrap "$DOMAIN" "$dest"
      echo "installed: $label"
    done
    ;;
  uninstall)
    for label in $LABELS; do
      launchctl bootout "$DOMAIN/$label" 2>/dev/null || true
      rm -f "$AGENTS_DIR/$label.plist"
      echo "removed: $label"
    done
    ;;
  *)
    echo "usage: $0 install|uninstall" >&2
    exit 2
    ;;
esac
