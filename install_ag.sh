#!/bin/sh
AG_VERSION=2.2.0
XZ_VERSION=5.2.5
PCRE_VERSION=8.4.4

## Setup
DIR="$( cd -P "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "sudo password required."
sudo echo "thank you..."

## Install xz
cd /tmp
curl -LO https://tukaani.org/xz/xz-${XZ_VERSION}.tar.gz
tar xvfz xz-${XZ_VERSION}.tar.gz
cd xz-${XZ_VERSION}/
./configure
make
sudo make install
cd ../
rm -rf xz-${XZ_VERSION}*

## Install pcre
cd /tmp
curl -LO https://ftp.pcre.org/pub/pcre/pcre-${PCRE_VERSION}.tar.gz
tar -xzvf pcre-${PCRE_VERSION}.tar.gz
cd pcre-${PCRE_VERSION}
./configure --prefix=/usr/local/pcre-${PCRE_VERSION}
make
sudo make install
sudo ln -s /usr/local/pcre-${PCRE_VERSION}/include/pcre.h /usr/local/include/pcre.h
cd ../
rm -rf /tmp/pcre-${PCRE_VERSION}*

## Install ag
cd /tmp
curl -LO https://github.com/ggreer/the_silver_searcher/archive/${AG_VERSION}.tar.gz
tar -xzvf ${AG_VERSION}.tar.gz
cd the_silver_searcher-${AG_VERSION}
./build.sh
make
sudo make install
cd ../
rm -rf ${AG_VERSION}.tar.gz
rm -rf /tmp/the_silver_searcher-${AG_VERSION}
