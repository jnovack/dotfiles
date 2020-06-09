#!/bin/sh
DIR="$( cd -P "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd /tmp
curl -O https://github.com/garabik/grc/archive/v1.11.3.tar.gz
tar -xzvf grc-1.11.3.tar.gz
cd grc-1.11.3
sudo ./install.sh
sudo rm /usr/share/grc/conf.ping
sudo ln -s $DIR/grc/conf.ping /usr/share/grc/conf.ping
