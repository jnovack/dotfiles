#!/bin/sh
# boom - http://zachholman.com/boom/
DIR="$( cd -P "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
read -p "Press [ENTER] when Xcode has been installed from the App Store (or break now to cancel.)"
read -p "Press [ENTER] when MacPorts has been installed from www.macports.org (or break now to cancel.)"
sudo port selfupdate
sudo port upgrade outdated
sudo port install ruby
sudo gem install boom
ln -s $DIR/boom/boom.conf ~/.boom.conf
ln -s $DIR/boom/boom ~/.boom
