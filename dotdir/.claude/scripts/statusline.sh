#!/usr/bin/env bash
# Claude Code Statusline
# 3-line display: session info, 5h usage, 7d usage

set -euo pipefail

input=$(cat)

# ── Colors ──
GREEN="\033[38;2;151;201;195m"
YELLOW="\033[38;2;229;192;123m"
RED="\033[38;2;224;108;117m"
GRAY="\033[38;2;74;88;92m"
RESET="\033[0m"

color_for_pct() {
  local pct=$1
  if (( pct >= 80 )); then
    printf '%s' "$RED"
  elif (( pct >= 50 )); then
    printf '%s' "$YELLOW"
  else
    printf '%s' "$GREEN"
  fi
}

# ── Progress bar (10 segments) ──
progress_bar() {
  local pct=$1
  local filled=$(( pct / 10 ))
  local empty=$(( 10 - filled ))
  local color
  color=$(color_for_pct "$pct")
  local bar=""
  for ((i=0; i<filled; i++)); do bar+="▰"; done
  for ((i=0; i<empty; i++)); do bar+="▱"; done
  printf '%b%s%b' "$color" "$bar" "$RESET"
}

# ── Line 1: Session info ──
model=$(echo "$input" | jq -r '.model.display_name // ""')
used_pct=$(echo "$input" | jq -r '.context_window.used_percentage // empty')
lines_added=$(echo "$input" | jq -r '.cost.total_lines_added // 0')
lines_removed=$(echo "$input" | jq -r '.cost.total_lines_removed // 0')
cwd=$(echo "$input" | jq -r '.workspace.current_dir // ""')

# Context percentage (integer)
ctx_int=0
if [ -n "$used_pct" ]; then
  printf -v ctx_int "%.0f" "$used_pct" 2>/dev/null || ctx_int="${used_pct%%.*}"
fi
ctx_color=$(color_for_pct "$ctx_int")

# Git branch
git_branch=""
if [ -n "$cwd" ] && git -C "$cwd" rev-parse --git-dir > /dev/null 2>&1; then
  git_branch=$(git -C "$cwd" symbolic-ref --short HEAD 2>/dev/null || git -C "$cwd" rev-parse --short HEAD 2>/dev/null)
fi

sep="${GRAY} │ ${RESET}"

line1="🤖 ${model}${sep}${ctx_color}📊 ${ctx_int}%${RESET}${sep}✏️ +${lines_added}/-${lines_removed}"
if [ -n "$git_branch" ]; then
  line1+="${sep}🔀 ${git_branch}"
fi

# ── Usage API (OAuth, cached 60s) ──
CACHE_FILE="/tmp/claude-usage-cache.json"
CACHE_TTL=360

fetch_usage() {
  # Get OAuth token from macOS Keychain
  local token
  token=$(security find-generic-password -s "Claude Code-credentials" -w 2>/dev/null || true)
  if [ -z "$token" ]; then
    return 1
  fi

  # Token is stored as JSON with nested structure
  local access_token
  access_token=$(echo "$token" | jq -r '.claudeAiOauth.accessToken // .accessToken // .access_token // empty' 2>/dev/null || true)
  if [ -z "$access_token" ]; then
    return 1
  fi

  local response
  response=$(curl -sf --max-time 5 \
    -H "Authorization: Bearer ${access_token}" \
    -H "anthropic-beta: oauth-2025-04-20" \
    "https://api.anthropic.com/api/oauth/usage" 2>/dev/null) || return 1

  # Write cache with timestamp
  local now
  now=$(date +%s)
  echo "$response" | jq --arg ts "$now" '. + {cached_at: ($ts | tonumber)}' > "$CACHE_FILE" 2>/dev/null
  echo "$response"
}

get_usage() {
  local now
  now=$(date +%s)

  # Check cache
  if [ -f "$CACHE_FILE" ]; then
    local cached_at
    cached_at=$(jq -r '.cached_at // 0' "$CACHE_FILE" 2>/dev/null || echo "0")
    local age=$(( now - cached_at ))
    if (( age < CACHE_TTL )); then
      jq -r 'del(.cached_at)' "$CACHE_FILE" 2>/dev/null
      return 0
    fi
  fi

  fetch_usage
}

# Convert ISO 8601 to epoch seconds (macOS compatible)
iso_to_epoch() {
  local iso_time=$1
  local stripped="${iso_time%%.*}"
  TZ=UTC date -j -f "%Y-%m-%dT%H:%M:%S" "$stripped" +%s 2>/dev/null || echo ""
}

# Format reset time for 5h window: "Resets 5pm (Asia/Tokyo)"
format_5h_reset() {
  local iso_time=$1
  local epoch
  epoch=$(iso_to_epoch "$iso_time")
  [ -z "$epoch" ] && return
  LC_ALL=en_US.UTF-8 TZ="Asia/Tokyo" date -r "$epoch" +"Resets %-l%p (Asia/Tokyo)" 2>/dev/null | sed 's/AM/am/;s/PM/pm/'
}

# Format reset time for 7d window: "Resets Mar 6 at 12pm (Asia/Tokyo)"
format_7d_reset() {
  local iso_time=$1
  local epoch
  epoch=$(iso_to_epoch "$iso_time")
  [ -z "$epoch" ] && return
  LC_ALL=en_US.UTF-8 TZ="Asia/Tokyo" date -r "$epoch" +"Resets %b %-d at %-l%p (Asia/Tokyo)" 2>/dev/null | sed 's/AM/am/;s/PM/pm/'
}

line2=""
line3=""

usage_json=$(get_usage 2>/dev/null || true)

if [ -n "$usage_json" ]; then
  five_util=$(echo "$usage_json" | jq -r '.five_hour.utilization // empty' 2>/dev/null)
  five_reset=$(echo "$usage_json" | jq -r '.five_hour.resets_at // empty' 2>/dev/null)
  seven_util=$(echo "$usage_json" | jq -r '.seven_day.utilization // empty' 2>/dev/null)
  seven_reset=$(echo "$usage_json" | jq -r '.seven_day.resets_at // empty' 2>/dev/null)

  if [ -n "$five_util" ]; then
    printf -v five_int "%.0f" "$five_util" 2>/dev/null || five_int="${five_util%%.*}"
    five_color=$(color_for_pct "$five_int")
    five_bar=$(progress_bar "$five_int")
    five_reset_str=""
    if [ -n "$five_reset" ]; then
      five_reset_str=$(format_5h_reset "$five_reset")
    fi
    line2="${five_color}⏰ 5h${RESET}  ${five_bar}  ${five_color}${five_int}%${RESET}"
    if [ -n "$five_reset_str" ]; then
      line2+="  ${GRAY}${five_reset_str}${RESET}"
    fi
  fi

  if [ -n "$seven_util" ]; then
    printf -v seven_int "%.0f" "$seven_util" 2>/dev/null || seven_int="${seven_util%%.*}"
    seven_color=$(color_for_pct "$seven_int")
    seven_bar=$(progress_bar "$seven_int")
    seven_reset_str=""
    if [ -n "$seven_reset" ]; then
      seven_reset_str=$(format_7d_reset "$seven_reset")
    fi
    line3="${seven_color}📅 7d${RESET}  ${seven_bar}  ${seven_color}${seven_int}%${RESET}"
    if [ -n "$seven_reset_str" ]; then
      line3+="  ${GRAY}${seven_reset_str}${RESET}"
    fi
  fi
fi

# ── Output ──
printf '%b' "$line1"
if [ -n "$line2" ]; then
  printf '\n%b' "$line2"
fi
if [ -n "$line3" ]; then
  printf '\n%b' "$line3"
fi
