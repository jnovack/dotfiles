#!/bin/sh
# MacVim - http://code.google.com/p/macvim/
DIR="$( cd -P "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
mkdir -p ~/.vim/
ln -s $DIR/vim/colors colors
ln -s $DIR/vim/doc doc
ln -s $DIR/vim/plugin plugin
ln -s $DIR/vim/syntax syntax
ln -s $DIR/vim/_vimrc ~/.vimrc
