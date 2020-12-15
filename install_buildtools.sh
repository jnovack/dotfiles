 #!/bin/sh
AUTOCONF_VERSION=2.69
AUTOMAKE_VERSION=1.16.3
PKGCONFIG_VERSION=0.29.2

## Setup
DIR="$( cd -P "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "sudo password required."
sudo echo "thank you..."

## Install Xcode Command Line Utilities
sudo xcode-select --install

## Install autoconf
cd /tmp
curl -LO https://ftp.gnu.org/gnu/autoconf/autoconf-${AUTOCONF_VERSION}.tar.gz
tar -xzvf autoconf-${AUTOCONF_VERSION}.tar.gz
cd autoconf-${AUTOCONF_VERSION}/
./configure
make
sudo make install
cd ../
rm -rf autoconf-${AUTOCONF_VERSION}*

## Install automake
cd /tmp
curl -LO https://ftp.gnu.org/gnu/automake/automake-${AUTOMAKE_VERSION}.tar.gz
tar -xzvf automake-${AUTOMAKE_VERSION}.tar.gz
cd automake-${AUTOMAKE_VERSION}/
./configure
make
sudo make install
cd ../
rm -rf automake-${AUTOMAKE_VERSION}*

## Install pkg-config
cd /tmp
curl -LO https://pkg-config.freedesktop.org/releases/pkg-config-${PKGCONFIG_VERSION}.tar.gz
tar -xzvf pkg-config-${PKGCONFIG_VERSION}.tar.gz
cd pkg-config-${PKGCONFIG_VERSION}/
LDFLAGS="-framework CoreFoundation -framework Carbon" ./configure --with-internal-glib
make
sudo make install
cd ../
rm -rf pkg-config-${PKGCONFIG_VERSION}*
