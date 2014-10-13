#!/bin/sh
# /etc/profile.d/services.sh

# If not running interactively, don't do anything
[[ "$-" != *i* ]] && return

# Export prettyprint for services function
prettyprint() { head -3 | grep -v Loaded | GREP_COLOR='1;37' grep -C 10000 --color=always -E '^|[a-zA-Z0-9_.-]+.service' | GREP_COLOR='1;32' grep -C 10000 --color=always -E '^| active|running' | GREP_COLOR='1;31' grep -C 10000 -E '^| inactive|dead|exited'; }
export -f prettyprint
