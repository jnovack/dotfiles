#!/bin/bash
# /etc/profile.d/gitprompt.sh

[[ "$-" != *i* ]] && return

##########################################################################
# Bash Coloring and Prompt Changing for git
# -- 09/07/11 by Justin J. Novack
#
# Purpose: Prepends the following line above the command prompt.
# ±{master}  Staged:   0 | UnStaged:   0 | Untracked:   3

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


in_git_repo() {
  # quickly traverse up (up to 10 levels) and look for a .git directory
  dir=${1:-.}
  count=`expr 0$2 + 1`

  if [[ $count == "10" ]]; then return 1; fi
  if [[ -d $dir/.git ]]; then return 0; fi

  in_git_repo $dir/.. $count
}

git_status() {

in_git_repo;

if [ $? == 1 ]; then return; fi

status=$(git status --porcelain 2> /dev/null)

if [ $? == 0 ]; then

    branch=$(git status --branch --short 2>/dev/null|head -1|cut -f2 -d' '|awk -v RS="..." '{print $1}'|head -1)
    isdirty=$(git status 2>/dev/null| grep "branch is ahead" | wc -l)
    if [ $isdirty -gt 0 ]; then
        dirty="${bldcyn}"
    else
        dirty="${txtcyn}"
  fi

    color="${bldmag}±${txtblu}{${dirty}${branch}${txtblu}}${txtrst} "

    #  untracked files
    if $(echo "$status" | grep '?? ' &> /dev/null); then
        line0="${txtwht} | ${txtred}Untracked:   ${bldred}`git status --porcelain 2>/dev/null | grep '^?? ' | wc -l`"
    else
        line0=""
    fi

    #  ready to commit / in the index
    if $(echo "$status" | grep '^[MARCD].' &> /dev/null); then
        line1="${txtgrn}Staged:   ${bldgrn}`git status --porcelain 2>/dev/null | grep '^[MARCD].' | wc -l`"
    else
        line1="${bldblk}Staged:   0"
    fi

    #  in workspace / not in the index
    if $(echo "$status" | grep '^.[MADT].' &> /dev/null); then
        line2="${txtwht} | ${txtylw}UnStaged:   ${bldylw}`git status --porcelain 2>/dev/null | grep '^.[MADT].' | wc -l`"
    else
        line2="${txtwht} | ${bldblk}UnStaged:   0"
    fi

  if [[ "$OSTYPE" =~ ^darwin ]]; then
      echo "$color $line1$line2$line3$line0"
  else
      echo -e "$color $line1$line2$line3$line0"
  fi

fi
}

export PROMPT_COMMAND='git_status'
