#!/bin/sh
# MacVim - http://code.google.com/p/macvim/
DIR="$( cd -P "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
mkdir -p ~/.vim/
ln -s $DIR/vim/colors ~/.vim/colors
ln -s $DIR/vim/doc ~/.vim/doc
ln -s $DIR/vim/plugin ~/.vim/plugin
ln -s $DIR/vim/syntax ~/.vim/syntax
ln -s $DIR/vim/_vimrc ~/.vimrc
