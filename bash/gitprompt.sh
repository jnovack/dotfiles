#!/bin/bash
# gitprompt.sh

##########################################################################
# Bash Coloring and Prompt Changing for git
# -- 09/07/11 by Justin J. Novack
#
# Documentation: Add the next line to .bashrc
#   export PROMPT_COMMAND="sh ~/gitprompt.sh"
# Purpose: Prepends the following line above the command prompt.
# GIT Status: 	Added:        0 | Updated:        0 | Deleted:        0

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
unkblk='\033[4;30m' # Black - Underline
undred='\033[4;31m' # Red
undgrn='\033[4;32m' # Green
undylw='\033[4;33m' # Yellow
undblu='\033[4;34m' # Blue
undpur='\033[4;35m' # Purple
undcyn='\033[4;36m' # Cyan
undwht='\033[4;37m' # White
bakblk='\033[40m'   # Black - Background
bakred='\033[41m'   # Red
badgrn='\033[42m'   # Green
bakylw='\033[43m'   # Yellow
bakblu='\033[44m'   # Blue
bakpur='\033[45m'   # Purple
bakcyn='\033[46m'   # Cyan
bakwht='\033[47m'   # White
txtrst='\033[m'   	# Text Reset


status=$(git status --porcelain 2> /dev/null)

if [ $? == 0 ]; then

	branch=$(git status 2>/dev/null| grep "On branch" | cut -f4 -d' ')

	color="${txtcyn}{${bldcyn}$branch${txtcyn}} ${txtrst}"

	#  untracked files
	if $(echo "$status" | grep '?? ' &> /dev/null); then
		line0="${txtwht} | ${txtred}Untracked: ${bldred}`git status --porcelain 2>/dev/null | grep '^?? ' | wc -l`"
	fi

	#  ready to commit / in the index
	if $(echo "$status" | grep '^[MARC].' &> /dev/null); then
		line1="${txtgrn}Staged: ${bldgrn}`git status --porcelain 2>/dev/null | grep '^[MARC].' | wc -l`"
	else
		line1="${bldblk}Staged:        0"
	fi

	#  in workspace / not in the index
	if $(echo "$status" | grep '^.[MAD].' &> /dev/null); then
    	line2="${txtwht} | ${txtylw}UnStaged: ${bldylw}`git status --porcelain 2>/dev/null | grep '^.[MAD].' | wc -l`"
	else
    	line2="${txtwht} | ${bldblk}UnStaged:        0"
	fi

	echo "$color	$line1$line2$line3$line0"
fi

