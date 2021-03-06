#!/bin/sh
DIR="$( cd -P "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
sudo mkdir /usr/local/bin/
sudo ln -s $DIR/bash/ssh /usr/local/bin/
sudo ln -s $DIR/bash/ssh-copy-id /usr/local/bin/

cat $DIR/bash/profile >> ~/.profile
echo "source $DIR/bash/gitprompt.sh" >> ~/.profile
echo "source $DIR/bash/colorize.sh" >> ~/.profile
cat $DIR/bash/complete.sh >> ~/.profile
cat $DIR/bash/aliases >> ~/.profile
