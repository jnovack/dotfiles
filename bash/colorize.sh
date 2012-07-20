#!/bin/sh
# /etc/colorize.sh

##########################################################################
# Bash Coloring and Prompt Changing
# -- 10/26/01 by Justin J. Novack
# Purpose: Changes Root Prompt to be Red

# Set Variables
Blk="\[\033[0;30m\]"	# Black 
Wht="\[\033[1;37m\]"	# White 
Red="\[\033[0;31m\]"	# Red 
LtRed="\[\033[1;31m\]"	# Light Red 
Grn="\[\033[0;32m\]"	# Green 
LtGrn="\[\033[1;32m\]"	# Light Green 
Brn="\[\033[0;33m\]"	# Brown 
LtBrn="\[\033[1;33m\]"	# Yellow 
Blu="\[\033[0;34m\]"	# Blue 
LtBlu="\[\033[1;34m\]"	# Light Blue 
Pur="\[\033[0;35m\]"	# Purple 
LtPur="\[\033[1;35m\]"	# Light Purple 
Cyn="\[\033[0;36m\]"	# Cyan 
LtCyn="\[\033[1;36m\]"	# Light Cyan
Gry="\[\033[1;30m\]"	# Gray 
LtGry="\[\033[0;37m\]"	# Light Gray 
Neu="\[\033[0m\]"	# Neutral 

# Set Prompt
# \w = Full Path           eg.  /usr/www/html
# \W = Current directory   eg.  html
if [ `id -u` = 0 ]; then
	PS1="$Wht[$Pur\D{%b %d} $LtPur\A$Wht] $LtRed[$Red\u@$LtRed\h $Grn\w$LtRed]$Neu\\$ "
else
	PS1="$Wht[$Pur\D{%b %d} $LtPur\A$Wht] $LtBlu[$Blu\u@$LtBlu\h $Grn\w$LtBlu]$Neu\\$ "
fi
