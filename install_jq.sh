#!/bin/sh

/usr/bin/sudo /usr/bin/curl -Lo /usr/local/bin/jq https://github.com/stedolan/jq/releases/download/jq-1.6/jq-osx-amd64
/usr/bin/xattr -d com.apple.quarantine /usr/local/bin/jq
/bin/chmod +x /usr/local/bin/jq
curl -Lo /tmp/sha256sum.txt https://raw.githubusercontent.com/stedolan/jq/master/sig/v1.6/sha256sum.txt

