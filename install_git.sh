#!/bin/sh
DIR="$( cd -P "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cat $DIR/_gitconfig >> ~/.gitconfig
