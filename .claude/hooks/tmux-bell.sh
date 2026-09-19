#!/bin/bash
# Ring the terminal bell so tmux flags the pane/window as needing attention.
#
# Wired to the Stop and Notification hooks: both fire at the moments Claude has
# stopped working and the prompt is waiting for you. tmux turns the BEL into its
# configured alert (monitor-bell / visual-bell / audible) — the "boop" you get
# while looking at another window.
#
# The bell has to land on the Claude pane's tty. The hook runner captures our
# stdout/stderr and may not hand us a controlling terminal, so prefer resolving
# the pane tty via tmux ($TMUX_PANE is inherited) and fall back to /dev/tty.
# No-op when not running inside tmux.

[ -n "$TMUX" ] || exit 0

tmux_bin=$(command -v tmux || true)
for c in /opt/homebrew/bin/tmux /usr/local/bin/tmux /usr/bin/tmux; do
  [ -n "$tmux_bin" ] && break
  [ -x "$c" ] && tmux_bin=$c
done

pane_tty=""
if [ -n "$tmux_bin" ] && [ -n "$TMUX_PANE" ]; then
  pane_tty=$("$tmux_bin" display -p -t "$TMUX_PANE" '#{pane_tty}' 2>/dev/null)
fi

if [ -n "$pane_tty" ] && [ -w "$pane_tty" ]; then
  printf '\a' > "$pane_tty"
else
  printf '\a' > /dev/tty 2>/dev/null || true
fi
