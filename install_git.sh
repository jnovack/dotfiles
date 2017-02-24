#!/bin/sh
DIR="$( cd -P "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cat $DIR/_gitconfig >> ~/.gitconfig
echo ".DS_Store" >> ~/.gitignore
git config --global core.excludesfile ~/.gitignore
echo
echo ** You must run the following commands:
echo      git config --global user.name "YOURNAME"
echo      git config --global user.email "email@add.ress"
