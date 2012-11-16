#!/bin/sh
# boom - http://zachholman.com/boom/
DIR="$( cd -P "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
read -p "Press [ENTER] when Xcode has been installed from the App Store (or break now to cancel.)"
read -p "Press [ENTER] when Command Line Tools has been installed from within Xcode (or break now to cancel.)"
curl -L https://get.rvm.io | bash -s stable --rails
source ~/.rvm/scripts/rvm
sudo gem install boom
ln -s $DIR/boom/boom.conf ~/.boom.conf
ln -s $DIR/boom/boom ~/.boom
