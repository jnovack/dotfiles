#!/bin/bash
# ~/bin/ssh

##########################################################################
# iTerm Background changing for ssh connected hosts
# -- 09/07/11 by Justin J. Novack
#
# Documenation:
#   cp $this ~/bin/ssh
#   chmod +x ~/bin/ssh
#
# Purpose:
#   SSH with host name and IP address in background (only in iTerm.app)
#
# Prerequisites:
#   ImageMagick in any form.  I prefer the custom cactuslab.com build
#   (http://cactuslab.com/imagemagick/assets/ImageMagick6.8.5-3.pkg.zip)
#   as it does not require homebrew or macports.

# First, check to see if we have the correct terminal!
if [ "$(tty)" == 'not a tty' ] || [ "$TERM_PROGRAM" != "iTerm.app" ] ; then
	/usr/bin/ssh "$@"
	exit $?
fi

function __calculate_iterm_window_dimensions {
	local size=( $(osascript -e "tell application \"iTerm\"
		get bounds of window 1
		end tell" | tr ',' ' ') )

		local x1=${size[0]} y1=${size[1]} x2=${size[2]} y2=${size[3]}
		# 15px - scrollbar width
		local w=$(( $x2 - $x1 - 15 ))
		# 44px - titlebar + tabs height
		local h=$(( $y2 - $y1 - 44))
		echo "${w}x${h}"
}

# Console dimensions
DIMENSIONS=$(__calculate_iterm_window_dimensions)
BG_COLOR="#000000"       # Background color
GRAVITY="NorthEast"      # Text gravity (NorthWest, North, NorthEast, West, Center, East, SouthWest, South, SouthEast)
OFFSET1="20,10"          # Text offset
OFFSET2="20,70"          # Text offset
OFFSET3="20,100"         # Text offset
FONT_SIZE1="50"          # Font size in points
FONT_SIZE2="30"          # Font size in points
FONT_STYLE="Normal"      # Font style (Any, Italic, Normal, Oblique)
FONT="/System/Library/Fonts/Menlo.ttc"	# Font path
HOST=`echo $@ | sed -e "s/.*@//" -e "s/ .*//"`

# RESOLVED_HOSTNAME=`nslookup $HOST|tail -n +4|grep '^Name:'|cut -f2 -d $'\t'`
# RESOLVED_IP=`nslookup $HOST|tail -n +4|grep '^Address:'|cut -f2 -d $':'|tail -c +2`
output=`dscacheutil -q host -a name $HOST`
RESOLVED_HOSTNAME=`echo -e "$output"|grep '^name:'|awk '{print $2}'`
RESOLVED_IP=`echo -e "$output"|grep '^ip_address:'|awk '{print $2}'`

# FG_COLOR is an RGBA color set (11,22,33,1.0) based on the uniqueness of the hash of the resolved IP.
#  helpful when you have multiple hosts of similar names in tabs or windows
IP_R=`echo ${RESOLVED_IP} | md5 | cut -c 1-2`
IP_G=`echo ${RESOLVED_IP} | md5 | cut -c 3-4`
IP_B=`echo ${RESOLVED_IP} | md5 | cut -c 5-6`
FG_COLOR=`echo $((0x${IP_R})),$((0x${IP_G})),$((0x${IP_B})),0.7`

function set_bg {
	local tty=$(tty)
	osascript -e "
		tell application \"iTerm\"
			repeat with theTerminal in terminals
				tell theTerminal
					try
						tell session id \"$tty\"
							set background image path to \"$1\"
						end tell
					on error errmesg number errn
					end try
				end tell
			end repeat
		end tell"
}

on_exit () {
	if [ ! -f /tmp/iTermBG.empty.png ]; then
		convert -size "$DIMENSIONS" xc:"$BG_COLOR" "/tmp/iTermBG.empty.png"
	fi
	set_bg "/tmp/iTermBG.empty.png"
	rm "/tmp/iTermBG.$$.png"
}
trap on_exit EXIT

convert \
    -size "$DIMENSIONS" xc:"$BG_COLOR" -gravity "$GRAVITY" -fill rgba\(${FG_COLOR}\) -font "$FONT" -style "$FONT_STYLE" \
    -pointsize "$FONT_SIZE1" -antialias -draw "text $OFFSET1 '${HOST}'" \
    -pointsize "$FONT_SIZE2" -antialias -draw "text $OFFSET2 '${RESOLVED_HOSTNAME:-$HOST}'" \
    -pointsize "$FONT_SIZE2" -antialias -draw "text $OFFSET3 '${RESOLVED_IP:-}'" -alpha on \
    "/tmp/iTermBG.$$.png"
set_bg "/tmp/iTermBG.$$.png"

echo -e "\033k$@\033\\"
/usr/bin/ssh "$@"
echo -e "\033k$USER@$HOSTNAME\033\\"

