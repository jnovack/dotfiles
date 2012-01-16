#!/bin/bash

cd ~/Source/scripts/
git remote update &> /dev/null

status=$(git status 2> /dev/null | egrep "behind|ahead")

if [ "$status" != "" ]
then
	/usr/local/bin/growlnotify -t "~/Source/scripts" --image ~/git.png -m "$status"
fi
