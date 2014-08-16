#!/bin/sh
# /etc/profile.d/colorize.sh

# If not running interactively, don't do anything
[[ "$-" != *i* ]] && return

##########################################################################
# Bash Coloring and Prompt Changing
# -- 10/26/01 by Justin J. Novack
# Purpose: Changes Root Prompt to be Red
# Purpose: Add in graphic for non-zero exits
# Documentation: Copy this file to /etc/profile.d/ and chmod +x
# ChangeLog: Mar 06, 2014 - Learned the wonders of tput

reset=$(   tput sgr0 )
bold=$(    tput bold )
under=$(   tput smul )

# Unstyled colors
black=$(   tput setaf 0 || tput AF 0 )
red=$(     tput setaf 1 || tput AF 1 )
green=$(   tput setaf 2 || tput AF 2 )
yellow=$(  tput setaf 3 || tput AF 3 )
blue=$(    tput setaf 4 || tput AF 4 )
magenta=$( tput setaf 5 || tput AF 5 )
cyan=$(    tput setaf 6 || tput AF 6 )
white=$(   tput setaf 7 || tput AF 7 )

# Background colors (use with unstyled colors)
onblk=$(   tput setab 0 || tput AB 0 )
onred=$(   tput setab 1 || tput AB 1 )
ongrn=$(   tput setab 2 || tput AB 2 )
onylw=$(   tput setab 3 || tput AB 3 )
onblu=$(   tput setab 4 || tput AB 4 )
onmag=$(   tput setab 5 || tput AB 5 )
oncyn=$(   tput setab 6 || tput AB 6 )
onwht=$(   tput setab 7 || tput AB 7 )

# Normal colors
txtblk=$reset$black
txtred=$reset$red
txtgrn=$reset$green
txtylw=$reset$yellow
txtblu=$reset$blue
txtmag=$reset$magenta
txtcyn=$reset$cyan
txtwht=$reset$white

# Bold colors
bldblk=$bold$black
bldred=$bold$red
bldgrn=$bold$green
bldylw=$bold$yellow
bldblu=$bold$blue
bldmag=$bold$magenta
bldcyn=$bold$cyan
bldwht=$bold$white

# Underline colors
undblk=$under$black
undred=$under$red
undgrn=$under$green
undylw=$under$yellow
undblu=$under$blue
undmag=$under$magenta
undcyn=$under$cyan
undwht=$under$white

# Set Prompt
# \w = Full Path           eg.  /usr/www/html
# \W = Current directory   eg.  html
#
# Sample:
#   [Jan 01 13:37] [user@hostname ~]$ true
#   [Jan 01 13:37] [user@hostname ~]$ false
#    ಠ╭╮ಠ ( return value: 1 )
#   [Jan 01 13:37] [user@hostname ~]$
#

__colorize_retval () {
  if (($1)); then
    printf "$bldred ಠ╭╮ಠ $txtred ( return value: $bldred$1$txtred )\n\r";
  fi
}

if [ `id -u` = 0 ]; then
	PS1='$(__colorize_retval "$?")'"\[$txtwht\][\[$txtmag\]\D{%b %d} \[$bldmag\]\A\[$txtwht\]] \[$txtred\][\[$bldred\]\u\[$txtred\]@\[$bldred\]\h \[$txtgrn\]\w\[$txtred\]]\[$reset\]\\# \]"
else
	PS1='$(__colorize_retval "$?")'"\[$txtwht\][\[$txtmag\]\D{%b %d} \[$bldmag\]\A\[$txtwht\]] \[$txtblu\][\[$bldblu\]\u\[$txtblu\]@\[$bldblu\]\h \[$txtgrn\]\w\[$txtblu\]]\[$reset\]\\$ \]"
fi
