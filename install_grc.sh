#!/bin/sh
DIR="$( cd -P "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd /tmp
curl -O http://kassiopeia.juls.savba.sk/~garabik/software/grc/grc_1.9.orig.tar.gz
tar -xzvf grc_1.9.orig.tar.gz
cd grc-1.9
sudo ./install.sh
sudo rm /usr/share/grc/conf.ping
sudo ln -s $DIR/grc/conf.ping /usr/share/grc/conf.ping
