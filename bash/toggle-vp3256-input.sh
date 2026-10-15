#!/bin/zsh
# Toggles the VP3256-4K (System UUID 757B5DBB-D4F0-4D6C-AC7B-D6CBA7040A60)
# between DisplayPort and USB-C via DDC/CI, so the OSD input button doesn't
# need to be reached behind the monitor. State is tracked in a file because
# m1ddc has no "get input" command to read the monitor's current source.
set -euo pipefail

M1DDC=/opt/homebrew/bin/m1ddc
DISPLAY_ID="757B5DBB-D4F0-4D6C-AC7B-D6CBA7040A60"
STATE_FILE="$HOME/.cache/vp3256-input-state"
DP_CODE=15
USBC_CODE=27

mkdir -p "$(dirname "$STATE_FILE")"

current="dp"
[[ -f "$STATE_FILE" ]] && current=$(cat "$STATE_FILE")

if [[ "$current" == "dp" ]]; then
  "$M1DDC" display "$DISPLAY_ID" set input "$USBC_CODE"
  echo "usbc" > "$STATE_FILE"
else
  "$M1DDC" display "$DISPLAY_ID" set input "$DP_CODE"
  echo "dp" > "$STATE_FILE"
fi
