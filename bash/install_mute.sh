#!/bin/bash

echo "#!/bin/bash" > /tmp/mute-on.sh
echo "osascript -e 'set volume with output muted'" >> /tmp/mute-on.sh

echo "#!/bin/bash" > /tmp/mute-off.sh
echo "osascript -e 'set volume without output muted'" >> /tmp/mute-off.sh

chmod +x /tmp/mute-on.sh
chmod +x /tmp/mute-off.sh

sudo mv /tmp/mute-on.sh /usr/local/bin/
sudo mv /tmp/mute-off.sh /usr/local/bin/

sudo chown root /usr/local/bin/mute-on.sh
sudo chown root /usr/local/bin/mute-off.sh

echo "Before Installation:"
echo -e "LoginHook: "
sudo defaults read com.apple.loginwindow LoginHook
echo -e "LogoutHook: "
sudo defaults read com.apple.loginwindow LogoutHook

echo "Installing files...:"
sudo defaults write com.apple.loginwindow LogoutHook /usr/local/bin/mute-on.sh
sudo defaults write com.apple.loginwindow LoginHook /usr/local/bin/mute-off.sh

echo "After Installation:"
echo -e "LoginHook: "
sudo defaults read com.apple.loginwindow LoginHook
echo -e "LogoutHook: "
sudo defaults read com.apple.loginwindow LogoutHook


