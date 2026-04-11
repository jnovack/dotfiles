#!/bin/sh
DIR="$( cd -P "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd /tmp
curl -LO https://github.com/garabik/grc/archive/v1.11.3.tar.gz
tar -xzvf v1.11.3.tar.gz
cd grc-1.11.3
sudo ./install.sh
sudo rm /usr/local/share/grc/conf.ping
sudo curl --output /usr/local/share/grc/conf.ping https://raw.githubusercontent.com/jnovack/dotfiles/master/grc/conf.ping 
