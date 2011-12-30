#!/bin/sh
git config --global alias.sum "log --graph --decorate --pretty=oneline --color --abbrev-commit --all"
git config --global alias.history "log --pretty=format:\"%h %ad | %s%d [%an]\" --graph --date=short --color --all"

