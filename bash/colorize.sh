#!/bin/sh
# /etc/profile.d/colorize.sh

##########################################################################
# Bash Coloring and Prompt Changing
# -- 10/26/01 by Justin J. Novack
# Purpose: Changes Root Prompt to be Red
# Documentation: Copy this file to /etc/profile.d/ and chmod +x

txtblk='\[\e[0;30m\]' # Black - Regular
txtred='\[\e[0;31m\]' # Red
txtgrn='\[\e[0;32m\]' # Green
txtylw='\[\e[0;33m\]' # Yellow
txtblu='\[\e[0;34m\]' # Blue
txtpur='\[\e[0;35m\]' # Purple
txtcyn='\[\e[0;36m\]' # Cyan
txtwht='\[\e[0;37m\]' # White
bldblk='\[\e[1;30m\]' # Black - Bold
bldred='\[\e[1;31m\]' # Red
bldgrn='\[\e[1;32m\]' # Green
bldylw='\[\e[1;33m\]' # Yellow
bldblu='\[\e[1;34m\]' # Blue
bldpur='\[\e[1;35m\]' # Purple
bldcyn='\[\e[1;36m\]' # Cyan
bldwht='\[\e[1;37m\]' # White
undblk='\[\e[4;30m\]' # Black - Underline
undred='\[\e[4;31m\]' # Red
undgrn='\[\e[4;32m\]' # Green
undylw='\[\e[4;33m\]' # Yellow
undblu='\[\e[4;34m\]' # Blue
undpur='\[\e[4;35m\]' # Purple
undcyn='\[\e[4;36m\]' # Cyan
undwht='\[\e[4;37m\]' # White
bakblk='\[\e[40m\]'   # Black - Background
bakred='\[\e[41m\]'   # Red
bakgrn='\[\e[42m\]'   # Green
bakylw='\[\e[43m\]'   # Yellow
bakblu='\[\e[44m\]'   # Blue
bakpur='\[\e[45m\]'   # Purple
bakcyn='\[\e[46m\]'   # Cyan
bakwht='\[\e[47m\]'   # White
txtrst='\[\e[0m\]'   	# Text Reset

# Set Prompt
# \w = Full Path           eg.  /usr/www/html
# \W = Current directory   eg.  html
if [ `id -u` = 0 ]; then
	PS1="\`if [ \$? != 0 ]; then echo -e \"$bldred ಠ╭╮ಠ $txtred( return value:$bldred $? $txtred)\"; printf '\n'; fi; \`$txtwht[$txtpur\D{%b %d} $bldpur\A$txtwht] $bldred[$txtred\u@$bldred\h $txtgrn\w$bldred]$txtrst\\$ "
else
	PS1="\`if [ \$? != 0 ]; then echo -e \"$bldred ಠ╭╮ಠ $txtred( return value:$bldred $? $txtred)\"; printf '\n'; fi; \`$txtwht[$txtpur\D{%b %d} $bldpur\A$txtwht] $bldblu[$txtblu\u@$bldblu\h $txtgrn\w$bldblu]$txtrst\\$ "
fi
