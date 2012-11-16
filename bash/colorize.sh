#!/bin/sh
# /etc/profile.d/colorize.sh

##########################################################################
# Bash Coloring and Prompt Changing
# -- 10/26/01 by Justin J. Novack
# Purpose: Changes Root Prompt to be Red
# Documentation: Copy this file to /etc/profile.d/ and chmod +x

txtblk='\033[0;30m' # Black - Regular
txtred='\033[0;31m' # Red
txtgrn='\033[0;32m' # Green
txtylw='\033[0;33m' # Yellow
txtblu='\033[0;34m' # Blue
txtpur='\033[0;35m' # Purple
txtcyn='\033[0;36m' # Cyan
txtwht='\033[0;37m' # White
bldblk='\033[1;30m' # Black - Bold
bldred='\033[1;31m' # Red
bldgrn='\033[1;32m' # Green
bldylw='\033[1;33m' # Yellow
bldblu='\033[1;34m' # Blue
bldpur='\033[1;35m' # Purple
bldcyn='\033[1;36m' # Cyan
bldwht='\033[1;37m' # White
undblk='\033[4;30m' # Black - Underline
undred='\033[4;31m' # Red
undgrn='\033[4;32m' # Green
undylw='\033[4;33m' # Yellow
undblu='\033[4;34m' # Blue
undpur='\033[4;35m' # Purple
undcyn='\033[4;36m' # Cyan
undwht='\033[4;37m' # White
bakblk='\033[40m'   # Black - Background
bakred='\033[41m'   # Red
bakgrn='\033[42m'   # Green
bakylw='\033[43m'   # Yellow
bakblu='\033[44m'   # Blue
bakpur='\033[45m'   # Purple
bakcyn='\033[46m'   # Cyan
bakwht='\033[47m'   # White
txtrst='\033[m'   	# Text Reset

# Set Prompt
# \w = Full Path           eg.  /usr/www/html
# \W = Current directory   eg.  html
if [ `id -u` = 0 ]; then
	PS1="$txtwht[$txtpur\D{%b %d} $bldpur\A$txtwht] $bldred[$txtred\u@$bldred\h $txtgrn\w$bldred]$txtrst\\$ "
else
	PS1="$txtwht[$txtpur\D{%b %d} $bldpur\A$txtwht] $bldblu[$txtblu\u@$bldblu\h $txtgrn\w$bldblu]$txtrst\\$ "
fi
